"""Report Repository - Data Access for Clinical Reports."""

from typing import Any, Dict

from src.repositories.base_repository import BaseRepository
from src.repositories.schema_compat import (
    normalize_ecg_result_record,
    normalize_mri_result_record,
)


class ReportRepository(BaseRepository):
    def __init__(self):
        super().__init__("generated_reports")

    async def list_reports(self, filters: Dict[str, Any], limit: int, offset: int):
        client = await self._get_client()
        query = client.table(self.table_name).select(
            "id, created_at, report_type, status, patients(id, mrn, first_name, last_name)"
        )
        for key, val in filters.items():
            if val is not None:
                query = query.eq(key, val)
        return await (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

    async def get_report_detail(self, report_id: str):
        client = await self._get_client()
        result = await (
            client.table(self.table_name)
            .select("""
                id, report_type, status, created_at,
                patients(id, mrn, first_name, last_name, gender, date_of_birth),
                medical_cases(id, case_number, status, priority),
                ecg_results(id, rhythm_classification, rhythm_confidence, analysis_status, created_at),
                mri_results:mri_segmentation_results(id, analysis_status, detected_abnormalities, measurements, severity_score, created_at)
            """)
            .eq("id", report_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None

        record = result.data[0]
        if record.get("ecg_results"):
            record["ecg_results"] = normalize_ecg_result_record(record["ecg_results"])
        if record.get("mri_results"):
            record["mri_results"] = normalize_mri_result_record(record["mri_results"])
        return record

