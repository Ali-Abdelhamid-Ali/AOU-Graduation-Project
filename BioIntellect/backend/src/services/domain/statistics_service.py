"""Real-time Statistics Service - Provides live dashboard data and metrics."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.repositories.analytics_repository import AnalyticsRepository
from src.repositories.user_repository import UserRepository
from src.repositories.clinical_repository import ClinicalRepository
from src.observability.logger import get_logger

logger = get_logger("service.statistics")


class StatisticsService:
    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        user_repo: UserRepository,
        clinical_repo: ClinicalRepository,
    ):
        self.analytics_repo = analytics_repo
        self.user_repo = user_repo
        self.clinical_repo = clinical_repo
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.last_updated: Dict[str, datetime] = {}
        self.cache_ttl: int = 60  # 60 seconds cache TTL

    async def get_dashboard_statistics(
        self, user_id: str, user_role: str
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics based on user role."""
        try:
            # cache_key = f"dashboard_stats:{user_id}:{user_role}"

            # Check cache first
            # if cache_key in self.cache:
            #     cached_data = self.cache[cache_key]
            #     if datetime.now() - self.last_updated[cache_key] < timedelta(
            #         seconds=self.cache_ttl
            #     ):
            #         logger.debug(f"Returning cached statistics for {user_id}")
            #         return cached_data

            # Get statistics based on role
            if user_role == "super_admin":
                stats = await self._get_super_admin_statistics()
            elif user_role == "admin":
                hospital_id = await self.analytics_repo.get_user_hospital_id(user_id)
                stats = await self._get_admin_statistics(hospital_id)
            elif user_role == "doctor":
                stats = await self._get_doctor_statistics(user_id)
            elif user_role == "patient":
                stats = await self._get_patient_statistics(user_id)
            else:
                stats = await self._get_basic_statistics()

            # Cache the results
            # self.cache[cache_key] = stats
            # self.last_updated[cache_key] = datetime.now()

            return stats

        except Exception as e:
            logger.error(f"Failed to get dashboard statistics: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve dashboard statistics",
            }

    async def _get_super_admin_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics for super admins."""
        try:
            # Section 11: Parallel Query Execution
            import asyncio

            tasks = [
                self.analytics_repo.get_total_users_count(),
                self.analytics_repo.get_active_users_count(),
                self.analytics_repo.get_user_distribution(),
                self.clinical_repo.count_medical_cases(),
                self.clinical_repo.count_medical_files(),
                self.clinical_repo.get_cases_by_status(),
                self.clinical_repo.get_files_by_type(),
                self.analytics_repo.get_user_growth_trend(),
                self.clinical_repo.get_case_trend(),
                self.analytics_repo.get_user_recent_activity("system"),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            t_users = results[0] if not isinstance(results[0], Exception) else 0
            a_users = results[1] if not isinstance(results[1], Exception) else 0
            u_dist = results[2] if not isinstance(results[2], Exception) else {}
            t_cases = results[3] if not isinstance(results[3], Exception) else 0
            t_files = results[4] if not isinstance(results[4], Exception) else 0
            c_status = results[5] if not isinstance(results[5], Exception) else {}
            f_types = results[6] if not isinstance(results[6], Exception) else {}
            u_growth = results[7] if not isinstance(results[7], Exception) else []
            c_trend = results[8] if not isinstance(results[8], Exception) else []
            r_activity = results[9] if not isinstance(results[9], Exception) else []

            return {
                "success": True,
                "data": {
                    "system": {
                        "total_users": t_users,
                        "active_users": a_users,
                        "user_distribution": u_dist,
                        "recent_activity": r_activity,
                    },
                    "clinical": {
                        "total_cases": t_cases,
                        "total_files": t_files,
                        "cases_by_status": c_status,
                        "files_by_type": f_types,
                    },
                    "trends": {
                        "user_growth": u_growth,
                        "case_trend": c_trend,
                    },
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get super admin statistics: {str(e)}")
            raise

    async def _get_admin_statistics(
        self, hospital_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get hospital-level statistics for admins."""
        try:
            if not hospital_id:
                return {
                    "success": False,
                    "error": "Hospital ID not provided",
                    "message": "Cannot retrieve admin statistics without hospital context",
                }

            # Section 11: Parallel Query Execution for Dashboard Load
            import asyncio

            tasks = [
                self.analytics_repo.get_hospital_users_count(hospital_id),
                self.analytics_repo.get_hospital_active_users_count(hospital_id),
                self.clinical_repo.count_hospital_cases(hospital_id),
                self.clinical_repo.count_hospital_files(hospital_id),
                self.analytics_repo.get_hospital_user_distribution(hospital_id),
                self.clinical_repo.get_hospital_cases_by_status(hospital_id),
                self.clinical_repo.get_hospital_files_by_type(hospital_id),
                self.analytics_repo.get_hospital_user_growth(hospital_id),
                self.clinical_repo.get_hospital_case_trend(hospital_id),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results (handle exceptions if any)
            # Order matches tasks list above
            h_users = results[0] if not isinstance(results[0], Exception) else 0
            h_active = results[1] if not isinstance(results[1], Exception) else 0
            h_cases = results[2] if not isinstance(results[2], Exception) else 0
            h_files = results[3] if not isinstance(results[3], Exception) else 0
            h_dist = results[4] if not isinstance(results[4], Exception) else {}
            h_status = results[5] if not isinstance(results[5], Exception) else {}
            h_types = results[6] if not isinstance(results[6], Exception) else {}
            h_growth = results[7] if not isinstance(results[7], Exception) else []
            h_trend = results[8] if not isinstance(results[8], Exception) else []

            return {
                "success": True,
                "data": {
                    "hospital": {
                        "id": hospital_id,
                        "total_users": h_users,
                        "active_users": h_active,
                        "user_distribution": h_dist,
                    },
                    "clinical": {
                        "total_cases": h_cases,
                        "total_files": h_files,
                        "cases_by_status": h_status,
                        "files_by_type": h_types,
                    },
                    "trends": {
                        "user_growth": h_growth,
                        "case_trend": h_trend,
                    },
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get admin statistics: {str(e)}")
            raise

    async def _get_doctor_statistics(self, doctor_id: str) -> Dict[str, Any]:
        """Get doctor-specific statistics."""
        try:
            # Section 11: Parallel Query Execution
            import asyncio

            tasks = [
                self.clinical_repo.get_doctor_patients(doctor_id),
                self.clinical_repo.get_doctor_cases(doctor_id),
                self.clinical_repo.get_doctor_appointments(doctor_id),
                self.analytics_repo.get_user_recent_activity(doctor_id),
                self.clinical_repo.get_doctor_cases_by_status(doctor_id),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            d_patients = results[0] if not isinstance(results[0], Exception) else []
            d_cases = results[1] if not isinstance(results[1], Exception) else []
            d_appts = results[2] if not isinstance(results[2], Exception) else []
            recent_act = results[3] if not isinstance(results[3], Exception) else []
            cases_status = results[4] if not isinstance(results[4], Exception) else {}

            return {
                "success": True,
                "data": {
                    "patients": {
                        "total": len(d_patients),
                        "recent": d_patients[:5],
                    },
                    "cases": {
                        "total": len(d_cases),
                        "by_status": cases_status,
                        "recent": d_cases[:5],
                    },
                    "appointments": {
                        "total": len(d_appts),
                        "upcoming": [
                            app for app in d_appts if app.get("status") == "scheduled"
                        ][:5],
                        "completed": [
                            app for app in d_appts if app.get("status") == "completed"
                        ][:5],
                    },
                    "activity": recent_act[:10],
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get doctor statistics: {str(e)}")
            raise

    async def _get_patient_statistics(self, patient_id: str) -> Dict[str, Any]:
        """Get patient-specific statistics."""
        try:
            # Section 11: Parallel Query Execution
            import asyncio

            tasks = [
                self.clinical_repo.get_patient_cases(patient_id),
                self.clinical_repo.get_patient_appointments(patient_id),
                self.clinical_repo.get_patient_files(patient_id),
                self.analytics_repo.get_user_recent_activity(patient_id),
                self.clinical_repo.get_patient_cases_by_status(patient_id),
                self.clinical_repo.get_patient_files_by_type(patient_id),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            p_cases = results[0] if not isinstance(results[0], Exception) else []
            p_appts = results[1] if not isinstance(results[1], Exception) else []
            p_files = results[2] if not isinstance(results[2], Exception) else []
            recent_act = results[3] if not isinstance(results[3], Exception) else []
            cases_status = results[4] if not isinstance(results[4], Exception) else {}
            files_type = results[5] if not isinstance(results[5], Exception) else {}

            return {
                "success": True,
                "data": {
                    "medical_cases": {
                        "total": len(p_cases),
                        "by_status": cases_status,
                        "recent": p_cases[:5],
                    },
                    "appointments": {
                        "total": len(p_appts),
                        "upcoming": [
                            app for app in p_appts if app.get("status") == "scheduled"
                        ],
                        "completed": [
                            app for app in p_appts if app.get("status") == "completed"
                        ],
                    },
                    "files": {
                        "total": len(p_files),
                        "by_type": files_type,
                        "recent": p_files[:5],
                    },
                    "activity": recent_act[:10],
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get patient statistics: {str(e)}")
            raise

    async def _get_basic_statistics(
        self, user_id: Optional[str] = None, user_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get basic statistics for users with limited access."""
        try:
            # Use provided context or default
            user_id = user_id or "system"
            user_role = user_role or "unknown"

            # Get basic system health
            system_health = await self.analytics_repo.get_system_health()

            # Get user's recent activity
            recent_activity = await self.analytics_repo.get_user_recent_activity(
                user_id
            )

            return {
                "success": True,
                "data": {
                    "system": {"health": system_health, "status": "healthy"},
                    "user": {
                        "role": user_role,
                        "recent_activity": recent_activity[
                            :5
                        ],  # Top 5 recent activities
                    },
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get basic statistics: {str(e)}")
            raise

    async def get_real_time_updates(
        self, user_id: str, user_role: str
    ) -> Dict[str, Any]:
        """Get real-time updates for dashboard (simulated for now)."""
        try:
            # In a real implementation, this would use WebSocket or SSE
            # For now, we'll return cached data with a timestamp

            # Get basic statistics
            stats = await self.get_dashboard_statistics(user_id, user_role)

            return {
                "success": True,
                "data": stats.get("data", {}),
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Real-time statistics update",
            }

        except Exception as e:
            logger.error(f"Failed to get real-time updates: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get real-time updates",
            }

    async def start_statistics_updater(self):
        """Start background task to update statistics periodically."""
        try:
            logger.info("Starting statistics updater background task")

            while True:
                # Update statistics every 30 seconds
                await asyncio.sleep(30)

                try:
                    # Clear old cache
                    for cache_key in list(self.cache.keys()):
                        if datetime.now() - self.last_updated.get(
                            cache_key, datetime.now()
                        ) > timedelta(seconds=self.cache_ttl * 2):
                            del self.cache[cache_key]
                            del self.last_updated[cache_key]

                    logger.debug("Statistics cache updated")

                except Exception as e:
                    logger.error(f"Error in statistics updater: {str(e)}")

        except asyncio.CancelledError:
            logger.info("Statistics updater background task cancelled")
        except Exception as e:
            logger.error(f"Statistics updater failed: {str(e)}")


# Global statistics service instance
statistics_service = None


async def get_statistics_service() -> StatisticsService:
    """Get the global statistics service instance."""
    global statistics_service

    if statistics_service is None:
        from src.repositories.analytics_repository import AnalyticsRepository
        from src.repositories.user_repository import UserRepository
        from src.repositories.clinical_repository import ClinicalRepository

        analytics_repo = AnalyticsRepository()
        user_repo = UserRepository()
        clinical_repo = ClinicalRepository()

        statistics_service = StatisticsService(analytics_repo, user_repo, clinical_repo)

        # Start background updater
        asyncio.create_task(statistics_service.start_statistics_updater())

    return statistics_service

