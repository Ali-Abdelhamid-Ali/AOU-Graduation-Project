from typing import Dict, Any, List
from src.repositories.analytics_repository import AnalyticsRepository
from src.observability.audit import log_audit, AuditAction


class AnalyticsService:
    """Service for clinical analytics and dashboard aggregation."""

    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo

    async def get_dashboard_summary(self, user_id: str, role: str) -> Dict[str, Any]:
        """Get summarized dashboard data based on role."""

        try:
            # For patients, we get their specific stats.
            # For doctors, we might get aggregated patient stats (future phase).

            if role == "patient":
                raw_stats = await self.repo.get_patient_stats(user_id)

                # Post-process for clinical status
                last_status = "No records"
                ecg = raw_stats.get("latest_ecg")
                mri = raw_stats.get("latest_mri")

                if ecg:
                    last_status = (
                        "Normal"
                        if ecg.get("confidence_score", 0) > 0.8
                        else "Review Needed"
                    )

                if mri:
                    if mri.get("tumor_detected"):
                        last_status = "Action Required"
                    elif not ecg:
                        last_status = "Stable"

                # Calculate a mock health score
                health_score = 100
                if mri and mri.get("tumor_detected"):
                    health_score -= 40
                if ecg and ecg.get("confidence_score", 0) < 0.7:
                    health_score -= 10

                # Log audit for dashboard access
                log_audit(
                    AuditAction.ACCESS_RESOURCE,
                    user_id=user_id,
                    details={"resource": "PATIENT_DASHBOARD"},
                )

                return {
                    "total_reports": raw_stats["total_reports"],
                    "next_appointment": raw_stats["next_appointment"].get(
                        "appointment_date"
                    )
                    if raw_stats["next_appointment"]
                    else "None",
                    "last_analysis": last_status,
                    "health_score": health_score,
                    "trends": await self.repo.get_health_trends(user_id),
                }

            elif role == "super_admin":
                # Super admin dashboard - get system-wide stats
                return await self.get_super_admin_dashboard_stats()

            elif role == "admin":
                # Admin dashboard - get hospital-specific stats
                return await self.get_admin_dashboard_stats(user_id)

            elif role == "doctor":
                # Doctor dashboard - get patient stats they're responsible for
                return await self.get_doctor_dashboard_stats(user_id)

            elif role == "nurse":
                # Nurse dashboard - get assigned patient stats
                return await self.get_nurse_dashboard_stats(user_id)

            return {"message": "Professional dashboard stats under development."}

        except Exception as e:
            # Log the error and return a safe response
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting dashboard summary for user {user_id}: {str(e)}"
            )

            return {
                "total_reports": 0,
                "next_appointment": "None",
                "last_analysis": "Error loading",
                "health_score": 0,
                "trends": [],
                "error": "Unable to load dashboard data",
            }

    async def get_patient_appointments(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch all appointments for the current user."""
        return await self.repo.list_appointments(user_id)

    async def update_appointment(self, user_id: str, appointment_id: str, data: dict):
        """Update appointment and log audit."""
        try:
            updated = await self.repo.update_appointment(appointment_id, data)
            log_audit(
                AuditAction.UPDATE_RESOURCE,
                user_id=user_id,
                details={"resource": f"APPOINTMENT_{appointment_id}"},
            )
            return updated
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
            raise

    async def get_super_admin_dashboard_stats(self) -> Dict[str, Any]:
        """Get super admin dashboard statistics."""
        try:
            # Get system-wide statistics
            total_users = await self.repo.get_total_users_count()
            active_users = await self.repo.get_active_users_count()
            system_health = await self.repo.get_system_health()
            audit_logs_count = await self.repo.get_audit_logs_count()

            return {
                "total_users": total_users,
                "active_users": active_users,
                "system_health": system_health,
                "audit_logs_count": audit_logs_count,
                "system_activity": await self.repo.get_system_activity_summary(),
                "user_activity": await self.repo.get_user_activity_summary(),
            }
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting super admin dashboard stats: {str(e)}")
            return {
                "total_users": 0,
                "active_users": 0,
                "system_health": "error",
                "audit_logs_count": 0,
                "system_activity": {},
                "user_activity": {},
                "error": "Unable to load system statistics",
            }

    async def get_admin_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Get admin dashboard statistics for their hospital."""
        try:
            # Get hospital-specific statistics
            hospital_id = await self.repo.get_user_hospital_id(user_id)
            total_users = await self.repo.get_hospital_users_count(hospital_id)
            active_users = await self.repo.get_hospital_active_users_count(hospital_id)
            system_health = await self.repo.get_hospital_system_health(hospital_id)

            return {
                "total_users": total_users,
                "active_users": active_users,
                "system_health": system_health,
                "hospital_id": hospital_id,
                "hospital_activity": await self.repo.get_hospital_activity_summary(
                    hospital_id
                ),
            }
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting admin dashboard stats for user {user_id}: {str(e)}"
            )
            return {
                "total_users": 0,
                "active_users": 0,
                "system_health": "error",
                "hospital_id": None,
                "hospital_activity": {},
                "error": "Unable to load hospital statistics",
            }

    async def get_doctor_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Get doctor dashboard statistics for their patients."""
        try:
            # Get doctor-specific statistics
            assigned_patients = await self.repo.get_doctor_assigned_patients_count(
                user_id
            )
            pending_cases = await self.repo.get_doctor_pending_cases_count(user_id)
            completed_cases = await self.repo.get_doctor_completed_cases_count(user_id)

            return {
                "assigned_patients": assigned_patients,
                "pending_cases": pending_cases,
                "completed_cases": completed_cases,
                "workload_summary": await self.repo.get_doctor_workload_summary(
                    user_id
                ),
            }
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting doctor dashboard stats for user {user_id}: {str(e)}"
            )
            return {
                "assigned_patients": 0,
                "pending_cases": 0,
                "completed_cases": 0,
                "workload_summary": {},
                "error": "Unable to load doctor statistics",
            }

    async def get_nurse_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Get nurse dashboard statistics for their assigned patients."""
        try:
            # Get nurse-specific statistics
            assigned_patients = await self.repo.get_nurse_assigned_patients_count(
                user_id
            )
            pending_tasks = await self.repo.get_nurse_pending_tasks_count(user_id)
            completed_tasks = await self.repo.get_nurse_completed_tasks_count(user_id)

            return {
                "assigned_patients": assigned_patients,
                "pending_tasks": pending_tasks,
                "completed_tasks": completed_tasks,
                "task_summary": await self.repo.get_nurse_task_summary(user_id),
            }
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting nurse dashboard stats for user {user_id}: {str(e)}"
            )
            return {
                "assigned_patients": 0,
                "pending_tasks": 0,
                "completed_tasks": 0,
                "task_summary": {},
                "error": "Unable to load nurse statistics",
            }

