from __future__ import annotations

import pytest

from src.api.routes import dashboard_routes


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_admin_overview_returns_composite_payload(monkeypatch) -> None:
    async def fake_collect(*_args, **_kwargs):
        return {
            "system_health": {
                "response_time_avg": 120,
                "error_rate": 1.2,
                "database_status": "healthy",
                "cache_status": "healthy",
                "timestamp": "2026-03-10T10:00:00+00:00",
            },
            "user_activity": {"active_users_24h": 19},
            "business_metrics": {"total_cases": 54},
            "patients_count": 140,
            "doctors_count": 18,
            "recent_audit_logs": [
                {
                    "id": "audit-1",
                    "action": "USER_LOGIN",
                    "description": "Doctor sign in",
                    "created_at": "2026-03-10T09:50:00+00:00",
                    "details": {"endpoint": "/v1/auth/signin"},
                }
            ],
            "disease_rows": [
                {"diagnosis_icd10": "I48", "diagnosis": "Atrial fibrillation"},
                {"diagnosis_icd10": "I48", "diagnosis": "Atrial fibrillation"},
                {"diagnosis_icd10": "G93", "diagnosis": "Brain edema"},
            ],
            "recent_notifications": [],
        }

    monkeypatch.setattr(dashboard_routes, "collect_admin_overview_sources", fake_collect)

    response = await dashboard_routes.get_admin_overview(
        user={"id": "admin-1"},
        dashboard_repo=object(),
        notifications_repo=object(),
    )

    assert response["success"] is True
    assert response["data"]["stats"]["patients"]["value"] == 140
    assert response["data"]["charts"]["daily_appointments_trend"]["available"] is False
    assert response["data"]["capabilities"] == {
        "appointments": False,
        "billing": False,
        "messaging": True,
        "disease_distribution": True,
    }
    assert response["data"]["charts"]["disease_distribution"]["data"][0]["label"] == "I48"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_doctor_overview_returns_capability_aware_schedule(monkeypatch) -> None:
    async def fake_collect(*_args, **_kwargs):
        return {
            "appointments": [],
            "doctor_cases": [
                {
                    "id": "case-1",
                    "case_number": "CASE-1001",
                    "patient_id": "patient-1",
                    "status": "pending_review",
                    "priority": "high",
                    "created_at": "2026-03-10T08:00:00+00:00",
                    "updated_at": "2026-03-10T09:00:00+00:00",
                    "patients": {
                        "id": "patient-1",
                        "first_name": "Layla",
                        "last_name": "Nabil",
                        "mrn": "MRN-44",
                    },
                }
            ],
            "pending_ecg_results": [
                {
                    "id": "ecg-1",
                    "case_id": "case-1",
                    "patient_id": "patient-1",
                    "created_at": "2026-03-10T09:30:00+00:00",
                    "analysis_status": "pending_review",
                    "rhythm_classification": "Atrial flutter",
                    "patients": {
                        "first_name": "Layla",
                        "last_name": "Nabil",
                        "mrn": "MRN-44",
                    },
                    "medical_cases": {"case_number": "CASE-1001"},
                }
            ],
            "pending_mri_results": [],
            "notifications": [
                {
                    "id": "notification-1",
                    "title": "Unread message",
                    "message": "Patient uploaded new ECG result",
                    "priority": "high",
                    "created_at": "2026-03-10T09:35:00+00:00",
                    "is_read": False,
                }
            ],
            "unread_notifications": 3,
        }

    monkeypatch.setattr(dashboard_routes, "collect_doctor_overview_sources", fake_collect)

    response = await dashboard_routes.get_doctor_overview(
        user={"id": "auth-1", "profile_id": "doctor-1", "hospital_id": "hospital-1"},
        clinical_repo=object(),
        notifications_repo=object(),
    )

    assert response["success"] is True
    assert response["data"]["today_schedule"]["available"] is False
    assert response["data"]["quick_stats"]["total_patients"]["value"] == 1
    assert response["data"]["quick_stats"]["pending_reports"]["value"] == 1
    assert response["data"]["quick_stats"]["unread_messages"]["value"] == 3
    assert response["data"]["patient_queue"][0]["patient_name"] == "Layla Nabil"
    assert response["data"]["pending_results"][0]["type"] == "ECG"


@pytest.mark.unit
def test_build_admin_overview_payload_flags_missing_modules() -> None:
    payload = dashboard_routes.build_admin_overview_payload(
        {
            "system_health": {
                "response_time_avg": 0,
                "error_rate": 0,
                "database_status": "healthy",
                "cache_status": "healthy",
            },
            "user_activity": {"active_users_24h": 0},
            "business_metrics": {"total_cases": 0},
            "patients_count": 0,
            "doctors_count": 0,
            "recent_audit_logs": [],
            "disease_rows": [],
            "recent_notifications": [],
        }
    )

    assert payload["stats"]["appointments"]["available"] is False
    assert payload["stats"]["revenue"]["available"] is False
    assert payload["capabilities"]["billing"] is False
    assert payload["charts"]["disease_distribution"]["available"] is False


@pytest.mark.unit
def test_build_doctor_overview_payload_aggregates_unique_patients() -> None:
    payload = dashboard_routes.build_doctor_overview_payload(
        {"id": "auth-1", "profile_id": "doctor-1", "hospital_id": "hospital-1"},
        {
            "appointments": [],
            "doctor_cases": [
                {
                    "id": "case-1",
                    "case_number": "CASE-1",
                    "patient_id": "patient-1",
                    "status": "open",
                    "priority": "normal",
                    "created_at": "2026-03-10T08:00:00+00:00",
                    "updated_at": "2026-03-10T09:00:00+00:00",
                    "patients": {"id": "patient-1", "first_name": "Sara", "last_name": "Ali"},
                },
                {
                    "id": "case-2",
                    "case_number": "CASE-2",
                    "patient_id": "patient-1",
                    "status": "in_progress",
                    "priority": "high",
                    "created_at": "2026-03-10T10:00:00+00:00",
                    "updated_at": "2026-03-10T10:30:00+00:00",
                    "patients": {"id": "patient-1", "first_name": "Sara", "last_name": "Ali"},
                },
            ],
            "pending_ecg_results": [],
            "pending_mri_results": [],
            "notifications": [],
            "unread_notifications": 0,
        },
    )

    assert payload["quick_stats"]["total_patients"]["value"] == 1
    assert len(payload["patient_queue"]) == 2
    assert payload["capabilities"]["appointments"] is False
