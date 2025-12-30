"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.patients import router as patients_router
from app.api.v1.cases import router as cases_router
from app.api.v1.files import router as files_router
from app.api.v1.ecg import router as ecg_router
from app.api.v1.mri import router as mri_router
from app.api.v1.llm import router as llm_router
from app.api.v1.reports import router as reports_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.geography import router as geography_router

router = APIRouter()

# Include all routers
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(patients_router, prefix="/patients", tags=["Patients"])
router.include_router(cases_router, prefix="/cases", tags=["Medical Cases"])
router.include_router(files_router, prefix="/files", tags=["Medical Files"])
router.include_router(ecg_router, prefix="/ecg", tags=["ECG Analysis"])
router.include_router(mri_router, prefix="/mri", tags=["MRI Segmentation"])
router.include_router(llm_router, prefix="/llm", tags=["Medical LLM"])
router.include_router(reports_router, prefix="/reports", tags=["Reports"])
router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
router.include_router(geography_router, prefix="/geography", tags=["Geography"])
