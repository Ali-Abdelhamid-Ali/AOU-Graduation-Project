"""Geography API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
import logging

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class HospitalCreateRequest(BaseModel):
    region_id: str
    hospital_code: str
    hospital_name_en: str
    hospital_name_ar: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None

class HospitalUpdateRequest(BaseModel):
    hospital_name_en: Optional[str] = None
    hospital_name_ar: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    is_active: Optional[bool] = None

# ============== ENDPOINTS ==============

@router.get("/countries")
async def list_countries(
    is_active: bool = True
):
    """List all countries."""
    try:
        result = supabase_admin.table("countries").select(
            "id, country_code, country_name_en, country_name_ar, phone_code, is_active"
        ).eq("is_active", is_active).order("country_name_en").execute()
        
        return {"success": True, "data": result.data}
    except Exception as e:
        logger.error(f"List countries error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/countries/{country_id}")
async def get_country(
    country_id: str
):
    """Get country by ID."""
    try:
        result = supabase_admin.table("countries").select(
            "*"
        ).eq("id", country_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Country not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get country error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regions")
async def list_regions(
    country_id: Optional[str] = None,
    is_active: bool = True
):
    """List regions with optional country filter."""
    try:
        query = supabase_admin.table("regions").select(
            "id, country_id, region_code, region_name_en, region_name_ar, is_active, countries(country_name_en)"
        ).eq("is_active", is_active)
        
        if country_id:
            query = query.eq("country_id", country_id)
        
        result = query.order("region_name_en").execute()
        
        return {"success": True, "data": result.data}
    except Exception as e:
        logger.error(f"List regions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regions/{region_id}")
async def get_region(
    region_id: str
):
    """Get region by ID."""
    try:
        result = supabase_admin.table("regions").select(
            "*, countries(*)"
        ).eq("id", region_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Region not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get region error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hospitals")
async def list_hospitals(
    region_id: Optional[str] = None,
    is_active: bool = True,
    search: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """List hospitals with filters."""
    try:
        query = supabase_admin.table("hospitals").select(
            "id, hospital_code, hospital_name_en, hospital_name_ar, address, phone, email, is_active, regions(region_name_en, countries(country_name_en))"
        ).eq("is_active", is_active)
        
        if region_id:
            query = query.eq("region_id", region_id)
        if search:
            query = query.ilike("hospital_name_en", f"%{search}%")
        
        result = query.order("hospital_name_en").range(offset, offset + limit - 1).execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List hospitals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hospitals/{hospital_id}")
async def get_hospital(
    hospital_id: str
):
    """Get hospital by ID."""
    try:
        result = supabase_admin.table("hospitals").select(
            "*, regions(*, countries(*))"
        ).eq("id", hospital_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get hospital error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hospitals")
async def create_hospital(
    request: HospitalCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new hospital (admin only)."""
    try:
        role = current_user["user_metadata"].get("role", "patient")
        if role not in ["administrator", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can create hospitals")
        
        hospital_data = request.dict()
        hospital_data["is_active"] = True
        hospital_data["settings"] = {}
        
        result = supabase_admin.table("hospitals").insert(hospital_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create hospital")
        
        logger.info(f"✅ Hospital created: {result.data[0]['hospital_code']}")
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create hospital error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/hospitals/{hospital_id}")
async def update_hospital(
    hospital_id: str,
    request: HospitalUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update hospital (admin only)."""
    try:
        role = current_user["user_metadata"].get("role", "patient")
        if role not in ["administrator", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can update hospitals")
        
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = supabase_admin.table("hospitals").update(update_data).eq(
            "id", hospital_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update hospital error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
