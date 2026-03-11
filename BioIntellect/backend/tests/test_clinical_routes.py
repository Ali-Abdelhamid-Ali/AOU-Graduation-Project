from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.api.routes import clinical_routes
from src.repositories.clinical_repository import ClinicalRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_patient_friendly_mri_result_uses_persisted_result(monkeypatch) -> None:
    async def fake_get_case(self, case_id: str):
        assert case_id == "case-1"
        return {"id": case_id, "patient_id": "patient-1"}

    async def fake_list_results(self, filters: dict, limit: int, offset: int):
        assert filters == {"case_id": "case-1"}
        assert limit == 5
        assert offset == 0
        return [
            {
                "id": "result-1",
                "analysis_status": "completed",
                "tumor_detected": True,
                "detected_abnormalities": ["Right frontal lesion"],
                "ai_recommendations": ["Discuss this study with your neurologist."],
                "measurements": {"largest_diameter_mm": 18.2},
                "severity_score": 62,
                "is_reviewed": True,
                "created_at": "2026-03-10T12:00:00+00:00",
            }
        ]

    monkeypatch.setattr(ClinicalRepository, "get_medical_case", fake_get_case)
    monkeypatch.setattr(ClinicalRepository, "list_mri_results", fake_list_results)

    payload = await clinical_routes.get_patient_friendly_mri_result(
        "case-1",
        user={"id": "auth-1", "profile_id": "patient-1", "role": "patient"},
    )

    assert payload["result_id"] == "result-1"
    assert payload["status"] == "completed"
    assert payload["summary"] == "The saved MRI analysis highlighted: Right frontal lesion."
    assert payload["next_step"] == "Discuss this study with your neurologist."
    assert payload["measurements"] == {"largest_diameter_mm": 18.2}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_patient_friendly_mri_result_enforces_patient_scope(monkeypatch) -> None:
    async def fake_get_case(self, case_id: str):
        return {"id": case_id, "patient_id": "patient-9"}

    monkeypatch.setattr(ClinicalRepository, "get_medical_case", fake_get_case)

    with pytest.raises(HTTPException) as excinfo:
        await clinical_routes.get_patient_friendly_mri_result(
            "case-7",
            user={"id": "auth-1", "profile_id": "patient-1", "role": "patient"},
        )

    assert excinfo.value.status_code == 403
