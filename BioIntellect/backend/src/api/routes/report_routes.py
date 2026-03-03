"""Report Routes & Controller - Medical Documentation API."""

from fastapi import APIRouter, Depends
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
    record = await service.create_report(user["id"], data.model_dump())
    return {"success": True, "data": record}


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


@router.post(
    "/{report_id}/approve",
    dependencies=[Depends(require_permission(Permission.MANAGE_PATIENTS))],
)  # Doctors can approve
async def approve_report(
    report_id: str,
    data: ReportApproveDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    record = await service.finalize_report(user["id"], report_id, data.notes)
    return {"success": True, "data": record}

