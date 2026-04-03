from __future__ import annotations

import ast
import csv
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default to CPU-only TensorFlow for ECG inference to avoid GPU/CUDA dependency conflicts.
_ECG_TF_CPU_ONLY = os.getenv("ECG_TF_CPU_ONLY", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
if _ECG_TF_CPU_ONLY:
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

import numpy as np
from scipy import signal as scipy_signal  # type: ignore[reportMissingTypeStubs]
import tensorflow as tf  # type: ignore[reportMissingTypeStubs]
import tf_keras  # type: ignore[reportMissingTypeStubs]
from tf_keras import Model  # type: ignore[reportMissingTypeStubs]
from src.services.ai.ecg_preprocessing import preprocess_ecg


CSV_FEATURE_COLUMNS = [
    "age",
    "sex",
    "height",
    "weight",
    "validated_by_human",
    "height_missing",
    "weight_missing",
]

# Normalization constants matching preprocess_ptbxl_dataset.ipynb.
_AGE_NORM = 89.0
_HEIGHT_NORM = 209.0
_WEIGHT_NORM = 250.0


class ECGReferenceLoader:
    """Loads and caches the two clinical reference JSON files once per process."""

    def __init__(self, reports_path: Path, schema_path: Path) -> None:
        self._reports: Optional[Dict[str, Any]] = None
        self._schema: Optional[Dict[str, Any]] = None
        self._reports_path = reports_path
        self._schema_path = schema_path

    def _load_reports(self) -> Dict[str, Any]:
        if self._reports is None:
            if self._reports_path.exists():
                with self._reports_path.open("r", encoding="utf-8") as f:
                    self._reports = json.load(f)
            else:
                self._reports = {}
        return self._reports

    def _load_schema(self) -> Dict[str, Any]:
        if self._schema is None:
            if self._schema_path.exists():
                with self._schema_path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                # schema is nested under "items"
                self._schema = raw.get("items", raw)
            else:
                self._schema = {}
        return self._schema

    def get_report(self, code: str) -> Dict[str, Any]:
        return self._load_reports().get(code, {})

    def get_schema(self, code: str) -> Dict[str, Any]:
        return self._load_schema().get(code, {})

    def enrich_code(self, code: str, confidence: float) -> Dict[str, Any]:
        """Return a fully enriched dict for one SCP code."""
        report = self.get_report(code)
        schema = self.get_schema(code)

        group = schema.get("group", {}) or {}
        types = schema.get("types", {}) or {}

        category_parts = []
        if types.get("rhythm"):
            category_parts.append("Rhythm")
        if types.get("form"):
            category_parts.append("Form")
        if types.get("diagnostic"):
            category_parts.append("Diagnostic")
        category_label = " / ".join(category_parts) if category_parts else "Unknown"

        return {
            "code": code,
            "confidence": round(confidence * 100, 1),
            "name": schema.get("name") or report.get("code", code),
            "superclass": group.get("superclass"),
            "subclass": group.get("subclass"),
            "category": group.get("category") or category_label,
            "type": category_label,
            "summary": report.get("summary", ""),
            "ecg_features": report.get("ecg_features", []),
            "clinical_significance": report.get("clinical_significance", ""),
            "common_associations": report.get("common_associations", []),
            "management_hints": report.get("management_hints", []),
            "report_template": report.get("report_template", ""),
        }


class ECGInferenceEngine:
    def __init__(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        base_dir = repo_root / "AI" / "ECG" / "App" / "classification"
        ref_dir = repo_root / "AI" / "ECG" / "App"

        self.model_path = Path(
            os.getenv(
                "ECG_MODEL_PATH",
                str(
                    base_dir
                    / "ecg_inceptiontime_multimodal_asymmetric_loss_loss-min_best.h5"
                ),
            )
        )
        self.thresholds_path = Path(
            os.getenv("ECG_THRESHOLDS_PATH", str(base_dir / "per_class_thresholds.npy"))
        )
        self.train_csv_path = Path(
            os.getenv("ECG_TRAIN_CSV_PATH", str(base_dir / "ptbxl_train.csv"))
        )

        self.reference = ECGReferenceLoader(
            reports_path=Path(os.getenv("ECG_REPORTS_PATH", str(ref_dir / "reports_by_code.json"))),
            schema_path=Path(os.getenv("ECG_SCHEMA_PATH", str(ref_dir / "scp_compact_schema.json"))),
        )

        self.signal_shape = (5000, 12)
        self.cpu_only = _ECG_TF_CPU_ONLY
        self._model: Optional[Model] = None
        self._thresholds: Optional[np.ndarray] = None
        self._class_names: Optional[list[str]] = None

        if self.cpu_only:
            try:
                tf.config.set_visible_devices([], "GPU")
            except Exception:
                pass

    def _load_thresholds(self) -> Optional[np.ndarray]:
        if self._thresholds is not None:
            return self._thresholds
        if self.thresholds_path.exists():
            self._thresholds = np.load(self.thresholds_path).astype(np.float32)
        return self._thresholds

    def _load_class_names(self) -> list[str]:
        if self._class_names is not None:
            return self._class_names

        thresholds = self._load_thresholds()
        thresholds_len = int(len(thresholds)) if thresholds is not None else 0

        if self.train_csv_path.exists():
            classes: set[str] = set()
            with self.train_csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw = row.get("scp_codes")
                    if not raw:
                        continue
                    try:
                        parsed = ast.literal_eval(str(raw))
                        if isinstance(parsed, dict):
                            classes.update(str(k) for k in parsed.keys())
                    except Exception:
                        continue
            if classes:
                csv_classes = sorted(classes)
                if thresholds_len and len(csv_classes) != thresholds_len:
                    self._class_names = [f"class_{i}" for i in range(thresholds_len)]
                else:
                    self._class_names = csv_classes
                return self._class_names

        if thresholds is not None:
            self._class_names = [f"class_{i}" for i in range(len(thresholds))]
        else:
            self._class_names = ["unknown"]
        return self._class_names

    def _load_model(self) -> Model:
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            raise FileNotFoundError(f"ECG model not found at: {self.model_path}")

        try:
            model = tf_keras.models.load_model(str(self.model_path), compile=False)
        except Exception as error:
            raise ValueError(
                f"Failed to load ECG model from {self.model_path}. error={error}"
            ) from error

        if not isinstance(model, (Model, tf_keras.Model)):
            raise ValueError("Loaded ECG artifact is not a valid Keras model instance.")

        self._model = model
        return self._model

    def _parse_text_matrix(self, text: str) -> np.ndarray:
        try:
            arr = np.loadtxt(io.StringIO(text), delimiter=",")
            if arr.ndim >= 1:
                return np.asarray(arr, dtype=np.float32)
        except Exception:
            pass

        arr = np.loadtxt(io.StringIO(text))
        return np.asarray(arr, dtype=np.float32)

    def _read_wfdb_dat(self, payload: bytes) -> np.ndarray:
        # PTB-XL .dat files are 16-bit signed integers, 12 leads interleaved.
        # Each sample is multiplied by gain (1000 ADC units/mV) and offset by baseline.
        # These are the standard PTB-XL format constants from the .hea header.
        _PTBXL_GAIN = 1000.0
        _PTBXL_N_LEADS = 12

        arr = np.frombuffer(payload, dtype=np.int16).astype(np.float32)
        if arr.size == 0 or arr.size % _PTBXL_N_LEADS != 0:
            raise ValueError("Payload size is not divisible by 12 leads.")

        signal = arr.reshape(-1, _PTBXL_N_LEADS) / _PTBXL_GAIN
        return signal

    def _try_binary_matrix(self, payload: bytes) -> np.ndarray:
        try:
            return self._read_wfdb_dat(payload)
        except Exception:
            pass

        for dtype in (np.int16, np.int32, np.float32, np.float64):
            arr = np.frombuffer(payload, dtype=dtype)
            if arr.size == 0:
                continue
            arr = arr.astype(np.float32, copy=False)
            if arr.size % 12 == 0:
                return arr.reshape(-1, 12)
            if arr.size % 5000 == 0:
                return arr.reshape(5000, -1)

        raise ValueError("Unable to decode ECG binary payload into a matrix.")

    def _extract_ecg_array(self, payload: Any) -> np.ndarray:
        if isinstance(payload, np.ndarray):
            return payload.astype(np.float32)

        if isinstance(payload, dict):
            for key in [
                "signal",
                "signals",
                "ecg",
                "data",
                "values",
                "ecg_signal",
                "signal_data",
                "raw_signal",
            ]:
                if key in payload:
                    return self._extract_ecg_array(payload[key])
            raise ValueError("ECG payload dictionary does not contain signal data.")

        if isinstance(payload, list):
            return np.asarray(payload, dtype=np.float32)

        if isinstance(payload, (bytes, bytearray)):
            raw_bytes = bytes(payload)
            if not raw_bytes:
                raise ValueError("Uploaded ECG file is empty.")

            text = raw_bytes.decode("utf-8", errors="ignore").strip()
            if text:
                try:
                    return self._extract_ecg_array(json.loads(text))
                except Exception:
                    pass
                try:
                    return self._parse_text_matrix(text)
                except Exception:
                    pass

            return self._try_binary_matrix(raw_bytes)

        if isinstance(payload, str):
            try:
                as_json = json.loads(payload)
                return self._extract_ecg_array(as_json)
            except Exception:
                return self._parse_text_matrix(payload)

        raise ValueError("Unsupported ECG payload format.")

    def _to_signal_shape(self, arr: np.ndarray) -> np.ndarray:
        arr = np.asarray(arr, dtype=np.float32)

        if arr.ndim == 1:
            if arr.size % 12 == 0:
                arr = arr.reshape(-1, 12)
            else:
                arr = arr[:, np.newaxis]

        if arr.ndim != 2:
            raise ValueError(f"Unsupported ECG shape: {arr.shape}")

        if arr.shape == (12, 5000):
            arr = arr.T

        if arr.shape[1] == 5000 and arr.shape[0] in {1, 12}:
            arr = arr.T

        if arr.shape[1] != 12 and arr.shape[0] == 12:
            arr = arr.T

        if arr.shape[1] > 12:
            arr = arr[:, :12]
        elif arr.shape[1] < 12:
            missing = 12 - arr.shape[1]
            if arr.shape[1] > 0:
                pad = np.tile(arr[:, -1:], (1, missing))
            else:
                pad = np.zeros((arr.shape[0], missing), dtype=np.float32)
            arr = np.concatenate([arr, pad], axis=1)

        if arr.shape[0] != 5000:
            arr = scipy_signal.resample(arr, 5000, axis=0).astype(np.float32)

        return arr.astype(np.float32)

    @staticmethod
    def _parse_sex(value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip().lower()
        if text in {"m", "male", "man", "\u0630\u0643\u0631"}:
            return 1.0
        if text in {"f", "female", "woman", "\u0627\u0646\u062b\u0649", "\u0623\u0646\u062b\u0649"}:
            return 0.0
        return float(text)

    def _build_csv_features(self, signal_meta: Optional[Dict[str, Any]] = None) -> np.ndarray:
        meta = signal_meta or {}

        age_raw = float(meta["age"]) if meta.get("age") is not None else 50.0
        age = min(age_raw, _AGE_NORM) / _AGE_NORM

        sex = self._parse_sex(meta["sex"]) if meta.get("sex") is not None else 0.5

        height_raw = meta.get("height")
        weight_raw = meta.get("weight")
        height = float(height_raw) / _HEIGHT_NORM if height_raw is not None else 170.0 / _HEIGHT_NORM
        weight = float(weight_raw) / _WEIGHT_NORM if weight_raw is not None else 70.0 / _WEIGHT_NORM
        height_missing = 0.0 if height_raw is not None else 1.0
        weight_missing = 0.0 if weight_raw is not None else 1.0
        validated = 0.0 if meta.get("validated_by_human") is False else 1.0

        return np.asarray(
            [age, sex, height, weight, validated, height_missing, weight_missing],
            dtype=np.float32,
        )

    def _build_clinical_report(
        self,
        enriched_conditions: List[Dict[str, Any]],
        signal_meta: Dict[str, Any],
        top_code: str,
        top_confidence: float,
    ) -> str:
        """Generate a structured plain-text clinical report from enriched conditions."""
        meta = signal_meta or {}

        age_raw = meta.get("age", "N/A")
        sex_raw = meta.get("sex", "N/A")
        if isinstance(sex_raw, (int, float)):
            sex_label = "Male" if float(sex_raw) >= 0.5 else "Female"
        else:
            sex_label = str(sex_raw).capitalize()

        height_raw = meta.get("height")
        weight_raw = meta.get("weight")
        height_str = f"{height_raw} cm" if height_raw is not None else "Not recorded"
        weight_str = f"{weight_raw} kg" if weight_raw is not None else "Not recorded"

        lines: List[str] = []

        lines.append("=" * 64)
        lines.append("         BioIntellect AI Diagnostic System")
        lines.append("              ECG CLINICAL REPORT")
        lines.append("=" * 64)
        lines.append("")

        lines.append("-" * 64)
        lines.append("SECTION 1 — PATIENT INFORMATION")
        lines.append("-" * 64)
        lines.append(f"  Age             : {age_raw}")
        lines.append(f"  Sex             : {sex_label}")
        lines.append(f"  Height          : {height_str}")
        lines.append(f"  Weight          : {weight_str}")
        lines.append(f"  Signal Leads    : 12")
        lines.append(f"  Sampling Rate   : 500 Hz")
        lines.append("")

        lines.append("-" * 64)
        lines.append("SECTION 2 — AI MODEL SUMMARY")
        lines.append("-" * 64)
        lines.append(f"  Model           : BioIntellect InceptionTime Multimodal")
        lines.append(f"  Primary Finding : {top_code}")
        lines.append(f"  Confidence      : {round(top_confidence * 100, 1)}%")
        lines.append(f"  Total Detected  : {len(enriched_conditions)} label(s)")
        lines.append("")

        lines.append("-" * 64)
        lines.append("SECTION 3 — DETECTED CONDITIONS (with Clinical Detail)")
        lines.append("-" * 64)

        primary = enriched_conditions[0] if enriched_conditions else None
        secondary = enriched_conditions[1:] if len(enriched_conditions) > 1 else []

        if primary:
            lines.append("")
            lines.append(f"  PRIMARY: {primary['code']} — {primary['name'].upper()}")
            lines.append(f"  Confidence      : {primary['confidence']}%")
            lines.append(f"  Superclass      : {primary['superclass'] or 'N/A'}")
            lines.append(f"  Category        : {primary['category']}")
            lines.append(f"  Type            : {primary['type']}")
            if primary["summary"]:
                lines.append(f"  Summary         : {primary['summary']}")
            if primary["ecg_features"]:
                lines.append("  ECG Features    :")
                for feat in primary["ecg_features"]:
                    lines.append(f"    • {feat}")
            if primary["clinical_significance"]:
                lines.append(f"  Clinical Note   : {primary['clinical_significance']}")
            if primary["report_template"]:
                lines.append(f"  Report Text     : {primary['report_template']}")

        if secondary:
            lines.append("")
            lines.append("  ADDITIONAL FINDINGS:")
            for cond in secondary:
                lines.append("")
                lines.append(f"  [{cond['code']}] {cond['name'].upper()}  —  {cond['confidence']}%")
                lines.append(f"    Superclass  : {cond['superclass'] or 'N/A'}")
                lines.append(f"    Category    : {cond['category']}")
                if cond["summary"]:
                    lines.append(f"    Summary     : {cond['summary']}")
                if cond["ecg_features"]:
                    lines.append("    ECG Features:")
                    for feat in cond["ecg_features"]:
                        lines.append(f"      • {feat}")
                if cond["report_template"]:
                    lines.append(f"    Report Text : {cond['report_template']}")

        lines.append("")
        lines.append("-" * 64)
        lines.append("SECTION 4 — CLINICAL RECOMMENDATIONS")
        lines.append("-" * 64)

        all_hints: List[str] = []
        all_associations: List[str] = []
        for cond in enriched_conditions:
            all_hints.extend(cond.get("management_hints", []))
            all_associations.extend(cond.get("common_associations", []))

        seen_hints: set[str] = set()
        unique_hints = [h for h in all_hints if not (h in seen_hints or seen_hints.add(h))]  # type: ignore[func-returns-value]

        seen_assoc: set[str] = set()
        unique_assoc = [a for a in all_associations if not (a in seen_assoc or seen_assoc.add(a))]  # type: ignore[func-returns-value]

        if unique_hints:
            lines.append("")
            lines.append("  Recommended Actions:")
            for hint in unique_hints:
                lines.append(f"    • {hint}")

        if unique_assoc:
            lines.append("")
            lines.append("  Common Associations to Consider:")
            for assoc in unique_assoc:
                lines.append(f"    • {assoc}")

        lines.append("")
        lines.append("-" * 64)
        lines.append("SECTION 5 — DISCLAIMER")
        lines.append("-" * 64)
        lines.append(
            "  This report is AI-generated and is intended solely to ASSIST"
        )
        lines.append(
            "  clinical decision-making, not to replace it. All findings must"
        )
        lines.append(
            "  be reviewed and confirmed by a licensed cardiologist or physician"
        )
        lines.append("  before any clinical action is taken.")
        lines.append("  BioIntellect AI Diagnostic System — PTB-XL v1.0.3")
        lines.append("")
        lines.append("=" * 64)

        return "\n".join(lines)

    def predict(self, raw_payload: Any, signal_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        model = self._load_model()
        thresholds = self._load_thresholds()
        class_names = self._load_class_names()

        raw = self._extract_ecg_array(raw_payload)
        signal = self._to_signal_shape(raw)
        signal = preprocess_ecg(signal, fs=500, training=False)

        signal_batch = np.expand_dims(signal.astype(np.float32), axis=0)
        csv_features = self._build_csv_features(signal_meta)
        csv_batch = np.expand_dims(csv_features, axis=0)

        scores = model.predict([signal_batch, csv_batch], verbose=0)[0].astype(np.float32)
        if np.isnan(scores).any() or np.isinf(scores).any():
            raise ValueError(
                "ECG model output contains NaN/Inf; the signal could not be decoded correctly."
            )
        if float(np.std(scores)) < 1e-6:
            raise ValueError(
                "ECG model output is nearly constant; verify loaded weights and runtime compatibility."
            )

        if thresholds is not None and len(thresholds) == len(scores):
            pred_mask = scores >= thresholds
        else:
            pred_mask = scores >= 0.5

        detected_indices = np.where(pred_mask)[0].tolist()

        top_idx = int(np.argmax(scores))
        top_label = class_names[top_idx]
        top_confidence = float(scores[top_idx])

        # Ensure top prediction is always included even if below threshold
        if top_idx not in detected_indices:
            detected_indices = [top_idx] + detected_indices

        # Sort by score descending
        detected_indices.sort(key=lambda i: float(scores[i]), reverse=True)

        # Enrich each detected condition with clinical data from JSON reference files
        enriched_conditions = [
            self.reference.enrich_code(class_names[i], float(scores[i]))
            for i in detected_indices
        ]

        # Backwards-compatible flat list for existing DB/frontend fields
        detected_conditions_flat = [
            {"condition": class_names[i], "confidence": float(scores[i])}
            for i in detected_indices
        ]

        # Build the full structured clinical report
        clinical_report = self._build_clinical_report(
            enriched_conditions=enriched_conditions,
            signal_meta=signal_meta or {},
            top_code=top_label,
            top_confidence=top_confidence,
        )

        return {
            "prediction": top_label,
            "confidence": top_confidence,
            "ai_notes": f"Model-based ECG classification completed with {len(enriched_conditions)} detected label(s).",
            "risk_score": float(top_confidence * 100.0),
            "heart_rate": None,
            "heart_rate_variability": None,
            "detected_conditions": detected_conditions_flat,
            "enriched_conditions": enriched_conditions,
            "clinical_report": clinical_report,
            "recommendations": list({
                hint
                for cond in enriched_conditions
                for hint in cond.get("management_hints", [])
            }),
            "lead_count": 12,
            "raw_scores": {class_names[i]: float(scores[i]) for i in range(len(class_names))},
        }
