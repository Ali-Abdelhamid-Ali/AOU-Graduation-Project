from typing import Any, Dict, List

from src.observability.audit import AuditAction, log_audit
from src.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    """Service for clinical analytics and dashboard aggregation."""

    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo

    @staticmethod
    def _resolve_actor_id(user: dict[str, Any]) -> str:
        return str(user.get("profile_id") or user.get("id") or "")

    @staticmethod
    def _can_manage_appointment(
        user: dict[str, Any], case_record: dict[str, Any]
    ) -> bool:
        role = str(user.get("role") or "").lower()
        actor_id = str(user.get("profile_id") or user.get("id") or "")

        if role == "super_admin":
            return True
        if role == "patient":
            return str(case_record.get("patient_id") or "") == actor_id
        if role == "doctor":
            return str(case_record.get("assigned_doctor_id") or "") == actor_id or str(
                case_record.get("created_by_doctor_id") or ""
            ) == actor_id
        if role in {"admin", "nurse"}:
            return bool(user.get("hospital_id")) and str(
                case_record.get("hospital_id") or ""
            ) == str(user.get("hospital_id"))
        return False

    async def get_dashboard_summary(self, user: dict[str, Any]) -> Dict[str, Any]:
        """Get summarized dashboard data based on role."""
        user_id = str(user.get("id") or "")
        role = str(user.get("role") or "")
        actor_id = self._resolve_actor_id(user)

        try:
            if role == "patient":
                raw_stats = await self.repo.get_patient_stats(actor_id)

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

                health_score = 100
                if mri and mri.get("tumor_detected"):
                    health_score -= 40
                if ecg and ecg.get("confidence_score", 0) < 0.7:
                    health_score -= 10

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
                    "trends": await self.repo.get_health_trends(actor_id),
                }

            if role == "super_admin":
                return await self.get_super_admin_dashboard_stats()

            if role == "admin":
                return await self.get_admin_dashboard_stats(
                    actor_id, hospital_id=user.get("hospital_id")
                )

            if role == "doctor":
                return await self.get_doctor_dashboard_stats(actor_id)

            if role == "nurse":
                return await self.get_nurse_dashboard_stats(actor_id)

            return {"message": "Professional dashboard stats under development."}

        except Exception as e:
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

    async def list_appointments(self, user: dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch appointments scoped to the current authenticated actor."""
        return await self.repo.list_appointments_for_user(
            role=str(user.get("role") or ""),
            actor_id=self._resolve_actor_id(user),
            hospital_id=user.get("hospital_id"),
        )

    async def create_appointment(self, user: dict[str, Any], data: dict):
        """Create appointment and log audit."""
        role = str(user.get("role") or "").lower()
        actor_id = self._resolve_actor_id(user)
        patient_id = actor_id if role == "patient" else data.get("patient_id")

        if not patient_id:
            raise ValueError("Patient ID is required to create an appointment.")

        patient_context = await self.repo.get_patient_context(str(patient_id))
        if not patient_context:
            raise LookupError("Patient profile not found.")

        if role == "patient" and str(data.get("patient_id") or actor_id) != actor_id:
            raise PermissionError("Patients can only create appointments for themselves.")

        assigned_doctor_id = data.get("doctor_id")
        if role == "doctor" and not assigned_doctor_id:
            assigned_doctor_id = actor_id
        if role == "patient" and not assigned_doctor_id:
            assigned_doctor_id = patient_context.get("primary_doctor_id")

        hospital_id = (
            data.get("hospital_id")
            or patient_context.get("hospital_id")
            or user.get("hospital_id")
        )
        if not hospital_id:
            raise ValueError("Hospital context is required to create an appointment.")

        payload = {
            **data,
            "patient_id": str(patient_id),
            "doctor_id": assigned_doctor_id,
            "hospital_id": hospital_id,
            "created_by_doctor_id": actor_id if role == "doctor" else None,
        }

        created = await self.repo.create_appointment(payload)
        if not created:
            raise ValueError("Failed to create appointment.")

        log_audit(
            AuditAction.CREATE_RESOURCE,
            user_id=str(user.get("id") or ""),
            details={"resource": f"APPOINTMENT_{created['id']}"},
        )
        return created

    async def update_appointment(
        self, user: dict[str, Any], appointment_id: str, data: dict
    ):
        """Update appointment and log audit."""
        try:
            case_record = await self.repo.get_appointment_case(appointment_id)
            if not case_record:
                raise LookupError("Appointment not found.")
            if not self._can_manage_appointment(user, case_record):
                raise PermissionError("You are not allowed to update this appointment.")

            updated = await self.repo.update_appointment(appointment_id, data)
            if not updated:
                raise ValueError("Failed to update appointment.")

            log_audit(
                AuditAction.UPDATE_RESOURCE,
                user_id=str(user.get("id") or ""),
                details={"resource": f"APPOINTMENT_{appointment_id}"},
            )
            return updated
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
            raise

    async def get_health_trends(
        self, user: dict[str, Any], days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get trend data for patient dashboards from persisted results only."""
        if str(user.get("role") or "").lower() != "patient":
            return []
        return await self.repo.get_health_trends(self._resolve_actor_id(user), days)

    async def get_super_admin_dashboard_stats(self) -> Dict[str, Any]:
        """Get super admin dashboard statistics."""
        try:
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

    async def get_admin_dashboard_stats(
        self, user_id: str, hospital_id: str | None = None
    ) -> Dict[str, Any]:
        """Get admin dashboard statistics for their hospital."""
        try:
            hospital_id = hospital_id or await self.repo.get_user_hospital_id(user_id)
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
