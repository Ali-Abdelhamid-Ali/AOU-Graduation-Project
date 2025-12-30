"""Authentication API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import logging

from app.db.supabase_client import supabase_admin, supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # patient, doctor, nurse, admin, super_admin
    first_name: str
    last_name: str
    phone: Optional[str] = None
    hospital_id: Optional[str] = None
    license_number: Optional[str] = None  # Required for doctors
    specialty: Optional[str] = None  # For doctors

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordUpdateRequest(BaseModel):
    new_password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# ============== HELPERS ==============

ROLE_ALIAS_MAP = {
    'admin': 'administrator',
    'administrator': 'administrator',
    'super_admin': 'super_admin',
    'doctor': 'doctor',
    'nurse': 'nurse',
    'patient': 'patient'
}

ROLE_TABLE_MAP = {
    'patient': 'patients',
    'doctor': 'doctors',
    'nurse': 'nurses',
    'administrator': 'administrators',
    'super_admin': 'administrators'
}

def normalize_role(role: str) -> str:
    """Normalize role to database standard."""
    return ROLE_ALIAS_MAP.get(role.lower(), 'patient')

async def get_current_user(authorization: str = Header(None)) -> Dict[str, Any]:
    """Extract and validate current user from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify token with Supabase
        user_response = supabase_admin.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "user_metadata": user_response.user.user_metadata
        }
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ============== ENDPOINTS ==============

@router.post("/signup")
async def sign_up(request: SignUpRequest):
    """Register a new user."""
    try:
        normalized_role = normalize_role(request.role)
        
        # Validate doctor requirements
        if normalized_role == 'doctor' and not request.license_number:
            raise HTTPException(status_code=400, detail="License number required for doctors")
        
        # Build metadata for auth
        metadata = {
            "role": normalized_role,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "full_name": f"{request.first_name} {request.last_name}",
            "phone": request.phone,
            "hospital_id": request.hospital_id,
        }
        
        if normalized_role == 'doctor':
            metadata["license_number"] = request.license_number
        
        # Create user in Supabase Auth
        auth_response = supabase_admin.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True,  # Auto-confirm for this system
            "user_metadata": metadata
        })
        
        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        user_id = auth_response.user.id
        logger.info(f"✅ User created: {user_id} with role {normalized_role}")
        
        # The SQL trigger should handle profile creation
        # But we'll verify and create manually if needed
        table_name = ROLE_TABLE_MAP.get(normalized_role, 'patients')
        
        # Check if profile was created by trigger
        check = supabase_admin.table(table_name).select("id").eq("user_id", user_id).execute()
        
        if not check.data:
            # Manually create profile if trigger didn't
            profile_data = {
                "user_id": user_id,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "email": request.email,
                "phone": request.phone,
                "is_active": True
            }
            
            if request.hospital_id:
                profile_data["hospital_id"] = request.hospital_id
            
            if normalized_role == 'doctor':
                profile_data["license_number"] = request.license_number
            
            if normalized_role == 'patient':
                # Generate MRN
                hospital_code = "GEN"
                if request.hospital_id:
                    h = supabase_admin.table("hospitals").select("hospital_code").eq("id", request.hospital_id).single().execute()
                    if h.data:
                        hospital_code = h.data.get("hospital_code", "GEN")
                
                from datetime import datetime
                year = datetime.now().strftime("%y")
                import random
                seq = str(random.randint(1, 999999)).zfill(6)
                profile_data["mrn"] = f"{hospital_code}{year}{seq}"
            
            supabase_admin.table(table_name).insert(profile_data).execute()
            logger.info(f"✅ Profile created manually for {user_id}")
        
        # Link specialty for doctors
        if normalized_role == 'doctor' and request.specialty:
            doc = supabase_admin.table("doctors").select("id").eq("user_id", user_id).single().execute()
            spec = supabase_admin.table("specialty_types").select("id").eq("specialty_code", request.specialty).single().execute()
            if doc.data and spec.data:
                supabase_admin.table("doctor_specialties").insert({
                    "doctor_id": doc.data["id"],
                    "specialty_id": spec.data["id"],
                    "is_primary": True
                }).execute()
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "User registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signin")
async def sign_in(request: SignInRequest):
    """Sign in user."""
    try:
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = auth_response.user
        role = user.user_metadata.get("role", "patient")
        normalized_role = normalize_role(role)
        
        # Fetch profile data
        table_name = ROLE_TABLE_MAP.get(normalized_role, 'patients')
        profile = supabase_admin.table(table_name).select(
            "*, hospitals(hospital_name_en)"
        ).eq("user_id", user.id).single().execute()
        
        profile_data = profile.data if profile.data else {}
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": normalized_role,
                "profile": profile_data
            },
            "session": {
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "expires_at": auth_response.session.expires_at
            },
            "must_reset_password": user.user_metadata.get("must_reset_password", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signin error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/signout")
async def sign_out(authorization: str = Header(None)):
    """Sign out user."""
    try:
        if authorization:
            token = authorization.replace("Bearer ", "")
            supabase_client.auth.sign_out()
        return {"success": True, "message": "Signed out successfully"}
    except Exception as e:
        logger.error(f"Signout error: {e}")
        return {"success": True, "message": "Signed out"}

@router.post("/refresh")
async def refresh_token(request: TokenRefreshRequest):
    """Refresh access token."""
    try:
        response = supabase_client.auth.refresh_session(request.refresh_token)
        if not response.session:
            raise HTTPException(status_code=401, detail="Failed to refresh token")
        
        return {
            "success": True,
            "session": {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at
            }
        }
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Failed to refresh token")

@router.post("/password-reset-request")
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset email."""
    try:
        supabase_client.auth.reset_password_email(request.email)
        return {"success": True, "message": "Password reset email sent"}
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # Don't reveal if email exists
        return {"success": True, "message": "If email exists, reset link will be sent"}

@router.post("/password-update")
async def update_password(request: PasswordUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update user password."""
    try:
        supabase_admin.auth.admin.update_user_by_id(
            current_user["id"],
            {"password": request.new_password}
        )
        
        # Clear must_reset_password flag
        supabase_admin.auth.admin.update_user_by_id(
            current_user["id"],
            {"user_metadata": {"must_reset_password": False}}
        )
        
        return {"success": True, "message": "Password updated successfully"}
    except Exception as e:
        logger.error(f"Password update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update password")

@router.get("/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    try:
        role = current_user["user_metadata"].get("role", "patient")
        normalized_role = normalize_role(role)
        table_name = ROLE_TABLE_MAP.get(normalized_role, 'patients')
        
        profile = supabase_admin.table(table_name).select(
            "*, hospitals(hospital_name_en)"
        ).eq("user_id", current_user["id"]).single().execute()
        
        return {
            "success": True,
            "user": {
                "id": current_user["id"],
                "email": current_user["email"],
                "role": normalized_role,
                "profile": profile.data if profile.data else {}
            }
        }
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")
