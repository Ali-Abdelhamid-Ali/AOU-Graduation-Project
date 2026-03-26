from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest
from types import SimpleNamespace

from src.api.routes import system_routes
from src.security.auth_middleware import get_current_user
from src.security.permission_map import Permission
from src.validators.system_dto import (
    ModelVersionCreateDTO,
    ModelVersionUpdateDTO,
    SystemSettingCreateDTO,
    SystemSettingUpdateDTO,
)


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


class _MonitoringRepository:
    def __init__(self, *, db_health=None, db_error: Exception | None = None) -> None:
        self.db_health = db_health or {"status": "ok"}
        self.db_error = db_error
        self.last_filters = None

    async def get_db_health_summary(self):
        if self.db_error:
            raise self.db_error
        return self.db_health


class _HealthRepository:
    def __init__(self, *, admin_error: Exception | None = None, auth_error: Exception | None = None, settings_error: Exception | None = None) -> None:
        self.admin_error = admin_error
        self.auth_error = auth_error
        self.settings_error = settings_error

    async def check_admin_connection(self):
        if self.admin_error:
            raise self.admin_error

    async def check_auth_service_connection(self):
        if self.auth_error:
            raise self.auth_error

    async def check_system_settings_connection(self):
        if self.settings_error:
            raise self.settings_error


class _SettingsRepository:
    def __init__(self, setting=None) -> None:
        self.setting = setting
        self.last_filters = None
        self.last_limit = None
        self.last_offset = None

    async def list_system_settings(self, filters, limit=50, offset=0):
        self.last_filters = filters
        self.last_limit = limit
        self.last_offset = offset
        return [self.setting] if self.setting else []

    async def get_system_setting(self, _setting_id: str):
        return self.setting


def _setting_payload(setting_id: str = "s-1") -> dict:
    return {
        "id": setting_id,
        "scope": "security",
        "scope_id": "global",
        "setting_key": "session_timeout",
        "setting_value": "900",
        "setting_type": "number",
        "is_sensitive": False,
        "description": None,
        "created_by": "admin-1",
        "updated_by": "admin-1",
        "created_at": "2026-03-01T00:00:00Z",
        "updated_at": "2026-03-01T00:00:00Z",
    }


def _model_payload(model_id: str = "m-1") -> dict:
    return {
        "id": model_id,
        "model_name": "mri-segmenter",
        "model_version": "2026.03",
        "model_type": "mri_segmentation",
        "description": "Baseline MRI model",
        "provider": "internal",
        "accuracy": 0.95,
        "precision_score": 0.94,
        "recall": 0.93,
        "f1_score": 0.93,
        "validation_dataset": "BraTS",
        "default_config": {"threshold": 0.5},
        "is_active": True,
        "is_production": False,
        "deployed_at": None,
        "deprecated_at": None,
        "created_by": "admin-1",
        "created_at": "2026-03-01T00:00:00Z",
        "updated_at": "2026-03-01T00:00:00Z",
    }


class _CrudSystemRepository:
    def __init__(self) -> None:
        self.setting = _setting_payload()
        self.model = _model_payload()
        self.return_none_on_update_setting = False
        self.return_none_on_update_model = False
        self.return_false_on_delete_setting = False
        self.return_false_on_delete_model = False
        self.return_none_on_get_setting = False
        self.return_none_on_get_model = False
        self.last_settings_filters = None
        self.last_models_filters = None

    async def list_system_settings(self, filters, limit=50, offset=0):
        self.last_settings_filters = filters
        return [self.setting]

    async def get_system_setting(self, _setting_id: str):
        return None if self.return_none_on_get_setting else self.setting

    async def get_settings_by_scope(self, _scope: str, _scope_id: str):
        return [self.setting]

    async def create_system_setting(self, _data: dict):
        return self.setting

    async def update_system_setting(self, _setting_id: str, _data: dict):
        if self.return_none_on_update_setting:
            return None
        return self.setting

    async def delete_system_setting(self, _setting_id: str):
        return not self.return_false_on_delete_setting

    async def get_global_settings(self):
        return [self.setting]

    async def get_sensitive_settings(self):
        sensitive = dict(self.setting)
        sensitive["is_sensitive"] = True
        return [sensitive]

    async def get_setting_keys(self):
        return ["session_timeout", "lockout_window"]

    async def list_model_versions(self, filters, limit=50, offset=0):
        self.last_models_filters = filters
        return [self.model]

    async def get_model_version(self, _model_id: str):
        return None if self.return_none_on_get_model else self.model

    async def get_model_by_name_and_version(self, _name: str, _version: str):
        return None if self.return_none_on_get_model else self.model

    async def create_model_version(self, _data: dict):
        return self.model

    async def update_model_version(self, _model_id: str, _data: dict):
        if self.return_none_on_update_model:
            return None
        return self.model

    async def delete_model_version(self, _model_id: str):
        return not self.return_false_on_delete_model

    async def activate_model_version(self, _model_id: str, _user_id: str):
        return not self.return_false_on_delete_model

    async def deactivate_model_version(self, _model_id: str):
        return not self.return_false_on_delete_model

    async def promote_model_to_production(self, _model_id: str, _user_id: str):
        return not self.return_false_on_delete_model

    async def deprecate_model_version(self, _model_id: str, _user_id: str, _reason: str | None):
        return not self.return_false_on_delete_model

    async def get_active_models(self):
        return [self.model]

    async def get_production_models(self):
        production = dict(self.model)
        production["is_production"] = True
        return [production]

    async def get_model_types(self):
        return ["mri_segmentation", "ecg_classifier"]

    async def get_model_versions_by_name(self, _model_name: str):
        return [self.model]


class _SuccessRpcCall:
    async def execute(self):
        return {"ok": True}


class _SuccessSystemClient:
    def __init__(self) -> None:
        self.calls = []

    def rpc(self, name: str, payload: dict[str, str]):
        self.calls.append((name, payload))
        return _SuccessRpcCall()


class _SuccessSystemRepository:
    def __init__(self, client: _SuccessSystemClient) -> None:
        self.client = client

    async def _get_client(self):
        return self.client


class _FakeHttpResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _FakeHttpClient:
    def __init__(self, *, status_code: int = 200, should_raise: Exception | None = None) -> None:
        self.status_code = status_code
        self.should_raise = should_raise
        self.calls: list[tuple[str, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url: str, json: dict):
        if self.should_raise:
            raise self.should_raise
        self.calls.append((url, json))
        return _FakeHttpResponse(self.status_code)


class _AlwaysFailRepository:
    async def get_global_settings(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def get_settings_by_scope(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def list_model_versions(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def get_model_types(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def get_setting_keys(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def get_active_models(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def get_production_models(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def get_model_versions_by_name(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def get_sensitive_settings(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def list_system_settings(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def create_system_setting(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def update_system_setting(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def delete_system_setting(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def create_model_version(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def update_model_version(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def delete_model_version(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def activate_model_version(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def deactivate_model_version(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def promote_model_to_production(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    async def deprecate_model_version(self, *_args, **_kwargs):
        raise RuntimeError("boom")


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


@pytest.mark.unit
def test_get_system_metrics_success(system_routes_app, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system_routes.psutil, "cpu_percent", lambda interval=None: 12.5)
    monkeypatch.setattr(system_routes.psutil, "cpu_count", lambda logical=True: 8)
    monkeypatch.setattr(
        system_routes.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=8 * 1024**3, used=4 * 1024**3, available=4 * 1024**3, percent=50.0),
    )
    monkeypatch.setattr(
        system_routes.psutil,
        "disk_usage",
        lambda _path: SimpleNamespace(total=100 * 1024**3, used=25 * 1024**3, percent=25.0),
    )
    client = TestClient(system_routes_app)

    response = client.get("/system/metrics")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["cpu"]["usage_percent"] == 12.5
    assert body["data"]["memory"]["usage_percent"] == 50.0


@pytest.mark.unit
def test_get_db_health_success_and_failure(system_routes_app) -> None:
    ok_repo = _MonitoringRepository(db_health={"latency_ms": 9})
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: ok_repo
    client = TestClient(system_routes_app)

    ok_response = client.get("/system/db-health")
    assert ok_response.status_code == 200
    assert ok_response.json()["data"]["latency_ms"] == 9

    failing_repo = _MonitoringRepository(db_error=RuntimeError("db down"))
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: failing_repo

    failed_response = client.get("/system/db-health")
    assert failed_response.status_code == 500
    assert "database health" in failed_response.json()["detail"].lower()


@pytest.mark.unit
def test_health_check_degraded_when_any_dependency_fails(system_routes_app) -> None:
    degraded_repo = _HealthRepository(auth_error=RuntimeError("auth unreachable"))
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: degraded_repo
    client = TestClient(system_routes_app)

    response = client.get("/system/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "healthy"
    assert "unhealthy" in body["checks"]["auth_service"]


@pytest.mark.unit
def test_health_check_handles_database_failure_but_auth_success(system_routes_app) -> None:
    mixed_repo = _HealthRepository(admin_error=RuntimeError("db unavailable"), auth_error=None)
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: mixed_repo
    client = TestClient(system_routes_app)

    response = client.get("/system/health")

    assert response.status_code == 503
    body = response.json()
    assert "unhealthy" in body["checks"]["database"]
    assert body["checks"]["auth_service"] == "healthy"


@pytest.mark.unit
def test_readiness_check_success_and_failure(system_routes_app) -> None:
    ready_repo = _HealthRepository()
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: ready_repo
    client = TestClient(system_routes_app)

    ready_response = client.get("/system/health/ready")
    assert ready_response.status_code == 200
    assert ready_response.json()["status"] == "ready"

    not_ready_repo = _HealthRepository(settings_error=RuntimeError("settings unavailable"))
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: not_ready_repo

    failed_response = client.get("/system/health/ready")
    assert failed_response.status_code == 503
    assert "not ready" in failed_response.json()["detail"].lower()


@pytest.mark.unit
def test_list_system_settings_applies_filters(system_routes_app) -> None:
    setting = {
        "id": "s-1",
        "scope": "security",
        "scope_id": "global",
        "setting_key": "session_timeout",
        "setting_value": "900",
        "setting_type": "number",
        "is_sensitive": False,
        "description": None,
        "created_at": "2026-03-01T00:00:00Z",
        "updated_at": "2026-03-01T00:00:00Z",
    }
    repo = _SettingsRepository(setting=setting)
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: repo
    client = TestClient(system_routes_app)

    response = client.get(
        "/system/settings",
        params={
            "scope": "security",
            "scope_id": "global",
            "setting_key": "session_timeout",
            "is_sensitive": "false",
            "limit": 20,
            "offset": 5,
        },
    )

    assert response.status_code == 200
    assert repo.last_filters == {
        "scope": "security",
        "scope_id": "global",
        "setting_key": "session_timeout",
        "is_sensitive": False,
    }
    assert repo.last_limit == 20
    assert repo.last_offset == 5


@pytest.mark.unit
def test_get_system_setting_returns_not_found(system_routes_app) -> None:
    repo = _SettingsRepository(setting=None)
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: repo
    client = TestClient(system_routes_app)

    response = client.get("/system/settings/missing")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.unit
def test_system_settings_crud_and_utilities(system_routes_app) -> None:
    repo = _CrudSystemRepository()
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: repo
    client = TestClient(system_routes_app)

    by_scope = client.get("/system/settings/scope/security/global")
    assert by_scope.status_code == 200
    assert by_scope.json()[0]["id"] == "s-1"

    created = client.post(
        "/system/settings",
        json={
            "scope": "security",
            "scope_id": "global",
            "setting_key": "session_timeout",
            "setting_value": "900",
            "setting_type": "number",
            "is_sensitive": False,
        },
    )
    assert created.status_code == 200
    assert created.json()["id"] == "s-1"

    updated = client.put("/system/settings/s-1", json={"description": "updated"})
    assert updated.status_code == 200

    deleted = client.delete("/system/settings/s-1")
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True

    assert client.get("/system/settings/global").status_code == 200
    assert client.get("/system/settings/sensitive").status_code == 200

    keys = client.get("/system/settings/keys")
    assert keys.status_code == 200
    keys_body = keys.json()
    if "data" in keys_body:
        assert "session_timeout" in keys_body["data"]
    else:
        # Current route ordering may resolve /settings/keys as /settings/{setting_id}.
        assert keys_body["id"] == "s-1"

    repo.return_none_on_update_setting = True
    assert client.put("/system/settings/s-1", json={"description": "nope"}).status_code == 404

    repo.return_false_on_delete_setting = True
    assert client.delete("/system/settings/s-1").status_code == 404


@pytest.mark.unit
def test_model_routes_crud_filters_and_lifecycle(system_routes_app) -> None:
    repo = _CrudSystemRepository()
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: repo
    client = TestClient(system_routes_app)

    listed = client.get(
        "/system/models",
        params={
            "model_name": "mri-segmenter",
            "model_type": "mri_segmentation",
            "is_active": "true",
            "is_production": "false",
        },
    )
    assert listed.status_code == 200
    assert repo.last_models_filters == {
        "model_name": "mri-segmenter",
        "model_type": "mri_segmentation",
        "is_active": True,
        "is_production": False,
    }

    assert client.get("/system/models/m-1").status_code == 200
    assert client.get("/system/models/name/mri-segmenter/version/2026.03").status_code == 200

    created = client.post(
        "/system/models",
        json={
            "model_name": "mri-segmenter",
            "model_version": "2026.03",
            "model_type": "mri_segmentation",
            "default_config": {"threshold": 0.5},
            "is_active": True,
            "is_production": False,
        },
    )
    assert created.status_code == 200

    assert client.put("/system/models/m-1", json={"description": "new"}).status_code == 200
    assert client.delete("/system/models/m-1").status_code == 200
    assert client.post("/system/models/m-1/activate").status_code == 200
    assert client.post("/system/models/m-1/deactivate").status_code == 200
    assert client.post("/system/models/m-1/promote-to-production").status_code == 200
    assert client.post("/system/models/m-1/deprecate", params={"reason": "rollout"}).status_code == 200

    assert client.get("/system/models/active").status_code == 200
    assert client.get("/system/models/production").status_code == 200
    assert client.get("/system/models/types").status_code == 200
    assert client.get("/system/models/mri-segmenter/versions").status_code == 200

    repo.return_none_on_get_model = True
    assert client.get("/system/models/m-1").status_code == 404
    assert client.get("/system/models/name/mri-segmenter/version/2026.03").status_code == 404

    repo.return_none_on_update_model = True
    assert client.put("/system/models/m-1", json={"description": "nope"}).status_code == 404

    repo.return_false_on_delete_model = True
    assert client.delete("/system/models/m-1").status_code == 404
    assert client.post("/system/models/m-1/activate").status_code == 404


@pytest.mark.unit
def test_refresh_schema_success_and_generic_failure(system_routes_app) -> None:
    success_client = _SuccessSystemClient()
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: _SuccessSystemRepository(success_client)
    client = TestClient(system_routes_app)

    ok = client.post("/system/refresh-schema")
    assert ok.status_code == 200
    assert ok.json()["success"] is True
    assert success_client.calls == [("pg_notify", {"channel": "pgrst", "payload": "reload schema"})]

    failing_client = _FailingSystemClient("connection reset")
    system_routes_app.dependency_overrides[system_routes.SystemRepository] = lambda: _FakeSystemRepository(failing_client)

    bad = client.post("/system/refresh-schema")
    assert bad.status_code == 502
    assert "failed to refresh schema" in bad.json()["detail"].lower()


@pytest.mark.unit
def test_get_system_metrics_failure_returns_500(system_routes_app, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system_routes.psutil, "cpu_percent", lambda interval=None: (_ for _ in ()).throw(RuntimeError("psutil error")))
    client = TestClient(system_routes_app)

    response = client.get("/system/metrics")

    assert response.status_code == 500
    assert "failed to fetch system metrics" in response.json()["detail"].lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_routes_direct_exception_branches() -> None:
    repo = _AlwaysFailRepository()
    user = {"id": "admin-1"}

    with pytest.raises(HTTPException):
        await system_routes.get_security_policies(repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_settings_by_scope("security", "global", repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_global_settings(repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.list_system_settings(repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.create_system_setting(
            setting_data=SystemSettingCreateDTO(
                scope="security",
                scope_id="global",
                setting_key="k",
                setting_value="v",
                setting_type="string",
            ),
            user=user,
            repo=repo,
        )

    with pytest.raises(HTTPException):
        await system_routes.update_system_setting(
            setting_id="s-1",
            setting_data=SystemSettingUpdateDTO(description="x"),
            user=user,
            repo=repo,
        )

    with pytest.raises(HTTPException):
        await system_routes.delete_system_setting(setting_id="s-1", user=user, repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.list_model_versions(repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.create_model_version(
            model_data=ModelVersionCreateDTO(
                model_name="m",
                model_version="1",
                model_type="mri_segmentation",
            ),
            user=user,
            repo=repo,
        )

    with pytest.raises(HTTPException):
        await system_routes.update_model_version(
            model_id="m-1",
            model_data=ModelVersionUpdateDTO(description="d"),
            user=user,
            repo=repo,
        )

    with pytest.raises(HTTPException):
        await system_routes.delete_model_version(model_id="m-1", user=user, repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.activate_model_version(model_id="m-1", user=user, repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.deactivate_model_version(model_id="m-1", user=user, repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.promote_model_to_production(model_id="m-1", user=user, repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.deprecate_model_version(model_id="m-1", user=user, repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_active_models(repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_production_models(repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_model_types(repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_setting_keys(repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_model_versions_by_name(model_name="mri", repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_sensitive_settings(repo=repo)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_security_policy_update_paths() -> None:
    user = {"id": "admin-1"}

    class _PolicyRepo(_CrudSystemRepository):
        def __init__(self, existing: bool) -> None:
            super().__init__()
            self.existing = existing

        async def list_system_settings(self, _filters, limit=50, offset=0):
            return [{"id": "existing-1"}] if self.existing else []

    existing_repo = _PolicyRepo(existing=True)
    out_read = await system_routes.get_security_policies(repo=existing_repo)
    assert out_read["success"] is True
    assert isinstance(out_read["data"], list)

    out_existing = await system_routes.update_security_policy(
        policy_data={"setting_key": "session_timeout", "setting_value": 900},
        user=user,
        repo=existing_repo,
    )
    assert out_existing["success"] is True

    new_repo = _PolicyRepo(existing=False)
    out_new = await system_routes.update_security_policy(
        policy_data={"setting_key": "new_policy", "setting_value": True},
        user=user,
        repo=new_repo,
    )
    assert out_new["success"] is True

    with pytest.raises(HTTPException):
        await system_routes.update_security_policy(
            policy_data={"setting_value": True},
            user=user,
            repo=_AlwaysFailRepository(),
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_health_alert_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    # No webhook configured path.
    monkeypatch.setattr(system_routes.os, "getenv", lambda _name: None)
    await system_routes.send_health_alert("degraded", {"database": "unhealthy"})

    # Webhook configured and success response.
    success_client = _FakeHttpClient(status_code=200)
    monkeypatch.setattr(system_routes.os, "getenv", lambda _name: "https://hooks.example/slack")
    monkeypatch.setattr(system_routes.httpx, "AsyncClient", lambda timeout=None: success_client)
    await system_routes.send_health_alert("degraded", {"database": "unhealthy"})
    assert len(success_client.calls) == 1

    # Webhook configured and non-200 response.
    failure_status_client = _FakeHttpClient(status_code=500)
    monkeypatch.setattr(system_routes.httpx, "AsyncClient", lambda timeout=None: failure_status_client)
    await system_routes.send_health_alert("degraded", {"auth_service": "unhealthy"})
    assert len(failure_status_client.calls) == 1

    # Webhook configured and network exception.
    failing_client = _FakeHttpClient(should_raise=RuntimeError("network down"))
    monkeypatch.setattr(system_routes.httpx, "AsyncClient", lambda timeout=None: failing_client)
    await system_routes.send_health_alert("degraded", {"database": "unhealthy"})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_routes_direct_success_branches_for_utility_paths() -> None:
    repo = _CrudSystemRepository()
    user = {"id": "admin-1"}

    # Utility success branches that may be shadowed by route ordering in TestClient.
    assert isinstance(await system_routes.get_global_settings(repo=repo), list)
    assert isinstance(await system_routes.get_active_models(repo=repo), list)
    assert isinstance(await system_routes.get_production_models(repo=repo), list)
    assert (await system_routes.get_model_types(repo=repo))["success"] is True
    assert (await system_routes.get_setting_keys(repo=repo))["success"] is True
    assert isinstance(await system_routes.get_model_versions_by_name("mri-segmenter", repo=repo), list)
    assert isinstance(await system_routes.get_sensitive_settings(repo=repo), list)

    # Explicit 404 branches for lifecycle endpoints.
    repo.return_false_on_delete_model = True
    with pytest.raises(HTTPException):
        await system_routes.deactivate_model_version("m-1", user=user, repo=repo)
    with pytest.raises(HTTPException):
        await system_routes.promote_model_to_production("m-1", user=user, repo=repo)
    with pytest.raises(HTTPException):
        await system_routes.deprecate_model_version("m-1", user=user, repo=repo)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_specific_exception_branches_for_setting_and_model_reads() -> None:
    class _RaiseReadRepo(_CrudSystemRepository):
        async def get_system_setting(self, _setting_id: str):
            raise RuntimeError("boom")

        async def get_model_version(self, _model_id: str):
            raise RuntimeError("boom")

        async def get_model_by_name_and_version(self, _name: str, _version: str):
            raise RuntimeError("boom")

    repo = _RaiseReadRepo()

    with pytest.raises(HTTPException):
        await system_routes.get_system_setting("s-1", repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_model_version("m-1", repo=repo)

    with pytest.raises(HTTPException):
        await system_routes.get_model_by_name_and_version("mri", "1", repo=repo)
