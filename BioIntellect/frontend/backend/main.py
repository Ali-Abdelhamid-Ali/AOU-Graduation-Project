from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from frontend root
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env.local")
print(f"🔍 [DEBUG] Loading environment from: {ENV_PATH}")
# Use override=True to ensure .env.local values take precedence
load_dotenv(dotenv_path=ENV_PATH, override=True)

# List available relevant environment variables for debugging
print("🔍 [DEBUG] Available Env Vars:", [k for k in os.environ.keys() if k.startswith("SUPABASE") or k.startswith("VITE")])

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BioIntellect Clinical Backend")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174", # Common fallback ports
        "http://127.0.0.1:5174",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase Admin Client
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
# Accept both common names for the service role key
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY")
ANON_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")

if SERVICE_ROLE_KEY:
    # Safely print only the prefix
    print(f"✅ [AUTH] Service Role Key detected (Prefix: {SERVICE_ROLE_KEY[:10]}...)")
    SUPABASE_KEY = SERVICE_ROLE_KEY
else:
    print("⚠️ [AUTH] Service Role Key MISSING. Falling back to Anon Key (RLS will be active).")
    SUPABASE_KEY = ANON_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Principal Re-Architecture: Schema Alignment (SQL Part 2-5) ---

class RegistrationBase(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str # 'patient', 'doctor', 'administrator', 'super_admin'
    firstName: str
    lastName: str
    phone: Optional[str] = None
    hospitalId: Optional[str] = None # UUID

class PatientRegistration(RegistrationBase):
    gender: Optional[str] = None
    dateOfBirth: Optional[str] = None
    bloodType: str = "unknown"
    mrn: Optional[str] = None
    nationalId: Optional[str] = None
    passportNumber: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    regionId: Optional[str] = None
    countryId: Optional[str] = None

class DoctorRegistration(RegistrationBase):
    employeeId: Optional[str] = None
    specialtyId: Optional[str] = None # Primary specialty reference
    licenseNumber: str
    yearsOfExperience: int = 0
    qualification: Optional[str] = None

class AdminRegistration(RegistrationBase):
    employeeId: Optional[str] = None
    department: Optional[str] = None

# --- Endpoints ---

@app.post("/api/v1/auth/register")
async def register_user(reg: RegistrationBase):
    """
    BioIntellect Atomic Registration Pipeline (SQL Aligned):
    1. Auth.SignUp (Creates record in auth.users)
    2. public.user_roles (Security Critical - role assignment)
    3. public.[profiles] (Doctor/Patient/Admin specific record)
    """
    
    print(f"🚀 [REGISTRATION] Initializing pipeline for {reg.email} with role {reg.role}")

    try:
        # 1. AUTH SIGNUP
        # We send metadata to stay consistent with existing frontend expectations
        metadata = {
            "role": reg.role,
            "full_name": f"{reg.firstName} {reg.lastName}",
            "first_name": reg.firstName,
            "last_name": reg.lastName,
        }
        
        auth_response = supabase.auth.sign_up({
            "email": reg.email,
            "password": reg.password,
            "options": {
                "data": metadata
            }
        })

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Supabase Auth failed to create user record.")

        user_id = auth_response.user.id
        print(f"✅ [AUTH] User created: {user_id}")

        # 2. ASSIGN ROLE (public.user_roles)
        # Standardizing role names to app_role enum values
        role_map = {
            "administrator": "administrator",
            "admin": "administrator",
            "super_admin": "super_admin",
            "doctor": "doctor",
            "nurse": "nurse",
            "patient": "patient"
        }
        app_role = role_map.get(reg.role.lower(), "patient")
        
        role_payload = {
            "user_id": user_id,
            "role": app_role,
            "hospital_id": reg.hospitalId
        }
        
        role_res = supabase.table("user_roles").insert(role_payload).execute()
        if not role_res.data:
            print("⚠️ [ROLE] Warning: Failure to insert into public.user_roles. Proceeding to profile...")

        # 3. CREATE PROFILE RECORD
        profile_data = {
            "user_id": user_id,
            "first_name": reg.firstName,
            "last_name": reg.lastName,
            "email": reg.email,
            "phone": reg.phone,
            "hospital_id": reg.hospitalId,
            "is_active": True
        }

        target_table = "patients"
        if app_role in ["administrator", "super_admin"]:
            target_table = "administrators"
            # Map specific admin fields if present
            profile_data["employee_id"] = getattr(reg, "employeeId", None)
            profile_data["department"] = getattr(reg, "department", None)
        elif app_role == "doctor":
            target_table = "doctors"
            profile_data["license_number"] = getattr(reg, "licenseNumber", "TBD")
            profile_data["employee_id"] = getattr(reg, "employeeId", None)
        elif app_role == "patient":
            target_table = "patients"
            profile_data["mrn"] = getattr(reg, "mrn", f"P-{user_id[:8].upper()}")
            profile_data["gender"] = getattr(reg, "gender", None)
            profile_data["date_of_birth"] = getattr(reg, "dateOfBirth", None)

        print(f"🚀 [DB] Attempting insert into public.{target_table}...")
        db_res = supabase.table(target_table).insert(profile_data).execute()

        if not db_res.data:
            raise Exception(f"Failed to create profile record in {target_table}. Ensure referential integrity (Hospital ID).")

        return {
            "success": True,
            "userId": user_id,
            "role": app_role,
            "message": f"Global identity and {app_role} profile provisioned successfully."
        }

    except Exception as e:
        import traceback
        full_trace = traceback.format_exc()
        msg = str(e)
        print(f"🚨 [PIPELINE CRASH]:\n{full_trace}")
        
        # Human-Readable parsing of Postgres Errors
        detail = msg
        if "23503" in msg:
            if "user_roles" in msg:
                detail = "Referential integrity failure in 'user_roles': The Hospital ID or User ID does not exist in the parent tables."
            elif "administrators" in msg:
                detail = "Referential integrity failure in 'administrators': The Hospital ID or User ID does not exist in the parent tables."
            else:
                detail = f"Referential integrity failure (23503): {msg}"
        elif "23505" in msg:
            detail = "Uniqueness violation: Email or ID already exists."
        elif "401" in msg or "Unauthorized" in msg:
            detail = "Supabase Authorization Error (401): Check your SUPABASE_SERVICE_ROLE_KEY or ANON_KEY."
            
        raise HTTPException(
            status_code=500,
            detail=f"Principal System Error: {detail}"
        )

@app.get("/health")
async def health():
    print("💓 [HEALTH] Ping received from client")
    return {"status": "Principal Backend Operational"}
