"""Medical Cases API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import random

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class CaseCreateRequest(BaseModel):
    patient_id: str
    assigned_doctor_id: Optional[str] = None
    priority: Optional[str] = "normal"  # low, normal, high, critical
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []

class CaseUpdateRequest(BaseModel):
    assigned_doctor_id: Optional[str] = None
    status: Optional[str] = None  # open, in_progress, pending_review, closed, archived
    priority: Optional[str] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    diagnosis_icd10: Optional[str] = None
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    follow_up_date: Optional[str] = None

# ============== HELPERS ==============

def generate_case_number(hospital_code: str) -> str:
    """Generate case number."""
    date_part = datetime.now().strftime("%Y%m%d")
    seq = str(random.randint(1, 9999)).zfill(4)
    return f"{hospital_code}-{date_part}-{seq}"

# ============== ENDPOINTS ==============

@router.get("")
async def list_cases(
    patient_id: Optional[str] = None,
    assigned_doctor_id: Optional[str] = None,
    hospital_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    is_archived: bool = False,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List medical cases with filters."""
    try:
        query = supabase_admin.table("medical_cases").select(
            "*, patients(id, mrn, first_name, last_name), doctors!medical_cases_assigned_doctor_id_fkey(id, first_name, last_name)"
        ).eq("is_archived", is_archived)
        
        if patient_id:
            query = query.eq("patient_id", patient_id)
        if assigned_doctor_id:
            query = query.eq("assigned_doctor_id", assigned_doctor_id)
        if hospital_id:
            query = query.eq("hospital_id", hospital_id)
        if status:
            query = query.eq("status", status)
        if priority:
            query = query.eq("priority", priority)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List cases error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{case_id}")
async def get_case(
    case_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get medical case by ID."""
    try:
        result = supabase_admin.table("medical_cases").select(
            "*, patients(*), doctors!medical_cases_assigned_doctor_id_fkey(*), hospitals(*)"
        ).eq("id", case_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Get associated files
        files = supabase_admin.table("medical_files").select(
            "*"
        ).eq("case_id", case_id).eq("is_deleted", False).execute()
        
        result.data["files"] = files.data
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get case error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_case(
    request: CaseCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new medical case."""
    try:
        # Get patient's hospital
        patient = supabase_admin.table("patients").select(
            "hospital_id, hospitals(hospital_code)"
        ).eq("id", request.patient_id).single().execute()
        
        if not patient.data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        hospital_id = patient.data["hospital_id"]
        hospital_code = patient.data.get("hospitals", {}).get("hospital_code", "GEN")
        
        # Get doctor ID from current user if applicable
        created_by_doctor_id = None
        role = current_user["user_metadata"].get("role", "patient")
        if role == "doctor":
            doc = supabase_admin.table("doctors").select("id").eq(
                "user_id", current_user["id"]
            ).single().execute()
            if doc.data:
                created_by_doctor_id = doc.data["id"]
        
        case_data = {
            "case_number": generate_case_number(hospital_code),
            "patient_id": request.patient_id,
            "hospital_id": hospital_id,
            "assigned_doctor_id": request.assigned_doctor_id,
            "created_by_doctor_id": created_by_doctor_id,
            "status": "open",
            "priority": request.priority or "normal",
            "chief_complaint": request.chief_complaint,
            "diagnosis": request.diagnosis,
            "treatment_plan": request.treatment_plan,
            "notes": request.notes,
            "tags": request.tags or [],
            "is_archived": False
        }
        
        result = supabase_admin.table("medical_cases").insert(case_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create case")
        
        logger.info(f"✅ Case created: {result.data[0]['case_number']}")
        return {"success": True, "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create case error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{case_id}")
async def update_case(
    case_id: str,
    request: CaseUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update medical case."""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = supabase_admin.table("medical_cases").update(update_data).eq(
            "id", case_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update case error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{case_id}/archive")
async def archive_case(
    case_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Archive a case."""
    try:
        result = supabase_admin.table("medical_cases").update({
            "is_archived": True,
            "archived_at": datetime.utcnow().isoformat(),
            "archived_by": current_user["id"]
        }).eq("id", case_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Case not found")
        
        return {"success": True, "message": "Case archived"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Archive case error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
