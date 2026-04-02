from __future__ import annotations

import ast
import csv
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

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


class ECGInferenceEngine:
    def __init__(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        base_dir = repo_root / "AI" / "ECG" / "App" / "classification"

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

        self.signal_shape = (5000, 12)
        self.cpu_only = _ECG_TF_CPU_ONLY
        self._model: Optional[Model] = None
        self._thresholds: Optional[np.ndarray] = None
        self._class_names: Optional[list[str]] = None

        if self.cpu_only:
            try:
                tf.config.set_visible_devices([], "GPU")
            except Exception:
                # Safe fallback when TF runtime is already initialized or no GPU exists.
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
                    # Keep output dimensions consistent with trained model thresholds.
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

    def _try_binary_matrix(self, payload: bytes) -> np.ndarray:
        for dtype in (np.float32, np.float64, np.int16, np.int32):
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
            text = bytes(payload).decode("utf-8", errors="ignore").strip()
            if text:
                try:
                    as_json = json.loads(text)
                    return self._extract_ecg_array(as_json)
                except Exception:
                    try:
                        return self._parse_text_matrix(text)
                    except Exception:
                        pass

            raw_bytes = bytes(payload)
            if not raw_bytes:
                raise ValueError("Uploaded ECG file is empty.")
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
        if text in {"m", "male", "man", "ذكر"}:
            return 1.0
        if text in {"f", "female", "woman", "انثى", "أنثى"}:
            return 0.0
        return float(text)

    def _build_csv_features(self, signal_meta: Optional[Dict[str, Any]] = None) -> np.ndarray:
        meta = signal_meta or {}

        age_raw = float(meta["age"]) if meta.get("age") is not None else 50.0
        age = age_raw / _AGE_NORM

        sex = self._parse_sex(meta["sex"]) if meta.get("sex") is not None else 0.5

        height_raw = meta.get("height")
        weight_raw = meta.get("weight")
        height = float(height_raw) / _HEIGHT_NORM if height_raw is not None else 170.0 / _HEIGHT_NORM
        weight = float(weight_raw) / _WEIGHT_NORM if weight_raw is not None else 70.0 / _WEIGHT_NORM
        height_missing = 0.0 if height_raw is not None else 1.0
        weight_missing = 0.0 if weight_raw is not None else 1.0
        validated = 1.0 if meta.get("validated_by_human") else 0.0

        return np.asarray(
            [age, sex, height, weight, validated, height_missing, weight_missing],
            dtype=np.float32,
        )

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
        if float(np.std(scores)) < 1e-6:
            raise ValueError(
                "ECG model output is nearly constant; verify loaded weights and runtime compatibility."
            )

        if thresholds is not None and len(thresholds) == len(scores):
            pred_mask = scores >= thresholds
        else:
            pred_mask = scores >= 0.5

        detected_conditions = [
            {"condition": class_names[i], "confidence": float(scores[i])}
            for i in np.where(pred_mask)[0].tolist()
        ]

        top_idx = int(np.argmax(scores))
        top_label = class_names[top_idx]
        top_confidence = float(scores[top_idx])

        if not detected_conditions:
            detected_conditions = [{"condition": top_label, "confidence": top_confidence}]

        return {
            "prediction": top_label,
            "confidence": top_confidence,
            "ai_notes": f"Model-based ECG classification completed with {len(detected_conditions)} detected label(s).",
            "risk_score": float(top_confidence * 100.0),
            "heart_rate": None,
            "heart_rate_variability": None,
            "detected_conditions": detected_conditions,
            "recommendations": [
                "Correlate AI labels with clinical context and physician interpretation.",
                "Review low-confidence labels before final diagnosis.",
            ],
            "lead_count": 12,
            "raw_scores": {class_names[i]: float(scores[i]) for i in range(len(class_names))},
        }
