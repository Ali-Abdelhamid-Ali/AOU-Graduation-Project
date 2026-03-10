from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import file_routes
from src.security.auth_middleware import get_current_user
from src.security.permission_map import Permission


class _FakeFileService:
    def __init__(self) -> None:
        self.upload_calls: list[dict[str, object]] = []

    async def upload_medical_file(
        self,
        user_id: str,
        patient_id: str,
        case_id: str,
        file_name: str,
        content: bytes,
        content_type: str,
        file_type: str,
        description: str | None = None,
    ):
        payload = {
            "user_id": user_id,
            "patient_id": patient_id,
            "case_id": case_id,
            "file_name": file_name,
            "content": content,
            "content_type": content_type,
            "file_type": file_type,
            "description": description,
        }
        self.upload_calls.append(payload)
        return {"id": "file-1", "storage_bucket": "mri-files", **payload}


@pytest.fixture
def file_routes_app():
    app = FastAPI()
    app.include_router(file_routes.router)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "doctor-1",
        "role": "doctor",
        "permissions": set(Permission),
    }
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
def test_upload_file_rejects_types_not_backed_by_schema(file_routes_app) -> None:
    fake_service = _FakeFileService()
    file_routes_app.dependency_overrides[file_routes.get_file_service] = (
        lambda: fake_service
    )
    client = TestClient(file_routes_app)

    response = client.post(
        "/files/upload",
        files={"file": ("report.pdf", b"pdf-bytes", "application/pdf")},
        data={
            "case_id": "case-1",
            "patient_id": "patient-1",
            "file_type": "pdf",
        },
    )

    assert response.status_code == 400
    assert "ecg, mri" in response.json()["detail"]
    assert fake_service.upload_calls == []


@pytest.mark.unit
def test_upload_file_passes_description_and_normalized_mime(file_routes_app) -> None:
    fake_service = _FakeFileService()
    file_routes_app.dependency_overrides[file_routes.get_file_service] = (
        lambda: fake_service
    )
    client = TestClient(file_routes_app)

    response = client.post(
        "/files/upload",
        files={"file": ("study_t1.nii.gz", b"nifti-bytes", "application/x-gzip")},
        data={
            "case_id": "case-1",
            "patient_id": "patient-1",
            "file_type": "mri",
            "description": "T1 modality uploaded for MRI segmentation",
        },
    )

    assert response.status_code == 200
    assert fake_service.upload_calls == [
        {
            "user_id": "doctor-1",
            "patient_id": "patient-1",
            "case_id": "case-1",
            "file_name": "study_t1.nii.gz",
            "content": b"nifti-bytes",
            "content_type": "application/octet-stream",
            "file_type": "mri",
            "description": "T1 modality uploaded for MRI segmentation",
        }
    ]
