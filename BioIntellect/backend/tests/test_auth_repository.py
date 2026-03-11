from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.repositories.auth_repository import AuthRepository


class _FakeQuery:
    def __init__(self, data: list[dict] | None = None) -> None:
        self.data = data or []
        self.filters: list[tuple[str, object]] = []

    def select(self, _columns: str):
        return self

    def eq(self, field: str, value: object):
        self.filters.append((field, value))
        return self

    def limit(self, _value: int):
        return self

    async def execute(self):
        return SimpleNamespace(data=self.data)


class _FakeClient:
    def __init__(self, query_data: list[list[dict]]) -> None:
        self.query_data = list(query_data)
        self.queries: list[_FakeQuery] = []

    def table(self, _name: str) -> _FakeQuery:
        query = _FakeQuery(self.query_data.pop(0) if self.query_data else [])
        self.queries.append(query)
        return query


@pytest.mark.unit
async def test_get_profile_by_user_id_falls_back_to_legacy_id(monkeypatch) -> None:
    repo = AuthRepository()
    fake_client = _FakeClient(
        [
            [],
            [{"id": "auth-user-1", "first_name": "Mina"}],
        ]
    )

    async def fake_get_admin():
        return fake_client

    monkeypatch.setattr(repo, "_get_admin", fake_get_admin)

    result = await repo.get_profile_by_user_id("patients", "auth-user-1")

    assert result == {"id": "auth-user-1", "first_name": "Mina"}
    assert fake_client.queries[0].filters == [("user_id", "auth-user-1")]
    assert fake_client.queries[1].filters == [("id", "auth-user-1")]


@pytest.mark.unit
async def test_resolve_user_role_accepts_legacy_patient_rows(monkeypatch) -> None:
    repo = AuthRepository()
    fake_client = _FakeClient(
        [
            [],
            [],
            [],
            [],
            [],
            [],
            [{"id": "auth-user-1"}],
        ]
    )

    async def fake_get_admin():
        return fake_client

    monkeypatch.setattr(repo, "_get_admin", fake_get_admin)

    result = await repo.resolve_user_role("auth-user-1")

    assert result == "patient"
