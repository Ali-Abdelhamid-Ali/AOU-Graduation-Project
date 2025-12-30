"""Analytics API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/dashboard")
async def get_dashboard_stats(
    hospital_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard statistics."""
    try:
        stats = {}
        
        # Patients count
        patients_query = supabase_admin.table("patients").select("id", count="exact").eq("is_active", True)
        if hospital_id:
            patients_query = patients_query.eq("hospital_id", hospital_id)
        patients_result = patients_query.execute()
        stats["total_patients"] = patients_result.count or 0
        
        # Doctors count
        doctors_query = supabase_admin.table("doctors").select("id", count="exact").eq("is_active", True)
        if hospital_id:
            doctors_query = doctors_query.eq("hospital_id", hospital_id)
        doctors_result = doctors_query.execute()
        stats["total_doctors"] = doctors_result.count or 0
        
        # Active cases count
        cases_query = supabase_admin.table("medical_cases").select("id", count="exact").eq("is_archived", False)
        if hospital_id:
            cases_query = cases_query.eq("hospital_id", hospital_id)
        cases_result = cases_query.execute()
        stats["active_cases"] = cases_result.count or 0
        
        # ECG analyses count
        ecg_result = supabase_admin.table("ecg_results").select("id", count="exact").execute()
        stats["total_ecg_analyses"] = ecg_result.count or 0
        
        # MRI analyses count
        mri_result = supabase_admin.table("mri_segmentation_results").select("id", count="exact").execute()
        stats["total_mri_analyses"] = mri_result.count or 0
        
        # Reports count
        reports_result = supabase_admin.table("generated_reports").select("id", count="exact").execute()
        stats["total_reports"] = reports_result.count or 0
        
        # Cases by status
        stats["cases_by_status"] = {}
        for status in ["open", "in_progress", "pending_review", "closed"]:
            status_query = supabase_admin.table("medical_cases").select("id", count="exact").eq("status", status).eq("is_archived", False)
            if hospital_id:
                status_query = status_query.eq("hospital_id", hospital_id)
            status_result = status_query.execute()
            stats["cases_by_status"][status] = status_result.count or 0
        
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Get dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients/trends")
async def get_patient_trends(
    hospital_id: Optional[str] = None,
    days: int = Query(30, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get patient registration trends."""
    try:
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = supabase_admin.table("patients").select(
            "id, created_at"
        ).gte("created_at", start_date)
        
        if hospital_id:
            query = query.eq("hospital_id", hospital_id)
        
        result = query.order("created_at", desc=False).execute()
        
        # Group by date
        trends = {}
        for patient in result.data:
            date = patient["created_at"][:10]  # Extract date part
            trends[date] = trends.get(date, 0) + 1
        
        return {"success": True, "data": trends}
    except Exception as e:
        logger.error(f"Get patient trends error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyses/summary")
async def get_analysis_summary(
    hospital_id: Optional[str] = None,
    days: int = Query(30, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get AI analysis summary."""
    try:
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        summary = {
            "ecg": {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "reviewed": 0,
                "abnormal_detected": 0
            },
            "mri": {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "reviewed": 0,
                "abnormal_detected": 0
            }
        }
        
        # ECG stats
        ecg_total = supabase_admin.table("ecg_results").select("id", count="exact").gte("created_at", start_date).execute()
        summary["ecg"]["total"] = ecg_total.count or 0
        
        ecg_completed = supabase_admin.table("ecg_results").select("id", count="exact").eq("analysis_status", "completed").gte("created_at", start_date).execute()
        summary["ecg"]["completed"] = ecg_completed.count or 0
        
        ecg_pending = supabase_admin.table("ecg_results").select("id", count="exact").eq("analysis_status", "pending").gte("created_at", start_date).execute()
        summary["ecg"]["pending"] = ecg_pending.count or 0
        
        ecg_reviewed = supabase_admin.table("ecg_results").select("id", count="exact").eq("is_reviewed", True).gte("created_at", start_date).execute()
        summary["ecg"]["reviewed"] = ecg_reviewed.count or 0
        
        # MRI stats
        mri_total = supabase_admin.table("mri_segmentation_results").select("id", count="exact").gte("created_at", start_date).execute()
        summary["mri"]["total"] = mri_total.count or 0
        
        mri_completed = supabase_admin.table("mri_segmentation_results").select("id", count="exact").eq("analysis_status", "completed").gte("created_at", start_date).execute()
        summary["mri"]["completed"] = mri_completed.count or 0
        
        mri_pending = supabase_admin.table("mri_segmentation_results").select("id", count="exact").eq("analysis_status", "pending").gte("created_at", start_date).execute()
        summary["mri"]["pending"] = mri_pending.count or 0
        
        mri_reviewed = supabase_admin.table("mri_segmentation_results").select("id", count="exact").eq("is_reviewed", True).gte("created_at", start_date).execute()
        summary["mri"]["reviewed"] = mri_reviewed.count or 0
        
        return {"success": True, "data": summary}
    except Exception as e:
        logger.error(f"Get analysis summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    patient_id: Optional[str] = None,
    is_sensitive: Optional[bool] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get audit logs (admin only)."""
    try:
        role = current_user["user_metadata"].get("role", "patient")
        if role not in ["administrator", "super_admin"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        query = supabase_admin.table("audit_logs").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        if action:
            query = query.eq("action", action)
        if resource_type:
            query = query.eq("resource_type", resource_type)
        if patient_id:
            query = query.eq("patient_id", patient_id)
        if is_sensitive is not None:
            query = query.eq("is_sensitive", is_sensitive)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
