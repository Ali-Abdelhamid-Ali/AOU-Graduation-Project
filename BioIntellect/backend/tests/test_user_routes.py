from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.api.routes import user_routes
from src.security.auth_middleware import get_current_user
from src.security.permission_map import Permission


class _FakeUserRepository:
    def __init__(self, role_row: dict[str, object]) -> None:
        self.role_row = role_row

    async def list_user_roles(self, *_args, **_kwargs):
        return [dict(self.role_row)]

    async def get_user_role(self, _role_id: str):
        return dict(self.role_row)


class _FakeProfileRepository:
    def __init__(self) -> None:
        self.updated_payload = None

    async def update_my_profile(self, _user_id: str, profile_data: dict, role: str | None = None):
        self.updated_payload = {"role": role, **profile_data}
        return {
            "id": "patient-1",
            "user_id": "auth-user-1",
            "first_name": "Mina",
            "last_name": "George",
            "address": profile_data.get("address"),
            "city": profile_data.get("city"),
            "created_at": "2026-03-11T10:00:00+00:00",
            "user_role": role,
        }


class _FakePatientListRepository:
    async def list_patients(self, *_args, **_kwargs):
        return [
            {
                "id": "patient-1",
                "user_id": "auth-user-1",
                "hospital_id": "hospital-1",
                "mrn": "MRN-1001",
                "first_name": "Mina",
                "last_name": "George",
                "first_name_ar": None,
                "last_name_ar": None,
                "email": "mina@example.com",
                "phone": "01000000000",
                "gender": "female",
                "date_of_birth": "1998-01-01",
                "blood_type": "A+",
                "national_id": None,
                "passport_number": None,
                "address": "New Cairo",
                "city": "Cairo",
                "region_id": None,
                "country_id": None,
                "emergency_contact_name": None,
                "emergency_contact_phone": None,
                "emergency_contact_relation": None,
                "allergies": [],
                "chronic_conditions": [],
                "current_medications": [],
                "insurance_provider": None,
                "insurance_number": None,
                "primary_doctor_id": None,
                "is_active": True,
                "notes": None,
                "settings": {},
                "created_at": "2026-03-11T10:00:00+00:00",
                "updated_at": "2026-03-11T10:00:00+00:00",
            }
        ]


@pytest.fixture
def user_routes_app():
    app = FastAPI()
    app.include_router(user_routes.router)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "admin-1",
        "role": "super_admin",
        "permissions": set(Permission),
    }
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
def test_list_user_roles_accepts_schema_shaped_rows_without_updated_at(
    user_routes_app,
) -> None:
    user_routes_app.dependency_overrides[user_routes.UserRepository] = lambda: (
        _FakeUserRepository(
            {
                "id": "role-1",
                "user_id": "user-1",
                "role": "doctor",
                "hospital_id": "hospital-1",
                "granted_by": "admin-1",
                "granted_at": "2026-03-10T10:00:00+00:00",
                "expires_at": None,
                "is_active": True,
                "created_at": "2026-03-10T10:00:00+00:00",
            }
        )
    )
    client = TestClient(user_routes_app)

    response = client.get("/users/roles")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["role"] == "doctor"
    assert payload[0].get("updated_at") is None


@pytest.mark.unit
def test_get_user_role_accepts_schema_shaped_rows_without_updated_at(
    user_routes_app,
) -> None:
    user_routes_app.dependency_overrides[user_routes.UserRepository] = lambda: (
        _FakeUserRepository(
            {
                "id": "role-1",
                "user_id": "user-1",
                "role": "doctor",
                "hospital_id": None,
                "granted_by": None,
                "granted_at": "2026-03-10T10:00:00+00:00",
                "expires_at": None,
                "is_active": True,
                "created_at": "2026-03-10T10:00:00+00:00",
            }
        )
    )
    client = TestClient(user_routes_app)

    response = client.get("/users/roles/role-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "role-1"
    assert payload["role"] == "doctor"
    assert payload.get("updated_at") is None


@pytest.mark.unit
def test_update_my_profile_accepts_address_and_city(user_routes_app) -> None:
    repo = _FakeProfileRepository()
    user_routes_app.dependency_overrides[user_routes.UserRepository] = lambda: repo
    user_routes_app.dependency_overrides[get_current_user] = lambda: {
        "id": "auth-user-1",
        "role": "patient",
        "permissions": set(Permission),
    }
    client = TestClient(user_routes_app)

    response = client.put(
        "/users/profile",
        json={"address": "New Cairo", "city": "Cairo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["address"] == "New Cairo"
    assert payload["city"] == "Cairo"
    assert repo.updated_payload == {
        "role": "patient",
        "address": "New Cairo",
        "city": "Cairo",
    }


@pytest.mark.unit
def test_list_patients_accepts_rows_without_avatar_url(user_routes_app) -> None:
    user_routes_app.dependency_overrides[user_routes.UserRepository] = (
        lambda: _FakePatientListRepository()
    )
    client = TestClient(user_routes_app)

    response = client.get("/users/patients")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["mrn"] == "MRN-1001"
    assert payload[0]["address"] == "New Cairo"
    assert payload[0]["avatar_url"] is None
