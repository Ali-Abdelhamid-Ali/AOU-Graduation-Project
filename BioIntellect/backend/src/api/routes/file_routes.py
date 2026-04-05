"""File Routes & Controller - Medical Document API."""
# ruff: noqa: B008

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.observability.logger import get_logger
from src.repositories.clinical_repository import ClinicalRepository
from src.repositories.storage_repository import StorageRepository
from src.repositories.user_repository import UserRepository
from src.security.auth_middleware import (
    Permission,
    get_current_user,
    require_permission,
)
from src.services.domain.file_service import (
    GENERAL_MEDICAL_FILE_TYPES,
    FileService,
    is_supported_ecg_upload,
    is_supported_mri_upload,
    normalize_upload_content_type,
)

logger = get_logger("routes.file")

READ_CHUNK_SIZE = 1024 * 1024

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


def _get_case_and_patient_repositories() -> tuple[ClinicalRepository, UserRepository]:
    return ClinicalRepository(), UserRepository()


async def _read_upload_with_size_limit(
    file: UploadFile, max_size: int, error_message: str
) -> bytes:
    declared_size = file.headers.get("content-length") if file.headers else None
    if declared_size:
        try:
            if int(declared_size) > max_size:
                raise HTTPException(status_code=413, detail=error_message)
        except ValueError:
            pass

    total_size = 0
    chunks: list[bytes] = []
    while True:
        chunk = await file.read(READ_CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size:
            raise HTTPException(status_code=413, detail=error_message)
        chunks.append(chunk)

    return b"".join(chunks)


async def _validate_case_and_patient(case_id: str, patient_id: str) -> None:
    clinical_repo, user_repo = _get_case_and_patient_repositories()

    case_record = await clinical_repo.get_medical_case(case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Medical case not found")

    patient_record = await user_repo.get_patient(patient_id)
    if not patient_record:
        raise HTTPException(status_code=404, detail="Patient not found")

    case_patient_id = str(case_record.get("patient_id") or "")
    if case_patient_id and case_patient_id != str(patient_id):
        raise HTTPException(
            status_code=400,
            detail="case_id does not belong to the provided patient_id",
        )


@router.post(
    "/upload", dependencies=[Depends(require_permission(Permission.UPLOAD_FILES))]
)
async def upload_file(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    patient_id: str = Form(...),
    file_type: str = Form(...),
    description: Optional[str] = Form(None),
    user: dict[str, Any] = Depends(get_current_user),
    service: FileService = Depends(get_file_service),
):
    """Upload a general medical file."""
    try:
        content = await _read_upload_with_size_limit(
            file,
            max_size=50 * 1024 * 1024,
            error_message="File too large. Maximum size is 50MB.",
        )

        if file_type not in GENERAL_MEDICAL_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid file type. Must be one of: "
                    f"{', '.join(GENERAL_MEDICAL_FILE_TYPES)}"
                ),
            )

        filename = file.filename or "unknown_file"
        normalized_content_type = normalize_upload_content_type(
            filename, file.content_type
        )
        if file_type == "mri" and not is_supported_mri_upload(
            filename, normalized_content_type
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid MRI file format. Supported formats: .nii, .nii.gz, "
                    ".dcm, .jpg, .jpeg, .png"
                ),
            )
        if file_type == "ecg" and not is_supported_ecg_upload(filename):
            raise HTTPException(
                status_code=400,
                detail="Invalid ECG file format. Supported format: .dat",
            )

        await _validate_case_and_patient(case_id, patient_id)

        record = await service.upload_medical_file(
            user["id"],
            patient_id,
            case_id,
            filename,
            content,
            normalized_content_type,
            file_type,
            description=description,
        )

        logger.info(f"File uploaded successfully by user {user['id']}: {record['id']}")
        return {"success": True, "data": record}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=str(e) or "Failed to upload file"
        ) from e


@router.post(
    "/ecg/upload", dependencies=[Depends(require_permission(Permission.UPLOAD_FILES))]
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
        content = await _read_upload_with_size_limit(
            file,
            max_size=10 * 1024 * 1024,
            error_message="ECG file too large. Maximum size is 10MB.",
        )

        filename = file.filename or ""
        if not is_supported_ecg_upload(filename):
            raise HTTPException(
                status_code=400,
                detail="Invalid ECG file format. Supported format: .dat",
            )

        await _validate_case_and_patient(case_id, patient_id)

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
        raise HTTPException(status_code=500, detail="Failed to upload ECG signal") from e


@router.post(
    "/mri/upload", dependencies=[Depends(require_permission(Permission.UPLOAD_FILES))]
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
        content = await _read_upload_with_size_limit(
            file,
            max_size=100 * 1024 * 1024,
            error_message="MRI file too large. Maximum size is 100MB.",
        )

        filename = file.filename or ""
        normalized_content_type = normalize_upload_content_type(
            filename, file.content_type
        )
        if not is_supported_mri_upload(filename, normalized_content_type):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid MRI file format. Supported formats: .nii, .nii.gz, "
                    ".dcm, .jpg, .jpeg, .png"
                ),
            )

        await _validate_case_and_patient(case_id, patient_id)

        result = await service.upload_mri_scan(
            user["id"],
            patient_id,
            case_id,
            filename,
            content,
            normalized_content_type,
        )

        logger.info(
            f"MRI scan uploaded successfully by user {user['id']}: {result['scan_record']['id']}"
        )
        return {"success": True, "data": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MRI upload failed for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=str(e) or "Failed to upload MRI scan"
        ) from e


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
        raise HTTPException(status_code=500, detail="Failed to get download URL") from e


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
        raise HTTPException(status_code=500, detail="Failed to delete file") from e
