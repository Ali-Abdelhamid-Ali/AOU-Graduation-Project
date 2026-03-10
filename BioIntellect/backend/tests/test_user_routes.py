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
