"""Report Service - Business Logic for Medical Documentation."""

import random
from datetime import datetime
from typing import Dict, Any, Optional
from src.repositories.report_repository import ReportRepository
from src.observability.audit import log_audit, AuditAction


class ReportService:
    def __init__(self, repository: ReportRepository):
        self.repo = repository

    def _generate_report_number(self, report_type: str) -> str:
        prefix = report_type[:3].upper()
        date_part = datetime.now().strftime("%Y%m%d")
        seq = str(random.randint(1, 99999)).zfill(5)
        return f"{prefix}-{date_part}-{seq}"

    async def create_report(self, user_id: str, data: Any) -> Dict[str, Any]:
        """Consolidates clinical data into a report record."""
        # Defensive check: Convert Pydantic model to dict if needed
        if hasattr(data, "dict") and callable(getattr(data, "dict")):
            data = data.dict()
        report_data = {
            "report_number": self._generate_report_number(
                data.get("report_type", "GEN")
            ),
            "patient_id": data["patient_id"],
            "case_id": data.get("case_id"),
            "report_type": data["report_type"],
            "ecg_result_id": data.get("ecg_result_id"),
            "mri_result_id": data.get("mri_result_id"),
            "title": data["title"],
            "summary": data.get("summary"),
            "content": data.get("content", {}),
            "status": "draft",
            "is_final": False,
            "created_by": user_id,
        }

        result = await self.repo.create(report_data)
        if not result:
            raise ValueError("Failed to create report record")

        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={"report_id": result["id"], "action": "generate_report"},
        )
        return result

    async def finalize_report(
        self, user_id: str, report_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approves and finalizes a report."""
        update_data = {
            "status": "approved",
            "is_final": True,
            "approved_at": datetime.utcnow().isoformat(),
            "approval_notes": notes,
        }
        result = await self.repo.update(report_id, update_data)
        if not result:
            raise ValueError(f"Failed to finalize report with id {report_id}")

        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={"report_id": report_id, "action": "finalize_report"},
        )
        return result

