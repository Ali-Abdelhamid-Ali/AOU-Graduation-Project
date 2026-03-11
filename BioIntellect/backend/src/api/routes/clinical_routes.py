"""Clinical Routes - Complete Medical Case and File Management API."""

from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from src.observability.logger import get_logger
from src.repositories.clinical_repository import ClinicalRepository
from src.security.auth_middleware import (
    Permission,
    get_current_user,
    require_permission,
)
from src.services.ai.ai_service import AIService
from src.services.domain.clinical_service import ClinicalService
from src.services.domain.file_service import (
    is_supported_mri_upload,
    normalize_upload_content_type,
)
from src.validators.medical_dto import (
    ECGResultCreateDTO,
    ECGResultResponseDTO,
    ECGResultUpdateDTO,
    ECGSignalCreateDTO,
    ECGSignalResponseDTO,
    GeneratedReportCreateDTO,
    GeneratedReportResponseDTO,
    GeneratedReportUpdateDTO,
    MedicalCaseCreateDTO,
    MedicalCaseResponseDTO,
    MedicalCaseUpdateDTO,
    MedicalFileCreateDTO,
    MedicalFileResponseDTO,
    MRIScanCreateDTO,
    MRIScanResponseDTO,
    MRISegmentationResultCreateDTO,
    MRISegmentationResultResponseDTO,
    MRISegmentationResultUpdateDTO,
)

logger = get_logger("routes.clinical")

router = APIRouter(
    prefix="/clinical",
    tags=["clinical"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        429: {"description": "Too Many Requests"},
        500: {"description": "Internal Server Error"},
    },
)


# Dependency Helper
def get_clinical_service():
    repo = ClinicalRepository()
    ai = AIService()
    return ClinicalService(repo, ai)


class SignalAnalysisRequest(BaseModel):
    signal_id: str = Field(..., description="ECG signal identifier")


class ScanAnalysisRequest(BaseModel):
    scan_id: str = Field(..., description="MRI scan identifier")


class ResultReviewRequest(BaseModel):
    is_reviewed: bool = True
    doctor_agrees_with_ai: Optional[bool] = None
    doctor_notes: Optional[str] = None


def _has_permission(user: dict[str, Any], permission: Permission) -> bool:
    permissions = user.get("permissions", set()) or set()
    normalized_permissions = {getattr(item, "value", item) for item in permissions}
    return permission in permissions or permission.value in normalized_permissions


def _resolve_request_patient_id(
    user: dict[str, Any], patient_id: Optional[str] = None
) -> Optional[str]:
    if user.get("role") != "patient":
        return patient_id

    current_patient_id = user.get("profile_id")
    if patient_id and patient_id != current_patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return current_patient_id


def _ensure_clinical_permission(
    user: dict[str, Any],
    permission: Permission,
    patient_id: Optional[str] = None,
) -> Optional[str]:
    scoped_patient_id = _resolve_request_patient_id(user, patient_id)
    if user.get("role") == "patient":
        return scoped_patient_id

    if _has_permission(user, permission):
        return scoped_patient_id

    raise HTTPException(status_code=403, detail="Access denied")


# â”پâ”پâ”پâ”پ MEDICAL CASES â”پâ”پâ”پâ”پ


@router.get(
    "/cases",
    response_model=List[MedicalCaseResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def list_medical_cases(
    patient_id: Optional[str] = None,
    hospital_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    is_archived: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """List medical cases with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if hospital_id:
            filters["hospital_id"] = hospital_id
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if is_archived is not None:
            filters["is_archived"] = is_archived

        cases = await repo.list_medical_cases(filters, limit, offset)
        return cases
    except Exception as e:
        logger.error(f"Failed to list medical cases: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve medical cases")


@router.get(
    "/cases/{case_id}",
    response_model=MedicalCaseResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_medical_case(
    case_id: str, repo: ClinicalRepository = Depends(ClinicalRepository)
):
    """Get a specific medical case by ID."""
    try:
        case = await repo.get_medical_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Medical case not found")
        return case
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medical case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve medical case")


@router.post(
    "/cases",
    response_model=MedicalCaseResponseDTO,
)
async def create_medical_case(
    case_data: MedicalCaseCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create a new medical case or a patient self-service case."""
    try:
        patient_id = _ensure_clinical_permission(
            user, Permission.CREATE_CASE, case_data.patient_id
        )
        payload = case_data.dict()
        payload["patient_id"] = patient_id or payload["patient_id"]
        if user.get("role") == "patient":
            payload["assigned_doctor_id"] = None
            payload["created_by_doctor_id"] = None

        case = await service.create_case(user["id"], payload)
        if not case:
            raise HTTPException(status_code=500, detail="Failed to create medical case")
        logger.info(f"Medical case created by user {user['id']}: {case['id']}")
        return case
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create medical case: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create medical case")


@router.put(
    "/cases/{case_id}",
    response_model=MedicalCaseResponseDTO,
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def update_medical_case(
    case_id: str,
    case_data: MedicalCaseUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Update a medical case (Doctor/Admin only)."""
    try:
        case = await repo.update_medical_case(
            case_id, case_data.dict(exclude_unset=True)
        )
        if not case:
            raise HTTPException(status_code=404, detail="Medical case not found")
        logger.info(f"Medical case updated by user {user['id']}: {case_id}")
        return case
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update medical case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update medical case")


@router.delete(
    "/cases/{case_id}",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def delete_medical_case(
    case_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Delete a medical case (Doctor/Admin only)."""
    try:
        success = await repo.delete_medical_case(case_id)
        if not success:
            raise HTTPException(status_code=404, detail="Medical case not found")
        logger.info(f"Medical case deleted by user {user['id']}: {case_id}")
        return {"success": True, "message": "Medical case deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete medical case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete medical case")


@router.post(
    "/cases/{case_id}/archive",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def archive_medical_case(
    case_id: str,
    reason: Optional[str] = None,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Archive a medical case (Doctor/Admin only)."""
    try:
        success = await repo.archive_medical_case(case_id, user["id"], reason)
        if not success:
            raise HTTPException(status_code=404, detail="Medical case not found")
        logger.info(f"Medical case archived by user {user['id']}: {case_id}")
        return {"success": True, "message": "Medical case archived successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive medical case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to archive medical case")


# â”پâ”پâ”پâ”پ MEDICAL FILES â”پâ”پâ”پâ”پ


@router.get(
    "/files",
    response_model=List[MedicalFileResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def list_medical_files(
    case_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    file_type: Optional[str] = None,
    is_analyzed: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """List medical files with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if case_id:
            filters["case_id"] = case_id
        if patient_id:
            filters["patient_id"] = patient_id
        if file_type:
            filters["file_type"] = file_type
        if is_analyzed is not None:
            filters["is_analyzed"] = is_analyzed
        if is_deleted is not None:
            filters["is_deleted"] = is_deleted

        files = await repo.list_medical_files(filters, limit, offset)
        return files
    except Exception as e:
        logger.error(f"Failed to list medical files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve medical files")


@router.get(
    "/files/{file_id}",
    response_model=MedicalFileResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_medical_file(
    file_id: str, repo: ClinicalRepository = Depends(ClinicalRepository)
):
    """Get a specific medical file by ID."""
    try:
        file_record = await repo.get_medical_file(file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="Medical file not found")
        return file_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medical file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve medical file")


@router.post(
    "/files",
    response_model=MedicalFileResponseDTO,
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def create_medical_file(
    file_data: MedicalFileCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create a new medical file (Doctor/Admin only)."""
    try:
        file_record = await service.create_medical_file(user["id"], file_data.dict())
        if not file_record:
            raise HTTPException(status_code=500, detail="Failed to create medical file")
        logger.info(f"Medical file created by user {user['id']}: {file_record['id']}")
        return file_record
    except Exception as e:
        logger.error(f"Failed to create medical file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create medical file")


@router.put(
    "/files/{file_id}",
    response_model=MedicalFileResponseDTO,
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def update_medical_file(
    file_id: str,
    file_data: MedicalFileCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Update a medical file (Doctor/Admin only)."""
    try:
        file_record = await repo.update_medical_file(
            file_id, file_data.dict(exclude_unset=True)
        )
        if not file_record:
            raise HTTPException(status_code=404, detail="Medical file not found")
        logger.info(f"Medical file updated by user {user['id']}: {file_id}")
        return file_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update medical file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update medical file")


@router.delete(
    "/files/{file_id}",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def delete_medical_file(
    file_id: str,
    reason: Optional[str] = None,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Delete a medical file (Doctor/Admin only)."""
    try:
        success = await repo.delete_medical_file(file_id, user["id"], reason)
        if not success:
            raise HTTPException(status_code=404, detail="Medical file not found")
        logger.info(f"Medical file deleted by user {user['id']}: {file_id}")
        return {"success": True, "message": "Medical file deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete medical file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete medical file")


# â”پâ”پâ”پâ”پ ECG SIGNALS â”پâ”پâ”پâ”پ


@router.get(
    "/ecg/signals",
    response_model=List[ECGSignalResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def list_ecg_signals(
    patient_id: Optional[str] = None,
    case_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """List ECG signals with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if case_id:
            filters["case_id"] = case_id

        signals = await service.list_ecg_signals(user["id"], filters, limit, offset)
        return signals
    except Exception as e:
        logger.error(f"Failed to list ECG signals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ECG signals")


@router.get(
    "/ecg/signals/{signal_id}",
    response_model=ECGSignalResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_ecg_signal(
    signal_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Get a specific ECG signal by ID."""
    try:
        signal = await service.get_ecg_signal(user["id"], signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="ECG signal not found")
        return signal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ECG signal {signal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ECG signal")


@router.post(
    "/ecg/signals",
    response_model=ECGSignalResponseDTO,
)
async def create_ecg_signal(
    signal_data: ECGSignalCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create a new ECG signal."""
    try:
        patient_id = _ensure_clinical_permission(
            user, Permission.CREATE_CASE, signal_data.patient_id
        )
        payload = signal_data.dict()
        payload["patient_id"] = patient_id or payload["patient_id"]
        signal = await service.create_ecg_signal(user["id"], payload)
        if not signal:
            raise HTTPException(status_code=500, detail="Failed to create ECG signal")
        logger.info(f"ECG signal created by user {user['id']}: {signal['id']}")
        return signal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create ECG signal: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create ECG signal")


@router.delete(
    "/ecg/signals/{signal_id}",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def delete_ecg_signal(
    signal_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Delete an ECG signal (Doctor/Admin only)."""
    try:
        success = await service.delete_ecg_signal(user["id"], signal_id)
        if not success:
            raise HTTPException(status_code=404, detail="ECG signal not found")
        logger.info(f"ECG signal deleted by user {user['id']}: {signal_id}")
        return {"success": True, "message": "ECG signal deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete ECG signal {signal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete ECG signal")


# â”پâ”پâ”پâ”پ ECG SIGNALS WITH FILE UPLOAD â”پâ”پâ”پâ”پ


@router.post(
    "/ecg/signals/from-file",
    response_model=ECGSignalResponseDTO,
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def create_ecg_signal_from_file(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    patient_id: str = Form(...),
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create ECG signal from uploaded file (Doctor/Admin only)."""
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

        signal_data = {
            "patient_id": patient_id,
            "case_id": case_id,
            "signal_data": {
                "file_name": filename,
                "file_size": len(content),
                "content_type": file.content_type,
                "uploaded_at": "now()",
            },
        }

        signal = await service.create_ecg_signal(user["id"], signal_data)
        if not signal:
            raise HTTPException(status_code=500, detail="Failed to create ECG signal")
        logger.info(
            f"ECG signal created from file by user {user['id']}: {signal['id']}"
        )
        return signal

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create ECG signal from file: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to create ECG signal from file"
        )


# â”پâ”پâ”پâ”پ ECG RESULTS â”پâ”پâ”پâ”پ


@router.get(
    "/ecg/results",
    response_model=List[ECGResultResponseDTO],
)
async def list_ecg_results(
    patient_id: Optional[str] = None,
    case_id: Optional[str] = None,
    analysis_status: Optional[str] = None,
    is_reviewed: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """List ECG results with optional filtering."""
    try:
        patient_id = _ensure_clinical_permission(user, Permission.VIEW_PATIENT, patient_id)
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if case_id:
            filters["case_id"] = case_id
        if analysis_status:
            filters["analysis_status"] = analysis_status
        if is_reviewed is not None:
            filters["is_reviewed"] = is_reviewed

        results = await repo.list_ecg_results(filters, limit, offset)
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list ECG results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ECG results")


@router.get(
    "/ecg/results/{result_id}",
    response_model=ECGResultResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_ecg_result(
    result_id: str, repo: ClinicalRepository = Depends(ClinicalRepository)
):
    """Get a specific ECG result by ID."""
    try:
        result = await repo.get_ecg_result(result_id)
        if not result:
            raise HTTPException(status_code=404, detail="ECG result not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ECG result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ECG result")


@router.post(
    "/ecg/results",
    response_model=ECGResultResponseDTO,
    dependencies=[Depends(require_permission(Permission.ANALYZE_ECG))],
)
async def create_ecg_result(
    result_data: ECGResultCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create a new ECG result (Doctor/Admin only)."""
    try:
        result = await service.create_ecg_result(user["id"], result_data.dict())
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create ECG result")
        logger.info(f"ECG result created by user {user['id']}: {result['id']}")
        return result
    except Exception as e:
        logger.error(f"Failed to create ECG result: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create ECG result")


@router.put(
    "/ecg/results/{result_id}",
    response_model=ECGResultResponseDTO,
    dependencies=[Depends(require_permission(Permission.ANALYZE_ECG))],
)
async def update_ecg_result(
    result_id: str,
    result_data: ECGResultUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Update an ECG result (Doctor/Admin only)."""
    try:
        result = await repo.update_ecg_result(
            result_id, result_data.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="ECG result not found")
        logger.info(f"ECG result updated by user {user['id']}: {result_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update ECG result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update ECG result")


@router.post(
    "/ecg/results/{result_id}/review",
    response_model=ECGResultResponseDTO,
    dependencies=[Depends(require_permission(Permission.ANALYZE_ECG))],
)
async def review_ecg_result(
    result_id: str,
    review_data: dict,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Review an ECG result (Doctor only)."""
    try:
        result = await service.review_result(
            user["id"], "ecg_results", result_id, review_data
        )
        logger.info(f"ECG result reviewed by user {user['id']}: {result_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to review ECG result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to review ECG result")


@router.delete(
    "/ecg/results/{result_id}",
    dependencies=[Depends(require_permission(Permission.ANALYZE_ECG))],
)
async def delete_ecg_result(
    result_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Delete an ECG result (Doctor/Admin only)."""
    try:
        success = await repo.delete_ecg_result(result_id)
        if not success:
            raise HTTPException(status_code=404, detail="ECG result not found")
        logger.info(f"ECG result deleted by user {user['id']}: {result_id}")
        return {"success": True, "message": "ECG result deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete ECG result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete ECG result")


# â”پâ”پâ”پâ”پ MRI SCANS â”پâ”پâ”پâ”پ


@router.get(
    "/mri/scans",
    response_model=List[MRIScanResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def list_mri_scans(
    patient_id: Optional[str] = None,
    case_id: Optional[str] = None,
    scan_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """List MRI scans with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if case_id:
            filters["case_id"] = case_id
        if scan_type:
            filters["scan_type"] = scan_type

        scans = await service.list_mri_scans(user["id"], filters, limit, offset)
        return scans
    except Exception as e:
        logger.error(f"Failed to list MRI scans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve MRI scans")


@router.get(
    "/mri/scans/{scan_id}",
    response_model=MRIScanResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_mri_scan(
    scan_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Get a specific MRI scan by ID."""
    try:
        scan = await service.get_mri_scan(user["id"], scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="MRI scan not found")
        return scan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MRI scan {scan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve MRI scan")


@router.post(
    "/mri/scans",
    response_model=MRIScanResponseDTO,
)
async def create_mri_scan(
    scan_data: MRIScanCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create a new MRI scan."""
    try:
        patient_id = _ensure_clinical_permission(
            user, Permission.CREATE_CASE, scan_data.patient_id
        )
        payload = scan_data.dict()
        payload["patient_id"] = patient_id or payload["patient_id"]
        scan = await service.create_mri_scan(user["id"], payload)
        if not scan:
            raise HTTPException(status_code=500, detail="Failed to create MRI scan")
        logger.info(f"MRI scan created by user {user['id']}: {scan['id']}")
        return scan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create MRI scan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create MRI scan")


@router.delete(
    "/mri/scans/{scan_id}",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def delete_mri_scan(
    scan_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Delete an MRI scan (Doctor/Admin only)."""
    try:
        success = await service.delete_mri_scan(user["id"], scan_id)
        if not success:
            raise HTTPException(status_code=404, detail="MRI scan not found")
        logger.info(f"MRI scan deleted by user {user['id']}: {scan_id}")
        return {"success": True, "message": "MRI scan deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete MRI scan {scan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete MRI scan")


# â”پâ”پâ”پâ”پ MRI SCANS WITH FILE UPLOAD â”پâ”پâ”پâ”پ


@router.post(
    "/mri/scans/from-file",
    response_model=MRIScanResponseDTO,
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def create_mri_scan_from_file(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    patient_id: str = Form(...),
    scan_type: Optional[str] = Form(None),
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create MRI scan from uploaded file (Doctor/Admin only)."""
    try:
        content = await file.read()

        # Validate file size (max 100MB for MRI)
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=413, detail="MRI file too large. Maximum size is 100MB."
            )

        # Validate file type for MRI
        filename = file.filename or ""
        normalized_content_type = normalize_upload_content_type(
            filename, file.content_type
        )
        if not is_supported_mri_upload(filename, normalized_content_type):
            raise HTTPException(
                status_code=400,
                detail="Invalid MRI file format. Supported formats: .nii, .nii.gz, .dcm, .jpg, .jpeg, .png",
            )

        scan_data = {
            "patient_id": patient_id,
            "case_id": case_id,
            "scan_type": scan_type or "unknown",
            "dicom_metadata": {
                "file_name": filename,
                "file_size": len(content),
                "content_type": normalized_content_type,
                "uploaded_at": "now()",
                "is_dicom": normalized_content_type == "application/dicom"
                or filename.lower().endswith(".dcm"),
            },
        }

        scan = await service.create_mri_scan(user["id"], scan_data)
        if not scan:
            raise HTTPException(status_code=500, detail="Failed to create MRI scan")
        logger.info(f"MRI scan created from file by user {user['id']}: {scan['id']}")
        return scan

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create MRI scan from file: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to create MRI scan from file"
        )


# â”پâ”پâ”پâ”پ MRI RESULTS â”پâ”پâ”پâ”پ


@router.get(
    "/mri/results",
    response_model=List[MRISegmentationResultResponseDTO],
)
async def list_mri_results(
    patient_id: Optional[str] = None,
    case_id: Optional[str] = None,
    analysis_status: Optional[str] = None,
    is_reviewed: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """List MRI results with optional filtering."""
    try:
        patient_id = _ensure_clinical_permission(user, Permission.VIEW_PATIENT, patient_id)
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if case_id:
            filters["case_id"] = case_id
        if analysis_status:
            filters["analysis_status"] = analysis_status
        if is_reviewed is not None:
            filters["is_reviewed"] = is_reviewed

        results = await service.list_mri_results(user["id"], filters, limit, offset)
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list MRI results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve MRI results")


@router.get(
    "/mri/results/{result_id}",
    response_model=MRISegmentationResultResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_mri_result(
    result_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Get a specific MRI result by ID."""
    try:
        result = await service.get_mri_result(user["id"], result_id)
        if not result:
            raise HTTPException(status_code=404, detail="MRI result not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MRI result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve MRI result")


@router.post(
    "/mri/results",
    response_model=MRISegmentationResultResponseDTO,
)
async def create_mri_result(
    result_data: MRISegmentationResultCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create a new MRI result."""
    try:
        patient_id = _ensure_clinical_permission(
            user, Permission.ANALYZE_MRI, result_data.patient_id
        )
        payload = result_data.dict()
        payload["patient_id"] = patient_id or payload["patient_id"]
        result = await service.create_mri_result(user["id"], payload)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create MRI result")
        logger.info(f"MRI result created by user {user['id']}: {result['id']}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create MRI result: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create MRI result")


@router.put(
    "/mri/results/{result_id}",
    response_model=MRISegmentationResultResponseDTO,
    dependencies=[Depends(require_permission(Permission.ANALYZE_MRI))],
)
async def update_mri_result(
    result_id: str,
    result_data: MRISegmentationResultUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Update an MRI result (Doctor/Admin only)."""
    try:
        result = await service.update_mri_result(
            user["id"], result_id, result_data.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="MRI result not found")
        logger.info(f"MRI result updated by user {user['id']}: {result_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update MRI result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update MRI result")


@router.post(
    "/mri/results/{result_id}/review",
    response_model=MRISegmentationResultResponseDTO,
    dependencies=[Depends(require_permission(Permission.ANALYZE_MRI))],
)
async def review_mri_result(
    result_id: str,
    review_data: dict,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Review an MRI result (Doctor only)."""
    try:
        result = await service.review_result(
            user["id"], "mri_segmentation_results", result_id, review_data
        )
        logger.info(f"MRI result reviewed by user {user['id']}: {result_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to review MRI result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to review MRI result")


@router.delete(
    "/mri/results/{result_id}",
    dependencies=[Depends(require_permission(Permission.ANALYZE_MRI))],
)
async def delete_mri_result(
    result_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Delete an MRI result (Doctor/Admin only)."""
    try:
        success = await service.delete_mri_result(user["id"], result_id)
        if not success:
            raise HTTPException(status_code=404, detail="MRI result not found")
        logger.info(f"MRI result deleted by user {user['id']}: {result_id}")
        return {"success": True, "message": "MRI result deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete MRI result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete MRI result")


# â”پâ”پâ”پâ”پ REPORTS â”پâ”پâ”پâ”پ


@router.get(
    "/reports",
    response_model=List[GeneratedReportResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def list_reports(
    patient_id: Optional[str] = None,
    case_id: Optional[str] = None,
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    is_final: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """List reports with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if case_id:
            filters["case_id"] = case_id
        if report_type:
            filters["report_type"] = report_type
        if status:
            filters["status"] = status
        if is_final is not None:
            filters["is_final"] = is_final

        reports = await repo.list_reports(filters, limit, offset)
        return reports
    except Exception as e:
        logger.error(f"Failed to list reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")


@router.get(
    "/reports/{report_id}",
    response_model=GeneratedReportResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_report(
    report_id: str, repo: ClinicalRepository = Depends(ClinicalRepository)
):
    """Get a specific report by ID."""
    try:
        report = await repo.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report")


@router.post(
    "/reports",
    response_model=GeneratedReportResponseDTO,
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def create_report(
    report_data: GeneratedReportCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Create a new report (Doctor/Admin only)."""
    try:
        report = await service.create_report(user["id"], report_data.dict())
        if not report:
            raise HTTPException(status_code=500, detail="Failed to create report")
        logger.info(f"Report created by user {user['id']}: {report['id']}")
        return report
    except Exception as e:
        logger.error(f"Failed to create report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create report")


@router.put(
    "/reports/{report_id}",
    response_model=GeneratedReportResponseDTO,
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def update_report(
    report_id: str,
    report_data: GeneratedReportUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Update a report (Doctor/Admin only)."""
    try:
        report = await repo.update_report(report_id, report_data.dict(exclude_unset=True))
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        logger.info(f"Report updated by user {user['id']}: {report_id}")
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update report")


@router.post(
    "/reports/{report_id}/approve",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def approve_report(
    report_id: str,
    approval_notes: Optional[str] = None,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Approve a report (Doctor/Admin only)."""
    try:
        success = await repo.approve_report(report_id, user["id"], approval_notes)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found")
        logger.info(f"Report approved by user {user['id']}: {report_id}")
        return {"success": True, "message": "Report approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to approve report")


@router.delete(
    "/reports/{report_id}",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def delete_report(
    report_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Delete a report (Doctor/Admin only)."""
    try:
        success = await repo.delete_report(report_id)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found")
        logger.info(f"Report deleted by user {user['id']}: {report_id}")
        return {"success": True, "message": "Report deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete report")


# â”پâ”پâ”پâ”پ PATIENT HISTORY â”پâ”پâ”پâ”پ


@router.get(
    "/patients/{patient_id}/history",
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_patient_history(
    patient_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Get complete patient medical history."""
    try:
        history = await service.get_patient_history(user["id"], patient_id)
        return {"success": True, "data": history}
    except Exception as e:
        logger.error(f"Failed to get patient history for {patient_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve patient history"
        )


# â”پâ”پâ”پâ”پ FRONTEND INTEGRATION HELPERS â”پâ”پâ”پâ”پ


@router.get("/model/info")
async def get_frontend_model_info(
    user: dict[str, Any] = Depends(get_current_user),
):
    """Return MRI model information used by the UI."""
    _ensure_clinical_permission(user, Permission.UPLOAD_FILES)
    return AIService().get_model_info("mri")


@router.post("/mri/segment")
async def segment_mri_modalities(
    t1: UploadFile = File(...),
    t1ce: UploadFile = File(...),
    t2: UploadFile = File(...),
    flair: UploadFile = File(...),
    gt: Optional[UploadFile] = File(None),
    patient_id: Optional[str] = Form(None),
    user: dict[str, Any] = Depends(get_current_user),
):
    """Accept the four MRI modalities and return a structured segmentation payload."""
    patient_id = _ensure_clinical_permission(user, Permission.UPLOAD_FILES, patient_id)
    try:
        files = {
            "t1": t1,
            "t1ce": t1ce,
            "t2": t2,
            "flair": flair,
        }
        return await AIService().segment_mri_modalities(
            files,
            patient_id=patient_id,
            gt_file=gt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/mri/visualization/{case_id}/image")
async def get_mri_visualization_image(
    case_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Proxy the generated MRI image volume artifact."""
    _ensure_clinical_permission(user, Permission.UPLOAD_FILES)
    try:
        artifact = await AIService().fetch_mri_visualization_artifact(case_id, "image")
        return Response(
            content=artifact["content"],
            media_type=artifact["content_type"],
            headers={"Content-Disposition": f'inline; filename="{artifact["filename"]}"'},
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/mri/visualization/{case_id}/labels")
async def get_mri_visualization_labels(
    case_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Proxy the generated MRI label volume artifact."""
    _ensure_clinical_permission(user, Permission.UPLOAD_FILES)
    try:
        artifact = await AIService().fetch_mri_visualization_artifact(case_id, "labels")
        return Response(
            content=artifact["content"],
            media_type=artifact["content_type"],
            headers={"Content-Disposition": f'inline; filename="{artifact["filename"]}"'},
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/mri/result/{case_id}/patient-view")
async def get_patient_friendly_mri_result(
    case_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    """Return a patient-friendly summary derived from the persisted MRI result."""
    repo = ClinicalRepository()
    case_record = await repo.get_medical_case(case_id)
    if not case_record:
        raise HTTPException(status_code=404, detail="Medical case not found")

    _ensure_clinical_permission(
        user, Permission.VIEW_PATIENT, case_record.get("patient_id")
    )

    results = await repo.list_mri_results({"case_id": case_id}, limit=5, offset=0)
    latest_result = results[0] if results else None

    if not latest_result:
        return {
            "case_id": case_id,
            "summary": "Your MRI scan has been uploaded and is waiting for a finalized AI result.",
            "next_step": "Please check back after the imaging workflow finishes or speak with your care team.",
            "status": "pending_result",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    abnormalities = latest_result.get("detected_abnormalities") or []
    if not isinstance(abnormalities, list):
        abnormalities = [str(abnormalities)]

    recommendations = latest_result.get("ai_recommendations") or []
    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    measurements = latest_result.get("measurements") or {}
    if not isinstance(measurements, dict):
        measurements = {}

    severity_score = latest_result.get("severity_score")
    tumor_detected = bool(latest_result.get("tumor_detected"))
    created_at = latest_result.get("updated_at") or latest_result.get("created_at")

    if tumor_detected:
        summary = (
            "The saved MRI analysis found an area that needs clinician review."
            if not abnormalities
            else f"The saved MRI analysis highlighted: {abnormalities[0]}."
        )
        next_step = (
            recommendations[0]
            if recommendations
            else "Please review this result with your doctor for final interpretation."
        )
    else:
        summary = (
            "The saved MRI analysis did not flag a major abnormality in this study."
        )
        next_step = (
            recommendations[0]
            if recommendations
            else "Continue follow-up with your care team if symptoms change or persist."
        )

    measurement_summary = {
        key: value
        for key, value in measurements.items()
        if not str(key).startswith("_")
    }

    return {
        "case_id": case_id,
        "result_id": latest_result.get("id"),
        "summary": summary,
        "next_step": next_step,
        "status": latest_result.get("analysis_status") or "completed",
        "reviewed": bool(latest_result.get("is_reviewed")),
        "severity_score": severity_score,
        "key_findings": abnormalities[:3],
        "measurements": measurement_summary,
        "generated_at": created_at or datetime.now(timezone.utc).isoformat(),
    }


# â”پâ”پâ”پâ”پ ANALYSIS ENDPOINTS â”پâ”پâ”پâ”پ


@router.post(
    "/analyze/ecg", dependencies=[Depends(require_permission(Permission.ANALYZE_ECG))]
)
async def analyze_ecg(
    case_id: str,
    signal_data: dict,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Run AI analysis on ECG and persist results."""
    try:
        result = await service.analyze_ecg(user["id"], case_id, signal_data)
        logger.info(f"ECG analysis completed by user {user['id']} for case {case_id}")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to analyze ECG for case {case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze ECG")


@router.post(
    "/analyze/mri", dependencies=[Depends(require_permission(Permission.ANALYZE_MRI))]
)
async def analyze_mri(
    scan_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Run AI analysis on MRI and persist results."""
    try:
        result = await service.run_mri_analysis(user["id"], scan_id)
        logger.info(f"MRI analysis completed by user {user['id']} for scan {scan_id}")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to analyze MRI for scan {scan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze MRI")


@router.post("/ecg/analyze")
async def analyze_ecg_by_signal(
    payload: SignalAnalysisRequest,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Frontend-friendly ECG analysis endpoint."""
    if user.get("role") != "patient":
        _ensure_clinical_permission(user, Permission.ANALYZE_ECG)

    try:
        if user.get("role") == "patient":
            signal = await service.get_ecg_signal(user["id"], payload.signal_id)
            if not signal or signal.get("patient_id") != user.get("profile_id"):
                raise HTTPException(status_code=403, detail="Access denied")

        result = await service.run_ecg_analysis(user["id"], payload.signal_id)
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to analyze ECG signal {payload.signal_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to analyze ECG")


@router.post("/mri/analyze")
async def analyze_mri_by_scan(
    payload: ScanAnalysisRequest,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Frontend-friendly MRI analysis endpoint."""
    if user.get("role") != "patient":
        _ensure_clinical_permission(user, Permission.ANALYZE_MRI)

    try:
        if user.get("role") == "patient":
            scan = await service.get_mri_scan(user["id"], payload.scan_id)
            if not scan or scan.get("patient_id") != user.get("profile_id"):
                raise HTTPException(status_code=403, detail="Access denied")

        result = await service.run_mri_analysis(user["id"], payload.scan_id)
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to analyze MRI scan {payload.scan_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to analyze MRI")


@router.put("/results/{table_name}/{result_id}/review")
async def review_result_alias(
    table_name: str,
    result_id: str,
    review_data: ResultReviewRequest,
    user: dict[str, Any] = Depends(get_current_user),
    service: ClinicalService = Depends(get_clinical_service),
):
    """Alias for the frontend review workflow."""
    if table_name == "mri_results":
        table_name = "mri_segmentation_results"
    elif table_name != "ecg_results":
        raise HTTPException(status_code=400, detail="Unsupported result table")

    _ensure_clinical_permission(
        user,
        Permission.ANALYZE_MRI if table_name == "mri_segmentation_results" else Permission.ANALYZE_ECG,
    )

    try:
        return await service.review_result(
            user["id"], table_name, result_id, review_data.model_dump(exclude_unset=True)
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to review result {result_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to review result")

