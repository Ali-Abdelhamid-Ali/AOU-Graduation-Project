"""Report Service - Business Logic for Medical Documentation."""

import random
from datetime import datetime
from typing import Any, Dict, Optional

from src.observability.audit import AuditAction, log_audit
from src.repositories.report_repository import ReportRepository


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
        if hasattr(data, "dict") and callable(data.dict):
            data = data.dict()
        report_data = {
            "report_number": self._generate_report_number(
                data.get("report_type", "GEN")
            ),
            "patient_id": data["patient_id"],
            "case_id": data.get("case_id"),
            "doctor_id": data.get("doctor_id") or user_id,
            "report_type": data["report_type"],
            "ecg_result_id": data.get("ecg_result_id"),
            "mri_result_id": data.get("mri_result_id"),
            "title": data["title"],
            "summary": data.get("summary"),
            "content": data.get("content", {}),
            "generated_by_model": data.get("generated_by_model"),
            "model_version": data.get("model_version"),
            "template_used": data.get("template_used"),
            "status": "draft",
            "is_final": False,
            "version": data.get("version", 1),
            "metadata": data.get("metadata", {}),
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

    async def update_report(
        self, user_id: str, report_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a draft report's title, summary, or content."""
        allowed = {"title", "summary", "content", "status"}
        payload = {k: v for k, v in data.items() if k in allowed}
        # Prevent editing finalized reports
        existing = await self.repo.get_by_id(report_id)
        if not existing:
            raise ValueError(f"Report {report_id} not found")
        if existing.get("is_final"):
            raise ValueError("Cannot edit a finalized report")
        result = await self.repo.update(report_id, payload)
        if not result:
            raise ValueError(f"Failed to update report {report_id}")
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={"report_id": report_id, "action": "update_report"},
        )
        return result

    async def discard_report(self, user_id: str, report_id: str) -> bool:
        """Soft-delete a draft report by setting status=discarded."""
        existing = await self.repo.get_by_id(report_id)
        if not existing:
            raise ValueError(f"Report {report_id} not found")
        if existing.get("is_final"):
            raise ValueError("Cannot discard a finalized report")
        result = await self.repo.update(report_id, {"status": "discarded"})
        if not result:
            raise ValueError(f"Failed to discard report {report_id}")
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={"report_id": report_id, "action": "discard_report"},
        )
        return True

