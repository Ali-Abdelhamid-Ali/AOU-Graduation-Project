"""Patients API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date
import logging
import random
from datetime import datetime

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hospital_id: str
    gender: Optional[str] = "male"
    date_of_birth: Optional[date] = None
    blood_type: Optional[str] = "unknown"
    national_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    allergies: Optional[List[str]] = []
    chronic_conditions: Optional[List[str]] = []
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    primary_doctor_id: Optional[str] = None
    notes: Optional[str] = None

class PatientUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    blood_type: Optional[str] = None
    national_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    current_medications: Optional[List[dict]] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    primary_doctor_id: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

# ============== HELPERS ==============

def generate_mrn(hospital_code: str) -> str:
    """Generate Medical Record Number."""
    year = datetime.now().strftime("%y")
    seq = str(random.randint(1, 999999)).zfill(6)
    return f"{hospital_code}{year}{seq}"

# ============== ENDPOINTS ==============

@router.get("")
async def list_patients(
    hospital_id: Optional[str] = None,
    primary_doctor_id: Optional[str] = None,
    is_active: bool = True,
    search: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List patients with filters."""
    try:
        query = supabase_admin.table("patients").select(
            "id, mrn, first_name, last_name, email, phone, gender, date_of_birth, blood_type, is_active, created_at, hospitals(hospital_name_en), doctors!patients_primary_doctor_id_fkey(first_name, last_name)"
        ).eq("is_active", is_active)
        
        if hospital_id:
            query = query.eq("hospital_id", hospital_id)
        if primary_doctor_id:
            query = query.eq("primary_doctor_id", primary_doctor_id)
        if search:
            query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,mrn.ilike.%{search}%")
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List patients error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get patient by ID."""
    try:
        result = supabase_admin.table("patients").select(
            "*, hospitals(hospital_name_en), doctors!patients_primary_doctor_id_fkey(id, first_name, last_name)"
        ).eq("id", patient_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get patient error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_patient(
    request: PatientCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new patient (without auth user)."""
    try:
        # Get hospital code for MRN
        hospital = supabase_admin.table("hospitals").select(
            "hospital_code"
        ).eq("id", request.hospital_id).single().execute()
        
        hospital_code = hospital.data.get("hospital_code", "GEN") if hospital.data else "GEN"
        mrn = generate_mrn(hospital_code)
        
        # Create patient record
        patient_data = request.dict()
        patient_data["mrn"] = mrn
        patient_data["is_active"] = True
        
        # Convert date to string if present
        if patient_data.get("date_of_birth"):
            patient_data["date_of_birth"] = patient_data["date_of_birth"].isoformat()
        
        result = supabase_admin.table("patients").insert(patient_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create patient")
        
        logger.info(f"✅ Patient created: {result.data[0]['id']}")
        return {"success": True, "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create patient error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{patient_id}")
async def update_patient(
    patient_id: str,
    request: PatientUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update patient."""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Convert date to string
        if update_data.get("date_of_birth"):
            update_data["date_of_birth"] = update_data["date_of_birth"].isoformat()
        
        result = supabase_admin.table("patients").update(update_data).eq(
            "id", patient_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update patient error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{patient_id}")
async def deactivate_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete (deactivate) patient."""
    try:
        result = supabase_admin.table("patients").update(
            {"is_active": False}
        ).eq("id", patient_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {"success": True, "message": "Patient deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate patient error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{patient_id}/history")
async def get_patient_history(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get patient's medical history."""
    try:
        # Get medical cases
        cases = supabase_admin.table("medical_cases").select(
            "*, doctors!medical_cases_assigned_doctor_id_fkey(first_name, last_name)"
        ).eq("patient_id", patient_id).order("created_at", desc=True).execute()
        
        # Get ECG results
        ecg_results = supabase_admin.table("ecg_results").select(
            "*"
        ).eq("patient_id", patient_id).order("created_at", desc=True).limit(10).execute()
        
        # Get MRI results
        mri_results = supabase_admin.table("mri_segmentation_results").select(
            "*"
        ).eq("patient_id", patient_id).order("created_at", desc=True).limit(10).execute()
        
        return {
            "success": True,
            "data": {
                "cases": cases.data,
                "ecg_results": ecg_results.data,
                "mri_results": mri_results.data
            }
        }
    except Exception as e:
        logger.error(f"Get patient history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
