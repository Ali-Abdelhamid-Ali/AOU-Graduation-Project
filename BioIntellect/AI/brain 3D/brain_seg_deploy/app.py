import os
import logging
import tempfile
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Dict, Optional
from keras import backend as K
import nibabel as nib
import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from scipy.ndimage import zoom
from huggingface_hub import hf_hub_download
from keras.models import load_model
# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Suppress TensorFlow noisy logs but keep errors
tf.get_logger().setLevel('ERROR')
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# --- App Configuration ---
class AppConfig:
    BASE_DIR = Path(__file__).parent
    OUTPUTS_DIR = BASE_DIR / "outputs"
    MODELS_DIR = BASE_DIR / "models"
    STATIC_DIR = BASE_DIR / "static"
    TEMPLATES_DIR = BASE_DIR / "templates"
    model_path = hf_hub_download(repo_id="Ali-Abdelhamid-Ali/The_Best_3D_Brain_Tumor_Segmentation_BraTS_2021",filename="The Best 3D Brain MRI Segmentation.keras")
    @classmethod
    def setup_directories(cls):
        cls.OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)
        cls.MODELS_DIR.mkdir(exist_ok=True, parents=True)
        cls.STATIC_DIR.mkdir(exist_ok=True, parents=True)
        cls.TEMPLATES_DIR.mkdir(exist_ok=True, parents=True)
        logger.info(f"Directories set up: {cls.OUTPUTS_DIR}, {cls.MODELS_DIR}")

# --- Create app instance properly ---
app_config = AppConfig()
app = Flask(__name__, template_folder=str(app_config.TEMPLATES_DIR))
app.config['MAX_CONTENT_LENGTH'] = 400 * 1024 * 1024  # 400 MB
CORS(app)
app_config.setup_directories()
with tempfile.TemporaryDirectory() as temp_dir:
    td_path = Path(temp_dir)
td_path = Path(os.getenv("TEMP_DIR", "default/temp/path"))

# --- Global settings ---
USE_FLOAT16 = True
MODALITIES = ["t1", "t1ce", "t2", "flair"]
TARGET_SPATIAL = (112, 112, 112)  # Desired D,H,W
CLASS_METADATA = {
    1: {"class_name": "Necrotic/Non-Enhancing Tumor Core", "color": [255, 80, 80]},
    2: {"class_name": "Peritumoral Edema", "color": [80, 255, 80]},
    3: {"class_name": "Enhancing Tumor", "color": [80, 80, 255]},
}

# --- Utility: preprocessing functions ---
def load_nifti_canonical(path: Path) -> Tuple[np.ndarray, np.ndarray, dict]:
    nii = nib.as_closest_canonical(nib.load(str(path)))
    data = nii.get_fdata(dtype=np.float32)
    affine = nii.affine
    header = {k: nii.header[k].tolist() if k in nii.header else None for k in ["dim", "pixdim"]}
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

def get_roi_bounds(mask: np.ndarray, margin: int = 5) -> Optional[Tuple[int, int, int, int, int, int]]:
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

def crop_to_roi(image: np.ndarray, mask: np.ndarray, margin: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    bounds = get_roi_bounds(mask, margin=margin)
    if bounds is None:
        return image, mask
    zmin, zmax, ymin, ymax, xmin, xmax = bounds
    img_c = image[zmin:zmax+1, ymin:ymax+1, xmin:xmax+1]
    msk_c = mask[zmin:zmax+1, ymin:ymax+1, xmin:xmax+1]
    return img_c, msk_c

def resample_to_target(vol: np.ndarray, target: Tuple[int,int,int], order: int = 1) -> np.ndarray:
    orig_shape = vol.shape
    if vol.ndim == 4:
        d0, h0, w0, c = vol.shape
        dz = target[0] / d0
        dy = target[1] / h0
        dx = target[2] / w0
        factors = (dz, dy, dx, 1.0)
    elif vol.ndim == 3:
        d0, h0, w0 = vol.shape
        dz = target[0] / d0
        dy = target[1] / h0
        dx = target[2] / w0
        factors = (dz, dy, dx)
    else:
        raise ValueError(f"Unexpected volume ndim for resampling: {vol.ndim}")

    vol_f = vol.astype(np.float32)
    try:
        res = zoom(vol_f, factors, order=order)
    except Exception as e:
        logger.error(f"Resampling failed from {vol.shape} to {target} (order={order}): {e}")
        raise
    return res

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
    shapes: list[Tuple[int, ...]],
    spacings: list[Tuple[float, float, float]],
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

def process_uploaded_case(
    modality_paths: Dict[str, Path],
    gt_path: Optional[Path] = None,
    patient_id: str = "uploaded",
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    metas = {"patient_id": patient_id, "modalities": MODALITIES}
    vols = []
    shapes = []
    spacings = []
    aff_m = None
    hdr_m = None

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
                f"[AlignmentError] Ground-truth mask shape {mask_vol.shape} does not match modalities {original_shape}"
            )
        mask = preprocess_mask_multiclass(mask_vol)
    else:
        mask = np.zeros(image_4ch.shape[:3], dtype=np.uint8)

    metas["shape_before_crop"] = list(original_shape)
    metas["original_spacing_mm"] = list(original_spacing)
    metas["gt_provided"] = gt_provided
    metas["roi_crop_applied"] = False
    metas["roi_bounds"] = None

    if gt_provided:
        bounds = get_roi_bounds(mask, margin=5)
        if bounds is not None:
            zmin, zmax, ymin, ymax, xmin, xmax = bounds
            image_4ch = image_4ch[zmin:zmax+1, ymin:ymax+1, xmin:xmax+1]
            mask = mask[zmin:zmax+1, ymin:ymax+1, xmin:xmax+1]
            metas["roi_crop_applied"] = True
            metas["roi_bounds"] = [zmin, zmax, ymin, ymax, xmin, xmax]

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

def process_one_patient(patient_folder: Path, patient_id: str) -> Tuple[np.ndarray, np.ndarray, Dict]:
    modality_paths = {
        mod: patient_folder / f"{patient_id}_{mod}.nii.gz" for mod in MODALITIES
    }
    mask_path = patient_folder / f"{patient_id}_seg.nii.gz"
    return process_uploaded_case(
        modality_paths=modality_paths,
        gt_path=mask_path if mask_path.exists() else None,
        patient_id=patient_id,
    )

def compute_effective_spacing_mm(
    original_spacing_mm: Tuple[float, float, float] | list[float],
    shape_after_crop: Tuple[int, int, int] | list[int],
    final_shape: Tuple[int, int, int] | list[int],
) -> list[float]:
    physical_extent_mm = [
        float(original_spacing_mm[idx]) * float(shape_after_crop[idx]) for idx in range(3)
    ]
    return [
        physical_extent_mm[idx] / max(float(final_shape[idx]), 1.0) for idx in range(3)
    ]

def calculate_prediction_confidence(pred_probs: np.ndarray, pred_labels: np.ndarray) -> dict:
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
) -> Tuple[list[dict], float]:
    voxel_volume_mm3 = float(np.prod(np.array(effective_spacing_mm, dtype=np.float64)))
    total_tumor_voxels = int(np.sum(pred_labels > 0))
    total_tumor_volume_mm3 = float(total_tumor_voxels * voxel_volume_mm3)
    regions = []

    for class_id in (1, 2, 3):
        voxel_count = int(np.sum(pred_labels == class_id))
        volume_mm3 = float(voxel_count * voxel_volume_mm3)
        volume_cm3 = volume_mm3 / 1000.0
        percentage = (
            (volume_mm3 / total_tumor_volume_mm3) * 100.0 if total_tumor_volume_mm3 > 0 else 0.0
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
    regions: list[dict],
) -> dict:
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
        "effective_spacing_mm": [round(float(value), 6) for value in effective_spacing_mm],
        "voxel_volume_mm3": round(float(np.prod(np.array(effective_spacing_mm))), 6),
        "class_volumes_cm3": {
            str(region["class_id"]): region["volume_cm3"] for region in regions
        },
    }

# --- Model load ---
def load_segmentation_model(model_path: Path):

    model = load_model(model_path, compile=False)
    
    return model

SMOOTH = 1e-6

def dice_coef(y_true, y_pred):
    """Calculate mean dice coefficient for all classes"""
    y_true = tf.squeeze(y_true, axis=-1)
    num_classes = K.int_shape(y_pred)[-1]
    y_true_oh = tf.one_hot(tf.cast(y_true, tf.int32), depth=num_classes)
    
    # Calculate dice for each class (excluding background class 0)
    dice_scores = []
    for class_id in range(1, num_classes):  # Skip background
        y_true_class = y_true_oh[..., class_id]
        y_pred_class = y_pred[..., class_id]
        
        y_true_f = K.flatten(y_true_class)
        y_pred_f = K.flatten(y_pred_class)
        inter = K.sum(y_true_f * y_pred_f)
        dice = (2. * inter + SMOOTH) / (K.sum(y_true_f) + K.sum(y_pred_f) + SMOOTH)
        dice_scores.append(dice)
    
    # Return mean dice across all classes
    return K.mean(tf.stack(dice_scores))

def dice_loss(y_true, y_pred):
    return 1.0 - dice_coef(y_true, y_pred)

def iou_coef(y_true, y_pred, smooth=1e-6):
    y_true = tf.squeeze(y_true, axis=-1)  
    num_classes = K.int_shape(y_pred)[-1]
    y_true_oh = tf.one_hot(tf.cast(y_true, tf.int32), depth=num_classes)  
    y_pred_arg = K.argmax(y_pred, axis=-1)
    y_pred_oh = tf.one_hot(y_pred_arg, depth=num_classes)
    intersection = K.sum(y_true_oh * y_pred_oh, axis=[0,1,2,3])
    union = K.sum(y_true_oh + y_pred_oh, axis=[0,1,2,3]) - intersection
    iou = (intersection + smooth) / (union + smooth)
    return K.mean(iou)

def combined_dice_ce_loss(y_true, y_pred):
    y_true = tf.squeeze(y_true, axis=-1)
    num_classes = K.int_shape(y_pred)[-1]
    y_true_oh = tf.one_hot(tf.cast(y_true, tf.int32), depth=num_classes)
    dice_sum = 0.0
    for c in range(1, num_classes):
        dice_sum += dice_coef(y_true_oh[..., c], y_pred[..., c])
    dice_mean = dice_sum / tf.cast(num_classes - 1, tf.float32)
    ce = K.categorical_crossentropy(y_true_oh, y_pred)
    ce_mean = K.mean(ce)
    return 0.5 * (1.0 - dice_mean) + 0.5 * ce_mean

def dice_whole_tumor(y_true, y_pred):
    """Calculate dice for whole tumor (classes 1, 2, 3)"""
    y_true = tf.squeeze(y_true, axis=-1)
    num_classes = K.int_shape(y_pred)[-1]
    y_true_oh = tf.one_hot(tf.cast(y_true, tf.int32), depth=num_classes)
    
    # Whole tumor = any non-background class (1, 2, 3)
    y_true_wt = K.cast(K.any(y_true_oh[..., 1:], axis=-1), 'float32')
    y_pred_wt = K.sum(y_pred[..., 1:], axis=-1)  # Sum probabilities of classes 1,2,3
    
    y_true_f = K.flatten(y_true_wt)
    y_pred_f = K.flatten(y_pred_wt)
    inter = K.sum(y_true_f * y_pred_f)
    return (2. * inter + SMOOTH) / (K.sum(y_true_f) + K.sum(y_pred_f) + SMOOTH)

def dice_tumor_core(y_true, y_pred):
    """Calculate dice for tumor core (classes 1, 3)"""
    y_true = tf.squeeze(y_true, axis=-1)
    num_classes = K.int_shape(y_pred)[-1]
    y_true_oh = tf.one_hot(tf.cast(y_true, tf.int32), depth=num_classes)
    
    # Tumor core = classes 1 and 3
    y_true_tc = K.cast(K.any(tf.stack([y_true_oh[..., 1], y_true_oh[..., 3]], axis=-1), axis=-1), 'float32')
    y_pred_tc = y_pred[..., 1] + y_pred[..., 3]  # Sum probabilities of classes 1,3
    
    y_true_f = K.flatten(y_true_tc)
    y_pred_f = K.flatten(y_pred_tc)
    inter = K.sum(y_true_f * y_pred_f)
    return (2. * inter + SMOOTH) / (K.sum(y_true_f) + K.sum(y_pred_f) + SMOOTH)

def dice_enhancing_tumor(y_true, y_pred):
    """Calculate dice for enhancing tumor (class 3 only)"""
    y_true = tf.squeeze(y_true, axis=-1)
    num_classes = K.int_shape(y_pred)[-1]
    y_true_oh = tf.one_hot(tf.cast(y_true, tf.int32), depth=num_classes)
    
    # Enhancing tumor = class 3 only
    y_true_et = y_true_oh[..., 3]
    y_pred_et = y_pred[..., 3]  # Probability of class 3
    
    y_true_f = K.flatten(y_true_et)
    y_pred_f = K.flatten(y_pred_et)
    inter = K.sum(y_true_f * y_pred_f)
    return (2. * inter + SMOOTH) / (K.sum(y_true_f) + K.sum(y_pred_f) + SMOOTH)

app.model = load_segmentation_model(app_config.model_path)

# --- Flask routes ---
@app.route('/')
def route_index():
    return render_template('index.html')

@app.route('/outputs/<filename>')
def serve_output(filename):
    # Set proper MIME type for .npy files
    if filename.endswith('.npy'):
        return send_from_directory(app_config.OUTPUTS_DIR, filename, mimetype='application/octet-stream')
    return send_from_directory(app_config.OUTPUTS_DIR, filename)

app_config.OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)

@app.route('/predict', methods=['POST'])
def route_predict():
    logger.info('=== Starting prediction request ===')

    if app.model is None:
        logger.error('Model not loaded')
        return jsonify({'ok': False, 'error': 'Model is not loaded on the server.'}), 500

    required_mods = MODALITIES
    try:
        modality_files = {}
        for m in required_mods:
            if m not in request.files or not request.files[m].filename:
                raise ValueError(f"Missing required modality: {m}")
            modality_files[m] = request.files[m]
            logger.info(f"Received file for {m}: {request.files[m].filename}")

        gt_file = request.files.get('gt') if 'gt' in request.files and request.files['gt'].filename else None

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            modality_paths = {}
            for m, fs in modality_files.items():
                outp = td_path / f"uploaded_{m}.nii.gz"
                fs.save(str(outp))
                modality_paths[m] = outp
                logger.debug(f"Saved uploaded {m} to {outp}")

            gt_path = None
            if gt_file:
                gt_path = td_path / 'uploaded_seg.nii.gz'
                gt_file.save(str(gt_path))

            try:
                image_4ch, mask, metas = process_uploaded_case(
                    modality_paths=modality_paths,
                    gt_path=gt_path,
                    patient_id='uploaded',
                )
                logger.info(f"Preprocessing produced image shape: {image_4ch.shape}")
            except Exception as e:
                logger.error(f"Preprocessing failed: {e}")
                return jsonify({'ok': False, 'error': f'File preprocessing failed: {str(e)}'}), 400

            try:
                if image_4ch.shape[:3] != TARGET_SPATIAL:
                    logger.info(f"Resampling image from {image_4ch.shape[:3]} to {TARGET_SPATIAL}")
                    img_res = resample_to_target(image_4ch, TARGET_SPATIAL, order=1)
                    image_4ch = img_res.astype(np.float16) if USE_FLOAT16 else img_res.astype(np.float32)
                    logger.info(f"Resampled image shape: {image_4ch.shape}")

                if mask.shape != TARGET_SPATIAL:
                    logger.info(f"Resampling mask from {mask.shape} to {TARGET_SPATIAL}")
                    mask_res = resample_to_target(mask, TARGET_SPATIAL, order=0)
                    mask = enforce_mask_values(mask_res)
                    logger.info(f"Resampled mask shape: {mask.shape}")

                metas["shape"] = list(mask.shape)
                metas["shape_after_resample"] = list(mask.shape)
                metas["effective_spacing_mm"] = compute_effective_spacing_mm(
                    metas["original_spacing_mm"],
                    metas["shape_after_crop"],
                    metas["shape_after_resample"],
                )
            except Exception as e:
                logger.error(f"Resampling to target shape failed: {e}")
                return jsonify({'ok': False, 'error': f'Failed to resample image/mask to {TARGET_SPATIAL}: {e}'}), 500

            model_input = np.expand_dims(image_4ch, axis=0)
            if model_input.dtype == np.float16:
                model_input = model_input.astype(np.float32)

            logger.info(f"Model input shape: {model_input.shape}, dtype: {model_input.dtype}")

            # Predict
            try:
                pred_probs = app.model.predict(model_input, verbose=0)
                if isinstance(pred_probs, list):
                    pred_probs = pred_probs[0]
                if pred_probs.ndim == 5:
                    pred_probs = pred_probs[0]
                logger.info(f"Pred probs shape: {pred_probs.shape}")
                pred_labels = np.argmax(pred_probs, axis=-1).astype(np.uint8)
                logger.info(f"Pred labels shape: {pred_labels.shape}, unique: {np.unique(pred_labels)}")
            except Exception as e:
                logger.error(f"Model prediction failed: {e}")
                return jsonify({'ok': False, 'error': f'Model prediction failed: {str(e)}'}), 500

            case_id = str(uuid.uuid4())
            outputs_dir = app_config.OUTPUTS_DIR
            image_data_cdhw = np.transpose(image_4ch.astype(np.float32), (3,0,1,2))
            image_filename = f"{case_id}_image_data.npy"
            np.save(outputs_dir / image_filename, image_data_cdhw)
            labels_filename = f"{case_id}_labels.npy"
            np.save(outputs_dir / labels_filename, pred_labels)
            logger.info(f"Saved outputs: {image_filename}, {labels_filename}")

            metrics = {}
            if metas["gt_provided"]:
                try:
                    pred_probs_tensor = tf.convert_to_tensor(pred_probs[None, ...], dtype=tf.float32)
                    gt_mask_tensor = tf.convert_to_tensor(mask[None, ..., None], dtype=tf.float32)

                    metrics['Mean_Dice'] = float(dice_coef(gt_mask_tensor, pred_probs_tensor).numpy())
                    metrics['IoU'] = float(iou_coef(gt_mask_tensor, pred_probs_tensor).numpy())
                    metrics['Dice_whole_tumor'] = float(dice_whole_tumor(gt_mask_tensor, pred_probs_tensor).numpy())
                    metrics['Dice_tumor_core'] = float(dice_tumor_core(gt_mask_tensor, pred_probs_tensor).numpy())
                    metrics['Dice_enhancing_tumor'] = float(dice_enhancing_tumor(gt_mask_tensor, pred_probs_tensor).numpy())
                    logger.info(f"Calculated metrics: {metrics}")
                except Exception as e:
                    logger.error(f"Metrics calculation failed with error: {e}")
                    metrics = {
                        'Mean_Dice': 0.0,
                        'IoU': 0.0,
                        'Dice_whole_tumor': 0.0,
                        'Dice_tumor_core': 0.0,
                        'Dice_enhancing_tumor': 0.0,
                    }
            else:
                logger.info("No ground truth provided, showing example metrics")
                metrics['Prediction_Stats'] = f"Classes found: {np.unique(pred_labels).tolist()}"
                metrics['Tumor_Volume'] = f"{np.sum(pred_labels > 0)} voxels"

            prediction_confidence = calculate_prediction_confidence(pred_probs, pred_labels)
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

            return jsonify({
                'ok': True,
                'case_id': case_id,
                'inference_timestamp': datetime.now(timezone.utc).isoformat(),
                'image_filename': image_filename,
                'labels_filename': labels_filename,
                'model_info': {
                    'name': 'BioIntellect Brain MRI 3D U-Net',
                    'version': '2026.03',
                    'checksum': 'mri-3d-unet-2026-03',
                    'release_date': '2026-03-01',
                },
                'tumor_detected': tumor_detected,
                'prediction_confidence': prediction_confidence,
                'regions': regions,
                'total_volume_cm3': total_volume_cm3,
                'measurements': measurements,
                'processing_metadata': metas,
                'metrics': metrics,
                'shape': metas["shape_after_resample"],
                'ai_recommendations': (
                    [
                        'Urgent neuroradiology review recommended.',
                        'Correlate with prior studies and clinical findings.',
                    ]
                    if tumor_detected
                    else ['No segmented lesion detected. Correlate clinically as needed.']
                ),
                'ai_interpretation': (
                    'Predicted abnormal enhancing intracranial lesion with volumetric segmentation.'
                    if tumor_detected
                    else 'No segmented intracranial tumor volume detected on the provided modalities.'
                ),
                'requires_review': tumor_detected,
                'disclaimer': 'AI output supports review only and must be confirmed by a clinician.',
            })

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=False)
