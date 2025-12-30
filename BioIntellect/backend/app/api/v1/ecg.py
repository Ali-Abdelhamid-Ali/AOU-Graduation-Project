"""ECG Analysis API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class ECGSignalRequest(BaseModel):
    file_id: str
    patient_id: str
    case_id: Optional[str] = None
    signal_data: Optional[Dict[str, Any]] = None
    sampling_rate: Optional[int] = 500
    duration_seconds: Optional[float] = 10.0
    lead_count: Optional[int] = 12
    leads_available: Optional[List[str]] = None
    recording_date: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None

class ECGAnalysisRequest(BaseModel):
    signal_id: str
    patient_id: str
    case_id: Optional[str] = None
    model_name: str = "ECG-Classifier-V1"
    model_version: str = "1.0.0"

class ECGResultUpdateRequest(BaseModel):
    heart_rate: Optional[int] = None
    heart_rate_variability: Optional[float] = None
    rhythm_classification: Optional[str] = None
    rhythm_confidence: Optional[float] = None
    detected_conditions: Optional[List[Dict[str, Any]]] = None
    pr_interval: Optional[int] = None
    qrs_duration: Optional[int] = None
    qt_interval: Optional[int] = None
    qtc_interval: Optional[int] = None
    ai_interpretation: Optional[str] = None
    ai_recommendations: Optional[List[str]] = None
    risk_score: Optional[float] = None
    analysis_status: Optional[str] = None

class ECGReviewRequest(BaseModel):
    doctor_notes: Optional[str] = None
    doctor_agrees_with_ai: Optional[bool] = None

# ============== ENDPOINTS ==============

@router.post("/signals")
async def create_ecg_signal(
    request: ECGSignalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create ECG signal record."""
    try:
        signal_data = {
            "file_id": request.file_id,
            "patient_id": request.patient_id,
            "case_id": request.case_id,
            "signal_data": request.signal_data,
            "sampling_rate": request.sampling_rate,
            "duration_seconds": request.duration_seconds,
            "lead_count": request.lead_count,
            "leads_available": request.leads_available or ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"],
            "recording_date": request.recording_date or datetime.utcnow().isoformat(),
            "device_info": request.device_info,
            "quality_score": request.quality_score,
            "metadata": {}
        }
        
        result = supabase_admin.table("ecg_signals").insert(signal_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create ECG signal")
        
        logger.info(f"✅ ECG signal created: {result.data[0]['id']}")
        return {"success": True, "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create ECG signal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_ecg(
    request: ECGAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Run ECG analysis (creates result record and simulates AI analysis)."""
    try:
        # Create result record with pending status
        result_data = {
            "signal_id": request.signal_id,
            "patient_id": request.patient_id,
            "case_id": request.case_id,
            "analyzed_by_model": request.model_name,
            "model_version": request.model_version,
            "analysis_status": "processing"
        }
        
        result = supabase_admin.table("ecg_results").insert(result_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create ECG result")
        
        result_id = result.data[0]["id"]
        
        # Simulate AI Analysis (In production, this would call actual ML model)
        # For now, we provide simulated results
        ai_analysis = {
            "heart_rate": 78,
            "heart_rate_variability": 0.045,
            "rhythm_classification": "Normal Sinus Rhythm",
            "rhythm_confidence": 0.94,
            "detected_conditions": [
                {"condition": "Normal Sinus Rhythm", "confidence": 0.94, "severity": "none"}
            ],
            "pr_interval": 160,
            "qrs_duration": 90,
            "qt_interval": 380,
            "qtc_interval": 410,
            "ai_interpretation": "Normal ECG. Regular sinus rhythm with normal intervals. No significant ST changes or arrhythmias detected.",
            "ai_recommendations": ["Continue routine monitoring", "No immediate intervention required"],
            "risk_score": 15.0,
            "analysis_status": "completed",
            "processing_time_ms": 2500
        }
        
        # Update result with AI analysis
        updated = supabase_admin.table("ecg_results").update(ai_analysis).eq(
            "id", result_id
        ).execute()
        
        # Mark file as analyzed
        supabase_admin.table("medical_files").update({
            "is_analyzed": True,
            "analyzed_at": datetime.utcnow().isoformat()
        }).eq("id", request.signal_id).execute()
        
        logger.info(f"✅ ECG analysis completed: {result_id}")
        return {"success": True, "data": updated.data[0] if updated.data else result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze ECG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results")
async def list_ecg_results(
    patient_id: Optional[str] = None,
    case_id: Optional[str] = None,
    analysis_status: Optional[str] = None,
    is_reviewed: Optional[bool] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List ECG results with filters."""
    try:
        query = supabase_admin.table("ecg_results").select(
            "*, ecg_signals(*), patients(id, mrn, first_name, last_name), doctors!ecg_results_reviewed_by_doctor_id_fkey(first_name, last_name)"
        )
        
        if patient_id:
            query = query.eq("patient_id", patient_id)
        if case_id:
            query = query.eq("case_id", case_id)
        if analysis_status:
            query = query.eq("analysis_status", analysis_status)
        if is_reviewed is not None:
            query = query.eq("is_reviewed", is_reviewed)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List ECG results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{result_id}")
async def get_ecg_result(
    result_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get ECG result by ID."""
    try:
        result = supabase_admin.table("ecg_results").select(
            "*, ecg_signals(*), patients(*), medical_cases(*)"
        ).eq("id", result_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="ECG result not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get ECG result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/results/{result_id}")
async def update_ecg_result(
    result_id: str,
    request: ECGResultUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update ECG result."""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = supabase_admin.table("ecg_results").update(update_data).eq(
            "id", result_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="ECG result not found")
        
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update ECG result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/results/{result_id}/review")
async def review_ecg_result(
    result_id: str,
    request: ECGReviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """Doctor review of ECG result."""
    try:
        # Get doctor ID
        doc = supabase_admin.table("doctors").select("id").eq(
            "user_id", current_user["id"]
        ).single().execute()
        
        if not doc.data:
            raise HTTPException(status_code=403, detail="Only doctors can review results")
        
        update_data = {
            "is_reviewed": True,
            "reviewed_by_doctor_id": doc.data["id"],
            "reviewed_at": datetime.utcnow().isoformat(),
            "doctor_notes": request.doctor_notes,
            "doctor_agrees_with_ai": request.doctor_agrees_with_ai
        }
        
        result = supabase_admin.table("ecg_results").update(update_data).eq(
            "id", result_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="ECG result not found")
        
        logger.info(f"✅ ECG result reviewed: {result_id}")
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review ECG result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
