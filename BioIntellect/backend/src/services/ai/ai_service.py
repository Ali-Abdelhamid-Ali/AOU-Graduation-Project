"""AI Service - Isolated AI Logic & Safety Gate."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import UploadFile

from src.config.settings import settings
from src.security.config import security_config
from src.services.ai.ecg_inference import ECGInferenceEngine
from src.services.ai.mri_inference import MRIInferenceEngine


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
        self.ecg_inference = ECGInferenceEngine()
        self.mri_inference = MRIInferenceEngine()

    def get_model_info(self, modality: str = "mri") -> Dict[str, str]:
        """Return stable metadata for the model exposed to the frontend."""
        catalog = {
            "ecg": {
                "name": "BioIntellect ECG Multimodal InceptionTime",
                "version": "2026.04",
                "checksum": "ecg-inceptiontime-multimodal-asymmetric-loss",
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

    async def analyze_ecg(
        self, signal_data: dict, raw_file_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Runs model-based ECG preprocessing + inference using trained weights."""
        payload: Any = raw_file_bytes if raw_file_bytes is not None else signal_data
        if payload is None:
            raise ValueError("Missing ECG payload for analysis.")

        analysis = self.ecg_inference.predict(payload, signal_meta=signal_data or {})
        analysis["model_info"] = self.get_model_info("ecg")
        return analysis

    async def analyze_mri(self, scan_data: dict) -> Dict[str, Any]:
        """Legacy MRI analysis path — no longer supported.

        Use ``segment_mri_modalities()`` with the four NIfTI modality files
        (T1, T1ce, T2, FLAIR) via ``POST /clinical/mri/segment`` instead.
        """
        raise NotImplementedError(
            "Legacy single-scan MRI analysis is retired. "
            "Use POST /clinical/mri/segment with the four NIfTI modality "
            "files (T1, T1ce, T2, FLAIR) for real model inference."
        )

    async def segment_mri_modalities(
        self,
        files: Dict[str, UploadFile],
        patient_id: Optional[str] = None,
        gt_file: Optional[UploadFile] = None,
    ) -> Dict[str, Any]:
        """Run 4-modality MRI segmentation using the local 3D U-Net model."""
        modality_bytes: Dict[str, bytes] = {}
        for modality, upload in files.items():
            if upload is None:
                raise ValueError(f"Missing required modality: {modality}")
            content = await upload.read()
            await upload.seek(0)
            if not content:
                raise ValueError(f"Uploaded {modality} file is empty.")
            modality_bytes[modality] = content

        gt_bytes: Optional[bytes] = None
        if gt_file is not None:
            gt_bytes = await gt_file.read()
            await gt_file.seek(0)
            if not gt_bytes:
                gt_bytes = None

        payload = await self.mri_inference.predict(
            modality_bytes=modality_bytes,
            patient_id=patient_id or "uploaded",
            gt_bytes=gt_bytes,
        )

        return self._normalize_segmentation_response(payload, patient_id=patient_id)

    async def fetch_mri_visualization_artifact(
        self, case_id: str, artifact_kind: str
    ) -> dict[str, Any]:
        """Read a generated NPY artifact from the local outputs directory."""
        suffix_map = {
            "image": "image_data.npy",
            "labels": "labels.npy",
        }
        if artifact_kind not in suffix_map:
            raise ValueError("Unsupported MRI visualization artifact requested.")

        filename = f"{case_id}_{suffix_map[artifact_kind]}"
        filepath = self.mri_inference.outputs_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"MRI visualization artifact not found: {filename}")

        return {
            "content": filepath.read_bytes(),
            "filename": filename,
            "content_type": "application/octet-stream",
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
        """Route medical chat to the configured LLM provider."""
        if not self.is_enabled:
            return (
                "Medical AI chat is not available. "
                "No LLM provider is currently configured. "
                "Please consult a qualified clinician."
            )

        raise NotImplementedError(
            "Medical LLM chat requires a configured LLM provider. "
            "Connect an LLM backend in settings to enable this feature."
        )
