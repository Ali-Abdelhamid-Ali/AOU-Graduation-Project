"""Report Routes & Controller - Medical Documentation API."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Any
from src.services.domain.report_service import ReportService
from src.repositories.report_repository import ReportRepository
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.validators.medical_dto import (
    GeneratedReportCreateDTO,
    GeneratedReportUpdateDTO,
    ReportApproveDTO,
)

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        429: {"description": "Too Many Requests"},
        500: {"description": "Internal Server Error"},
    },
)


def get_report_service():
    return ReportService(ReportRepository())


@router.post("", dependencies=[Depends(require_permission(Permission.CREATE_CASE))])
async def create_report(
    data: GeneratedReportCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    import logging as _logging
    _log = _logging.getLogger("routes.reports")
    try:
        actor_id = user.get("profile_id") or user.get("id") or ""
        record = await service.create_report(actor_id, data.model_dump())
        return {"success": True, "data": record}
    except Exception as exc:
        _log.error("create_report failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(exc)}")


@router.get("", dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))])
async def list_reports(
    patient_id: Optional[str] = None,
    report_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    repo: ReportRepository = Depends(ReportRepository),
):
    filters: dict[str, Any] = {"patient_id": patient_id, "report_type": report_type}
    result = await repo.list_reports(filters, limit, offset)
    return {"success": True, "data": result.data}


@router.get(
    "/by-result/{result_type}/{result_id}",
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_report_by_result(
    result_type: str,
    result_id: str,
    repo: ReportRepository = Depends(ReportRepository),
):
    """Return the latest draft/approved report linked to a specific ECG or MRI result."""
    if result_type not in ("ecg", "mri"):
        raise HTTPException(status_code=400, detail="result_type must be 'ecg' or 'mri'")
    record = await repo.get_report_by_result(result_type, result_id)
    return {"success": True, "data": record}


@router.get(
    "/patient/{patient_id}",
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def list_patient_reports(
    patient_id: str,
    limit: int = 20,
    offset: int = 0,
    repo: ReportRepository = Depends(ReportRepository),
):
    """List all reports for a patient — used by patient portal and chat context."""
    result = await repo.get_reports_for_patient(patient_id, limit, offset, finalized_only=True)
    return {"success": True, "data": result.data}


@router.get(
    "/{report_id}",
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_report(
    report_id: str,
    repo: ReportRepository = Depends(ReportRepository),
):
    record = await repo.get_report_detail(report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"success": True, "data": record}


@router.put(
    "/{report_id}",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def update_report(
    report_id: str,
    data: GeneratedReportUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """Edit a draft report's title, summary, or content."""
    try:
        record = await service.update_report(user["id"], report_id, data.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": record}


@router.post(
    "/{report_id}/approve",
    dependencies=[Depends(require_permission(Permission.MANAGE_PATIENTS))],
)
async def approve_report(
    report_id: str,
    data: ReportApproveDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    record = await service.finalize_report(user["id"], report_id, data.notes)
    return {"success": True, "data": record}


@router.post(
    "/{report_id}/discard",
    dependencies=[Depends(require_permission(Permission.CREATE_CASE))],
)
async def discard_report(
    report_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """Soft-delete a draft report (sets status=discarded)."""
    try:
        await service.discard_report(user["id"], report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "data": {"discarded": True}}
