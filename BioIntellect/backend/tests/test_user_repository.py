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
        self.preset_data = data is not None
        self.data = data or []
        self.selected: str | None = None
        self.filters: list[tuple[str, object]] = []
        self.or_filters: list[str] = []
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

    def or_(self, expression: str):
        self.or_filters.append(expression)
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
        if not self.preset_data:
            self.data = [payload]
        return self

    def update(self, payload: dict):
        self.update_payload = payload
        if not self.preset_data:
            self.data = [payload]
        return self

    async def execute(self):
        return SimpleNamespace(data=self.data)


class _FakeClient:
    def __init__(
        self,
        data: list[dict] | None = None,
        query_data: list[list[dict]] | None = None,
    ) -> None:
        self.data = data
        self.query_data = list(query_data or [])
        self.last_table: str | None = None
        self.last_query: _FakeQuery | None = None
        self.queries: list[_FakeQuery] = []

    def table(self, name: str) -> _FakeQuery:
        self.last_table = name
        data = (
            self.query_data.pop(0)
            if self.query_data
            else (list(self.data) if self.data is not None else None)
        )
        self.last_query = _FakeQuery(list(data) if data is not None else None)
        self.queries.append(self.last_query)
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
    update_query = next(
        query for query in fake_client.queries if query.update_payload is not None
    )
    assert update_query.update_payload == {
        "first_name": "Mina",
        "notes": "Needs follow-up",
    }
    assert update_query.filters == [("user_id", "user-1")]


@pytest.mark.unit
async def test_get_my_profile_falls_back_to_legacy_id_lookup(monkeypatch) -> None:
    repo = UserRepository()
    fake_client = _FakeClient(
        query_data=[
            [],
            [{"id": "user-1", "first_name": "Mina", "last_name": "George"}],
        ]
    )

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.get_my_profile("user-1", role="patient")

    assert result == {"id": "user-1", "first_name": "Mina", "last_name": "George"}
    assert len(fake_client.queries) == 2
    assert fake_client.queries[0].filters == [("user_id", "user-1")]
    assert fake_client.queries[1].filters == [("id", "user-1")]


@pytest.mark.unit
async def test_update_my_profile_falls_back_to_legacy_id_lookup(monkeypatch) -> None:
    repo = UserRepository()
    fake_client = _FakeClient(
        query_data=[
            [],
            [{"id": "user-1"}],
            [],
            [],
            [{"id": "user-1", "city": "Cairo", "address": "New Cairo"}],
        ]
    )

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.update_my_profile(
        "user-1",
        {"city": "Cairo", "address": "New Cairo"},
        role="patient",
    )

    assert result == {"id": "user-1", "city": "Cairo", "address": "New Cairo"}
    assert len(fake_client.queries) == 5
    assert fake_client.queries[0].filters == [("user_id", "user-1")]
    assert fake_client.queries[1].filters == [("id", "user-1")]
    assert fake_client.queries[2].update_payload == {
        "city": "Cairo",
        "address": "New Cairo",
    }
    assert fake_client.queries[2].filters == [("id", "user-1")]


@pytest.mark.unit
async def test_list_patients_selects_full_response_shape_and_searches_phone(
    monkeypatch,
) -> None:
    repo = UserRepository()
    fake_client = _FakeClient(
        [
            {
                "id": "patient-1",
                "user_id": "user-1",
                "hospital_id": "hospital-1",
                "mrn": "MRN-001",
                "first_name": "Mina",
                "last_name": "George",
                "blood_type": "A+",
                "allergies": [],
                "chronic_conditions": [],
                "current_medications": [],
                "is_active": True,
                "settings": {},
                "created_at": "2026-03-10T10:00:00+00:00",
                "updated_at": "2026-03-10T10:00:00+00:00",
            }
        ]
    )

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.list_patients({"search": "0100"}, 10, 0)

    assert result
    assert fake_client.last_table == "patients"
    assert fake_client.last_query is not None
    assert fake_client.last_query.selected is not None
    assert "current_medications" in fake_client.last_query.selected
    assert "avatar_url" not in fake_client.last_query.selected
    assert fake_client.last_query.or_filters == [
        "first_name.ilike.%0100%,last_name.ilike.%0100%,mrn.ilike.%0100%,phone.ilike.%0100%"
    ]


@pytest.mark.unit
async def test_update_patient_falls_back_to_user_id_when_profile_id_misses(
    monkeypatch,
) -> None:
    repo = UserRepository()
    fake_client = _FakeClient(
        query_data=[
            [],
            [{"id": "patient-1", "user_id": "user-1", "first_name": "Mina"}],
        ]
    )

    async def fake_get_client():
        return fake_client

    monkeypatch.setattr(repo, "_get_client", fake_get_client)

    result = await repo.update_patient("user-1", {"first_name": "Mina"})

    assert result == {"id": "patient-1", "user_id": "user-1", "first_name": "Mina"}
    assert len(fake_client.queries) == 2
    assert fake_client.queries[0].filters == [("id", "user-1")]
    assert fake_client.queries[1].filters == [("user_id", "user-1")]
    assert fake_client.queries[0].update_payload == {"first_name": "Mina"}
    assert fake_client.queries[1].update_payload == {"first_name": "Mina"}
