from __future__ import annotations

import numpy as np
import pywt
from scipy import signal as scipy_signal


def quality_check(ecg: np.ndarray, fs=500) -> dict:
    report = {}

    report["has_nan"] = np.isnan(ecg).any()
    report["has_inf"] = np.isinf(ecg).any()

    flat_leads = []
    for i in range(ecg.shape[1]):
        if ecg[:, i].std() < 1e-6:
            flat_leads.append(i)
    report["flat_leads"] = flat_leads

    report["amplitude_ok"] = np.abs(ecg).max() < 50.0

    saturation_ratio = (np.abs(ecg) > 10.0).mean()
    report["saturation_ratio"] = saturation_ratio
    report["is_saturated"] = saturation_ratio > 0.05

    report["is_valid"] = (
        not report["has_nan"]
        and not report["has_inf"]
        and len(report["flat_leads"]) == 0
        and report["amplitude_ok"]
        and not report["is_saturated"]
    )

    return report


def fix_signal(ecg: np.ndarray) -> np.ndarray:
    ecg = np.nan_to_num(ecg, nan=0.0, posinf=0.0, neginf=0.0)

    for i in range(ecg.shape[1]):
        if ecg[:, i].std() < 1e-6:
            if i > 0:
                ecg[:, i] = ecg[:, i - 1]
            else:
                ecg[:, i] = np.zeros(ecg.shape[0])

    return ecg


def remove_baseline_wander(ecg: np.ndarray, fs=500) -> np.ndarray:
    corrected = np.zeros_like(ecg, dtype=np.float32)

    for i in range(ecg.shape[1]):
        wavelet = "db4"
        level = 9

        coeffs = pywt.wavedec(ecg[:, i], wavelet, level=level)
        coeffs[0] = np.zeros_like(coeffs[0])
        coeffs[1] = np.zeros_like(coeffs[1])

        corrected[:, i] = pywt.waverec(coeffs, wavelet)[: ecg.shape[0]]

    return corrected


def remove_powerline_noise(ecg: np.ndarray, fs=500, freq=50.0) -> np.ndarray:
    b, a = scipy_signal.iirnotch(freq, Q=30, fs=fs)

    filtered = np.zeros_like(ecg, dtype=np.float32)
    for i in range(ecg.shape[1]):
        filtered[:, i] = scipy_signal.filtfilt(b, a, ecg[:, i])

    for harmonic in [100.0, 150.0]:
        if harmonic < fs / 2:
            b, a = scipy_signal.iirnotch(harmonic, Q=30, fs=fs)
            for i in range(ecg.shape[1]):
                filtered[:, i] = scipy_signal.filtfilt(b, a, filtered[:, i])

    return filtered


def bandpass_filter(
    ecg: np.ndarray, lowcut=0.5, highcut=40.0, fs=500, order=4
) -> np.ndarray:
    nyquist = fs / 2.0

    lowcut = max(lowcut, 0.1)
    highcut = min(highcut, nyquist - 1)

    sos = scipy_signal.butter(
        order,
        [lowcut / nyquist, highcut / nyquist],
        btype="bandpass",
        output="sos",
    )

    filtered = np.zeros_like(ecg, dtype=np.float32)
    for i in range(ecg.shape[1]):
        filtered[:, i] = scipy_signal.sosfiltfilt(sos, ecg[:, i])

    return filtered


def wavelet_denoise(ecg: np.ndarray, wavelet="db6", level=4) -> np.ndarray:
    denoised = np.zeros_like(ecg, dtype=np.float32)

    for i in range(ecg.shape[1]):
        coeffs = pywt.wavedec(ecg[:, i], wavelet, level=level)

        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(ecg[:, i])))

        coeffs_thresh = [pywt.threshold(c, threshold, mode="soft") for c in coeffs]
        coeffs_thresh[0] = coeffs[0]

        denoised[:, i] = pywt.waverec(coeffs_thresh, wavelet)[: ecg.shape[0]]

    return denoised


def normalize_ecg(ecg: np.ndarray, method="robust_zscore") -> np.ndarray:
    eps = 1e-8

    if method == "per_lead_zscore":
        mean = ecg.mean(axis=0, keepdims=True)
        std = ecg.std(axis=0, keepdims=True)
        return ((ecg - mean) / (std + eps)).astype(np.float32)

    if method == "clip_zscore":
        mean = ecg.mean(axis=0, keepdims=True)
        std = ecg.std(axis=0, keepdims=True)
        return np.clip((ecg - mean) / (std + eps), -4.0, 4.0).astype(np.float32)

    if method == "robust_zscore":
        median = np.median(ecg, axis=0, keepdims=True)
        mad = np.median(np.abs(ecg - median), axis=0, keepdims=True)
        normalized = (ecg - median) / (mad * 1.4826 + eps)
        return np.clip(normalized, -4.0, 4.0).astype(np.float32)

    if method == "minmax":
        min_val = ecg.min(axis=0, keepdims=True)
        max_val = ecg.max(axis=0, keepdims=True)
        return ((ecg - min_val) / (max_val - min_val + eps)).astype(np.float32)

    raise ValueError(f"Unknown method: {method}")


def full_preprocess_pipeline(
    ecg: np.ndarray,
    fs=500,
    training=False,
    use_wavelet=True,
    return_features=False,
) -> dict:
    results = {}

    report = quality_check(ecg, fs)
    results["quality_report"] = report
    if not report["is_valid"]:
        ecg = fix_signal(ecg)

    ecg = remove_baseline_wander(ecg, fs)
    ecg = remove_powerline_noise(ecg, fs, freq=50.0)
    ecg = bandpass_filter(ecg, lowcut=0.5, highcut=40.0, fs=fs, order=4)

    if use_wavelet:
        ecg = wavelet_denoise(ecg, wavelet="db6", level=4)

    ecg = normalize_ecg(ecg, method="clip_zscore")
    results["processed_ecg"] = ecg
    return results


def preprocess_ecg(ecg: np.ndarray, fs=500, training=False) -> np.ndarray:
    result = full_preprocess_pipeline(
        ecg,
        fs=fs,
        training=training,
        use_wavelet=True,
        return_features=False,
    )
    return result["processed_ecg"]
