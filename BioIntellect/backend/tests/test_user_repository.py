from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.repositories.user_repository import UserRepository

EXPECTED_USER_ROLE_COLUMNS = (
    "id, user_id, role, hospital_id, granted_by, granted_at, expires_at, "
    "is_active, created_at"
)


class _FakeQuery:
    def __init__(self, data: list[dict] | None = None) -> None:
        self.data = data or []
        self.selected: str | None = None
        self.filters: list[tuple[str, object]] = []
        self.ordering: tuple[str, bool] | None = None
        self.page: tuple[int, int] | None = None
        self.limit_value: int | None = None
        self.insert_payload: dict | None = None
        self.update_payload: dict | None = None

    def select(self, columns: str):
        self.selected = columns
        return self

    def eq(self, field: str, value: object):
        self.filters.append((field, value))
        return self

    def order(self, column: str, desc: bool = False):
        self.ordering = (column, desc)
        return self

    def range(self, start: int, end: int):
        self.page = (start, end)
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def insert(self, payload: dict):
        self.insert_payload = payload
        self.data = [payload]
        return self

    def update(self, payload: dict):
        self.update_payload = payload
        self.data = [payload]
        return self

    async def execute(self):
        return SimpleNamespace(data=self.data)


class _FakeClient:
    def __init__(self, data: list[dict] | None = None) -> None:
        self.data = data or []
        self.last_table: str | None = None
        self.last_query: _FakeQuery | None = None

    def table(self, name: str) -> _FakeQuery:
        self.last_table = name
        self.last_query = _FakeQuery(list(self.data))
        return self.last_query


@pytest.mark.unit
async def test_list_user_roles_selects_schema_backed_columns(monkeypatch) -> None:
    repo = UserRepository()
    fake_client = _FakeClient(
        [
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
        ]
    )

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.list_user_roles({"role": "doctor", "is_active": True}, 25, 5)

    assert result
    assert fake_client.last_table == "user_roles"
    assert fake_client.last_query is not None
    assert fake_client.last_query.selected == EXPECTED_USER_ROLE_COLUMNS
    assert fake_client.last_query.filters == [("role", "doctor"), ("is_active", True)]
    assert fake_client.last_query.ordering == ("created_at", True)
    assert fake_client.last_query.page == (5, 29)


@pytest.mark.unit
async def test_get_user_role_selects_schema_backed_columns(monkeypatch) -> None:
    repo = UserRepository()
    fake_client = _FakeClient(
        [
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
        ]
    )

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.get_user_role("role-1")

    assert result is not None
    assert fake_client.last_table == "user_roles"
    assert fake_client.last_query is not None
    assert fake_client.last_query.selected == EXPECTED_USER_ROLE_COLUMNS
    assert fake_client.last_query.filters == [("id", "role-1")]
    assert fake_client.last_query.limit_value == 1


@pytest.mark.unit
async def test_create_user_role_drops_unknown_columns(monkeypatch) -> None:
    repo = UserRepository()
    fake_client = _FakeClient()

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.create_user_role(
        {
            "user_id": "user-1",
            "role": "doctor",
            "hospital_id": "hospital-1",
            "is_active": True,
            "permissions": ["legacy"],
            "updated_at": "2026-03-10T10:00:00+00:00",
        }
    )

    assert result == {
        "user_id": "user-1",
        "role": "doctor",
        "hospital_id": "hospital-1",
        "is_active": True,
    }
    assert fake_client.last_query is not None
    assert fake_client.last_query.insert_payload == result


@pytest.mark.unit
async def test_update_user_role_drops_unknown_columns(monkeypatch) -> None:
    repo = UserRepository()
    fake_client = _FakeClient()

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.update_user_role(
        "role-1",
        {
            "role": "nurse",
            "expires_at": "2026-04-10T10:00:00+00:00",
            "permissions": ["legacy"],
        },
    )

    assert result == {
        "role": "nurse",
        "expires_at": "2026-04-10T10:00:00+00:00",
    }
    assert fake_client.last_query is not None
    assert fake_client.last_query.update_payload == result
    assert fake_client.last_query.filters == [("id", "role-1")]


@pytest.mark.unit
async def test_update_my_profile_patient_drops_non_schema_columns(monkeypatch) -> None:
    repo = UserRepository()
    fake_client = _FakeClient([{"id": "patient-1", "first_name": "Mina"}])

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.update_my_profile(
        "user-1",
        {
            "first_name": "Mina",
            "notes": "Needs follow-up",
            "avatar_url": "https://example.com/avatar.png",
            "permissions": ["legacy"],
        },
        role="patient",
    )

    assert result is not None
    assert fake_client.last_table == "patients"
    assert fake_client.last_query is not None
    assert fake_client.last_query.update_payload == {
        "first_name": "Mina",
        "notes": "Needs follow-up",
    }
    assert fake_client.last_query.filters == [("user_id", "user-1")]
