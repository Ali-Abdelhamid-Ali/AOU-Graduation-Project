"""Logging Service - Business logic for audit logging."""

from typing import Optional, Dict, Any
from datetime import datetime

from src.repositories.logging_repository import LoggingRepository
from src.observability.logger import get_logger

logger = get_logger("services.logging")


class LoggingService:
    """Service layer for audit logging operations."""

    def __init__(self):
        self.repository = LoggingRepository()

    async def log_user_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a user action for audit purposes."""
        try:
            # Validate required fields
            if not user_id or not action or not resource_type:
                raise ValueError("user_id, action, and resource_type are required")

            # Normalize action name
            action = action.upper().replace(" ", "_")

            result = await self.repository.create_audit_log(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if result["success"]:
                logger.info(f"User action logged: {action} by user {user_id}")
            else:
                logger.error(f"Failed to log user action: {action} by user {user_id}")

            return result

        except Exception as e:
            logger.error(f"Error logging user action: {str(e)}")
            return {"success": False, "message": f"Error logging user action: {str(e)}"}

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get audit logs with filtering options."""
        try:
            # Validate date format if provided
            if start_date:
                try:
                    datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                except ValueError:
                    raise ValueError(
                        "Invalid start_date format. Use ISO format (e.g., 2023-01-01T00:00:00)"
                    )

            if end_date:
                try:
                    datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                except ValueError:
                    raise ValueError(
                        "Invalid end_date format. Use ISO format (e.g., 2023-01-01T00:00:00)"
                    )

            result = await self.repository.get_audit_logs(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset,
            )

            if result["success"]:
                logger.info(f"Retrieved {result.get('count', 0)} audit logs")
            else:
                logger.error("Failed to retrieve audit logs")

            return result

        except Exception as e:
            logger.error(f"Error retrieving audit logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving audit logs: {str(e)}",
            }

    async def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """Get activity summary for a specific user."""
        try:
            if not user_id:
                raise ValueError("user_id is required")

            result = await self.repository.get_user_activity_summary(user_id)

            if result["success"]:
                logger.info(f"Retrieved activity summary for user {user_id}")
            else:
                logger.error(f"Failed to retrieve activity summary for user {user_id}")

            return result

        except Exception as e:
            logger.error(f"Error retrieving user activity summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving user activity summary: {str(e)}",
            }

    async def get_system_activity_summary(self) -> Dict[str, Any]:
        """Get system-wide activity summary."""
        try:
            result = await self.repository.get_system_activity_summary()

            if result["success"]:
                logger.info("Retrieved system activity summary")
            else:
                logger.error("Failed to retrieve system activity summary")

            return result

        except Exception as e:
            logger.error(f"Error retrieving system activity summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving system activity summary: {str(e)}",
            }

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Clean up audit logs older than specified days."""
        try:
            if days_to_keep < 1:
                raise ValueError("days_to_keep must be greater than 0")

            result = await self.repository.cleanup_old_logs(days_to_keep)

            if result["success"]:
                logger.info(
                    f"Cleaned up {result.get('deleted_count', 0)} old audit logs"
                )
            else:
                logger.error("Failed to clean up old audit logs")

            return result

        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error cleaning up old audit logs: {str(e)}",
            }

    # Convenience methods for common logging scenarios
    async def log_user_login(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log user login action."""
        return await self.log_user_action(
            user_id=user_id,
            action="USER_LOGIN",
            resource_type="AUTH",
            details={"login_method": "web"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_user_logout(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log user logout action."""
        return await self.log_user_action(
            user_id=user_id,
            action="USER_LOGOUT",
            resource_type="AUTH",
            details={"logout_method": "web"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_patient_creation(
        self, user_id: str, patient_id: str, details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log patient creation action."""
        return await self.log_user_action(
            user_id=user_id,
            action="PATIENT_CREATE",
            resource_type="PATIENT",
            resource_id=patient_id,
            details=details,
        )

    async def log_doctor_creation(
        self, user_id: str, doctor_id: str, details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log doctor creation action."""
        return await self.log_user_action(
            user_id=user_id,
            action="DOCTOR_CREATE",
            resource_type="DOCTOR",
            resource_id=doctor_id,
            details=details,
        )

    async def log_admin_creation(
        self, user_id: str, admin_id: str, details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log admin creation action."""
        return await self.log_user_action(
            user_id=user_id,
            action="ADMIN_CREATE",
            resource_type="ADMIN",
            resource_id=admin_id,
            details=details,
        )

    async def log_medical_analysis(
        self,
        user_id: str,
        analysis_type: str,
        patient_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Log medical analysis action."""
        return await self.log_user_action(
            user_id=user_id,
            action=f"{analysis_type.upper()}_ANALYSIS",
            resource_type="CLINICAL",
            resource_id=patient_id,
            details=details,
        )

    async def log_report_creation(
        self,
        user_id: str,
        report_id: str,
        patient_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Log report creation action."""
        return await self.log_user_action(
            user_id=user_id,
            action="REPORT_CREATE",
            resource_type="REPORT",
            resource_id=report_id,
            details=details,
        )

    async def log_report_approval(
        self,
        user_id: str,
        report_id: str,
        patient_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Log report approval action."""
        return await self.log_user_action(
            user_id=user_id,
            action="REPORT_APPROVE",
            resource_type="REPORT",
            resource_id=report_id,
            details=details,
        )

