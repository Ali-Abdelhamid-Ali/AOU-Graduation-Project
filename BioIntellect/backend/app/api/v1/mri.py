"""MRI Segmentation API endpoints."""
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

class MRIScanRequest(BaseModel):
    file_id: str
    patient_id: str
    case_id: Optional[str] = None
    scan_type: Optional[str] = "brain"  # brain, cardiac, spine, etc.
    sequence_type: Optional[str] = "T1"  # T1, T2, FLAIR, DWI, T1ce
    body_part: Optional[str] = None
    slice_count: Optional[int] = None
    slice_thickness_mm: Optional[float] = None
    field_strength: Optional[float] = 1.5  # Tesla
    scan_date: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    dicom_metadata: Optional[Dict[str, Any]] = None

class MRIAnalysisRequest(BaseModel):
    scan_id: str
    patient_id: str
    case_id: Optional[str] = None
    model_name: str = "MRI-Segmentation-V1"
    model_version: str = "1.0.0"

class MRIResultUpdateRequest(BaseModel):
    segmentation_mask_path: Optional[str] = None
    segmented_regions: Optional[List[Dict[str, Any]]] = None
    detected_abnormalities: Optional[List[Dict[str, Any]]] = None
    measurements: Optional[Dict[str, Any]] = None
    ai_interpretation: Optional[str] = None
    ai_recommendations: Optional[List[str]] = None
    severity_score: Optional[float] = None
    analysis_status: Optional[str] = None

class MRIReviewRequest(BaseModel):
    doctor_notes: Optional[str] = None
    doctor_agrees_with_ai: Optional[bool] = None

# ============== ENDPOINTS ==============

@router.post("/scans")
async def create_mri_scan(
    request: MRIScanRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create MRI scan record."""
    try:
        scan_data = {
            "file_id": request.file_id,
            "patient_id": request.patient_id,
            "case_id": request.case_id,
            "scan_type": request.scan_type,
            "sequence_type": request.sequence_type,
            "body_part": request.body_part,
            "slice_count": request.slice_count,
            "slice_thickness_mm": request.slice_thickness_mm,
            "field_strength": request.field_strength,
            "scan_date": request.scan_date or datetime.utcnow().isoformat(),
            "device_info": request.device_info,
            "dicom_metadata": request.dicom_metadata
        }
        
        result = supabase_admin.table("mri_scans").insert(scan_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create MRI scan")
        
        logger.info(f"✅ MRI scan created: {result.data[0]['id']}")
        return {"success": True, "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create MRI scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_mri(
    request: MRIAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Run MRI segmentation analysis."""
    try:
        # Create result record with pending status
        result_data = {
            "scan_id": request.scan_id,
            "patient_id": request.patient_id,
            "case_id": request.case_id,
            "analyzed_by_model": request.model_name,
            "model_version": request.model_version,
            "analysis_status": "processing"
        }
        
        result = supabase_admin.table("mri_segmentation_results").insert(result_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create MRI result")
        
        result_id = result.data[0]["id"]
        
        # Simulate AI Segmentation Analysis
        ai_analysis = {
            "segmented_regions": [
                {"region": "whole_tumor", "volume_ml": 42.5, "area_cm2": 15.8},
                {"region": "enhancing_core", "volume_ml": 21.0, "area_cm2": 8.2},
                {"region": "peritumoral_edema", "volume_ml": 15.2, "area_cm2": 5.6},
                {"region": "necrotic_core", "volume_ml": 6.3, "area_cm2": 2.0}
            ],
            "detected_abnormalities": [
                {
                    "finding": "High-grade glioma",
                    "location": "Right frontal lobe",
                    "size_mm": [45, 38, 32],
                    "confidence": 0.92,
                    "who_grade": "IV"
                }
            ],
            "measurements": {
                "total_tumor_volume": 42.5,
                "edema_volume": 15.2,
                "enhancing_volume": 21.0,
                "necrosis_volume": 6.3,
                "midline_shift_mm": 3.2
            },
            "ai_interpretation": "MRI brain scan reveals a heterogeneous mass in the right frontal lobe consistent with high-grade glioma (WHO Grade IV). The tumor demonstrates irregular enhancement with central necrosis and significant peritumoral edema. Mild mass effect with 3.2mm midline shift.",
            "ai_recommendations": [
                "Urgent neurosurgical consultation recommended",
                "Consider stereotactic biopsy for histopathological confirmation",
                "Multidisciplinary tumor board review advised",
                "Follow-up MRI in 4-6 weeks post-treatment"
            ],
            "severity_score": 85.0,
            "analysis_status": "completed",
            "processing_time_ms": 4500
        }
        
        # Update result with AI analysis
        updated = supabase_admin.table("mri_segmentation_results").update(ai_analysis).eq(
            "id", result_id
        ).execute()
        
        # Mark file as analyzed
        supabase_admin.table("medical_files").update({
            "is_analyzed": True,
            "analyzed_at": datetime.utcnow().isoformat()
        }).eq("id", request.scan_id).execute()
        
        logger.info(f"✅ MRI analysis completed: {result_id}")
        return {"success": True, "data": updated.data[0] if updated.data else result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze MRI error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results")
async def list_mri_results(
    patient_id: Optional[str] = None,
    case_id: Optional[str] = None,
    analysis_status: Optional[str] = None,
    is_reviewed: Optional[bool] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List MRI results with filters."""
    try:
        query = supabase_admin.table("mri_segmentation_results").select(
            "*, mri_scans(*), patients(id, mrn, first_name, last_name), doctors!mri_segmentation_results_reviewed_by_doctor_id_fkey(first_name, last_name)"
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
        logger.error(f"List MRI results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{result_id}")
async def get_mri_result(
    result_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get MRI result by ID."""
    try:
        result = supabase_admin.table("mri_segmentation_results").select(
            "*, mri_scans(*), patients(*), medical_cases(*)"
        ).eq("id", result_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="MRI result not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get MRI result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/results/{result_id}")
async def update_mri_result(
    result_id: str,
    request: MRIResultUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update MRI result."""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = supabase_admin.table("mri_segmentation_results").update(update_data).eq(
            "id", result_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="MRI result not found")
        
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update MRI result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/results/{result_id}/review")
async def review_mri_result(
    result_id: str,
    request: MRIReviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """Doctor review of MRI result."""
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
        
        result = supabase_admin.table("mri_segmentation_results").update(update_data).eq(
            "id", result_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="MRI result not found")
        
        logger.info(f"✅ MRI result reviewed: {result_id}")
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review MRI result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
