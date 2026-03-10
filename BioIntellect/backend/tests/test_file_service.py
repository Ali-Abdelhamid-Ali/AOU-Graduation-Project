from __future__ import annotations

import pytest

from src.services.domain.file_service import (
    FileService,
    get_preserved_extension,
    normalize_upload_content_type,
)


class _FakeStorageRepository:
    def __init__(self) -> None:
        self.upload_calls: list[tuple[str, bytes, str, str | None]] = []
        self.signed_url_calls: list[tuple[str, int, str | None]] = []
        self.delete_calls: list[tuple[str, str | None]] = []

    async def upload_file(
        self,
        path: str,
        content: bytes,
        content_type: str,
        bucket_name: str | None = None,
    ) -> str:
        self.upload_calls.append((path, content, content_type, bucket_name))
        return path

    async def get_signed_url(
        self, path: str, expires_in: int = 3600, bucket_name: str | None = None
    ) -> str:
        self.signed_url_calls.append((path, expires_in, bucket_name))
        return f"https://example.com/{bucket_name}/{path}"

    async def delete_file(self, path: str, bucket_name: str | None = None):
        self.delete_calls.append((path, bucket_name))


class _FakeClinicalRepository:
    def __init__(self) -> None:
        self.created_file_payload: dict | None = None
        self.file_meta: dict | None = None
        self.deleted_args: tuple[str, str, str | None] | None = None

    async def create_medical_file(self, metadata: dict):
        self.created_file_payload = dict(metadata)
        return {"id": "file-1", **metadata}

    async def get_medical_file(self, _file_id: str):
        return self.file_meta

    async def delete_medical_file(
        self, file_id: str, deleted_by: str, reason: str | None = None
    ) -> bool:
        self.deleted_args = (file_id, deleted_by, reason)
        return True


@pytest.mark.unit
def test_normalize_upload_content_type_rewrites_nifti_gzip_to_octet_stream() -> None:
    assert (
        normalize_upload_content_type("study_flair.nii.gz", "application/x-gzip")
        == "application/octet-stream"
    )
    assert get_preserved_extension("study_flair.nii.gz") == ".nii.gz"


@pytest.mark.unit
async def test_upload_medical_file_routes_mri_to_mri_bucket() -> None:
    storage_repo = _FakeStorageRepository()
    clinical_repo = _FakeClinicalRepository()
    service = FileService(storage_repo, clinical_repo)

    result = await service.upload_medical_file(
        user_id="doctor-1",
        patient_id="patient-1",
        case_id="case-1",
        file_name="BraTS2021_0100_flair.nii.gz",
        content=b"fake-nifti-payload",
        content_type="application/x-gzip",
        file_type="mri",
        description="FLAIR modality uploaded for MRI segmentation",
    )

    assert result["id"] == "file-1"
    assert storage_repo.upload_calls
    storage_path, _, content_type, bucket_name = storage_repo.upload_calls[0]
    assert storage_path.endswith(".nii.gz")
    assert content_type == "application/octet-stream"
    assert bucket_name == "mri-files"
    assert clinical_repo.created_file_payload is not None
    assert clinical_repo.created_file_payload["mime_type"] == "application/octet-stream"
    assert clinical_repo.created_file_payload["file_path"].endswith(".nii.gz")
    assert clinical_repo.created_file_payload["storage_bucket"] == "mri-files"
    assert (
        clinical_repo.created_file_payload["description"]
        == "FLAIR modality uploaded for MRI segmentation"
    )


@pytest.mark.unit
async def test_upload_medical_file_routes_ecg_to_ecg_bucket() -> None:
    storage_repo = _FakeStorageRepository()
    clinical_repo = _FakeClinicalRepository()
    service = FileService(storage_repo, clinical_repo)

    await service.upload_medical_file(
        user_id="doctor-1",
        patient_id="patient-1",
        case_id="case-1",
        file_name="lead-II.dcm",
        content=b"fake-dicom-payload",
        content_type="application/dicom",
        file_type="ecg",
    )

    assert storage_repo.upload_calls[0][3] == "ecg-files"
    assert clinical_repo.created_file_payload is not None
    assert clinical_repo.created_file_payload["storage_bucket"] == "ecg-files"


@pytest.mark.unit
async def test_get_download_link_prefers_bucket_stored_on_record() -> None:
    storage_repo = _FakeStorageRepository()
    clinical_repo = _FakeClinicalRepository()
    clinical_repo.file_meta = {
        "id": "file-1",
        "file_path": "patient-1/case-1/file.nii.gz",
        "file_type": "mri",
        "storage_bucket": "mri-files",
    }
    service = FileService(storage_repo, clinical_repo)

    url = await service.get_download_link("doctor-1", "file-1")

    assert url == "https://example.com/mri-files/patient-1/case-1/file.nii.gz"
    assert storage_repo.signed_url_calls == [
        ("patient-1/case-1/file.nii.gz", 3600, "mri-files")
    ]


@pytest.mark.unit
async def test_delete_medical_file_falls_back_to_bucket_from_file_type() -> None:
    storage_repo = _FakeStorageRepository()
    clinical_repo = _FakeClinicalRepository()
    clinical_repo.file_meta = {
        "id": "file-1",
        "file_path": "patient-1/case-1/file.nii.gz",
        "file_type": "mri",
        "storage_bucket": None,
    }
    service = FileService(storage_repo, clinical_repo)

    deleted = await service.delete_medical_file("doctor-1", "file-1", "cleanup")

    assert deleted is True
    assert storage_repo.delete_calls == [("patient-1/case-1/file.nii.gz", "mri-files")]
    assert clinical_repo.deleted_args == ("file-1", "doctor-1", "cleanup")
