"""Users API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

@router.get("/doctors")
async def list_doctors(
    hospital_id: Optional[str] = None,
    specialty_code: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List all doctors with optional filters."""
    try:
        query = supabase_admin.table("doctors").select(
            "*, hospitals(hospital_name_en), doctor_specialties(specialty_types(specialty_code, specialty_name_en))"
        ).eq("is_active", is_active)
        
        if hospital_id:
            query = query.eq("hospital_id", hospital_id)
        
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List doctors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/doctors/{doctor_id}")
async def get_doctor(doctor_id: str, current_user: dict = Depends(get_current_user)):
    """Get doctor by ID."""
    try:
        result = supabase_admin.table("doctors").select(
            "*, hospitals(hospital_name_en), doctor_specialties(specialty_types(*))"
        ).eq("id", doctor_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get doctor error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nurses")
async def list_nurses(
    hospital_id: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List all nurses."""
    try:
        query = supabase_admin.table("nurses").select(
            "*, hospitals(hospital_name_en)"
        ).eq("is_active", is_active)
        
        if hospital_id:
            query = query.eq("hospital_id", hospital_id)
        
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List nurses error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/administrators")
async def list_administrators(
    hospital_id: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List all administrators."""
    try:
        query = supabase_admin.table("administrators").select(
            "*, hospitals(hospital_name_en)"
        ).eq("is_active", is_active)
        
        if hospital_id:
            query = query.eq("hospital_id", hospital_id)
        
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List administrators error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/specialties")
async def list_specialties(
    category: Optional[str] = None,
    is_active: bool = True
):
    """List all medical specialties."""
    try:
        query = supabase_admin.table("specialty_types").select("*").eq("is_active", is_active)
        
        if category:
            query = query.eq("specialty_category", category)
        
        result = query.execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        logger.error(f"List specialties error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile")
async def update_profile(
    request: UserUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile."""
    try:
        role = current_user["user_metadata"].get("role", "patient")
        table_map = {
            'patient': 'patients',
            'doctor': 'doctors',
            'nurse': 'nurses',
            'administrator': 'administrators',
            'super_admin': 'administrators'
        }
        table_name = table_map.get(role, 'patients')
        
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = supabase_admin.table(table_name).update(update_data).eq(
            "user_id", current_user["id"]
        ).execute()
        
        return {"success": True, "data": result.data[0] if result.data else {}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
