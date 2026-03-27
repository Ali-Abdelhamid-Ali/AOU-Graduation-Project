"""File Service - Secure Medical Document Management."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.observability.audit import AuditAction, log_audit
from src.observability.logger import get_logger
from src.repositories.clinical_repository import ClinicalRepository
from src.repositories.storage_repository import StorageRepository

logger = get_logger("service.file")


MRI_FILE_SUFFIXES = (".dcm", ".dicom", ".jpg", ".jpeg", ".png", ".nii", ".nii.gz")
GENERAL_MEDICAL_FILE_TYPES = ("ecg", "mri")
DEFAULT_STORAGE_BUCKET = "medical-files"
STORAGE_BUCKET_BY_FILE_TYPE = {
    "ecg": "ecg-files",
    "mri": "mri-files",
}


def get_preserved_extension(file_name: str) -> str:
    """Preserve compound extensions such as `.nii.gz` for stored filenames."""
    normalized_name = (file_name or "").lower()
    if normalized_name.endswith(".nii.gz"):
        return ".nii.gz"

    suffix = Path(file_name or "").suffix.lower()
    return suffix or ".bin"


def normalize_upload_content_type(file_name: str, content_type: Optional[str]) -> str:
    """Normalize browser-specific MIME types to storage-safe values."""
    normalized_type = (content_type or "").split(";")[0].strip().lower()
    extension = get_preserved_extension(file_name)

    if extension in {".nii", ".nii.gz", ".gz"}:
        return "application/octet-stream"
    if extension in {".dcm", ".dicom"}:
        return "application/dicom"
    if extension == ".pdf":
        return "application/pdf"
    if extension in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if extension == ".png":
        return "image/png"
    if normalized_type in {"application/x-gzip", "application/gzip"}:
        return "application/octet-stream"

    return normalized_type or "application/octet-stream"


def is_supported_mri_upload(file_name: str, content_type: Optional[str]) -> bool:
    """Validate MRI uploads including NIfTI and DICOM payloads."""
    normalized_name = (file_name or "").lower()
    if not normalized_name.endswith(MRI_FILE_SUFFIXES):
        return False

    return normalize_upload_content_type(file_name, content_type) in {
        "application/dicom",
        "application/octet-stream",
        "image/jpeg",
        "image/png",
    }


def resolve_storage_bucket(
    file_type: Optional[str] = None, storage_bucket: Optional[str] = None
) -> str:
    """Resolve the storage bucket from persisted metadata or file type."""
    if storage_bucket:
        return storage_bucket

    normalized_file_type = str(file_type or "").strip().lower()
    return STORAGE_BUCKET_BY_FILE_TYPE.get(
        normalized_file_type, DEFAULT_STORAGE_BUCKET
    )


class FileService:
    def __init__(
        self, storage_repo: StorageRepository, clinical_repo: ClinicalRepository
    ):
        self.storage_repo = storage_repo
        self.clinical_repo = clinical_repo

    async def upload_medical_file(
        self,
        user_id: str,
        patient_id: str,
        case_id: str,
        file_name: str,
        content: bytes,
        content_type: str,
        file_type: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Orchestrates storage upload and metadata persistence."""

        try:
            normalized_content_type = normalize_upload_content_type(
                file_name, content_type
            )
            storage_bucket = resolve_storage_bucket(file_type=file_type)

            unique_name = (
                f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                f"{get_preserved_extension(file_name)}"
            )
            storage_path = f"{patient_id}/{case_id}/{unique_name}"

            await self.storage_repo.upload_file(
                storage_path,
                content,
                normalized_content_type,
                bucket_name=storage_bucket,
            )

            metadata = {
                "case_id": case_id,
                "patient_id": patient_id,
                "uploaded_by": user_id,
                "file_type": file_type,
                "file_name": file_name,
                "file_path": storage_path,
                "file_size": len(content),
                "mime_type": normalized_content_type,
                "storage_bucket": storage_bucket,
                "description": description,
                "is_analyzed": False,
            }

            file_record = await self.clinical_repo.create_medical_file(metadata)
            if not file_record:
                raise Exception("Failed to create medical file record")

            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={
                    "file_id": file_record["id"],
                    "action": "upload_file",
                    "file_type": file_type,
                    "storage_bucket": storage_bucket,
                },
            )

            logger.info(
                f"Medical file uploaded successfully: {file_record['id']} for patient {patient_id}"
            )
            return file_record

        except Exception as e:
            logger.error(f"Failed to upload medical file: {str(e)}")
            raise

    async def get_download_link(self, user_id: str, file_id: str) -> str:
        """Fetch signed URL for a specific file."""
        try:
            file_meta = await self.clinical_repo.get_medical_file(file_id)
            if not file_meta:
                raise Exception("File not found")

            storage_bucket = resolve_storage_bucket(
                file_type=file_meta.get("file_type"),
                storage_bucket=file_meta.get("storage_bucket"),
            )
            url = await self.storage_repo.get_signed_url(
                file_meta["file_path"], bucket_name=storage_bucket
            )

            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={"file_id": file_id, "action": "get_download_link"},
            )

            logger.info(f"Download link generated for file: {file_id}")
            return url

        except Exception as e:
            logger.error(f"Failed to get download link for file {file_id}: {str(e)}")
            raise

    async def upload_ecg_signal(
        self,
        user_id: str,
        patient_id: str,
        case_id: str,
        file_name: str,
        content: bytes,
        content_type: str,
    ) -> Dict[str, Any]:
        """Upload ECG signal file and create corresponding signal record."""

        try:
            normalized_content_type = normalize_upload_content_type(
                file_name, content_type
            )

            file_record = await self.upload_medical_file(
                user_id,
                patient_id,
                case_id,
                file_name,
                content,
                normalized_content_type,
                "ecg",
            )

            signal_data = {
                "patient_id": patient_id,
                "case_id": case_id,
                "file_id": file_record["id"],
                "signal_data": {
                    "file_name": file_name,
                    "file_size": len(content),
                    "content_type": normalized_content_type,
                    "uploaded_at": datetime.now().isoformat(),
                },
            }

            ecg_signal = await self.clinical_repo.create_ecg_signal(signal_data)
            if not ecg_signal:
                raise Exception("Failed to create ECG signal record")

            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={
                    "signal_id": ecg_signal["id"],
                    "action": "create_ecg_signal",
                    "file_id": file_record["id"],
                },
            )

            logger.info(
                f"ECG signal created successfully: {ecg_signal['id']} for patient {patient_id}"
            )
            return {"file_record": file_record, "signal_record": ecg_signal}

        except Exception as e:
            logger.error(f"Failed to upload ECG signal: {str(e)}")
            raise

    async def upload_mri_scan(
        self,
        user_id: str,
        patient_id: str,
        case_id: str,
        file_name: str,
        content: bytes,
        content_type: str,
    ) -> Dict[str, Any]:
        """Upload MRI scan file and create corresponding scan record."""

        try:
            normalized_content_type = normalize_upload_content_type(
                file_name, content_type
            )

            file_record = await self.upload_medical_file(
                user_id,
                patient_id,
                case_id,
                file_name,
                content,
                normalized_content_type,
                "mri",
            )

            scan_data = {
                "patient_id": patient_id,
                "case_id": case_id,
                "file_id": file_record["id"],
                "dicom_metadata": {
                    "file_name": file_name,
                    "file_size": len(content),
                    "content_type": normalized_content_type,
                    "uploaded_at": datetime.now().isoformat(),
                    "is_dicom": normalized_content_type == "application/dicom"
                    or file_name.lower().endswith(".dcm"),
                },
            }

            mri_scan = await self.clinical_repo.create_mri_scan(scan_data)
            if not mri_scan:
                raise Exception("Failed to create MRI scan record")

            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={
                    "scan_id": mri_scan["id"],
                    "action": "create_mri_scan",
                    "file_id": file_record["id"],
                },
            )

            logger.info(
                f"MRI scan created successfully: {mri_scan['id']} for patient {patient_id}"
            )
            return {"file_record": file_record, "scan_record": mri_scan}

        except Exception as e:
            logger.error(f"Failed to upload MRI scan: {str(e)}")
            raise

    async def delete_medical_file(
        self, user_id: str, file_id: str, reason: Optional[str] = None
    ) -> bool:
        """Delete a medical file from storage and mark as deleted in database."""

        try:
            file_meta = await self.clinical_repo.get_medical_file(file_id)
            if not file_meta:
                raise Exception("File not found")

            storage_bucket = resolve_storage_bucket(
                file_type=file_meta.get("file_type"),
                storage_bucket=file_meta.get("storage_bucket"),
            )
            await self.storage_repo.delete_file(
                file_meta["file_path"], bucket_name=storage_bucket
            )

            success = await self.clinical_repo.delete_medical_file(
                file_id, user_id, reason
            )

            if success:
                log_audit(
                    AuditAction.DELETE_MEDICAL_DATA,
                    user_id=user_id,
                    details={
                        "file_id": file_id,
                        "action": "delete_medical_file",
                        "reason": reason,
                    },
                )

                logger.info(f"Medical file deleted successfully: {file_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete medical file {file_id}: {str(e)}")
            raise

    async def upload_avatar(
        self, user_id: str, file_name: str, content: bytes, content_type: str
    ) -> str:
        """Uploads user identity photo and returns the storage path."""
        try:
            ext = file_name.split(".")[-1] if "." in file_name else "png"
            path = f"avatars/{user_id}/{uuid.uuid4().hex}.{ext}"

            await self.storage_repo.upload_file(
                path, content, content_type, bucket_name="avatars"
            )

            log_audit(
                AuditAction.ANALYZE_IMAGE,
                user_id=user_id,
                details={"action": "upload_avatar", "path": path},
            )

            logger.info(f"Avatar uploaded successfully for user: {user_id}")
            return path

        except Exception as e:
            logger.error(f"Failed to upload avatar for user {user_id}: {str(e)}")
            raise
