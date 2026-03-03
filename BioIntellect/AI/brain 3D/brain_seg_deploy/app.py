import os
import logging
import tempfile
import traceback
import uuid
from pathlib import Path
from typing import Tuple, Dict
from keras import backend as K
import nibabel as nib
import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from scipy.ndimage import zoom
import traceback
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

def crop_to_roi(image: np.ndarray, mask: np.ndarray, margin: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    coords = np.array(np.nonzero(mask))
    if coords.size == 0:
        return image, mask
    zmin, ymin, xmin = coords.min(axis=1)
    zmax, ymax, xmax = coords.max(axis=1)
    zmin = max(zmin - margin, 0)
    ymin = max(ymin - margin, 0)
    xmin = max(xmin - margin, 0)
    zmax = min(zmax + margin, mask.shape[0] - 1)
    ymax = min(ymax + margin, mask.shape[1] - 1)
    xmax = min(xmax + margin, mask.shape[2] - 1)
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

def process_one_patient(patient_folder: Path, patient_id: str) -> Tuple[np.ndarray, np.ndarray, Dict]:
    image_4ch = None
    mask = None
    metas = {"patient_id": patient_id, "modalities": MODALITIES}

    # Load modalities
    vols = []
    for mod in MODALITIES:
        p = patient_folder / f"{patient_id}_{mod}.nii.gz"
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
        vol, aff, hdr = load_nifti_canonical(p)
        vols.append(vol)
        metas[f"affine_{mod}"] = aff.tolist()
        metas[f"header_{mod}"] = hdr

    # Check if all modalities have the same shape
    shapes = [v.shape for v in vols]
    if len(set(shapes)) != 1:
        raise ValueError(f"[AlignmentError] Modality shapes differ for patient {patient_id}: {shapes}")

    # Stack modalities into a 4-channel image
    image_4ch = np.stack(vols, axis=-1)

    # Load and preprocess mask
    mask_path = patient_folder / f"{patient_id}_seg.nii.gz"
    aff_m = None
    hdr_m = None
    if mask_path.exists():
        mask_vol, aff_m, hdr_m = load_nifti_canonical(mask_path)
        mask = preprocess_mask_multiclass(mask_vol)
    else:
        logger.warning(f"Mask file not found: {mask_path}. Proceeding without mask.")
        mask = np.zeros(image_4ch.shape[:3], dtype=np.uint8)

    # Crop to ROI
    image_4ch, mask = crop_to_roi(image_4ch, mask)

    # Normalize each channel
    for i in range(image_4ch.shape[-1]):
        image_4ch[..., i] = normalize_nonzero(image_4ch[..., i])

    if USE_FLOAT16:
        image_4ch = image_4ch.astype(np.float16)

    metas["affine_mask"] = aff_m.tolist() if aff_m is not None else None
    metas["header_mask"] = hdr_m if hdr_m is not None else None
    metas["shape"] = list(mask.shape)

    return image_4ch, mask, metas

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

        # Save uploaded files to temp dir and call process_one_patient
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            for m, fs in modality_files.items():
                outp = td_path / f"uploaded_{m}.nii.gz"
                fs.save(str(outp))
                logger.debug(f"Saved uploaded {m} to {outp}")
            
            if gt_file:
                gt_out = td_path / 'uploaded_gt.nii.gz'
                gt_file.save(str(gt_out))

            # Preprocess using process_one_patient
            try:
                image_4ch, mask, metas = process_one_patient(td_path, 'uploaded')
                logger.info(f"Preprocessing produced image shape: {image_4ch.shape}")
            except Exception as e:
                logger.error(f"Preprocessing failed: {e}")
                return jsonify({'ok': False, 'error': f'File preprocessing failed: {str(e)}'}), 400

            # Ensure fixed spatial shape
            try:
                if image_4ch.shape[:3] != TARGET_SPATIAL:
                    logger.info(f"Resampling image from {image_4ch.shape[:3]} to {TARGET_SPATIAL}")
                    img_res = resample_to_target(image_4ch, TARGET_SPATIAL, order=1)
                    if USE_FLOAT16:
                        image_4ch = img_res.astype(np.float16)
                    else:
                        image_4ch = img_res.astype(np.float32)
                    logger.info(f"Resampled image shape: {image_4ch.shape}")

                if mask.shape != TARGET_SPATIAL:
                    logger.info(f"Resampling mask from {mask.shape} to {TARGET_SPATIAL}")
                    mask_res = resample_to_target(mask, TARGET_SPATIAL, order=0)
                    mask = enforce_mask_values(mask_res)
                    logger.info(f"Resampled mask shape: {mask.shape}")

                metas["shape"] = list(mask.shape)
            except Exception as e:
                logger.error(f"Resampling to target shape failed: {e}")
                return jsonify({'ok': False, 'error': f'Failed to resample image/mask to {TARGET_SPATIAL}: {e}'}), 500

            # Prepare batch and dtype
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

            # Save outputs
            case_id = str(uuid.uuid4())
            outputs_dir = app_config.OUTPUTS_DIR
            
            # Save image data in CDHW format for visualization
            image_data_cdhw = np.transpose(image_4ch.astype(np.float32), (3,0,1,2))
            image_filename = f"{case_id}_image_data.npy"
            np.save(outputs_dir / image_filename, image_data_cdhw)
            
            # Save labels
            labels_filename = f"{case_id}_labels.npy"
            np.save(outputs_dir / labels_filename, pred_labels)

            logger.info(f"Saved outputs: {image_filename}, {labels_filename}")

            # Calculate metrics using functions only
            metrics = {}
            if gt_file:
                try:
                    # Load and process ground truth
                    gt_vol = load_nifti_canonical(td_path / 'uploaded_gt.nii.gz')[0]
                    gt_mask = preprocess_mask_multiclass(gt_vol)
                    
                    # Resample ground truth to match prediction
                    if gt_mask.shape != TARGET_SPATIAL:
                        gt_mask_res = resample_to_target(gt_mask, TARGET_SPATIAL, order=0)
                        gt_mask = enforce_mask_values(gt_mask_res)
                    
                    # Convert to proper format for TensorFlow functions
                    pred_probs_tensor = tf.convert_to_tensor(pred_probs[None, ...], dtype=tf.float32)  # (1,D,H,W,C)
                    gt_mask_tensor = tf.convert_to_tensor(gt_mask[None, ..., None], dtype=tf.float32)  # (1,D,H,W,1)
                    
                    # Calculate all metrics using the defined functions only
                    metrics['Mean_Dice'] = float(dice_coef(gt_mask_tensor, pred_probs_tensor).numpy())
                    metrics['IoU'] = float(iou_coef(gt_mask_tensor, pred_probs_tensor).numpy())
                    metrics['Dice_whole_tumor'] = float(dice_whole_tumor(gt_mask_tensor, pred_probs_tensor).numpy())
                    metrics['Dice_tumor_core'] = float(dice_tumor_core(gt_mask_tensor, pred_probs_tensor).numpy())
                    metrics['Dice_enhancing_tumor'] = float(dice_enhancing_tumor(gt_mask_tensor, pred_probs_tensor).numpy())
                    
                    # Print metrics to console
                    logger.info(f"Calculated metrics: {metrics}")
                    print(f"Case ID: {case_id}")
                    print(f"Metrics: {metrics}")
                        
                except Exception as e:
                    logger.error(f"Metrics calculation failed with error: {e}")
                    print(f"ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Try to calculate metrics one by one to see which one fails
                    try:
                        metrics['Mean_Dice'] = float(dice_coef(gt_mask_tensor, pred_probs_tensor).numpy())
                        print("Mean_Dice calculated successfully")
                    except Exception as e1:
                        print(f"Mean_Dice failed: {e1}")
                        metrics['Mean_Dice'] = 0.0
                    
                    try:
                        metrics['IoU'] = float(iou_coef(gt_mask_tensor, pred_probs_tensor).numpy())
                        print("IoU calculated successfully")
                    except Exception as e2:
                        print(f"IoU failed: {e2}")
                        metrics['IoU'] = 0.0
                    
                    try:
                        metrics['Dice_whole_tumor'] = float(dice_whole_tumor(gt_mask_tensor, pred_probs_tensor).numpy())
                        print("Dice_whole_tumor calculated successfully")
                    except Exception as e3:
                        print(f"Dice_whole_tumor failed: {e3}")
                        metrics['Dice_whole_tumor'] = 0.0
                    
                    try:
                        metrics['Dice_tumor_core'] = float(dice_tumor_core(gt_mask_tensor, pred_probs_tensor).numpy())
                        print("Dice_tumor_core calculated successfully")
                    except Exception as e4:
                        print(f"Dice_tumor_core failed: {e4}")
                        metrics['Dice_tumor_core'] = 0.0
                    
                    try:
                        metrics['Dice_enhancing_tumor'] = float(dice_enhancing_tumor(gt_mask_tensor, pred_probs_tensor).numpy())
                        print("Dice_enhancing_tumor calculated successfully")
                    except Exception as e5:
                        print(f"Dice_enhancing_tumor failed: {e5}")
                        metrics['Dice_enhancing_tumor'] = 0.0
            else:
                # Provide dummy metrics when no ground truth
                logger.info("No ground truth provided, showing example metrics")
                metrics['Prediction_Stats'] = f"Classes found: {np.unique(pred_labels).tolist()}"
                metrics['Tumor_Volume'] = f"{np.sum(pred_labels > 0)} voxels"

            return jsonify({
                'ok': True,
                'case_id': case_id,
                'image_filename': image_filename,
                'labels_filename': labels_filename,
                'metrics': metrics,
                'shape': metas["shape"]
            })

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=False)
