

from __future__ import annotations

import logging
import os
import tempfile
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Suppress TF noise – keep errors only.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
warnings.filterwarnings("ignore", category=UserWarning)

import nibabel as nib  # noqa: E402
from scipy.ndimage import zoom  # noqa: E402

logger = logging.getLogger("service.ai.mri")

# ---------------------------------------------------------------------------
# Constants (must match the training pipeline)
# ---------------------------------------------------------------------------
MODALITIES: list[str] = ["t1", "t1ce", "t2", "flair"]
TARGET_SPATIAL: Tuple[int, int, int] = (112, 112, 112)
USE_FLOAT16: bool = True

CLASS_METADATA: dict[int, dict[str, Any]] = {
    1: {"class_name": "Necrotic/Non-Enhancing Tumor Core", "color": [255, 80, 80]},
    2: {"class_name": "Peritumoral Edema", "color": [80, 255, 80]},
    3: {"class_name": "Enhancing Tumor", "color": [80, 80, 255]},
}

# ---------------------------------------------------------------------------
# Preprocessing utilities (identical to the Flask app)
# ---------------------------------------------------------------------------

def load_nifti_canonical(path: Path) -> Tuple[np.ndarray, np.ndarray, dict]:
    nii = nib.as_closest_canonical(nib.load(str(path)))
    data = nii.get_fdata(dtype=np.float32)
    affine = nii.affine
    header = {
        k: nii.header[k].tolist() if k in nii.header else None
        for k in ["dim", "pixdim"]
    }
    return data, affine, header


def normalize_nonzero(volume: np.ndarray) -> np.ndarray:
    vol = volume.astype(np.float32)
    nz = vol[vol != 0]
    if nz.size > 0:
        mean, std = float(nz.mean()), float(nz.std())
    else:
        mean, std = float(vol.mean()), float(vol.std())
    vol = (vol - mean) / (std + 1e-8)
    return vol


def preprocess_mask_multiclass(mask: np.ndarray) -> np.ndarray:
    m = np.rint(mask).astype(np.uint8)
    m[m == 4] = 3
    return m


def get_roi_bounds(
    mask: np.ndarray, margin: int = 5
) -> Optional[Tuple[int, int, int, int, int, int]]:
    coords = np.array(np.nonzero(mask))
    if coords.size == 0:
        return None
    zmin, ymin, xmin = coords.min(axis=1)
    zmax, ymax, xmax = coords.max(axis=1)
    zmin = max(zmin - margin, 0)
    ymin = max(ymin - margin, 0)
    xmin = max(xmin - margin, 0)
    zmax = min(zmax + margin, mask.shape[0] - 1)
    ymax = min(ymax + margin, mask.shape[1] - 1)
    xmax = min(xmax + margin, mask.shape[2] - 1)
    return (int(zmin), int(zmax), int(ymin), int(ymax), int(xmin), int(xmax))


def resample_to_target(
    vol: np.ndarray, target: Tuple[int, int, int], order: int = 1
) -> np.ndarray:
    if vol.ndim == 4:
        d0, h0, w0, _c = vol.shape
        factors = (target[0] / d0, target[1] / h0, target[2] / w0, 1.0)
    elif vol.ndim == 3:
        d0, h0, w0 = vol.shape
        factors = (target[0] / d0, target[1] / h0, target[2] / w0)
    else:
        raise ValueError(f"Unexpected volume ndim for resampling: {vol.ndim}")
    return zoom(vol.astype(np.float32), factors, order=order)


def enforce_mask_values(mask: np.ndarray) -> np.ndarray:
    m = np.rint(mask).astype(np.int32)
    m[m == 4] = 3
    m = np.clip(m, 0, 3).astype(np.uint8)
    return m


def extract_spacing_mm(header: dict) -> Tuple[float, float, float]:
    pixdim = (header or {}).get("pixdim") or []
    if len(pixdim) >= 4:
        return (float(pixdim[1]), float(pixdim[2]), float(pixdim[3]))
    return (1.0, 1.0, 1.0)


def validate_spatial_compatibility(
    shapes: List[Tuple[int, ...]],
    spacings: List[Tuple[float, float, float]],
    patient_id: str,
) -> Tuple[Tuple[int, int, int], Tuple[float, float, float]]:
    if len(set(shapes)) != 1:
        raise ValueError(
            f"[AlignmentError] Modality shapes differ for patient {patient_id}: {shapes}"
        )
    reference_spacing = spacings[0]
    for spacing in spacings[1:]:
        if not np.allclose(reference_spacing, spacing, rtol=1e-3, atol=1e-3):
            raise ValueError(
                f"[SpacingError] Modality spacing differs for patient {patient_id}: {spacings}"
            )
    return shapes[0], reference_spacing


def compute_effective_spacing_mm(
    original_spacing_mm: Tuple[float, float, float] | list[float],
    shape_after_crop: Tuple[int, int, int] | list[int],
    final_shape: Tuple[int, int, int] | list[int],
) -> list[float]:
    physical_extent_mm = [
        float(original_spacing_mm[i]) * float(shape_after_crop[i]) for i in range(3)
    ]
    return [
        physical_extent_mm[i] / max(float(final_shape[i]), 1.0) for i in range(3)
    ]


# ---------------------------------------------------------------------------
# Full preprocessing pipeline
# ---------------------------------------------------------------------------

def process_uploaded_case(
    modality_paths: Dict[str, Path],
    gt_path: Optional[Path] = None,
    patient_id: str = "uploaded",
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Load, validate, normalise and crop a set of 4-modality NIfTI files."""
    metas: Dict[str, Any] = {"patient_id": patient_id, "modalities": MODALITIES}
    vols: list[np.ndarray] = []
    shapes: list[Tuple[int, ...]] = []
    spacings: list[Tuple[float, float, float]] = []

    for mod in MODALITIES:
        modality_path = modality_paths.get(mod)
        if modality_path is None or not modality_path.exists():
            raise FileNotFoundError(f"File not found: {modality_path}")
        vol, aff, hdr = load_nifti_canonical(modality_path)
        vols.append(vol)
        shapes.append(vol.shape)
        spacings.append(extract_spacing_mm(hdr))
        metas[f"affine_{mod}"] = aff.tolist()
        metas[f"header_{mod}"] = hdr

    original_shape, original_spacing = validate_spatial_compatibility(
        shapes, spacings, patient_id
    )
    image_4ch = np.stack(vols, axis=-1)

    gt_provided = gt_path is not None and gt_path.exists()
    if gt_provided:
        mask_vol, aff_m, hdr_m = load_nifti_canonical(gt_path)
        if mask_vol.shape != original_shape:
            raise ValueError(
                f"[AlignmentError] Ground-truth mask shape {mask_vol.shape} "
                f"does not match modalities {original_shape}"
            )
        mask = preprocess_mask_multiclass(mask_vol)
    else:
        mask = np.zeros(image_4ch.shape[:3], dtype=np.uint8)
        aff_m = None  # type: ignore[assignment]
        hdr_m = None  # type: ignore[assignment]

    metas["shape_before_crop"] = list(original_shape)
    metas["original_spacing_mm"] = list(original_spacing)
    metas["gt_provided"] = gt_provided
    metas["roi_crop_applied"] = False
    metas["roi_bounds"] = None

    if gt_provided:
        bounds = get_roi_bounds(mask, margin=5)
        if bounds is not None:
            zmin, zmax, ymin, ymax, xmin, xmax = bounds
            image_4ch = image_4ch[zmin : zmax + 1, ymin : ymax + 1, xmin : xmax + 1]
            mask = mask[zmin : zmax + 1, ymin : ymax + 1, xmin : xmax + 1]
            metas["roi_crop_applied"] = True
            metas["roi_bounds"] = [zmin, zmax, ymin, ymax, xmin, xmax]

    # Per-channel Z-score normalisation on non-zero voxels.
    for i in range(image_4ch.shape[-1]):
        image_4ch[..., i] = normalize_nonzero(image_4ch[..., i])

    if USE_FLOAT16:
        image_4ch = image_4ch.astype(np.float16)

    metas["affine_mask"] = aff_m.tolist() if aff_m is not None else None
    metas["header_mask"] = hdr_m if hdr_m is not None else None
    metas["shape_after_crop"] = list(mask.shape)
    metas["shape"] = list(mask.shape)
    metas["default_modality"] = "t1ce"
    return image_4ch, mask, metas


# ---------------------------------------------------------------------------
# Post-processing helpers
# ---------------------------------------------------------------------------

def calculate_prediction_confidence(
    pred_probs: np.ndarray, pred_labels: np.ndarray
) -> dict[str, float]:
    voxel_confidence = np.max(pred_probs, axis=-1)
    tumor_mask = pred_labels > 0
    tumor_presence = float(np.mean(np.sum(pred_probs[..., 1:], axis=-1)))
    if np.any(tumor_mask):
        overall = float(np.mean(voxel_confidence[tumor_mask]))
    else:
        overall = float(np.mean(voxel_confidence))
    return {
        "overall": round(overall, 4),
        "tumor_presence": round(tumor_presence, 4),
        "segmentation_quality": round(float(np.mean(voxel_confidence)), 4),
    }


def calculate_region_stats(
    pred_labels: np.ndarray,
    effective_spacing_mm: Tuple[float, float, float] | list[float],
) -> Tuple[list[dict[str, Any]], float]:
    voxel_volume_mm3 = float(np.prod(np.array(effective_spacing_mm, dtype=np.float64)))
    total_tumor_voxels = int(np.sum(pred_labels > 0))
    total_tumor_volume_mm3 = float(total_tumor_voxels * voxel_volume_mm3)
    regions: list[dict[str, Any]] = []

    for class_id in (1, 2, 3):
        voxel_count = int(np.sum(pred_labels == class_id))
        volume_mm3 = float(voxel_count * voxel_volume_mm3)
        volume_cm3 = volume_mm3 / 1000.0
        percentage = (
            (volume_mm3 / total_tumor_volume_mm3) * 100.0
            if total_tumor_volume_mm3 > 0
            else 0.0
        )
        regions.append(
            {
                "class_id": class_id,
                "class_name": CLASS_METADATA[class_id]["class_name"],
                "color": CLASS_METADATA[class_id]["color"],
                "voxel_count": voxel_count,
                "volume_voxels": voxel_count,
                "volume_mm3": round(volume_mm3, 4),
                "volume_cm3": round(volume_cm3, 4),
                "percentage": round(percentage, 4),
                "present": voxel_count > 0,
            }
        )
    return regions, round(total_tumor_volume_mm3 / 1000.0, 4)


def calculate_measurements(
    pred_labels: np.ndarray,
    effective_spacing_mm: Tuple[float, float, float] | list[float],
    regions: list[dict[str, Any]],
) -> dict[str, Any]:
    tumor_coords = np.argwhere(pred_labels > 0)
    if tumor_coords.size == 0:
        largest_diameter_mm = 0.0
    else:
        mins = tumor_coords.min(axis=0)
        maxs = tumor_coords.max(axis=0)
        extents_voxels = (maxs - mins + 1).astype(np.float32)
        extents_mm = extents_voxels * np.array(effective_spacing_mm, dtype=np.float32)
        largest_diameter_mm = float(np.max(extents_mm))
    return {
        "largest_diameter_mm": round(largest_diameter_mm, 4),
        "effective_spacing_mm": [round(float(v), 6) for v in effective_spacing_mm],
        "voxel_volume_mm3": round(
            float(np.prod(np.array(effective_spacing_mm))), 6
        ),
        "class_volumes_cm3": {
            str(r["class_id"]): r["volume_cm3"] for r in regions
        },
    }


# ---------------------------------------------------------------------------
# Inference Engine
# ---------------------------------------------------------------------------

class MRIInferenceEngine:
    """Loads the Keras 3D U-Net once and performs segmentation on demand."""

    # Resolved at first instantiation inside __init__ so that settings is
    # already loaded (avoids import-time circular issues).
    _MODEL_PATH: Path | None = None
    _OUTPUTS_DIR: Path | None = None  # type: ignore[assignment]

    def __init__(self) -> None:
        from src.config.settings import settings  # local import avoids circular deps

        self._model: Any | None = None

        # Resolve model path: prefer .env / settings, fall back to repo-relative default.
        _default_model = (
            Path(__file__).resolve().parents[4]
            / "AI"
            / "brain 3D"
            / "brain_seg_deploy"
            / "models"
            / "The Best 3D Brain MRI Segmentation.keras"
        )
        self._MODEL_PATH: Path = Path(settings.mri_model_path or str(_default_model))

        # Resolve outputs dir.
        _default_outputs = Path(__file__).resolve().parents[3] / "mri_outputs"
        self._OUTPUTS_DIR: Path = Path(settings.mri_outputs_dir or str(_default_outputs))
        self._OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"MRI Inference Engine initialised. Model path: {self._MODEL_PATH}")

    @property
    def outputs_dir(self) -> Path:
        return self._OUTPUTS_DIR  # type: ignore[return-value]

    def _ensure_model(self) -> Any:
        """Lazy-load the Keras model on first inference request."""
        if self._model is not None:
            return self._model

        import tensorflow as tf  # noqa: E402

        tf.get_logger().setLevel("ERROR")

        model_path = self._MODEL_PATH
        logger.info(f"MRI model path resolved to: {model_path}")

        if not model_path.exists():
            # Try downloading from HuggingFace as fallback.
            logger.info("Model not found locally – downloading from HuggingFace…")
            from huggingface_hub import hf_hub_download

            hf_path = hf_hub_download(
                repo_id="Ali-Abdelhamid-Ali/The_Best_3D_Brain_Tumor_Segmentation_BraTS_2021",
                filename="The Best 3D Brain MRI Segmentation.keras",
            )
            model_path = Path(hf_path)
            logger.info(f"Downloaded model to: {model_path}")

        # Use tf_keras if available (matches the training environment),
        # otherwise fall back to keras.models.load_model.
        logger.info(f"Loading MRI model from {model_path} …")
        try:
            import tf_keras  # noqa: E402
            self._model = tf_keras.models.load_model(str(model_path), compile=False)
        except (ImportError, Exception):
            from keras.models import load_model  # noqa: E402
            self._model = load_model(str(model_path), compile=False)

        logger.info("MRI model loaded successfully.")
        return self._model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def predict(
        self,
        modality_bytes: Dict[str, bytes],
        patient_id: str = "uploaded",
        gt_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Run end-to-end segmentation and return structured results.

        Parameters
        ----------
        modality_bytes : dict
            Mapping ``{"t1": bytes, "t1ce": bytes, "t2": bytes, "flair": bytes}``
            where each value is the raw content of a NIfTI file.
        patient_id : str
            Patient identifier for metadata tagging.
        gt_bytes : bytes | None
            Optional ground-truth NIfTI for validation metrics.
        """
        model = self._ensure_model()

        # Write bytes to temp files so nibabel can load them.
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            modality_paths: Dict[str, Path] = {}
            for mod in MODALITIES:
                raw = modality_bytes.get(mod)
                if raw is None:
                    raise ValueError(f"Missing required modality: {mod}")
                p = td_path / f"uploaded_{mod}.nii.gz"
                p.write_bytes(raw)
                modality_paths[mod] = p

            gt_path: Optional[Path] = None
            if gt_bytes:
                gt_path = td_path / "uploaded_seg.nii.gz"
                gt_path.write_bytes(gt_bytes)

            # --- Preprocessing ---
            image_4ch, mask, metas = process_uploaded_case(
                modality_paths=modality_paths,
                gt_path=gt_path,
                patient_id=patient_id,
            )
            logger.info(f"Preprocessing produced image shape: {image_4ch.shape}")

            # --- Resample to target ---
            if image_4ch.shape[:3] != TARGET_SPATIAL:
                logger.info(
                    f"Resampling image from {image_4ch.shape[:3]} to {TARGET_SPATIAL}"
                )
                img_res = resample_to_target(image_4ch, TARGET_SPATIAL, order=1)
                image_4ch = (
                    img_res.astype(np.float16) if USE_FLOAT16 else img_res.astype(np.float32)
                )

            if mask.shape != TARGET_SPATIAL:
                logger.info(
                    f"Resampling mask from {mask.shape} to {TARGET_SPATIAL}"
                )
                mask = enforce_mask_values(
                    resample_to_target(mask, TARGET_SPATIAL, order=0)
                )

            metas["shape"] = list(mask.shape)
            metas["shape_after_resample"] = list(mask.shape)
            metas["effective_spacing_mm"] = compute_effective_spacing_mm(
                metas["original_spacing_mm"],
                metas["shape_after_crop"],
                metas["shape_after_resample"],
            )

            # --- Model inference ---
            model_input = np.expand_dims(image_4ch, axis=0)
            if model_input.dtype == np.float16:
                model_input = model_input.astype(np.float32)

            logger.info(
                f"Model input shape: {model_input.shape}, dtype: {model_input.dtype}"
            )

            pred_probs = model.predict(model_input, verbose=0)
            if isinstance(pred_probs, list):
                pred_probs = pred_probs[0]
            if pred_probs.ndim == 5:
                pred_probs = pred_probs[0]

            pred_labels = np.argmax(pred_probs, axis=-1).astype(np.uint8)
            logger.info(
                f"Prediction done – labels shape: {pred_labels.shape}, "
                f"unique: {np.unique(pred_labels).tolist()}"
            )

            # --- Save .npy artifacts ---
            case_id = str(uuid.uuid4())
            image_data_cdhw = np.transpose(image_4ch.astype(np.float32), (3, 0, 1, 2))
            image_filename = f"{case_id}_image_data.npy"
            labels_filename = f"{case_id}_labels.npy"
            np.save(self._OUTPUTS_DIR / image_filename, image_data_cdhw)
            np.save(self._OUTPUTS_DIR / labels_filename, pred_labels)
            logger.info(f"Saved artifacts: {image_filename}, {labels_filename}")

            # --- Metrics (only when GT is provided) ---
            metrics: Dict[str, Any] = {}
            if metas["gt_provided"]:
                metrics = self._compute_gt_metrics(pred_probs, mask)
            else:
                metrics["Prediction_Stats"] = (
                    f"Classes found: {np.unique(pred_labels).tolist()}"
                )
                metrics["Tumor_Volume"] = f"{np.sum(pred_labels > 0)} voxels"

            # --- Post-processing ---
            prediction_confidence = calculate_prediction_confidence(
                pred_probs, pred_labels
            )
            regions, total_volume_cm3 = calculate_region_stats(
                pred_labels, metas["effective_spacing_mm"]
            )
            measurements = calculate_measurements(
                pred_labels, metas["effective_spacing_mm"], regions
            )
            tumor_detected = bool(np.any(pred_labels > 0))

            metas["label_shape_dhw"] = list(pred_labels.shape)
            metas["image_shape_cdhw"] = list(image_data_cdhw.shape)
            metas["shape_after_resample"] = list(pred_labels.shape)

            return {
                "ok": True,
                "case_id": case_id,
                "inference_timestamp": datetime.now(timezone.utc).isoformat(),
                "image_filename": image_filename,
                "labels_filename": labels_filename,
                "model_info": {
                    "name": "BioIntellect Brain MRI 3D U-Net",
                    "version": "2026.03",
                    "checksum": "mri-3d-unet-2026-03",
                    "release_date": "2026-03-01",
                },
                "tumor_detected": tumor_detected,
                "prediction_confidence": prediction_confidence,
                "regions": regions,
                "total_volume_cm3": total_volume_cm3,
                "measurements": measurements,
                "processing_metadata": metas,
                "metrics": metrics,
                "shape": metas["shape_after_resample"],
                "ai_recommendations": (
                    [
                        "Urgent neuroradiology review recommended.",
                        "Correlate with prior studies and clinical findings.",
                    ]
                    if tumor_detected
                    else [
                        "No segmented lesion detected. Correlate clinically as needed."
                    ]
                ),
                "ai_interpretation": (
                    "Predicted abnormal enhancing intracranial lesion with volumetric segmentation."
                    if tumor_detected
                    else "No segmented intracranial tumor volume detected on the provided modalities."
                ),
                "requires_review": tumor_detected,
                "disclaimer": "AI output supports review only and must be confirmed by a clinician.",
            }

    # ------------------------------------------------------------------
    # Ground-truth metrics
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_gt_metrics(
        pred_probs: np.ndarray, mask: np.ndarray
    ) -> Dict[str, float]:
        """Dice / IoU metrics when ground-truth is available."""
        import tensorflow as tf
        from keras import backend as K

        SMOOTH = 1e-6

        pred_probs_t = tf.convert_to_tensor(pred_probs[None, ...], dtype=tf.float32)
        gt_mask_t = tf.convert_to_tensor(mask[None, ..., None], dtype=tf.float32)

        y_true = tf.squeeze(gt_mask_t, axis=-1)
        num_classes = pred_probs_t.shape[-1]
        y_true_oh = tf.one_hot(tf.cast(y_true, tf.int32), depth=num_classes)

        def _dice_class(cls: int) -> float:
            yt = K.flatten(y_true_oh[..., cls])
            yp = K.flatten(pred_probs_t[..., cls])
            inter = K.sum(yt * yp)
            return float(((2.0 * inter + SMOOTH) / (K.sum(yt) + K.sum(yp) + SMOOTH)).numpy())

        dice_scores = [_dice_class(c) for c in range(1, num_classes)]
        mean_dice = float(np.mean(dice_scores))

        # IoU
        y_pred_oh = tf.one_hot(K.argmax(pred_probs_t, axis=-1), depth=num_classes)
        intersection = K.sum(y_true_oh * y_pred_oh, axis=[0, 1, 2, 3])
        union = K.sum(y_true_oh + y_pred_oh, axis=[0, 1, 2, 3]) - intersection
        iou = float(K.mean((intersection + SMOOTH) / (union + SMOOTH)).numpy())

        # Whole tumor (1, 2, 3)
        y_true_wt = K.cast(K.any(y_true_oh[..., 1:], axis=-1), "float32")
        y_pred_wt = K.sum(pred_probs_t[..., 1:], axis=-1)
        yt_f, yp_f = K.flatten(y_true_wt), K.flatten(y_pred_wt)
        dice_wt = float(
            ((2.0 * K.sum(yt_f * yp_f) + SMOOTH) / (K.sum(yt_f) + K.sum(yp_f) + SMOOTH)).numpy()
        )

        # Tumor core (1, 3)
        y_true_tc = K.cast(
            K.any(tf.stack([y_true_oh[..., 1], y_true_oh[..., 3]], axis=-1), axis=-1),
            "float32",
        )
        y_pred_tc = pred_probs_t[..., 1] + pred_probs_t[..., 3]
        yt_f, yp_f = K.flatten(y_true_tc), K.flatten(y_pred_tc)
        dice_tc = float(
            ((2.0 * K.sum(yt_f * yp_f) + SMOOTH) / (K.sum(yt_f) + K.sum(yp_f) + SMOOTH)).numpy()
        )

        # Enhancing tumor (3)
        yt_f = K.flatten(y_true_oh[..., 3])
        yp_f = K.flatten(pred_probs_t[..., 3])
        dice_et = float(
            ((2.0 * K.sum(yt_f * yp_f) + SMOOTH) / (K.sum(yt_f) + K.sum(yp_f) + SMOOTH)).numpy()
        )

        return {
            "Mean_Dice": round(mean_dice, 4),
            "IoU": round(iou, 4),
            "Dice_whole_tumor": round(dice_wt, 4),
            "Dice_tumor_core": round(dice_tc, 4),
            "Dice_enhancing_tumor": round(dice_et, 4),
        }
