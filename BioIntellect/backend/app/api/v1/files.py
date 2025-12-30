"""Medical Files API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import hashlib
import uuid

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class FileMetadataRequest(BaseModel):
    case_id: str
    patient_id: str
    file_type: str  # ecg_signal, mri_scan, lab_report, xray, ct_scan, other
    description: Optional[str] = None

# ============== HELPERS ==============

def calculate_checksum(content: bytes) -> str:
    """Calculate SHA-256 checksum."""
    return hashlib.sha256(content).hexdigest()

# ============== ENDPOINTS ==============

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    patient_id: str = Form(...),
    file_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload a medical file."""
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        checksum = calculate_checksum(content)
        
        # Generate storage path
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        unique_name = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
        storage_path = f"{patient_id}/{case_id}/{unique_name}"
        
        # Upload to Supabase Storage
        storage_response = supabase_admin.storage.from_("medical-files").upload(
            path=storage_path,
            file=content,
            file_options={"content-type": file.content_type or "application/octet-stream"}
        )
        
        # Create file record in database
        file_record = {
            "case_id": case_id,
            "patient_id": patient_id,
            "uploaded_by": current_user["id"],
            "file_type": file_type,
            "file_name": file.filename,
            "file_path": storage_path,
            "file_size": file_size,
            "mime_type": file.content_type,
            "storage_bucket": "medical-files",
            "description": description,
            "metadata": {"checksum": checksum},
            "is_analyzed": False,
            "is_deleted": False
        }
        
        result = supabase_admin.table("medical_files").insert(file_record).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create file record")
        
        logger.info(f"✅ File uploaded: {storage_path}")
        return {"success": True, "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}")
async def get_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get file metadata."""
    try:
        result = supabase_admin.table("medical_files").select(
            "*"
        ).eq("id", file_id).eq("is_deleted", False).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}/download-url")
async def get_download_url(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get signed download URL for file."""
    try:
        # Get file record
        file_record = supabase_admin.table("medical_files").select(
            "file_path, storage_bucket"
        ).eq("id", file_id).eq("is_deleted", False).single().execute()
        
        if not file_record.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate signed URL (valid for 1 hour)
        signed_url = supabase_admin.storage.from_(
            file_record.data["storage_bucket"]
        ).create_signed_url(
            file_record.data["file_path"],
            3600  # 1 hour
        )
        
        return {"success": True, "url": signed_url.get("signedURL")}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get download URL error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a file."""
    try:
        result = supabase_admin.table("medical_files").update({
            "is_deleted": True,
            "deleted_at": datetime.utcnow().isoformat(),
            "deleted_by": current_user["id"]
        }).eq("id", file_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"success": True, "message": "File deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/case/{case_id}")
async def list_case_files(
    case_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List all files for a case."""
    try:
        result = supabase_admin.table("medical_files").select(
            "*"
        ).eq("case_id", case_id).eq("is_deleted", False).order(
            "created_at", desc=True
        ).execute()
        
        return {"success": True, "data": result.data}
    except Exception as e:
        logger.error(f"List case files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
