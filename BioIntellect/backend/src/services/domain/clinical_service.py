"""Clinical Service - Medical Data Orchestration."""

from typing import Dict, Any, List, Optional
from src.repositories.clinical_repository import ClinicalRepository
from src.services.ai.ai_service import AIService
from src.observability.audit import log_audit, AuditAction
from src.observability.logger import get_logger

logger = get_logger("service.clinical")


class ClinicalService:
    def __init__(self, clinical_repo: ClinicalRepository, ai_service: AIService):
        self.clinical_repo = clinical_repo
        self.ai_service = ai_service

    async def create_case(
        self, user_id: str, case_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Creates a new medical case."""
        case = await self.clinical_repo.create_medical_case(case_data)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={
                "case_id": case.get("id")
                if isinstance(case, dict)
                else getattr(case, "id", None),
                "action": "create",
            },
        )
        return case

    async def analyze_ecg(
        self, user_id: str, case_id: str, signal_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Runs AI analysis on ECG and persists results."""
        # 1. AI Analysis
        analysis = await self.ai_service.analyze_ecg(signal_data)

        # 2. Persist Result
        result_data = {
            "case_id": case_id,
            "rhythm_classification": analysis.get("prediction"),
            "rhythm_confidence": analysis.get("confidence"),
            "ai_interpretation": analysis.get("ai_notes"),
            "analysis_status": "completed",
            "performed_by": user_id,
        }
        saved_result = await self.clinical_repo.create_ecg_result(result_data)

        log_audit(
            AuditAction.ANALYZE_IMAGE,
            user_id=user_id,
            details={"case_id": case_id, "modality": "ECG"},
        )
        return saved_result

    async def review_result(
        self, user_id: str, table_name: str, result_id: str, data: dict
    ):
        """Allow doctors to review and confirm AI results."""
        try:
            # Table name validation for security
            if table_name not in ["ecg_results", "mri_segmentation_results"]:
                raise Exception("Invalid result table")

            # Use specific update methods based on table
            if table_name == "ecg_results":
                updated = await self.clinical_repo.update_ecg_result(
                    result_id,
                    {
                        "is_reviewed": True,
                        "reviewed_at": "now()",
                        "doctor_id": user_id,
                        **data,
                    },
                )
            elif table_name == "mri_segmentation_results":
                updated = await self.clinical_repo.update_mri_result(
                    result_id,
                    {
                        "is_reviewed": True,
                        "reviewed_at": "now()",
                        "doctor_id": user_id,
                        **data,
                    },
                )
            else:
                raise Exception("Unsupported table for review")

            log_audit(
                AuditAction.REPORT_SIGN,
                user_id=user_id,
                details={"result_id": result_id, "table": table_name},
            )
            return {"success": True, "data": updated}
        except Exception as e:
            logger.error(f"Review failed for {result_id}: {str(e)}")
            raise e

    async def get_patient_history(
        self, user_id: str, patient_id: str
    ) -> Dict[str, Any]:
        """Fetch all cases and results for a patient."""
        history = await self.clinical_repo.get_patient_history(patient_id)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={"patient_id": patient_id, "action": "view_history"},
        )
        return history

    # â”پâ”پâ”پâ”پ ECG DOMAIN â”پâ”پâ”پâ”پ

    async def create_ecg_signal(
        self, user_id: str, data: dict
    ) -> Optional[Dict[str, Any]]:
        """Creates an ECG signal record."""
        signal = await self.clinical_repo.create_ecg_signal(data)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={
                "signal_id": signal.get("id")
                if isinstance(signal, dict)
                else getattr(signal, "id", None),
                "action": "create_signal",
            },
        )
        return signal

    async def run_ecg_analysis(
        self, user_id: str, signal_id: str
    ) -> Optional[Dict[str, Any]]:
        """Orchestrates ECG analysis: Creates result, calls AI, updates result."""
        # 1. Fetch signal data
        signal = await self.clinical_repo.get_ecg_signal(signal_id)
        if not signal:
            raise Exception("ECG Signal not found")

        # 2. Call AI Service (Isolated logic)
        analysis = await self.ai_service.analyze_ecg(signal.get("signal_data", {}))

        # 3. Persist Result
        result_data = {
            "signal_id": signal_id,
            "patient_id": signal["patient_id"],
            "case_id": signal.get("case_id"),
            "rhythm_classification": analysis.get("prediction"),
            "rhythm_confidence": analysis.get("confidence"),
            "ai_interpretation": analysis.get("ai_notes"),
            "analysis_status": "completed",
            "performed_by": user_id,
        }

        saved_result = await self.clinical_repo.create_ecg_result(result_data)

        log_audit(
            AuditAction.ANALYZE_IMAGE,
            user_id=user_id,
            details={
                "result_id": saved_result.get("id")
                if isinstance(saved_result, dict)
                else getattr(saved_result, "id", None),
                "modality": "ECG",
            },
        )
        return saved_result

    # â”پâ”پâ”پâ”پ MRI DOMAIN â”پâ”پâ”پâ”پ

    async def create_mri_scan(
        self, user_id: str, data: dict
    ) -> Optional[Dict[str, Any]]:
        """Creates an MRI scan record."""
        scan = await self.clinical_repo.create_mri_scan(data)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={
                "scan_id": scan.get("id")
                if isinstance(scan, dict)
                else getattr(scan, "id", None),
                "action": "create_scan",
            },
        )
        return scan

    async def run_mri_analysis(
        self, user_id: str, scan_id: str
    ) -> Optional[Dict[str, Any]]:
        """Orchestrates MRI analysis: Fetches scan, calls AI, and persists result."""
        # 1. Fetch scan data
        scan = await self.clinical_repo.get_mri_scan(scan_id)
        if not scan:
            raise Exception("MRI Scan not found")

        # 2. Call AI Service
        analysis = await self.ai_service.analyze_mri(scan.get("dicom_metadata", {}))

        # 3. Persist Result
        result_data = {
            "scan_id": scan_id,
            "patient_id": scan["patient_id"],
            "case_id": scan.get("case_id"),
            "severity_score": analysis.get("severity_score"),
            "ai_interpretation": analysis.get("ai_notes"),
            "analysis_status": "completed",
            "performed_by": user_id,
        }

        saved_result = await self.clinical_repo.create_mri_result(result_data)

        log_audit(
            AuditAction.ANALYZE_IMAGE,
            user_id=user_id,
            details={
                "result_id": saved_result.get("id")
                if isinstance(saved_result, dict)
                else getattr(saved_result, "id", None),
                "modality": "MRI",
            },
        )
        return saved_result

    async def create_mri_result(
        self, user_id: str, data: dict
    ) -> Optional[Dict[str, Any]]:
        """Creates an MRI segmentation result record."""
        result = await self.clinical_repo.create_mri_result(data)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={
                "result_id": result.get("id")
                if isinstance(result, dict)
                else getattr(result, "id", None),
                "action": "create_mri_result",
            },
        )
        return result

    async def create_medical_file(
        self, user_id: str, file_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Creates a medical file record."""
        file_record = await self.clinical_repo.create_medical_file(file_data)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={
                "file_id": file_record.get("id")
                if isinstance(file_record, dict)
                else getattr(file_record, "id", None),
                "action": "create_file",
            },
        )
        return file_record

    async def get_medical_file(
        self, user_id: str, file_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get medical file by ID."""
        file_record = await self.clinical_repo.get_medical_file(file_id)
        if file_record:
            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={"file_id": file_id, "action": "view_file"},
            )
        return file_record

    async def delete_medical_file(
        self, user_id: str, file_id: str, reason: Optional[str] = None
    ) -> bool:
        """Delete a medical file."""
        success = await self.clinical_repo.delete_medical_file(file_id, user_id, reason)
        if success:
            log_audit(
                AuditAction.DELETE_MEDICAL_DATA,
                user_id=user_id,
                details={"file_id": file_id, "action": "delete_file", "reason": reason},
            )
        return success

    # â”پâ”پâ”پâ”پ ECG SIGNALS â”پâ”پâ”پâ”پ

    async def get_ecg_signal(
        self, user_id: str, signal_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get ECG signal by ID."""
        signal = await self.clinical_repo.get_ecg_signal(signal_id)
        if signal:
            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={"signal_id": signal_id, "action": "view_signal"},
            )
        return signal

    async def list_ecg_signals(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List ECG signals with filtering."""
        signals = await self.clinical_repo.list_ecg_signals(filters, limit, offset)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={"action": "list_signals", "count": len(signals)},
        )
        return signals

    async def delete_ecg_signal(self, user_id: str, signal_id: str) -> bool:
        """Delete an ECG signal."""
        success = await self.clinical_repo.delete_ecg_signal(signal_id)
        if success:
            log_audit(
                AuditAction.DELETE_MEDICAL_DATA,
                user_id=user_id,
                details={"signal_id": signal_id, "action": "delete_signal"},
            )
        return success

    # â”پâ”پâ”پâ”پ MRI SCANS â”پâ”پâ”پâ”پ

    async def get_mri_scan(
        self, user_id: str, scan_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get MRI scan by ID."""
        scan = await self.clinical_repo.get_mri_scan(scan_id)
        if scan:
            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={"scan_id": scan_id, "action": "view_scan"},
            )
        return scan

    async def list_mri_scans(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List MRI scans with filtering."""
        scans = await self.clinical_repo.list_mri_scans(filters, limit, offset)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={"action": "list_scans", "count": len(scans)},
        )
        return scans

    async def delete_mri_scan(self, user_id: str, scan_id: str) -> bool:
        """Delete an MRI scan."""
        success = await self.clinical_repo.delete_mri_scan(scan_id)
        if success:
            log_audit(
                AuditAction.DELETE_MEDICAL_DATA,
                user_id=user_id,
                details={"scan_id": scan_id, "action": "delete_scan"},
            )
        return success

    async def get_mri_result(
        self, user_id: str, result_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get MRI result by ID."""
        result = await self.clinical_repo.get_mri_result(result_id)
        if result:
            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={"result_id": result_id, "action": "view_mri_result"},
            )
        return result

    async def list_mri_results(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List MRI results with filtering."""
        results = await self.clinical_repo.list_mri_results(filters, limit, offset)
        log_audit(
            AuditAction.ACCESS_MEDICAL_DATA,
            user_id=user_id,
            details={"action": "list_mri_results", "count": len(results)},
        )
        return results

    async def update_mri_result(
        self, user_id: str, result_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update MRI result (for review)."""
        result = await self.clinical_repo.update_mri_result(result_id, data)
        if result:
            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={"result_id": result_id, "action": "update_mri_result"},
            )
        return result

    async def delete_mri_result(self, user_id: str, result_id: str) -> bool:
        """Delete an MRI result."""
        success = await self.clinical_repo.delete_mri_result(result_id)
        if success:
            log_audit(
                AuditAction.DELETE_MEDICAL_DATA,
                user_id=user_id,
                details={"result_id": result_id, "action": "delete_mri_result"},
            )
        return success

    # â”پâ”پâ”پâ”پ REPORTS â”پâ”پâ”پâ”پ

    async def create_report(
        self, user_id: str, report_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Creates a generated report."""
        report = await self.clinical_repo.create_report(report_data)
        log_audit(
            AuditAction.REPORT_SIGN,
            user_id=user_id,
            details={
                "report_id": report.get("id")
                if isinstance(report, dict)
                else getattr(report, "id", None),
                "action": "create_report",
            },
        )
        return report

    async def get_report(
        self, user_id: str, report_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get report by ID."""
        report = await self.clinical_repo.get_report(report_id)
        if report:
            log_audit(
                AuditAction.ACCESS_MEDICAL_DATA,
                user_id=user_id,
                details={"report_id": report_id, "action": "view_report"},
            )
        return report

