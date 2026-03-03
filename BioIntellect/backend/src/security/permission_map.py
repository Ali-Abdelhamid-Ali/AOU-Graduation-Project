"""Permission Matrix - Centralized Source of Truth for Authorization."""

from enum import Enum
from typing import Set, Dict


class Permission(str, Enum):
    # User Permissions
    LIST_USERS = "users:list"
    VIEW_USER = "users:view"
    UPDATE_PROFILE = "profile:update"

    # Clinical Permissions
    CREATE_CASE = "clinical:create_case"
    VIEW_PATIENT = "clinical:view_patient"
    MANAGE_PATIENTS = "clinical:manage_patients"
    ANALYZE_ECG = "clinical:analyze_ecg"
    ANALYZE_MRI = "clinical:analyze_mri"
    CHAT_LLM = "clinical:chat_llm"

    # Administrative Permissions
    VIEW_DASHBOARD = "admin:view_dashboard"
    VIEW_TRENDS = "admin:view_trends"
    VIEW_AUDIT_LOGS = "admin:view_logs"
    MANAGE_HOSPITALS = "admin:manage_hospitals"
    APPROVE_ACCOUNTS = "admin:approve_accounts"
    MANAGE_GEOGRAPHY = "admin:manage_geography"
    MANAGE_USERS = "admin:manage_users"
    UPLOAD_FILES = "files:upload"

    # Super Admin Specific Permissions
    MANAGE_SUPER_ADMINS = "super_admin:manage"  # Manage other super admins
    SYSTEM_CONFIG = "super_admin:system_config"  # System-wide configuration

    # LLM System Permissions
    MANAGE_SYSTEM = "llm:manage_system"
    VIEW_NOTIFICATIONS = "llm:view_notifications"
    MANAGE_NOTIFICATIONS = "llm:manage_notifications"

    # System Management Permissions
    VIEW_SYSTEM_SETTINGS = "system:view_settings"
    MANAGE_AUDIT_LOGS = "system:manage_audit_logs"

    # New permissions for enhanced requirements
    CREATE_APPOINTMENTS = "appointments:create"
    MANAGE_APPOINTMENTS = "appointments:manage"
    VIEW_STATISTICS = "stats:view"
    MANAGE_STATISTICS = "stats:manage"

    # New system monitoring & security permissions
    VIEW_SYSTEM_METRICS = "system:view_metrics"
    MANAGE_SYSTEM_SECURITY = "system:manage_security"


# Role permissions mapping
ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    "patient": {
        Permission.VIEW_USER,
        Permission.UPDATE_PROFILE,
        Permission.CHAT_LLM,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.VIEW_NOTIFICATIONS,
        Permission.CREATE_APPOINTMENTS,
        Permission.VIEW_STATISTICS,
        Permission.UPLOAD_FILES,
    },
    "doctor": {
        Permission.LIST_USERS,  # Required for Directory
        Permission.VIEW_USER,
        Permission.UPDATE_PROFILE,
        Permission.CREATE_CASE,
        Permission.VIEW_PATIENT,
        Permission.MANAGE_PATIENTS,
        Permission.ANALYZE_ECG,
        Permission.ANALYZE_MRI,
        Permission.CHAT_LLM,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.VIEW_NOTIFICATIONS,
        Permission.MANAGE_NOTIFICATIONS,
        Permission.CREATE_APPOINTMENTS,
        Permission.MANAGE_APPOINTMENTS,
        Permission.VIEW_STATISTICS,
        Permission.UPLOAD_FILES,
    },
    "nurse": {
        Permission.VIEW_USER,
        Permission.UPDATE_PROFILE,
        Permission.VIEW_PATIENT,
        Permission.MANAGE_PATIENTS,
        Permission.CHAT_LLM,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.VIEW_NOTIFICATIONS,
        Permission.CREATE_APPOINTMENTS,
        Permission.MANAGE_APPOINTMENTS,
        Permission.VIEW_STATISTICS,
        Permission.UPLOAD_FILES,
    },
    "admin": {
        Permission.LIST_USERS,
        Permission.VIEW_USER,
        Permission.UPDATE_PROFILE,
        Permission.MANAGE_PATIENTS,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_HOSPITALS,
        Permission.APPROVE_ACCOUNTS,
        Permission.MANAGE_GEOGRAPHY,
        Permission.MANAGE_USERS,
        Permission.UPLOAD_FILES,
        Permission.VIEW_NOTIFICATIONS,
        Permission.MANAGE_NOTIFICATIONS,
        Permission.MANAGE_SYSTEM,
        Permission.CREATE_APPOINTMENTS,
        Permission.MANAGE_APPOINTMENTS,
        Permission.VIEW_STATISTICS,
        Permission.MANAGE_STATISTICS,
    },
    "super_admin": {
        Permission.LIST_USERS,
        Permission.VIEW_USER,
        Permission.UPDATE_PROFILE,
        Permission.MANAGE_PATIENTS,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_HOSPITALS,
        Permission.APPROVE_ACCOUNTS,
        Permission.CREATE_CASE,
        Permission.VIEW_PATIENT,
        Permission.ANALYZE_ECG,
        Permission.ANALYZE_MRI,
        Permission.CHAT_LLM,
        Permission.VIEW_NOTIFICATIONS,
        Permission.MANAGE_NOTIFICATIONS,
        Permission.MANAGE_SYSTEM,
        Permission.MANAGE_SUPER_ADMINS,
        Permission.SYSTEM_CONFIG,
        Permission.CREATE_APPOINTMENTS,
        Permission.MANAGE_APPOINTMENTS,
        Permission.VIEW_STATISTICS,
        Permission.MANAGE_STATISTICS,
        Permission.MANAGE_AUDIT_LOGS,
        Permission.VIEW_SYSTEM_METRICS,
        Permission.MANAGE_SYSTEM_SECURITY,
        Permission.UPLOAD_FILES,
        Permission.MANAGE_USERS,
    },
}


def get_role_permissions(role: str) -> Set[Permission]:
    """Returns the set of permissions for a given role name."""
    normalized_role = (role or "").strip().lower()
    return ROLE_PERMISSIONS.get(normalized_role, set())
