import re

import pytest

from src.services.domain.clinical_service import ClinicalService


class _DummyClinicalRepository:
    def __init__(self) -> None:
        self.last_payload = None

    async def create_medical_case(self, case_data):
        self.last_payload = dict(case_data)
        return {"id": "case-1", **self.last_payload}

    async def create_report(self, report_data):
        self.last_payload = dict(report_data)
        return {"id": "report-1", **self.last_payload}


class _DummyAIService:
    pass


@pytest.mark.unit
async def test_create_case_generates_case_number_when_missing() -> None:
    repo = _DummyClinicalRepository()
    service = ClinicalService(repo, _DummyAIService())

    result = await service.create_case(
        "user-1",
        {
            "patient_id": "patient-1",
            "hospital_id": "1d00d003-3f6e-4878-b3a8-e1fdefe70e94",
            "chief_complaint": "Brain MRI Volumetric Study - AI Segmentation",
        },
    )

    assert repo.last_payload is not None
    assert result is not None
    assert re.fullmatch(
        r"MC-1D00D0-\d{8}-[0-9A-F]{6}",
        repo.last_payload["case_number"],
    )


@pytest.mark.unit
async def test_create_case_preserves_existing_case_number() -> None:
    repo = _DummyClinicalRepository()
    service = ClinicalService(repo, _DummyAIService())

    result = await service.create_case(
        "user-1",
        {
            "patient_id": "patient-1",
            "hospital_id": "1d00d003-3f6e-4878-b3a8-e1fdefe70e94",
            "chief_complaint": "Automated AI ECG Screening",
            "case_number": "MC-CUSTOM-20260309-ABC123",
        },
    )

    assert repo.last_payload is not None
    assert result is not None
    assert repo.last_payload["case_number"] == "MC-CUSTOM-20260309-ABC123"


@pytest.mark.unit
async def test_create_report_generates_report_number_when_missing() -> None:
    repo = _DummyClinicalRepository()
    service = ClinicalService(repo, _DummyAIService())

    result = await service.create_report(
        "user-1",
        {
            "patient_id": "patient-1",
            "report_type": "mri",
            "title": "MRI Segmentation Summary",
            "content": {"finding": "Large lesion volume"},
        },
    )

    assert repo.last_payload is not None
    assert result is not None
    assert re.fullmatch(r"MRI-\d{8}-[0-9A-F]{5}", repo.last_payload["report_number"])
    assert repo.last_payload["status"] == "draft"
    assert repo.last_payload["is_final"] is False
    assert repo.last_payload["version"] == 1
