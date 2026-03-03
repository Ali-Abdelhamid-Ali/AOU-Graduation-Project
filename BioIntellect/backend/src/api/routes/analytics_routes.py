"""Analytics Routes & Controller."""

from fastapi import APIRouter, Depends, Query
from typing import Dict, Any
from src.services.domain.analytics_service import AnalyticsService
from src.repositories.analytics_repository import AnalyticsRepository
from src.validators.analytics_dto import AppointmentUpdateDTO
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service():
    return AnalyticsService(AnalyticsRepository())


@router.get("/appointments", response_model=Dict[str, Any])
async def get_appointments(
    user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Retrieve all appointments for the current user."""
    appointments = await service.get_patient_appointments(user["id"])
    return {"success": True, "data": appointments}


@router.put("/appointments/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdateDTO,
    user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Update a specific appointment record."""
    updated = await service.update_appointment(
        user["id"], appointment_id, data.model_dump(exclude_unset=True)
    )
    return {"success": True, "data": updated}


@router.get(
    "/dashboard", dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))]
)
async def get_dashboard(
    user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get dashboard stats for the current user."""
    role = user["role"]
    return {
        "success": True,
        "data": await service.get_dashboard_summary(user["id"], role),
    }


@router.get(
    "/trends", dependencies=[Depends(require_permission(Permission.VIEW_TRENDS))]
)
async def get_trends(
    days: int = Query(30, le=365),
    user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get health trends for the current user."""
    return {"success": True, "data": await service.get_health_trends(user["id"], days)}

