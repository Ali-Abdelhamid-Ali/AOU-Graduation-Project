"""File Service - Secure Medical Document Management."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from src.repositories.storage_repository import StorageRepository
from src.repositories.clinical_repository import ClinicalRepository
from src.observability.audit import log_audit, AuditAction
from src.observability.logger import get_logger

logger = get_logger("service.file")


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
    ) -> Dict[str, Any]:
        """Orchestrates storage upload and metadata persistence."""

        try:
            # 1. Generate secure path
            ext = file_name.split(".")[-1] if "." in file_name else "bin"
            unique_name = (
                f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            )
            storage_path = f"{patient_id}/{case_id}/{unique_name}"

            # 2. Upload to storage
            await self.storage_repo.upload_file(storage_path, content, content_type)

            # 3. Create DB Record (Metadata)
            metadata = {
                "case_id": case_id,
                "patient_id": patient_id,
                "uploaded_by": user_id,
                "file_type": file_type,
                "file_name": file_name,
                "file_path": storage_path,
                "file_size": len(content),
                "mime_type": content_type,
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

            url = await self.storage_repo.get_signed_url(file_meta["file_path"])

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
            # 1. Upload medical file
            file_record = await self.upload_medical_file(
                user_id, patient_id, case_id, file_name, content, content_type, "ecg"
            )

            # 2. Create ECG signal record
            signal_data = {
                "patient_id": patient_id,
                "case_id": case_id,
                "file_id": file_record["id"],
                "signal_data": {
                    "file_name": file_name,
                    "file_size": len(content),
                    "content_type": content_type,
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
            # 1. Upload medical file
            file_record = await self.upload_medical_file(
                user_id, patient_id, case_id, file_name, content, content_type, "mri"
            )

            # 2. Create MRI scan record
            scan_data = {
                "patient_id": patient_id,
                "case_id": case_id,
                "file_id": file_record["id"],
                "dicom_metadata": {
                    "file_name": file_name,
                    "file_size": len(content),
                    "content_type": content_type,
                    "uploaded_at": datetime.now().isoformat(),
                    "is_dicom": content_type == "application/dicom"
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
            # 1. Get file metadata
            file_meta = await self.clinical_repo.get_medical_file(file_id)
            if not file_meta:
                raise Exception("File not found")

            # 2. Delete from storage
            await self.storage_repo.delete_file(file_meta["file_path"])

            # 3. Mark as deleted in database
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

            await self.storage_repo.upload_file(path, content, content_type)

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

