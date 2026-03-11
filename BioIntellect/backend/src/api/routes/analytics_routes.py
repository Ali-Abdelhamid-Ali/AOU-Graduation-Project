"""Analytics Routes & Controller."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
from src.services.domain.analytics_service import AnalyticsService
from src.repositories.analytics_repository import AnalyticsRepository
from src.validators.analytics_dto import AppointmentCreateDTO, AppointmentUpdateDTO
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
    appointments = await service.list_appointments(user)
    return {"success": True, "data": appointments}


@router.post("/appointments")
async def create_appointment(
    data: AppointmentCreateDTO,
    user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Create a follow-up appointment backed by the medical_cases schema."""
    try:
        created = await service.create_appointment(
            user, data.model_dump(exclude_unset=True)
        )
        return {"success": True, "data": created}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/appointments/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdateDTO,
    user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Update a specific appointment record."""
    try:
        updated = await service.update_appointment(
            user, appointment_id, data.model_dump(exclude_unset=True)
        )
        return {"success": True, "data": updated}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/dashboard", dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))]
)
async def get_dashboard(
    user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get dashboard stats for the current user."""
    return {
        "success": True,
        "data": await service.get_dashboard_summary(user),
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
    return {"success": True, "data": await service.get_health_trends(user, days)}

