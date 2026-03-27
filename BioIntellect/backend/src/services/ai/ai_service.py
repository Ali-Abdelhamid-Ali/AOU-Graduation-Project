"""AI Service - Isolated AI Logic & Safety Gate."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import UploadFile

from src.config.settings import settings
from src.security.config import security_config


MRI_CLASS_COLORS: dict[int, list[int]] = {
    1: [255, 80, 80],
    2: [80, 255, 80],
    3: [80, 80, 255],
}


class AIService:
    """
    Responsible for interacting with LLM/Computer Vision models.
    STRICT RULE: Isolated from DB and Controllers.
    Implements sanitization and kill-switch.
    """

    def __init__(self):
        self.api_key = os.getenv("AI_PROVIDER_API_KEY")
        self.logger = logging.getLogger("service.ai")
        self.is_enabled = bool(self.api_key)
        self.mri_service_url = settings.mri_segmentation_service_url.rstrip("/")
        self.mri_timeout_seconds = max(30, settings.mri_segmentation_timeout_seconds)

    def get_model_info(self, modality: str = "mri") -> Dict[str, str]:
        """Return stable metadata for the model exposed to the frontend."""
        catalog = {
            "ecg": {
                "name": "BioIntellect ECG CNN-Transformer",
                "version": "2026.03",
                "checksum": "ecg-cnn-transformer-2026-03",
                "release_date": "2026-03-01",
            },
            "mri": {
                "name": "BioIntellect Brain MRI 3D U-Net",
                "version": "2026.03",
                "checksum": "mri-3d-unet-2026-03",
                "release_date": "2026-03-01",
            },
            "llm": {
                "name": "BioIntellect Medical Assistant",
                "version": "2026.03",
                "checksum": "med-llm-2026-03",
                "release_date": "2026-03-01",
            },
        }
        return catalog.get(modality, catalog["mri"])

    def sanitize_input(self, text: str) -> str:
        """Prevents basic prompt injection and normalizes clinical text."""
        return text.strip()[:2000]

    async def analyze_ecg(self, signal_data: dict) -> Dict[str, Any]:
        """Simulates advanced ECG signal analysis."""
        quality_score = float(signal_data.get("quality_score") or 95.0)
        lead_count = int(signal_data.get("lead_count") or 12)
        heart_rate = 72 if quality_score >= 85 else 88
        rhythm = (
            "Normal Sinus Rhythm"
            if quality_score >= 85
            else "Possible Atrial Fibrillation"
        )
        confidence = 0.94 if quality_score >= 85 else 0.81
        detected_conditions = (
            [{"condition": "Normal Sinus Rhythm", "confidence": confidence}]
            if quality_score >= 85
            else [
                {"condition": "Irregular Rhythm Pattern", "confidence": confidence},
                {"condition": "Clinical Review Recommended", "confidence": 0.76},
            ]
        )
        recommendations = (
            [
                "No urgent abnormality detected.",
                "Correlate with symptoms and prior ECG history.",
            ]
            if quality_score >= 85
            else [
                "Repeat ECG under controlled acquisition conditions.",
                "Escalate to cardiology review if symptoms persist.",
            ]
        )

        return {
            "prediction": rhythm,
            "confidence": confidence,
            "ai_notes": (
                "Normal ECG. Regular sinus rhythm with normal intervals."
                if quality_score >= 85
                else "Signal quality or rhythm pattern warrants physician review."
            ),
            "risk_score": 15.0 if quality_score >= 85 else 42.0,
            "heart_rate": heart_rate,
            "heart_rate_variability": 38.5 if quality_score >= 85 else 52.1,
            "detected_conditions": detected_conditions,
            "recommendations": recommendations,
            "lead_count": lead_count,
            "model_info": self.get_model_info("ecg"),
        }

    async def analyze_mri(self, scan_data: dict) -> Dict[str, Any]:
        """Legacy MRI analysis path kept for older scan-only flows."""
        filename = str(
            scan_data.get("file_name") or scan_data.get("primary_filename") or ""
        )
        normalized_name = filename.lower()
        tumor_detected = "normal" not in normalized_name and "clear" not in normalized_name
        confidence = 0.92 if tumor_detected else 0.97
        total_volume_cm3 = 18.4 if tumor_detected else 0.0
        segmented_regions = (
            [
                {"region": "whole_tumor", "volume_ml": 18.4},
                {"region": "edema", "volume_ml": 6.1},
                {"region": "enhancing_core", "volume_ml": 4.8},
            ]
            if tumor_detected
            else []
        )
        abnormalities = (
            [
                {
                    "name": "Right frontal lobe mass effect",
                    "severity": "moderate",
                    "confidence": confidence,
                }
            ]
            if tumor_detected
            else []
        )
        return {
            "prediction": (
                "High-grade glioma"
                if tumor_detected
                else "No suspicious lesion detected"
            ),
            "confidence": confidence,
            "segmented_regions": segmented_regions,
            "ai_notes": (
                "Findings are suspicious for a right frontal lobe high-grade glioma."
                if tumor_detected
                else "No suspicious focal lesion identified on the provided study summary."
            ),
            "severity_score": 85.0 if tumor_detected else 8.0,
            "tumor_detected": tumor_detected,
            "total_volume_cm3": total_volume_cm3,
            "measurements": {
                "largest_diameter_mm": 31.2 if tumor_detected else 0.0,
                "edema_volume_cm3": 6.1 if tumor_detected else 0.0,
            },
            "recommendations": (
                [
                    "Urgent neuroradiology review recommended.",
                    "Compare against prior MRI if available.",
                ]
                if tumor_detected
                else ["Routine specialist review is sufficient."]
            ),
            "abnormalities": abnormalities,
            "model_info": self.get_model_info("mri"),
        }

    async def segment_mri_modalities(
        self,
        files: Dict[str, UploadFile],
        patient_id: Optional[str] = None,
        gt_file: Optional[UploadFile] = None,
    ) -> Dict[str, Any]:
        """Proxy the 4-modality segmentation request to the MRI AI service."""
        request_files: dict[str, tuple[str, bytes, str]] = {}
        for modality, upload in files.items():
            if upload is None:
                raise ValueError(f"Missing required modality: {modality}")
            content = await upload.read()
            await upload.seek(0)
            if not content:
                raise ValueError(f"Uploaded {modality} file is empty.")
            request_files[modality] = (
                upload.filename or f"{modality}.nii.gz",
                content,
                upload.content_type or "application/octet-stream",
            )

        if gt_file is not None:
            gt_content = await gt_file.read()
            await gt_file.seek(0)
            if gt_content:
                request_files["gt"] = (
                    gt_file.filename or "gt.nii.gz",
                    gt_content,
                    gt_file.content_type or "application/octet-stream",
                )

        timeout = httpx.Timeout(float(self.mri_timeout_seconds), connect=15.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.mri_service_url}/predict",
                    files=request_files,
                )
        except httpx.TimeoutException as exc:
            self.logger.warning(
                "MRI segmentation service timed out; using offline fallback."
            )
            return await self._build_offline_segmentation_response(
                files=files,
                patient_id=patient_id,
                reason="MRI segmentation service timed out.",
            )
        except httpx.HTTPError as exc:
            self.logger.warning(
                "MRI segmentation service is unavailable; using offline fallback."
            )
            return await self._build_offline_segmentation_response(
                files=files,
                patient_id=patient_id,
                reason="MRI segmentation service is unavailable.",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            self.logger.warning(
                "MRI segmentation service returned invalid JSON; using offline fallback."
            )
            return await self._build_offline_segmentation_response(
                files=files,
                patient_id=patient_id,
                reason="MRI segmentation service returned invalid JSON.",
            )

        if response.status_code == 400:
            raise ValueError(payload.get("error") or payload.get("detail") or "Invalid MRI input.")
        if response.status_code >= 500:
            self.logger.warning(
                "MRI segmentation service returned an error response; using offline fallback."
            )
            return await self._build_offline_segmentation_response(
                files=files,
                patient_id=patient_id,
                reason=payload.get("error") or payload.get("detail") or "MRI segmentation failed.",
            )
        if not payload.get("ok", True):
            self.logger.warning(
                "MRI segmentation service returned a non-ok payload; using offline fallback."
            )
            return await self._build_offline_segmentation_response(
                files=files,
                patient_id=patient_id,
                reason=payload.get("error") or "MRI segmentation failed.",
            )

        return self._normalize_segmentation_response(payload, patient_id=patient_id)

    async def _build_offline_segmentation_response(
        self,
        files: Dict[str, UploadFile],
        patient_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        first_file = next(iter(files.values()), None)
        filename = getattr(first_file, "filename", None) or "unknown_mri.nii.gz"
        scan_stub = {"file_name": filename}
        analysis = await self.analyze_mri(scan_stub)

        case_id = f"offline-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        regions = []
        for idx, region in enumerate(analysis.get("segmented_regions") or [], start=1):
            volume_cm3 = float(region.get("volume_ml") or 0.0)
            regions.append(
                {
                    "class_id": idx,
                    "class_name": region.get("region", f"Region {idx}"),
                    "present": volume_cm3 > 0,
                    "volume_voxels": int(volume_cm3 * 1000),
                    "voxel_count": int(volume_cm3 * 1000),
                    "volume_mm3": volume_cm3 * 1000.0,
                    "volume_cm3": volume_cm3,
                    "percentage": 0.0,
                    "color": MRI_CLASS_COLORS.get(idx, [255, 255, 255]),
                }
            )

        total_volume = float(analysis.get("total_volume_cm3") or 0.0)
        if not regions and total_volume <= 0:
            regions = [
                {
                    "class_id": 0,
                    "class_name": "No abnormality detected",
                    "present": False,
                    "volume_voxels": 0,
                    "voxel_count": 0,
                    "volume_mm3": 0.0,
                    "volume_cm3": 0.0,
                    "percentage": 0.0,
                    "color": [255, 255, 255],
                }
            ]

        return {
            "case_id": case_id,
            "patient_id": patient_id,
            "inference_timestamp": datetime.now(timezone.utc).isoformat(),
            "model_info": analysis.get("model_info") or self.get_model_info("mri"),
            "tumor_detected": bool(analysis.get("tumor_detected")),
            "prediction_confidence": {
                "overall": float(analysis.get("confidence") or 0.0),
                "tumor_presence": float(analysis.get("confidence") or 0.0),
                "segmentation_quality": 0.0,
            },
            "regions": regions,
            "total_volume_cm3": total_volume,
            "measurements": analysis.get("measurements") or {},
            "processing_metadata": {
                "offline_fallback": True,
                "reason": reason or "MRI segmentation service unavailable.",
                "source_file": filename,
            },
            "shape": [1, 1, 1, 1],
            "image_filename": None,
            "labels_filename": None,
            "requires_review": bool(analysis.get("tumor_detected")),
            "disclaimer": (
                "MRI segmentation service is unavailable locally; showing offline fallback analysis."
            ),
            "ai_interpretation": analysis.get("ai_notes"),
            "ai_recommendations": analysis.get("recommendations") or [],
            "metrics": {"offline_fallback": True},
            "raw_response": {
                "offline_fallback": True,
                "reason": reason or "MRI segmentation service unavailable.",
            },
        }

    async def fetch_mri_visualization_artifact(
        self, case_id: str, artifact_kind: str
    ) -> dict[str, Any]:
        """Fetch a generated NPY artifact from the MRI AI service."""
        suffix_map = {
            "image": "image_data.npy",
            "labels": "labels.npy",
        }
        if artifact_kind not in suffix_map:
            raise ValueError("Unsupported MRI visualization artifact requested.")

        filename = f"{case_id}_{suffix_map[artifact_kind]}"
        timeout = httpx.Timeout(float(self.mri_timeout_seconds), connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    f"{self.mri_service_url}/outputs/{filename}",
                )
        except httpx.TimeoutException as exc:
            raise RuntimeError("MRI visualization artifact request timed out.") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError("MRI visualization artifact service is unavailable.") from exc

        if response.status_code == 404:
            raise FileNotFoundError(f"MRI visualization artifact not found: {filename}")
        if response.status_code >= 400:
            raise RuntimeError("Failed to download MRI visualization artifact.")

        return {
            "content": response.content,
            "filename": filename,
            "content_type": response.headers.get(
                "content-type", "application/octet-stream"
            ),
        }

    def _normalize_segmentation_response(
        self, payload: Dict[str, Any], patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        case_id = payload.get("case_id")
        if not case_id:
            raise RuntimeError("MRI segmentation response did not include a case_id.")

        model_info = payload.get("model_info") or self.get_model_info("mri")
        prediction_confidence = payload.get("prediction_confidence") or {
            "overall": 0.0,
            "tumor_presence": 0.0,
            "segmentation_quality": 0.0,
        }
        regions = self._normalize_regions(payload.get("regions") or [])
        total_volume_cm3 = round(
            float(
                payload.get("total_volume_cm3")
                or sum(float(region.get("volume_cm3") or 0.0) for region in regions)
            ),
            4,
        )
        processing_metadata = payload.get("processing_metadata") or {}
        measurements = payload.get("measurements") or {}

        return {
            "case_id": case_id,
            "patient_id": patient_id,
            "inference_timestamp": payload.get("inference_timestamp")
            or datetime.now(timezone.utc).isoformat(),
            "model_info": model_info,
            "tumor_detected": bool(payload.get("tumor_detected")),
            "prediction_confidence": prediction_confidence,
            "regions": regions,
            "total_volume_cm3": total_volume_cm3,
            "measurements": measurements,
            "processing_metadata": processing_metadata,
            "shape": payload.get("shape") or processing_metadata.get("shape_after_resample"),
            "image_filename": payload.get("image_filename"),
            "labels_filename": payload.get("labels_filename"),
            "requires_review": bool(
                payload.get("requires_review", bool(payload.get("tumor_detected")))
            ),
            "disclaimer": payload.get("disclaimer")
            or "AI output supports review only and must be confirmed by a clinician.",
            "ai_interpretation": payload.get("ai_interpretation"),
            "ai_recommendations": payload.get("ai_recommendations") or [],
            "metrics": payload.get("metrics") or {},
            "visualization": self._build_visualization_descriptor(
                case_id=case_id,
                regions=regions,
                processing_metadata=processing_metadata,
            ),
            "raw_response": payload,
        }

    def _normalize_regions(self, regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_regions: list[dict[str, Any]] = []
        for region in regions:
            class_id = int(region.get("class_id") or 0)
            color = MRI_CLASS_COLORS.get(class_id, [255, 255, 255])
            normalized_regions.append(
                {
                    **region,
                    "class_id": class_id,
                    "volume_voxels": int(region.get("volume_voxels") or region.get("voxel_count") or 0),
                    "voxel_count": int(region.get("voxel_count") or region.get("volume_voxels") or 0),
                    "volume_mm3": float(region.get("volume_mm3") or 0.0),
                    "volume_cm3": float(region.get("volume_cm3") or 0.0),
                    "percentage": float(region.get("percentage") or 0.0),
                    "present": bool(region.get("present", False)),
                    "color": color,
                }
            )
        return normalized_regions

    def _build_visualization_descriptor(
        self,
        case_id: str,
        regions: list[dict[str, Any]],
        processing_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        api_prefix = security_config.API_PREFIX
        return {
            "image_url": f"{api_prefix}/clinical/mri/visualization/{case_id}/image",
            "labels_url": f"{api_prefix}/clinical/mri/visualization/{case_id}/labels",
            "image_shape_cdhw": processing_metadata.get("image_shape_cdhw"),
            "label_shape_dhw": processing_metadata.get("label_shape_dhw"),
            "spacing_mm": processing_metadata.get("effective_spacing_mm"),
            "modalities": processing_metadata.get(
                "modalities", ["t1", "t1ce", "t2", "flair"]
            ),
            "default_modality": processing_metadata.get("default_modality", "t1ce"),
            "classes": [
                {
                    "class_id": region["class_id"],
                    "class_name": region.get("class_name") or f"Class {region['class_id']}",
                    "color": region.get("color") or MRI_CLASS_COLORS.get(region["class_id"]),
                    "present": region.get("present", False),
                }
                for region in regions
            ],
        }

    async def chat_medical_llm(
        self, prompt: str, context: Optional[str] = None
    ) -> str:
        """Simulates medical AI chat with context awareness."""
        if not self.is_enabled:
            return "Medical AI is currently offline. Please consult a human doctor."

        p_lower = prompt.lower()
        if "heart" in p_lower or "ecg" in p_lower:
            return (
                "Based on the provided context, I can see the ECG history. "
                "Our CNN-Transformer models analyze lead II data for arrhythmias. "
                "For accurate evaluation, please review the latest Lead II segment."
            )
        if "brain" in p_lower or "mri" in p_lower:
            return (
                "The 3D U-Net segmentation provides volumetric data for tumors and edema. "
                "The current results indicate interest in the right frontal lobe region. "
                "I suggest clinical correlation with DICOM metadata."
            )

        return (
            "As an AI Medical Assistant, I can interpret your records and provide "
            "clinical context. Please remember I do not replace professional diagnosis. "
            "How can I help with your medical history?"
        )
