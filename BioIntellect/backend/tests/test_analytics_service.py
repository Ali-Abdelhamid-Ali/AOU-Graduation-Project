from __future__ import annotations

import pytest

from src.services.domain.analytics_service import AnalyticsService


class FakeAnalyticsRepo:
    def __init__(self) -> None:
        self.list_args = None
        self.create_payload = None
        self.case_record = None
        self.updated_payload = None

    async def list_appointments_for_user(self, **kwargs):
        self.list_args = kwargs
        return [{"id": "appointment-1"}]

    async def get_patient_context(self, patient_id: str):
        if patient_id != "patient-1":
            return None
        return {
            "id": patient_id,
            "hospital_id": "hospital-1",
            "primary_doctor_id": "doctor-9",
        }

    async def create_appointment(self, payload: dict):
        self.create_payload = payload
        return {"id": "appointment-2", **payload}

    async def get_appointment_case(self, appointment_id: str):
        _ = appointment_id
        return self.case_record

    async def update_appointment(self, appointment_id: str, data: dict):
        self.updated_payload = {"id": appointment_id, **data}
        return self.updated_payload


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_appointments_uses_profile_scope_for_patient() -> None:
    repo = FakeAnalyticsRepo()
    service = AnalyticsService(repo)

    user = {
        "id": "auth-1",
        "profile_id": "patient-1",
        "role": "patient",
        "hospital_id": "hospital-1",
    }

    payload = await service.list_appointments(user)

    assert payload == [{"id": "appointment-1"}]
    assert repo.list_args == {
        "role": "patient",
        "actor_id": "patient-1",
        "hospital_id": "hospital-1",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_appointment_for_patient_uses_owned_profile_and_defaults() -> None:
    repo = FakeAnalyticsRepo()
    service = AnalyticsService(repo)

    user = {
        "id": "auth-1",
        "profile_id": "patient-1",
        "role": "patient",
        "hospital_id": "hospital-1",
    }

    created = await service.create_appointment(
        user,
        {
            "appointment_date": "2026-03-20",
            "appointment_time": "09:30",
            "appointment_type": "MRI Follow-up",
            "reason": "Review recent MRI findings",
            "department": "Neurology",
        },
    )

    assert created["id"] == "appointment-2"
    assert repo.create_payload["patient_id"] == "patient-1"
    assert repo.create_payload["doctor_id"] == "doctor-9"
    assert repo.create_payload["hospital_id"] == "hospital-1"
    assert repo.create_payload["created_by_doctor_id"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_appointment_denies_patient_cross_access() -> None:
    repo = FakeAnalyticsRepo()
    repo.case_record = {
        "id": "case-1",
        "patient_id": "patient-2",
        "assigned_doctor_id": "doctor-1",
        "hospital_id": "hospital-1",
    }
    service = AnalyticsService(repo)

    user = {
        "id": "auth-1",
        "profile_id": "patient-1",
        "role": "patient",
        "hospital_id": "hospital-1",
    }

    with pytest.raises(PermissionError):
        await service.update_appointment(
            user,
            "case-1",
            {"status": "Cancelled"},
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_appointment_allows_assigned_doctor() -> None:
    repo = FakeAnalyticsRepo()
    repo.case_record = {
        "id": "case-1",
        "patient_id": "patient-1",
        "assigned_doctor_id": "doctor-4",
        "created_by_doctor_id": None,
        "hospital_id": "hospital-1",
    }
    service = AnalyticsService(repo)

    user = {
        "id": "auth-doctor",
        "profile_id": "doctor-4",
        "role": "doctor",
        "hospital_id": "hospital-1",
    }

    updated = await service.update_appointment(
        user,
        "case-1",
        {"status": "Completed"},
    )

    assert updated["id"] == "case-1"
    assert repo.updated_payload == {"id": "case-1", "status": "Completed"}
