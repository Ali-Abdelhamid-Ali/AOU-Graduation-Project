from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.api.routes import system_routes
from src.security.auth_middleware import get_current_user
from src.security.permission_map import Permission


class _FailingRpcCall:
    def __init__(self, error_message: str) -> None:
        self.error_message = error_message

    async def execute(self):
        raise Exception(self.error_message)


class _FailingSystemClient:
    def __init__(self, error_message: str) -> None:
        self.error_message = error_message
        self.rpc_calls: list[tuple[str, dict[str, str]]] = []

    def rpc(self, name: str, payload: dict[str, str]):
        self.rpc_calls.append((name, payload))
        return _FailingRpcCall(self.error_message)


class _FakeSystemRepository:
    def __init__(self, client: _FailingSystemClient) -> None:
        self.client = client

    async def _get_client(self):
        return self.client


@pytest.fixture
def system_routes_app():
    app = FastAPI()
    app.include_router(system_routes.router)
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
def test_refresh_schema_returns_controlled_error_when_backend_refresh_is_unavailable(
    system_routes_app,
) -> None:
    fake_client = _FailingSystemClient(
        "{'code': 'PGRST202', 'message': 'Could not find the function public.pg_notify'}"
    )
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: (
        _FakeSystemRepository(fake_client)
    )
    client = TestClient(system_routes_app)

    response = client.post("/system/refresh-schema")

    assert response.status_code == 501
    assert "not supported" in response.json()["detail"]
    assert fake_client.rpc_calls == [
        ("pg_notify", {"channel": "pgrst", "payload": "reload schema"})
    ]
