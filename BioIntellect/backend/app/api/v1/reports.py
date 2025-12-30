"""Reports API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import random

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class ReportCreateRequest(BaseModel):
    patient_id: str
    case_id: Optional[str] = None
    report_type: str  # ecg_analysis, mri_analysis, comprehensive
    ecg_result_id: Optional[str] = None
    mri_result_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    content: Optional[Dict[str, Any]] = None

class ReportUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    status: Optional[str] = None  # draft, pending_review, approved, rejected
    approval_notes: Optional[str] = None

# ============== HELPERS ==============

def generate_report_number(report_type: str) -> str:
    """Generate report number."""
    prefix = report_type[:3].upper()
    date_part = datetime.now().strftime("%Y%m%d")
    seq = str(random.randint(1, 99999)).zfill(5)
    return f"{prefix}-{date_part}-{seq}"

# ============== ENDPOINTS ==============

@router.get("")
async def list_reports(
    patient_id: Optional[str] = None,
    case_id: Optional[str] = None,
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    doctor_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List reports with filters."""
    try:
        query = supabase_admin.table("generated_reports").select(
            "*, patients(id, mrn, first_name, last_name), doctors(id, first_name, last_name)"
        )
        
        if patient_id:
            query = query.eq("patient_id", patient_id)
        if case_id:
            query = query.eq("case_id", case_id)
        if report_type:
            query = query.eq("report_type", report_type)
        if status:
            query = query.eq("status", status)
        if doctor_id:
            query = query.eq("doctor_id", doctor_id)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List reports error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get report by ID."""
    try:
        result = supabase_admin.table("generated_reports").select(
            "*, patients(*), doctors(*), medical_cases(*), ecg_results(*), mri_segmentation_results(*)"
        ).eq("id", report_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_report(
    request: ReportCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new report."""
    try:
        # Get doctor ID if applicable
        doctor_id = None
        role = current_user["user_metadata"].get("role", "patient")
        if role == "doctor":
            doc = supabase_admin.table("doctors").select("id").eq(
                "user_id", current_user["id"]
            ).single().execute()
            if doc.data:
                doctor_id = doc.data["id"]
        
        # Generate report content if not provided
        content = request.content
        if not content:
            content = {
                "sections": [],
                "findings": [],
                "conclusion": "",
                "recommendations": []
            }
            
            # Build content from ECG result if provided
            if request.ecg_result_id:
                ecg = supabase_admin.table("ecg_results").select("*").eq(
                    "id", request.ecg_result_id
                ).single().execute()
                if ecg.data:
                    content["sections"].append({
                        "title": "ECG Analysis Results",
                        "content": ecg.data.get("ai_interpretation", ""),
                        "findings": ecg.data.get("detected_conditions", [])
                    })
                    content["recommendations"].extend(ecg.data.get("ai_recommendations", []))
            
            # Build content from MRI result if provided
            if request.mri_result_id:
                mri = supabase_admin.table("mri_segmentation_results").select("*").eq(
                    "id", request.mri_result_id
                ).single().execute()
                if mri.data:
                    content["sections"].append({
                        "title": "MRI Segmentation Results",
                        "content": mri.data.get("ai_interpretation", ""),
                        "findings": mri.data.get("detected_abnormalities", [])
                    })
                    content["recommendations"].extend(mri.data.get("ai_recommendations", []))
        
        report_data = {
            "report_number": generate_report_number(request.report_type),
            "patient_id": request.patient_id,
            "case_id": request.case_id,
            "doctor_id": doctor_id,
            "report_type": request.report_type,
            "ecg_result_id": request.ecg_result_id,
            "mri_result_id": request.mri_result_id,
            "title": request.title,
            "summary": request.summary,
            "content": content,
            "generated_by_model": "Report-Generator-V1",
            "model_version": "1.0.0",
            "status": "draft",
            "is_final": False,
            "version": 1
        }
        
        result = supabase_admin.table("generated_reports").insert(report_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create report")
        
        logger.info(f"✅ Report created: {result.data[0]['report_number']}")
        return {"success": True, "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{report_id}")
async def update_report(
    report_id: str,
    request: ReportUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update report."""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = supabase_admin.table("generated_reports").update(update_data).eq(
            "id", report_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{report_id}/approve")
async def approve_report(
    report_id: str,
    approval_notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Approve a report."""
    try:
        # Get doctor ID
        doc = supabase_admin.table("doctors").select("id").eq(
            "user_id", current_user["id"]
        ).single().execute()
        
        if not doc.data:
            raise HTTPException(status_code=403, detail="Only doctors can approve reports")
        
        update_data = {
            "status": "approved",
            "approved_by_doctor_id": doc.data["id"],
            "approved_at": datetime.utcnow().isoformat(),
            "approval_notes": approval_notes,
            "is_final": True
        }
        
        result = supabase_admin.table("generated_reports").update(update_data).eq(
            "id", report_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        logger.info(f"✅ Report approved: {report_id}")
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{report_id}/sign")
async def sign_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Digitally sign a report."""
    try:
        # Get doctor ID
        doc = supabase_admin.table("doctors").select("id, first_name, last_name, license_number").eq(
            "user_id", current_user["id"]
        ).single().execute()
        
        if not doc.data:
            raise HTTPException(status_code=403, detail="Only doctors can sign reports")
        
        # Generate digital signature (simplified - in production use proper PKI)
        import hashlib
        signature_data = f"{report_id}:{doc.data['id']}:{datetime.utcnow().isoformat()}"
        signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
        update_data = {
            "digital_signature": signature,
            "signature_timestamp": datetime.utcnow().isoformat(),
            "signed_by_doctor_id": doc.data["id"],
            "status": "approved",
            "is_final": True
        }
        
        result = supabase_admin.table("generated_reports").update(update_data).eq(
            "id", report_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        logger.info(f"✅ Report signed: {report_id}")
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
