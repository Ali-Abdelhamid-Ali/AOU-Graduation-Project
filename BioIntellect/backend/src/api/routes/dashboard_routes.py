"""Dashboard API Routes - Admin and Super Admin dashboard endpoints."""

from collections import Counter
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Optional
from src.db.supabase.client import SupabaseProvider
from src.repositories.dashboard_repository import DashboardRepository
from src.repositories.analytics_repository import AnalyticsRepository
from src.repositories.clinical_repository import ClinicalRepository
from src.repositories.notifications_repository import NotificationsRepository
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger
import asyncio

logger = get_logger("routes.dashboard")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _extract_log_status_code(log: dict[str, Any]) -> Optional[int]:
    payload = log.get("changes") or log.get("details") or {}
    if not isinstance(payload, dict):
        return None
    try:
        status_code = payload.get("status_code")
        return int(status_code) if status_code is not None else None
    except (TypeError, ValueError):
        return None


def _matches_log_severity(log: dict[str, Any], severity: str) -> bool:
    normalized = severity.lower()
    status_code = _extract_log_status_code(log)

    if normalized == "critical":
        return bool(log.get("is_flagged")) or (
            status_code is not None and status_code >= 500
        )
    if normalized == "error":
        return status_code is not None and 400 <= status_code < 500
    if normalized == "warning":
        return bool(log.get("flag_reason")) or (
            status_code is not None and 300 <= status_code < 400
        )
    return True


def _safe_name(record: Any, fallback: str = "Unknown") -> str:
    if isinstance(record, list):
        record = record[0] if record else {}
    if not isinstance(record, dict):
        return fallback

    full_name = " ".join(
        part.strip()
        for part in (
            str(record.get("first_name") or "").strip(),
            str(record.get("last_name") or "").strip(),
        )
        if part.strip()
    )
    return full_name or str(record.get("full_name") or record.get("mrn") or fallback)


def _safe_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _relative_time(value: Any) -> str:
    timestamp = _safe_datetime(value)
    if not timestamp:
        return "Unknown time"

    now = datetime.now(timezone.utc)
    delta = now - timestamp.astimezone(timezone.utc)
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "Just now"
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr ago"
    days = hours // 24
    return f"{days} day ago" if days == 1 else f"{days} days ago"


def _severity_tone(severity: str) -> str:
    normalized = severity.lower()
    if normalized in {"critical", "error"}:
        return "critical"
    if normalized in {"warning", "degraded"}:
        return "warning"
    if normalized in {"success", "healthy"}:
        return "success"
    return "info"


def _build_metric_card(
    label: str,
    value: Any,
    *,
    helper: str,
    available: bool = True,
    tone: str = "info",
) -> dict[str, Any]:
    return {
        "label": label,
        "value": value,
        "helper": helper,
        "available": available,
        "tone": tone,
    }


def _build_unavailable_chart(message: str) -> dict[str, Any]:
    return {"available": False, "data": [], "message": message}


def _summarize_health_status(system_health: dict[str, Any]) -> str:
    if str(system_health.get("database_status") or "").lower() not in {
        "healthy",
        "connected",
    }:
        return "warning"
    if float(system_health.get("error_rate") or 0) >= 5:
        return "warning"
    if float(system_health.get("response_time_avg") or 0) >= 1000:
        return "warning"
    return "healthy"


def _build_recent_activity(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    activity: list[dict[str, Any]] = []
    for log in logs[:8]:
        payload = log.get("changes") or log.get("details") or {}
        severity = (
            "critical"
            if _matches_log_severity(log, "critical")
            else "warning"
            if _matches_log_severity(log, "warning")
            else "info"
        )
        activity.append(
            {
                "id": str(log.get("id") or len(activity)),
                "title": str(log.get("description") or log.get("action") or "System activity"),
                "message": str(
                    payload.get("endpoint")
                    or payload.get("outcome")
                    or log.get("resource_type")
                    or "Recorded in audit trail"
                ),
                "timestamp": log.get("created_at") or log.get("timestamp"),
                "time_ago": _relative_time(log.get("created_at") or log.get("timestamp")),
                "severity": severity,
            }
        )
    return activity


def _build_disease_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        label = (
            str(row.get("diagnosis_icd10") or "").strip()
            or str(row.get("diagnosis") or "").strip()
        )
        if label:
            counter[label] += 1
    return [{"label": label, "value": count} for label, count in counter.most_common(6)]


def _normalize_appointment_status(value: Any) -> str:
    text = str(value or "Scheduled").replace("_", " ").strip()
    return " ".join(fragment.capitalize() for fragment in text.split()) or "Scheduled"


def _build_appointment_trend(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        date_value = str(row.get("follow_up_date") or "").strip()[:10]
        if date_value:
            counter[date_value] += 1
    return [{"label": label, "value": count} for label, count in sorted(counter.items())[-10:]]


def _summarize_appointment_scope(rows: list[dict[str, Any]]) -> dict[str, Any]:
    today = datetime.now(timezone.utc).date().isoformat()
    active = 0
    upcoming = 0

    for row in rows:
        metadata = row.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        status = _normalize_appointment_status(metadata.get("appointment_status"))
        if status != "Cancelled":
            active += 1
        if str(row.get("follow_up_date") or "")[:10] >= today and status != "Cancelled":
            upcoming += 1

    return {
        "total": len(rows),
        "active": active,
        "upcoming": upcoming,
        "trend": _build_appointment_trend(rows),
    }


def _build_admin_alerts(
    system_health: dict[str, Any],
    logs: list[dict[str, Any]],
    notifications: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    error_rate = float(system_health.get("error_rate") or 0)
    response_time = float(system_health.get("response_time_avg") or 0)
    database_status = str(system_health.get("database_status") or "unknown")

    if database_status.lower() not in {"healthy", "connected"}:
        alerts.append(
            {
                "id": "db-status",
                "title": "Database status requires attention",
                "message": f"Current database status is {database_status}.",
                "severity": "critical",
                "timestamp": system_health.get("timestamp"),
            }
        )

    if error_rate >= 5:
        alerts.append(
            {
                "id": "error-rate",
                "title": "Elevated API error rate",
                "message": f"Error rate reached {error_rate:.1f}% in the recent monitoring window.",
                "severity": "warning",
                "timestamp": system_health.get("timestamp"),
            }
        )

    if response_time >= 1000:
        alerts.append(
            {
                "id": "latency",
                "title": "Latency threshold exceeded",
                "message": f"Average response time is {response_time:.0f} ms.",
                "severity": "warning",
                "timestamp": system_health.get("timestamp"),
            }
        )

    for log in logs[:3]:
        payload = log.get("changes") or log.get("details") or {}
        severity = "critical" if _matches_log_severity(log, "critical") else "warning"
        alerts.append(
            {
                "id": str(log.get("id") or f"log-{len(alerts)}"),
                "title": str(log.get("description") or log.get("action") or "Audit event"),
                "message": str(
                    payload.get("endpoint")
                    or log.get("flag_reason")
                    or "Recent flagged audit event detected."
                ),
                "severity": severity,
                "timestamp": log.get("created_at") or log.get("timestamp"),
            }
        )

    for notification in notifications:
        if str(notification.get("priority", "")).lower() in {"high", "urgent"}:
            alerts.append(
                {
                    "id": str(notification.get("id") or f"notification-{len(alerts)}"),
                    "title": str(notification.get("title") or "Priority notification"),
                    "message": str(notification.get("message") or ""),
                    "severity": "warning",
                    "timestamp": notification.get("created_at"),
                }
            )

    return alerts[:6]


def build_admin_overview_payload(sources: dict[str, Any]) -> dict[str, Any]:
    system_health = sources.get("system_health") or {}
    user_activity = sources.get("user_activity") or {}
    business_metrics = sources.get("business_metrics") or {}
    recent_notifications = sources.get("recent_notifications") or []
    recent_audit_logs = sources.get("recent_audit_logs") or []
    disease_distribution = _build_disease_distribution(sources.get("disease_rows") or [])
    appointment_scope = _summarize_appointment_scope(sources.get("appointment_rows") or [])

    capabilities = {
        "appointments": True,
        "billing": False,
        "messaging": True,
        "disease_distribution": bool(disease_distribution),
    }

    return {
        "stats": {
            "patients": _build_metric_card(
                "Patients",
                int(sources.get("patients_count") or 0),
                helper=f"{int(user_activity.get('active_users_24h') or 0)} active users in the last 24 hours",
                tone="info",
            ),
            "doctors": _build_metric_card(
                "Doctors",
                int(sources.get("doctors_count") or 0),
                helper=f"{int(business_metrics.get('total_cases') or 0)} medical cases tracked",
                tone="success",
            ),
            "appointments": _build_metric_card(
                "Appointments",
                appointment_scope["active"],
                helper=(
                    f"{appointment_scope['upcoming']} upcoming follow-up appointments in the current scope."
                    if appointment_scope["upcoming"]
                    else "No upcoming follow-up appointments are scheduled yet."
                ),
                tone="success" if appointment_scope["active"] else "info",
            ),
            "revenue": _build_metric_card(
                "Revenue",
                None,
                helper="Billing and payments module not configured in the current schema.",
                available=False,
                tone="warning",
            ),
        },
        "charts": {
            "daily_appointments_trend": {
                "available": True,
                "data": appointment_scope["trend"],
                "message": (
                    "Daily follow-up load derived from medical_cases.follow_up_date."
                    if appointment_scope["trend"]
                    else "No follow-up appointments have been scheduled in this scope yet."
                ),
            },
            "revenue_by_month": _build_unavailable_chart(
                "Billing and payments module not configured."
            ),
            "disease_distribution": {
                "available": bool(disease_distribution),
                "data": disease_distribution,
                "message": (
                    "Distribution derived from medical_cases diagnosis fields."
                    if disease_distribution
                    else "No ICD-10 or diagnosis data available yet."
                ),
            },
        },
        "recent_activity": _build_recent_activity(recent_audit_logs),
        "system_health": {
            "status": _summarize_health_status(system_health),
            "summary": "Operational telemetry pulled from audit logs and runtime health checks.",
            "metrics": [
                {
                    "label": "Average response time",
                    "value": f"{float(system_health.get('response_time_avg') or 0):.0f} ms",
                    "tone": _severity_tone(
                        "warning"
                        if float(system_health.get("response_time_avg") or 0) >= 1000
                        else "healthy"
                    ),
                },
                {
                    "label": "API error rate",
                    "value": f"{float(system_health.get('error_rate') or 0):.1f}%",
                    "tone": _severity_tone(
                        "warning"
                        if float(system_health.get("error_rate") or 0) >= 5
                        else "healthy"
                    ),
                },
                {
                    "label": "Database",
                    "value": str(system_health.get("database_status") or "unknown").title(),
                    "tone": _severity_tone(
                        "healthy"
                        if str(system_health.get("database_status") or "").lower()
                        in {"healthy", "connected"}
                        else "warning"
                    ),
                },
                {
                    "label": "Cache",
                    "value": str(system_health.get("cache_status") or "unknown").title(),
                    "tone": _severity_tone(
                        "healthy"
                        if str(system_health.get("cache_status") or "").lower()
                        in {"healthy", "active"}
                        else "warning"
                    ),
                },
            ],
        },
        "alerts": _build_admin_alerts(system_health, recent_audit_logs, recent_notifications),
        "capabilities": capabilities,
    }


def build_doctor_overview_payload(user: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    appointments = sources.get("appointments") or []
    doctor_cases = sources.get("doctor_cases") or []
    notifications = sources.get("notifications") or []
    pending_ecg_results = sources.get("pending_ecg_results") or []
    pending_mri_results = sources.get("pending_mri_results") or []

    unique_patients: dict[str, dict[str, Any]] = {}
    queue_items: list[dict[str, Any]] = []

    for case in doctor_cases:
        patient = case.get("patients") or {}
        if isinstance(patient, list):
            patient = patient[0] if patient else {}

        patient_id = str(case.get("patient_id") or patient.get("id") or "")
        if patient_id and patient_id not in unique_patients:
            unique_patients[patient_id] = {
                "id": patient_id,
                "name": _safe_name(patient, fallback="Patient"),
                "mrn": patient.get("mrn"),
                "last_visit": case.get("updated_at") or case.get("created_at"),
                "last_visit_label": _relative_time(case.get("updated_at") or case.get("created_at")),
            }

        if str(case.get("status") or "").lower() in {"open", "in_progress", "pending_review"}:
            queue_items.append(
                {
                    "id": str(case.get("id")),
                    "case_number": case.get("case_number"),
                    "patient_name": _safe_name(patient, fallback="Patient"),
                    "mrn": patient.get("mrn"),
                    "status": str(case.get("status") or "open"),
                    "priority": str(case.get("priority") or "normal"),
                    "wait_time_label": _relative_time(case.get("created_at")),
                }
            )

    pending_results: list[dict[str, Any]] = []
    for ecg in pending_ecg_results:
        patient = ecg.get("patients") or {}
        if isinstance(patient, list):
            patient = patient[0] if patient else {}
        medical_case = ecg.get("medical_cases") or {}
        if isinstance(medical_case, list):
            medical_case = medical_case[0] if medical_case else {}
        pending_results.append(
            {
                "id": str(ecg.get("id")),
                "type": "ECG",
                "patient_name": _safe_name(patient, fallback="Patient"),
                "mrn": patient.get("mrn"),
                "case_number": medical_case.get("case_number"),
                "status": ecg.get("analysis_status") or "pending_review",
                "summary": ecg.get("rhythm_classification") or "Awaiting physician review",
                "created_at": ecg.get("created_at"),
                "time_ago": _relative_time(ecg.get("created_at")),
            }
        )

    for mri in pending_mri_results:
        patient = mri.get("patients") or {}
        if isinstance(patient, list):
            patient = patient[0] if patient else {}
        medical_case = mri.get("medical_cases") or {}
        if isinstance(medical_case, list):
            medical_case = medical_case[0] if medical_case else {}
        abnormalities = mri.get("detected_abnormalities") or []
        summary = abnormalities[0] if isinstance(abnormalities, list) and abnormalities else "Awaiting radiology review"
        pending_results.append(
            {
                "id": str(mri.get("id")),
                "type": "MRI",
                "patient_name": _safe_name(patient, fallback="Patient"),
                "mrn": patient.get("mrn"),
                "case_number": medical_case.get("case_number"),
                "status": mri.get("analysis_status") or "pending_review",
                "summary": summary,
                "created_at": mri.get("created_at"),
                "time_ago": _relative_time(mri.get("created_at")),
            }
        )

    pending_results.sort(
        key=lambda item: _safe_datetime(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    today_iso = datetime.now(timezone.utc).date().isoformat()
    schedule_entries = []
    for appointment in appointments:
        patient = appointment.get("patients") or {}
        if isinstance(patient, list):
            patient = patient[0] if patient else {}
        schedule_entries.append(
            {
                "id": str(appointment.get("id") or ""),
                "date": appointment.get("appointment_date"),
                "time": appointment.get("appointment_time") or "Time TBD",
                "patient_name": _safe_name(patient, fallback="Patient"),
                "title": f"{appointment.get('appointment_type') or 'Follow-up'} appointment",
                "reason": appointment.get("reason") or "Follow-up visit",
                "status": _normalize_appointment_status(appointment.get("status")),
            }
        )

    today_schedule = [
        entry for entry in schedule_entries if str(entry.get("date") or "") == today_iso
    ]
    schedule_message = (
        "Today's appointments loaded from the follow-up schedule."
        if today_schedule
        else "No appointments scheduled for today. Showing the next follow-up visits."
        if schedule_entries
        else "No follow-up appointments are scheduled yet."
    )
    displayed_schedule = today_schedule or schedule_entries[:8]

    capabilities = {
        "appointments": True,
        "billing": False,
        "messaging": True,
        "disease_distribution": False,
    }

    return {
        "today_schedule": {
            "available": True,
            "message": schedule_message,
            "data": displayed_schedule,
        },
        "patient_queue": queue_items[:8],
        "quick_stats": {
            "total_patients": _build_metric_card(
                "Total Patients",
                len(unique_patients),
                helper="Unique patients associated with your assigned cases.",
                tone="info",
            ),
            "pending_reports": _build_metric_card(
                "Pending Reports",
                len(pending_results),
                helper="Unread ECG and MRI analyses waiting for review.",
                tone="warning" if pending_results else "success",
            ),
            "unread_messages": _build_metric_card(
                "Unread Messages",
                int(sources.get("unread_notifications") or 0),
                helper="Unread notifications and care-team alerts.",
                tone="warning" if int(sources.get("unread_notifications") or 0) else "info",
            ),
        },
        "recent_patients": list(unique_patients.values())[:6],
        "pending_results": pending_results[:8],
        "notifications": [
            {
                "id": str(notification.get("id")),
                "title": notification.get("title") or "Notification",
                "message": notification.get("message") or "",
                "priority": notification.get("priority") or "normal",
                "created_at": notification.get("created_at"),
                "time_ago": _relative_time(notification.get("created_at")),
                "is_read": bool(notification.get("is_read")),
            }
            for notification in notifications[:8]
        ],
        "capabilities": capabilities,
        "doctor_context": {
            "doctor_id": user.get("profile_id") or user.get("id"),
            "hospital_id": user.get("hospital_id"),
        },
    }


async def collect_admin_overview_sources(
    user: dict[str, Any],
    dashboard_repo: DashboardRepository,
    notifications_repo: NotificationsRepository,
) -> dict[str, Any]:
    client = await SupabaseProvider.get_admin()
    time_col = await dashboard_repo._resolve_audit_time_column(client)
    appointment_query = (
        client.table("medical_cases")
        .select("id, hospital_id, follow_up_date, status, metadata")
        .not_.is_("follow_up_date", "null")
        .order("follow_up_date", desc=False)
        .limit(500)
    )
    if user.get("role") != "super_admin" and user.get("hospital_id"):
        appointment_query = appointment_query.eq("hospital_id", user["hospital_id"])

    (
        system_health,
        user_activity,
        business_metrics,
        patients_result,
        doctors_result,
        audit_result,
        disease_result,
        recent_notifications,
        appointment_result,
    ) = await asyncio.gather(
        dashboard_repo.get_system_health_metrics(),
        dashboard_repo.get_user_activity_metrics(),
        dashboard_repo.get_business_metrics(),
        client.table("patients").select("id", count="exact").execute(),
        client.table("doctors").select("id", count="exact").execute(),
        client.table("audit_logs").select("*").order(time_col, desc=True).limit(20).execute(),
        client.table("medical_cases").select("diagnosis, diagnosis_icd10, created_at").order("created_at", desc=True).limit(500).execute(),
        notifications_repo.get_user_notifications(user["id"], limit=10),
        appointment_query.execute(),
    )

    return {
        "system_health": system_health,
        "user_activity": user_activity,
        "business_metrics": business_metrics,
        "patients_count": patients_result.count or 0,
        "doctors_count": doctors_result.count or 0,
        "recent_audit_logs": audit_result.data or [],
        "disease_rows": disease_result.data or [],
        "recent_notifications": recent_notifications,
        "appointment_rows": appointment_result.data or [],
    }


async def collect_doctor_overview_sources(
    user: dict[str, Any],
    clinical_repo: ClinicalRepository,
    notifications_repo: NotificationsRepository,
) -> dict[str, Any]:
    doctor_id = user.get("profile_id") or user.get("id")
    client = await SupabaseProvider.get_admin()

    doctor_cases_result = await (
        client.table("medical_cases")
        .select("id, case_number, patient_id, status, priority, created_at, updated_at, patients(id, first_name, last_name, mrn)")
        .eq("assigned_doctor_id", doctor_id)
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )
    doctor_cases = doctor_cases_result.data or []
    case_ids = [row.get("id") for row in doctor_cases if row.get("id")]

    if case_ids:
        pending_ecg_result = await (
            client.table("ecg_results")
            .select("id, case_id, patient_id, created_at, analysis_status, rhythm_classification, risk_score, is_reviewed, patients(first_name, last_name, mrn), medical_cases(case_number)")
            .in_("case_id", case_ids)
            .eq("is_reviewed", False)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        pending_mri_result = await (
            client.table("mri_segmentation_results")
            .select("id, case_id, patient_id, created_at, analysis_status, detected_abnormalities, is_reviewed, patients(first_name, last_name, mrn), medical_cases(case_number)")
            .in_("case_id", case_ids)
            .eq("is_reviewed", False)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        pending_ecg = pending_ecg_result.data or []
        pending_mri = pending_mri_result.data or []
    else:
        pending_ecg = []
        pending_mri = []

    appointments, notifications, unread_notifications = await asyncio.gather(
        clinical_repo.get_doctor_appointments(doctor_id),
        notifications_repo.get_user_notifications(user["id"], limit=10),
        notifications_repo.get_unread_count(user["id"]),
    )

    return {
        "appointments": appointments,
        "doctor_cases": doctor_cases,
        "pending_ecg_results": pending_ecg,
        "pending_mri_results": pending_mri,
        "notifications": notifications,
        "unread_notifications": unread_notifications,
    }


# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
# ADMIN DASHBOARD ENDPOINTS (Operational)
# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ


@router.get(
    "/admin/overview",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_overview(
    user: dict[str, Any] = Depends(get_current_user),
    dashboard_repo: DashboardRepository = Depends(DashboardRepository),
    notifications_repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Return a composite admin overview payload for the production dashboard."""
    try:
        sources = await collect_admin_overview_sources(
            user, dashboard_repo, notifications_repo
        )
        return {
            "success": True,
            "data": build_admin_overview_payload(sources),
            "message": "Admin overview retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get admin overview for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin overview")


@router.get(
    "/doctor/overview",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_doctor_overview(
    user: dict[str, Any] = Depends(get_current_user),
    clinical_repo: ClinicalRepository = Depends(ClinicalRepository),
    notifications_repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Return a composite doctor overview payload for the production dashboard."""
    try:
        sources = await collect_doctor_overview_sources(
            user, clinical_repo, notifications_repo
        )
        return {
            "success": True,
            "data": build_doctor_overview_payload(user, sources),
            "message": "Doctor overview retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get doctor overview for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve doctor overview"
        )


@router.get(
    "/admin/system-health",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_system_health(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get system health metrics for admin dashboard.

    Returns:
        - response_time_avg: Average API response time
        - error_rate: Percentage of errors
        - uptime_24h, uptime_7d: System uptime
        - database_status: DB health status
    """
    try:
        metrics = await repo.get_system_health_metrics()

        return {
            "success": True,
            "data": metrics,
            "message": "System health metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get system health for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system health metrics"
        )


@router.get(
    "/admin/user-activity",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_user_activity(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get user activity metrics for admin dashboard.

    Returns:
        - active_users_now, active_users_24h: Active user counts
        - recent_logins: Last 50 login events
        - failed_login_attempts: Recent failed logins
    """
    try:
        metrics = await repo.get_user_activity_metrics()

        return {
            "success": True,
            "data": metrics,
            "message": "User activity metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get user activity for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve user activity metrics"
        )


@router.get(
    "/admin/business-metrics",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_business_metrics(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get business/clinical metrics for admin dashboard.

    Returns:
        - total_cases: Medical cases count
        - ecg_analysis_count, mri_analysis_count: Analysis counts
        - api_usage_stats: API usage statistics
    """
    try:
        metrics = await repo.get_business_metrics()

        return {
            "success": True,
            "data": metrics,
            "message": "Business metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get business metrics for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve business metrics"
        )


@router.get(
    "/admin/logs-filtered",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_admin_filtered_logs(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, le=100, description="Number of logs to return"),
    user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get filtered error logs for admin dashboard.

    Query Parameters:
        - severity: Filter by log severity (error, warning, critical)
        - limit: Maximum number of logs to return
    """
    try:
        from src.repositories.audit_repository import AuditRepository

        audit_repo = AuditRepository()

        # Build filters
        filters = {}
        if severity:
            filters["severity"] = severity

        # Get audit logs (filtered)
        logs = await audit_repo.list_audit_logs(filters, limit=limit, offset=0)

        return {
            "success": True,
            "data": logs,
            "count": len(logs),
            "message": "Filtered logs retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get filtered logs for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve filtered logs")


@router.get(
    "/admin/permissions",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_permissions(
    user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get current user's permissions and role information.

    Returns:
        - role: Current user role
        - permissions: List of allowed permissions
        - restrictions: List of restricted actions
    """
    try:
        # Extract user role and permissions from token
        role = user.get("role", "unknown")
        permissions = user.get("permissions", [])

        # Define common restrictions based on role
        restrictions = []
        if role != "super_admin":
            restrictions.extend(
                [
                    "Cannot modify system configuration",
                    "Cannot access super admin dashboard",
                    "Cannot manage other admins",
                ]
            )

        if role not in ["admin", "super_admin"]:
            restrictions.extend(["Cannot manage users", "Cannot view audit logs"])

        return {
            "success": True,
            "data": {
                "role": role,
                "permissions": permissions,
                "restrictions": restrictions,
                "user_id": user.get("id"),
            },
            "message": "Permissions retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get permissions for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve permissions")


# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
# SUPER ADMIN DASHBOARD ENDPOINTS (Strategic)
# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ


@router.get(
    "/super-admin/global-overview",
    dependencies=[Depends(require_permission(Permission.VIEW_STATISTICS))],
)
async def get_super_admin_global_overview(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get global system overview for super admin.

    Returns comprehensive system-wide metrics including:
    - Total admins count
    - System health across all services
    - Database statistics
    - Global user metrics
    """
    try:
        # Fetch multiple metrics in parallel
        results = await asyncio.gather(
            repo.get_system_health_metrics(),
            repo.get_user_activity_metrics(),
            repo.get_business_metrics(),
            return_exceptions=True,
        )

        system_health: dict | Exception = results[0]  # type: ignore
        user_activity: dict | Exception = results[1]  # type: ignore
        business_metrics: dict | Exception = results[2]  # type: ignore

        # Get admin count from analytics (Safely)
        analytics_repo = AnalyticsRepository()

        try:
            active_users = await analytics_repo.get_active_users_count()
        except Exception:
            active_users = 0

        overview = {
            "system_health": system_health
            if not isinstance(system_health, Exception)
            else {},
            "user_metrics": {
                "total_users": user_activity.get("total_users", 0)
                if not isinstance(user_activity, Exception)
                else 0,
                "active_users": active_users,
                "active_now": user_activity.get("active_users_now", 0)
                if not isinstance(user_activity, Exception)
                else 0,
                "active_24h": user_activity.get("active_users_24h", 0)
                if not isinstance(user_activity, Exception)
                else 0,
            },
            "business_metrics": business_metrics
            if not isinstance(business_metrics, Exception)
            else {},
            "services_status": {
                "api": "healthy",
                "database": system_health.get("database_status", "unknown")
                if not isinstance(system_health, Exception)
                else "unknown",
                "cache": system_health.get("cache_status", "unknown")
                if not isinstance(system_health, Exception)
                else "unknown",
            },
        }

        logger.info(f"[DEBUG] Overview object constructed: {overview}")
        logger.info(f"[DEBUG] Services status: {overview.get('services_status')}")

        return {
            "success": True,
            "data": overview,
            "message": "Global overview retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get global overview for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve global overview"
        )


@router.get(
    "/super-admin/security-center",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_super_admin_security_center(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get security metrics and threat detection data.

    Returns:
        - failed_login_trends: Login failure patterns
        - suspicious_ips: IPs with multiple failed attempts
        - security_alerts: Recent security events
    """
    try:
        security_metrics = await repo.get_security_metrics()

        # Get additional login failure stats
        analytics_repo = AnalyticsRepository()
        login_stats = await analytics_repo.get_login_failure_stats()

        # Combine data
        security_data = {**security_metrics, "detailed_login_stats": login_stats}

        return {
            "success": True,
            "data": security_data,
            "message": "Security metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get security center for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve security metrics"
        )


@router.get(
    "/super-admin/admin-audit",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_super_admin_audit_trail(
    limit: int = Query(50, le=100, description="Number of audit records"),
    admin_id: Optional[str] = Query(None, description="Filter by admin ID"),
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get admin activity audit trail.

    Returns detailed audit log of admin actions including:
    - Who performed the action
    - What action was performed
    - When and from where
    - Before/after state changes
    """
    try:
        audit_trail = await repo.get_admin_audit_trail(limit=limit, admin_id=admin_id)

        return {
            "success": True,
            "data": audit_trail,
            "count": audit_trail.get("total_actions", 0),
            "message": "Admin audit trail retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get audit trail for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve admin audit trail"
        )


@router.get(
    "/super-admin/system-config",
    dependencies=[Depends(require_permission(Permission.SYSTEM_CONFIG))],
)
async def get_super_admin_system_config(
    user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get system configuration settings (read-only view).

    Returns:
        - Feature toggles
        - Global limits
        - Rate limiting rules
        - Environment info (sanitized)
    """
    try:
        from src.repositories.system_repository import SystemRepository

        system_repo = SystemRepository()

        # Get global settings
        settings = await system_repo.get_global_settings()

        # Get active models
        active_models = await system_repo.get_active_models()

        config_data = {
            "global_settings": settings,
            "active_models": active_models,
        }

        return {
            "success": True,
            "data": config_data,
            "message": "System configuration retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get system config for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system configuration"
        )


@router.get(
    "/super-admin/analytics-trends",
    dependencies=[Depends(require_permission(Permission.VIEW_STATISTICS))],
)
async def get_super_admin_analytics_trends(
    timeframe: str = Query("week", description="week or month"),
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get long-term strategic analytics and trends.

    Query Parameters:
        - timeframe: 'week' or 'month'

    Returns:
        - user_growth_trend: User registration trends
        - error_patterns: Common error patterns
        - performance_trends: System performance over time
    """
    try:
        analytics = await repo.get_strategic_analytics(timeframe=timeframe)

        # Get additional error trends
        analytics_repo = AnalyticsRepository()
        hours = 168 if timeframe == "week" else 720  # 7 days or 30 days
        error_trends = await analytics_repo.get_error_trends(hours=hours)

        trends_data = {**analytics, "error_trends": error_trends}

        return {
            "success": True,
            "data": trends_data,
            "timeframe": timeframe,
            "message": "Analytics trends retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get analytics trends for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve analytics trends"
        )


@router.post(
    "/super-admin/config/update",
    dependencies=[Depends(require_permission(Permission.SYSTEM_CONFIG))],
)
async def update_super_admin_config(
    config_data: dict,
    user: dict[str, Any] = Depends(get_current_user),
):
    """
    Update system configuration (Super Admin only).

    Request Body:
        - setting_key: Configuration key to update
        - setting_value: New value
    """
    try:
        # TODO: Implement actual config update via SystemRepository
        # from src.repositories.system_repository import SystemRepository
        # system_repo = SystemRepository()

        # Log this action for audit
        logger.info(
            f"Super admin {user['id']} updating config: {config_data.get('setting_key')}"
        )

        # Update setting (this is a simplified version)
        # In production, you'd want more validation and specific handling

        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_by": user["id"],
        }
    except Exception as e:
        logger.error(f"Failed to update config for super admin {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to update system configuration"
        )

