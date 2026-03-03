"""File Routes & Controller - Medical Document API."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Optional, Any
from src.services.domain.file_service import FileService
from src.repositories.storage_repository import StorageRepository
from src.repositories.clinical_repository import ClinicalRepository
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger

logger = get_logger("routes.file")

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        429: {"description": "Too Many Requests"},
        500: {"description": "Internal Server Error"},
    },
)


def get_file_service():
    return FileService(StorageRepository(), ClinicalRepository())


@router.post(
    "/upload", dependencies=[Depends(require_permission(Permission.CREATE_CASE))]
)
async def upload_file(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    patient_id: str = Form(...),
    file_type: str = Form(...),
    user: dict[str, Any] = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
):
    """Upload a general medical file."""
    try:
        content = await file.read()

        # Validate file size (max 50MB)
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=413, detail="File too large. Maximum size is 50MB."
            )

        # Validate file type
        valid_types = ["ecg", "mri", "pdf", "image"]
        if file_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Must be one of: {', '.join(valid_types)}",
            )

        filename = file.filename or "unknown_file"
        record = await service.upload_medical_file(
            user["id"],
            patient_id,
            case_id,
            filename,
            content,
            file.content_type or "application/octet-stream",
            file_type,
        )

        logger.info(f"File uploaded successfully by user {user['id']}: {record['id']}")
        return {"success": True, "data": record}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


@router.post(
    "/ecg/upload", dependencies=[Depends(require_permission(Permission.CREATE_CASE))]
)
async def upload_ecg_signal(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    patient_id: str = Form(...),
    user: dict[str, Any] = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
):
    """Upload an ECG signal file and create corresponding signal record."""
    try:
        content = await file.read()

        # Validate file size (max 10MB for ECG)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413, detail="ECG file too large. Maximum size is 10MB."
            )

        # Validate file type for ECG
        filename = file.filename or ""
        valid_ecg_types = [
            "application/dicom",
            "application/octet-stream",
            "image/jpeg",
            "image/png",
        ]
        if file.content_type not in valid_ecg_types and not filename.lower().endswith(
            (".dcm", ".jpg", ".jpeg", ".png")
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid ECG file format. Must be DICOM or medical image format.",
            )

        result = await service.upload_ecg_signal(
            user["id"],
            patient_id,
            case_id,
            filename,
            content,
            file.content_type or "application/octet-stream",
        )

        logger.info(
            f"ECG signal uploaded successfully by user {user['id']}: {result['signal_record']['id']}"
        )
        return {"success": True, "data": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ECG upload failed for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload ECG signal")


@router.post(
    "/mri/upload", dependencies=[Depends(require_permission(Permission.CREATE_CASE))]
)
async def upload_mri_scan(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    patient_id: str = Form(...),
    user: dict[str, Any] = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
):
    """Upload an MRI scan file and create corresponding scan record."""
    try:
        content = await file.read()

        # Validate file size (max 100MB for MRI)
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=413, detail="MRI file too large. Maximum size is 100MB."
            )

        # Validate file type for MRI
        filename = file.filename or ""
        valid_mri_types = [
            "application/dicom",
            "application/octet-stream",
            "image/jpeg",
            "image/png",
        ]
        if file.content_type not in valid_mri_types and not filename.lower().endswith(
            (".dcm", ".jpg", ".jpeg", ".png")
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid MRI file format. Must be DICOM or medical image format.",
            )

        result = await service.upload_mri_scan(
            user["id"],
            patient_id,
            case_id,
            filename,
            content,
            file.content_type or "application/octet-stream",
        )

        logger.info(
            f"MRI scan uploaded successfully by user {user['id']}: {result['scan_record']['id']}"
        )
        return {"success": True, "data": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MRI upload failed for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload MRI scan")


@router.get(
    "/{file_id}/download",
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_download_url(
    file_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
):
    """Get a signed URL for downloading a file."""
    try:
        url = await service.get_download_link(user["id"], file_id)
        logger.info(f"Download URL generated for file {file_id} by user {user['id']}")
        return {"success": True, "url": url}

    except Exception as e:
        logger.error(f"Failed to get download URL for file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get download URL")


@router.delete(
    "/{file_id}", dependencies=[Depends(require_permission(Permission.CREATE_CASE))]
)
async def delete_medical_file(
    file_id: str,
    reason: Optional[str] = Form(None),
    user: dict[str, Any] = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
):
    """Delete a medical file from storage and mark as deleted in database."""
    try:
        success = await service.delete_medical_file(user["id"], file_id, reason)

        if not success:
            raise HTTPException(status_code=404, detail="File not found")

        logger.info(
            f"Medical file deleted successfully by user {user['id']}: {file_id}"
        )
        return {"success": True, "message": "File deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete file")

