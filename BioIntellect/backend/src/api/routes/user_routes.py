"""User Routes - Complete User Management API."""

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from typing import Optional, List, Any
from src.repositories.user_repository import UserRepository
from src.repositories.auth_repository import AuthRepository
from src.repositories.storage_repository import StorageRepository
from src.repositories.clinical_repository import ClinicalRepository
from src.services.domain.file_service import FileService
from src.services.domain.auth_service import AuthService
from src.validators.medical_dto import (
    UserRoleCreateDTO,
    UserRoleUpdateDTO,
    DoctorCreateDTO,
    DoctorUpdateDTO,
    NurseCreateDTO,
    NurseUpdateDTO,
    AdministratorCreateDTO,
    AdministratorUpdateDTO,
    PatientCreateDTO,
    PatientUpdateDTO,
    DoctorSpecialtyCreateDTO,
    UserRoleResponseDTO,
    DoctorResponseDTO,
    NurseResponseDTO,
    AdministratorResponseDTO,
    PatientResponseDTO,
    DoctorSpecialtyResponseDTO,
    UserProfileResponseDTO,
    UserProfileUpdateDTO,
)
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger

logger = get_logger("routes.user")

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        429: {"description": "Too Many Requests"},
        500: {"description": "Internal Server Error"},
    },
)


def get_auth_service():
    repo = AuthRepository()
    return AuthService(repo)


def _enforce_user_detail_access(user: dict[str, Any], target_id: str) -> None:
    """Allow self-access or privileged user-management access."""
    if user.get("id") == target_id:
        return

    role = str(user.get("role", "")).strip().lower()
    if role in {"admin", "super_admin"}:
        return

    permissions = user.get("permissions", set())
    if Permission.MANAGE_USERS in permissions:
        return

    raise HTTPException(status_code=403, detail="Access denied")


# â”پâ”پâ”پâ”پ USER ROLES â”پâ”پâ”پâ”پ


@router.get(
    "/roles",
    response_model=List[UserRoleResponseDTO],
    dependencies=[Depends(require_permission(Permission.LIST_USERS))],
)
async def list_user_roles(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    role: Optional[str] = Query(None, description="Filter by role"),
    hospital_id: Optional[str] = Query(None, description="Filter by hospital ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: UserRepository = Depends(UserRepository),
):
    """List all user roles with optional filtering (Admin/Super Admin only)."""
    try:
        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if role:
            filters["role"] = role
        if hospital_id:
            filters["hospital_id"] = hospital_id
        if is_active is not None:
            filters["is_active"] = is_active

        roles = await repo.list_user_roles(filters, limit, offset)
        return roles
    except Exception as e:
        logger.error(f"Failed to list user roles: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user roles")


@router.get(
    "/roles/{role_id}",
    response_model=UserRoleResponseDTO,
    dependencies=[Depends(require_permission(Permission.LIST_USERS))],
)
async def get_user_role(role_id: str, repo: UserRepository = Depends(UserRepository)):
    """Get a specific user role by ID (Admin/Super Admin only)."""
    try:
        role = await repo.get_user_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="User role not found")
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user role {role_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user role")


@router.post(
    "/roles",
    response_model=UserRoleResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def create_user_role(
    role_data: UserRoleCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Create a new user role (Admin/Super Admin only)."""
    try:
        role = await repo.create_user_role(role_data.dict())
        logger.info(f"User role created by user {user['id']}: {role['id']}")
        return role
    except Exception as e:
        logger.error(f"Failed to create user role: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user role")


@router.put(
    "/roles/{role_id}",
    response_model=UserRoleResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def update_user_role(
    role_id: str,
    role_data: UserRoleUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Update a user role (Admin/Super Admin only)."""
    try:
        role = await repo.update_user_role(role_id, role_data.dict(exclude_unset=True))
        if not role:
            raise HTTPException(status_code=404, detail="User role not found")
        logger.info(f"User role updated by user {user['id']}: {role_id}")
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user role {role_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user role")


@router.delete(
    "/roles/{role_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def delete_user_role(
    role_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Delete a user role (Admin/Super Admin only)."""
    try:
        success = await repo.delete_user_role(role_id)
        if not success:
            raise HTTPException(status_code=404, detail="User role not found")
        logger.info(f"User role deleted by user {user['id']}: {role_id}")
        return {"success": True, "message": "User role deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user role {role_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete user role")


# â”پâ”پâ”پâ”پ DOCTORS â”پâ”پâ”پâ”پ


@router.get(
    "/doctors",
    response_model=List[DoctorResponseDTO],
    dependencies=[Depends(require_permission(Permission.LIST_USERS))],
)
async def list_doctors(
    hospital_id: Optional[str] = Query(None, description="Filter by hospital ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: UserRepository = Depends(UserRepository),
):
    """List all doctors with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if hospital_id:
            filters["hospital_id"] = hospital_id
        if is_active is not None:
            filters["is_active"] = is_active

        doctors = await repo.list_doctors(filters, limit, offset)
        return doctors
    except Exception as e:
        logger.error(f"Failed to list doctors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve doctors")


@router.get("/doctors/{doctor_id}", response_model=DoctorResponseDTO)
async def get_doctor(
    doctor_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Get a specific doctor by ID."""
    try:
        _enforce_user_detail_access(user, doctor_id)
        doctor = await repo.get_doctor(doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return doctor
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get doctor {doctor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve doctor")


@router.post(
    "/doctors",
    response_model=DoctorResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def create_doctor(
    doctor_data: DoctorCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create a new doctor (Admin/Super Admin only)."""
    try:
        # 1. Use AuthService to create both Auth account and Doctor Profile
        # model_dump with mode='json' ensures date objects become ISO strings
        result = await auth_service.admin_create_user(
            "doctor", doctor_data.model_dump(mode="json")
        )

        # 2. Re-fetch the newly created doctor profile for the response
        repo = UserRepository()
        doctor = await repo.get_doctor(result["user_id"])

        if doctor:
            logger.info(f"Doctor created by user {user['id']}: {doctor.get('id')}")
        else:
            logger.warning(
                f"Doctor profile not found after creation for user_id: {result['user_id']}"
            )
            # We might want to return a partial response or raise a specific error
            # But for now, we'll try to return the result with user_id at least
            doctor = {
                "user_id": result["user_id"],
                "message": "Profile created but could not be retrieved immediately",
            }

        return doctor
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to create doctor: {error_msg}")

        # Check for specific known conflict errors
        if "already been registered" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="A user with this email address has already been registered.",
            )

        raise HTTPException(status_code=500, detail=error_msg)


@router.put(
    "/doctors/{doctor_id}",
    response_model=DoctorResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def update_doctor(
    doctor_id: str,
    doctor_data: DoctorUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Update a doctor (Admin/Super Admin only)."""
    try:
        doctor = await repo.update_doctor(
            doctor_id, doctor_data.dict(exclude_unset=True)
        )
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        logger.info(f"Doctor updated by user {user['id']}: {doctor_id}")
        return doctor
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update doctor {doctor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update doctor")


@router.delete(
    "/doctors/{doctor_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def delete_doctor(
    doctor_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Delete a doctor (Admin/Super Admin only)."""
    try:
        success = await repo.delete_doctor(doctor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Doctor not found")
        logger.info(f"Doctor deleted by user {user['id']}: {doctor_id}")
        return {"success": True, "message": "Doctor deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete doctor {doctor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete doctor")


# â”پâ”پâ”پâ”پ DOCTOR SPECIALTIES â”پâ”پâ”پâ”پ


@router.get(
    "/doctors/{doctor_id}/specialties", response_model=List[DoctorSpecialtyResponseDTO]
)
async def list_doctor_specialties(
    doctor_id: str,
    is_primary: Optional[bool] = Query(None, description="Filter by primary specialty"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: UserRepository = Depends(UserRepository),
):
    """List a doctor's specialties."""
    try:
        filters: dict[str, Any] = {"doctor_id": doctor_id}
        if is_primary is not None:
            filters["is_primary"] = is_primary

        specialties = await repo.list_doctor_specialties(filters, limit, offset)
        return specialties
    except Exception as e:
        logger.error(f"Failed to list doctor specialties for {doctor_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve doctor specialties"
        )


@router.post(
    "/doctors/{doctor_id}/specialties",
    response_model=DoctorSpecialtyResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def add_doctor_specialty(
    doctor_id: str,
    specialty_data: DoctorSpecialtyCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Add a specialty to a doctor (Admin/Super Admin only)."""
    try:
        specialty = await repo.add_doctor_specialty(doctor_id, specialty_data.dict())
        logger.info(
            f"Specialty added to doctor {doctor_id} by user {user['id']}: {specialty['id']}"
        )
        return specialty
    except Exception as e:
        logger.error(f"Failed to add specialty to doctor {doctor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add doctor specialty")


@router.delete(
    "/doctors/{doctor_id}/specialties/{specialty_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def remove_doctor_specialty(
    doctor_id: str,
    specialty_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Remove a specialty from a doctor (Admin/Super Admin only)."""
    try:
        success = await repo.remove_doctor_specialty(doctor_id, specialty_id)
        if not success:
            raise HTTPException(status_code=404, detail="Doctor specialty not found")
        logger.info(
            f"Specialty removed from doctor {doctor_id} by user {user['id']}: {specialty_id}"
        )
        return {"success": True, "message": "Doctor specialty removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove specialty from doctor {doctor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove doctor specialty")


# â”پâ”پâ”پâ”پ NURSES â”پâ”پâ”پâ”پ


@router.get(
    "/nurses",
    response_model=List[NurseResponseDTO],
    dependencies=[Depends(require_permission(Permission.LIST_USERS))],
)
async def list_nurses(
    hospital_id: Optional[str] = Query(None, description="Filter by hospital ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: UserRepository = Depends(UserRepository),
):
    """List all nurses with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if hospital_id:
            filters["hospital_id"] = hospital_id
        if is_active is not None:
            filters["is_active"] = is_active

        nurses = await repo.list_nurses(filters, limit, offset)
        return nurses
    except Exception as e:
        logger.error(f"Failed to list nurses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve nurses")


@router.get("/nurses/{nurse_id}", response_model=NurseResponseDTO)
async def get_nurse(
    nurse_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Get a specific nurse by ID."""
    try:
        _enforce_user_detail_access(user, nurse_id)
        nurse = await repo.get_nurse(nurse_id)
        if not nurse:
            raise HTTPException(status_code=404, detail="Nurse not found")
        return nurse
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get nurse {nurse_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve nurse")


@router.post(
    "/nurses",
    response_model=NurseResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def create_nurse(
    nurse_data: NurseCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Create a new nurse (Admin/Super Admin only)."""
    try:
        nurse = await repo.create_nurse(nurse_data.dict())
        logger.info(f"Nurse created by user {user['id']}: {nurse['id']}")
        return nurse
    except Exception as e:
        logger.error(f"Failed to create nurse: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create nurse")


@router.put(
    "/nurses/{nurse_id}",
    response_model=NurseResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def update_nurse(
    nurse_id: str,
    nurse_data: NurseUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Update a nurse (Admin/Super Admin only)."""
    try:
        nurse = await repo.update_nurse(nurse_id, nurse_data.dict(exclude_unset=True))
        if not nurse:
            raise HTTPException(status_code=404, detail="Nurse not found")
        logger.info(f"Nurse updated by user {user['id']}: {nurse_id}")
        return nurse
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update nurse {nurse_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update nurse")


@router.delete(
    "/nurses/{nurse_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def delete_nurse(
    nurse_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Delete a nurse (Admin/Super Admin only)."""
    try:
        success = await repo.delete_nurse(nurse_id)
        if not success:
            raise HTTPException(status_code=404, detail="Nurse not found")
        logger.info(f"Nurse deleted by user {user['id']}: {nurse_id}")
        return {"success": True, "message": "Nurse deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete nurse {nurse_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete nurse")


# â”پâ”پâ”پâ”پ ADMINISTRATORS â”پâ”پâ”پâ”پ


@router.get(
    "/administrators",
    response_model=List[AdministratorResponseDTO],
    dependencies=[Depends(require_permission(Permission.LIST_USERS))],
)
async def list_administrators(
    hospital_id: Optional[str] = Query(None, description="Filter by hospital ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: UserRepository = Depends(UserRepository),
):
    """List all administrators with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if hospital_id:
            filters["hospital_id"] = hospital_id
        if is_active is not None:
            filters["is_active"] = is_active

        admins = await repo.list_administrators(filters, limit, offset)
        return admins
    except Exception as e:
        logger.error(f"Failed to list administrators: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve administrators")


@router.get("/administrators/{admin_id}", response_model=AdministratorResponseDTO)
async def get_administrator(
    admin_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Get a specific administrator by ID."""
    try:
        _enforce_user_detail_access(user, admin_id)
        admin = await repo.get_administrator(admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Administrator not found")
        return admin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get administrator {admin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve administrator")


@router.post(
    "/administrators",
    response_model=AdministratorResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def create_administrator(
    admin_data: AdministratorCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create a new administrator (Admin/Super Admin only)."""
    try:
        # Use the specific role provided in data (admin or super_admin)
        role = admin_data.role or "admin"
        # model_dump with mode='json' ensures date objects become ISO strings
        result = await auth_service.admin_create_user(
            role, admin_data.model_dump(mode="json")
        )

        repo = UserRepository()
        admin = await repo.get_administrator(result["user_id"])

        if admin:
            logger.info(
                f"Administrator created by user {user['id']}: {admin.get('id')}"
            )
        else:
            logger.warning(
                f"Administrator profile not found after creation for user_id: {result['user_id']}"
            )
            admin = {
                "user_id": result["user_id"],
                "message": "Profile created but could not be retrieved immediately",
            }

        return admin
    except Exception as e:
        logger.error(f"Failed to create administrator: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create administrator")


@router.put(
    "/administrators/{admin_id}",
    response_model=AdministratorResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def update_administrator(
    admin_id: str,
    admin_data: AdministratorUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Update an administrator (Admin/Super Admin only)."""
    try:
        admin = await repo.update_administrator(
            admin_id, admin_data.dict(exclude_unset=True)
        )
        if not admin:
            raise HTTPException(status_code=404, detail="Administrator not found")
        logger.info(f"Administrator updated by user {user['id']}: {admin_id}")
        return admin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update administrator {admin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update administrator")


@router.delete(
    "/administrators/{admin_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def delete_administrator(
    admin_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Delete an administrator (Admin/Super Admin only)."""
    try:
        success = await repo.delete_administrator(admin_id)
        if not success:
            raise HTTPException(status_code=404, detail="Administrator not found")
        logger.info(f"Administrator deleted by user {user['id']}: {admin_id}")
        return {"success": True, "message": "Administrator deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete administrator {admin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete administrator")


# â”پâ”پâ”پâ”پ PATIENTS â”پâ”پâ”پâ”پ


@router.get(
    "/patients",
    response_model=List[PatientResponseDTO],
    dependencies=[Depends(require_permission(Permission.LIST_USERS))],
)
async def list_patients(
    hospital_id: Optional[str] = Query(None, description="Filter by hospital ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or MRN"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: UserRepository = Depends(UserRepository),
):
    """List all patients with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if hospital_id:
            filters["hospital_id"] = hospital_id
        if is_active is not None:
            filters["is_active"] = is_active
        if search:
            filters["search"] = search

        patients = await repo.list_patients(filters, limit, offset)
        return patients
    except Exception as e:
        logger.error(f"Failed to list patients: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patients")


@router.get("/patients/{patient_id}", response_model=PatientResponseDTO)
async def get_patient(
    patient_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Get a specific patient by ID."""
    try:
        _enforce_user_detail_access(user, patient_id)
        patient = await repo.get_patient(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient")


@router.post(
    "/patients",
    response_model=PatientResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_PATIENTS))],
)
async def create_patient(
    patient_data: PatientCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create a new patient (Doctor/Admin only)."""
    try:
        # model_dump with mode='json' ensures date objects become ISO strings
        result = await auth_service.admin_create_user(
            "patient", patient_data.model_dump(mode="json")
        )

        repo = UserRepository()
        patient = await repo.get_patient(result["user_id"])

        if patient:
            logger.info(f"Patient created by user {user['id']}: {patient.get('id')}")
        else:
            logger.warning(
                f"Patient profile not found after creation for user_id: {result['user_id']}"
            )
            patient = {
                "user_id": result["user_id"],
                "message": "Profile created but could not be retrieved immediately",
            }

        return patient
    except Exception as e:
        logger.error(f"Failed to create patient: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create patient")


@router.put(
    "/patients/{patient_id}",
    response_model=PatientResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_PATIENTS))],
)
async def update_patient(
    patient_id: str,
    patient_data: PatientUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Update a patient (Doctor/Admin only)."""
    try:
        patient = await repo.update_patient(
            patient_id, patient_data.dict(exclude_unset=True)
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        logger.info(f"Patient updated by user {user['id']}: {patient_id}")
        return patient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update patient")


@router.delete(
    "/patients/{patient_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_PATIENTS))],
)
async def delete_patient(
    patient_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Delete a patient (Doctor/Admin only)."""
    try:
        success = await repo.delete_patient(patient_id)
        if not success:
            raise HTTPException(status_code=404, detail="Patient not found")
        logger.info(f"Patient deleted by user {user['id']}: {patient_id}")
        return {"success": True, "message": "Patient deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete patient")


# â”پâ”پâ”پâ”پ USER PROFILE MANAGEMENT â”پâ”پâ”پâ”پ


@router.get("/profile", response_model=UserProfileResponseDTO)
async def get_my_profile(
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Get current user's profile."""
    try:
        profile = await repo.get_my_profile(user["id"], role=user.get("role"))
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        # Add user_role from middleware if missing in profile row
        if "user_role" not in profile:
            profile["user_role"] = user.get("role") or user.get("user_role")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")


@router.put("/profile", response_model=UserProfileResponseDTO)
async def update_my_profile(
    profile_data: UserProfileUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: UserRepository = Depends(UserRepository),
):
    """Update current user's profile."""
    try:
        profile = await repo.update_my_profile(
            user["id"],
            profile_data.model_dump(exclude_unset=True),
            role=user.get("role"),
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        logger.info(f"Profile updated by user {user['id']}")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


# â”پâ”پâ”پâ”پ AVATAR MANAGEMENT â”پâ”پâ”پâ”پ


@router.post(
    "/avatar", dependencies=[Depends(require_permission(Permission.UPLOAD_FILES))]
)
async def upload_avatar(
    file: UploadFile = File(...),
    user: dict[str, Any] = Depends(get_current_user),
    user_repo: UserRepository = Depends(UserRepository),
    storage_repo: StorageRepository = Depends(StorageRepository),
    clinical_repo: ClinicalRepository = Depends(ClinicalRepository),
):
    """Upload user avatar."""
    try:
        logger.info(
            f"Upload avatar attempt: filename={file.filename}, content_type={file.content_type}"
        )
        file_service = FileService(storage_repo, clinical_repo)
        content = await file.read()

        path = await file_service.upload_avatar(
            user["id"],
            file.filename or "avatar",
            content,
            file.content_type or "application/octet-stream",
        )

        # Get public URL
        # NOTE: This depends on storage_repo.admin_client being available.
        # But we refactored StorageRepository to use async client and removed .admin_client property!
        # This line will FAIL!
        # public_url = f"{storage_repo.admin_client.storage_url}/object/public/{storage_repo.bucket}/{path}"

        # We need a method in StorageRepository to get public URL.
        # But for now, let's look at how to construct it.
        # Supabase storage URL structure is constant.
        # Or I can add a method `get_public_url` to StorageRepository.

        # Adding get_public_url to StorageRepo would be cleaner.
        # But I can't edit StorageRepo in this tool call.
        # I'll rely on constructing it manually if I know the base URL.
        # OR, assuming get_public_url exists (I didn't add it).

        # Wait, I can probably infer the URL if I have the project URL.
        # _config.url in client.py.
        # But here I don't have access to it easily.

        # Let's fix this by calling a new method `get_public_url` on storage_repo,
        # AND I Must add that method to StorageRepository in next step.
        # Or I can use `storage_repo.get_signed_url` if public is not required?
        # Avatars are usually public.

        # Let's assume I'll add `get_public_url` to `StorageRepository`.
        public_url = storage_repo.get_public_url(path)

        # Update user profile with avatar URL
        # Create new repo instance? No, use injected `user_repo`

        profile = await user_repo.update_my_profile(
            user["id"], {"avatar_url": public_url}
        )

        logger.info(f"Avatar uploaded by user {user['id']}: {path}")
        return {"success": True, "avatar_url": public_url, "profile": profile}
    except Exception as e:
        logger.error(f"Failed to upload avatar for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")

