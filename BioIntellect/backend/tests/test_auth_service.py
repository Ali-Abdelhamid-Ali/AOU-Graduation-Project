from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.services.domain.auth_service import AuthService
from src.validators.auth_dto import SignUpDTO


class _FakeAuthRepository:
    def __init__(self) -> None:
        self.created_profile_payload = None
        self.linked_doctor_specialty = None

    async def create_auth_user(self, email: str, password: str, metadata: dict):
        return "auth-user-1"

    async def create_profile(self, table: str, profile_data: dict):
        self.created_profile_payload = (table, dict(profile_data))
        return SimpleNamespace(data=[{"id": "doctor-profile-1"}])

    async def link_doctor_specialty(self, doctor_id: str, specialty_code: str):
        self.linked_doctor_specialty = (doctor_id, specialty_code)
        return SimpleNamespace(data=[{"id": "doctor-specialty-1"}])

    async def get_profile_by_user_id(self, table: str, user_id: str):
        return {"id": "doctor-profile-1", "user_id": user_id}

    async def delete_auth_user(self, user_id: str):
        return None


@pytest.mark.unit
async def test_admin_create_user_links_specialty_with_profile_id() -> None:
    repo = _FakeAuthRepository()
    service = AuthService(repo)

    result = await service.admin_create_user(
        "doctor",
        {
            "email": "doctor@example.com",
            "password": "ValidPass1!",
            "first_name": "Salma",
            "last_name": "Hassan",
            "hospital_id": "1d00d003-3f6e-4878-b3a8-e1fdefe70e94",
            "license_number": "DOC-1001",
            "employee_id": "EMP-9001",
            "specialty": "CARD",
        },
    )

    assert result["success"] is True
    assert repo.created_profile_payload is not None
    assert repo.created_profile_payload[0] == "doctors"
    assert repo.linked_doctor_specialty == ("doctor-profile-1", "CARD")


@pytest.mark.unit
async def test_public_signup_rejects_staff_roles_before_auth_creation() -> None:
    repo = _FakeAuthRepository()
    service = AuthService(repo)

    with pytest.raises(
        ValueError,
        match="Public signup currently supports patient accounts only",
    ):
        await service.sign_up(
            SignUpDTO(
                email="doctor@example.com",
                password="ValidPass1!",
                first_name="Salma",
                last_name="Hassan",
                role="doctor",
                hospital_id="1d00d003-3f6e-4878-b3a8-e1fdefe70e94",
                employee_id="EMP-9001",
            )
        )
