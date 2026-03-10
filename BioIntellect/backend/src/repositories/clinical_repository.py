from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import (
    build_follow_up_appointment,
    build_mri_result_payload,
    normalize_ecg_result_record,
    normalize_mri_result_record,
    sanitize_for_table,
)
from src.services.infrastructure.memory_cache import global_cache
from src.services.infrastructure.retry_utils import async_retry

logger = get_logger("repository.clinical")


class ClinicalRepository:
    def __init__(self):
        # Cache instance for aggregation queries
        self.cache = global_cache
        # Request-scoped cache placeholder
        self._cached_repo = None

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    async def _get_hospital_case_ids(self, hospital_id: str) -> List[str]:
        client = await self._get_client()
        result = await (
            client.table("medical_cases")
            .select("id")
            .eq("hospital_id", hospital_id)
            .execute()
        )
        return [row["id"] for row in (result.data or []) if row.get("id")]

    async def _list_follow_up_appointments(
        self, filter_field: str, filter_value: str
    ) -> List[Dict[str, Any]]:
        client = await self._get_client()
        result = await (
            client.table("medical_cases")
            .select(
                "id, patient_id, assigned_doctor_id, follow_up_date, status, notes, chief_complaint, metadata"
            )
            .eq(filter_field, filter_value)
            .not_.is_("follow_up_date", "null")
            .order("follow_up_date", desc=False)
            .execute()
        )
        appointments: List[Dict[str, Any]] = []
        for case_record in result.data or []:
            appointment = build_follow_up_appointment(case_record)
            if appointment:
                appointments.append(appointment)
        return appointments

    # â”پâ”پâ”پâ”پ MEDICAL CASES â”پâ”پâ”پâ”پ

    @async_retry(max_retries=3)
    async def create_medical_case(
        self, case_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new medical case."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("medical_cases", case_data)
            result = await client.table("medical_cases").insert(payload).execute()
            if result.data:
                # Section 5.A: Invalidate related caches on write
                await self.cache.delete("clinical:cases_by_status")
                await self.cache.delete("clinical:case_trend")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create medical case: {str(e)}")
            raise

    async def get_medical_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get medical case by ID with related data."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("*")
                .eq("id", case_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get medical case {case_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_medical_case(
        self, case_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update medical case."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("medical_cases", data)
            result = await (
                client.table("medical_cases").update(payload).eq("id", case_id).execute()
            )
            if result.data:
                # Section 5.A: Invalidate related caches on write
                await self.cache.delete("clinical:cases_by_status")
                await self.cache.delete("clinical:case_trend")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update medical case {case_id}: {str(e)}")
            raise

    async def list_medical_cases(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List medical cases with filtering and optimized selection."""
        client = await self._get_client()
        try:
            query = client.table("medical_cases").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list medical cases: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_medical_case(self, case_id: str) -> bool:
        """Delete a medical case."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases").delete().eq("id", case_id).execute()
            )
            if len(result.data) > 0:
                # Section 5.A: Invalidate related caches on write
                await self.cache.delete("clinical:cases_by_status")
                await self.cache.delete("clinical:case_trend")
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete medical case {case_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def archive_medical_case(
        self, case_id: str, archived_by: str, reason: Optional[str] = None
    ) -> bool:
        """Archive a medical case."""
        client = await self._get_client()
        try:
            data = {
                "is_archived": True,
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "archived_by": archived_by,
            }
            if reason:
                data["notes"] = reason

            result = await (
                client.table("medical_cases").update(data).eq("id", case_id).execute()
            )
            if len(result.data) > 0:
                # Section 5.A: Invalidate related caches on write
                await self.cache.delete("clinical:cases_by_status")
                await self.cache.delete("clinical:case_trend")
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to archive medical case {case_id}: {str(e)}")
            raise

    async def count_medical_cases(self) -> int:
        """Count all medical cases."""
        client = await self._get_client()
        try:
            # execute(count="exact") is how supabase-py handles count
            # But the return type from execute() contains count
            result = await (
                client.table("medical_cases").select("id", count="exact").execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to count medical cases: {str(e)}")
            return 0

    async def count_medical_files(self) -> int:
        """Count all medical files."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_files")
                .select("id", count="exact")
                .eq("is_deleted", False)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to count medical files: {str(e)}")
            return 0

    async def get_cases_by_status(self) -> Dict[str, int]:
        """Get cases count grouped by status."""
        cache_key = "clinical:cases_by_status"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        client = await self._get_client()
        try:
            # PostgREST doesn't support group by directly, so we fetch and aggregate
            # Optimization: Select only status column
            result = await client.table("medical_cases").select("status").execute()
            counts: dict[str, int] = {}
            for row in result.data:
                status = row.get("status", "unknown")
                counts[status] = counts.get(status, 0) + 1

            await self.cache.set(cache_key, counts, ttl_seconds=300)
            return counts
        except Exception as e:
            logger.error(f"Failed to get cases by status: {str(e)}")
            return {}

    async def get_files_by_type(self) -> Dict[str, int]:
        """Get files count grouped by type."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_files")
                .select("file_type")
                .eq("is_deleted", False)
                .execute()
            )
            counts: dict[str, int] = {}
            for row in result.data:
                ftype = row.get("file_type", "unknown")
                counts[ftype] = counts.get(ftype, 0) + 1
            return counts
        except Exception as e:
            logger.error(f"Failed to get files by type: {str(e)}")
            return {}

    async def get_case_trend(self) -> List[Dict[str, Any]]:
        """Get case creation trend over time."""
        cache_key = "clinical:case_trend"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        client = await self._get_client()
        try:
            # Simplified trend returning counts by month
            result = await client.table("medical_cases").select("created_at").execute()
            trend: dict[str, int] = {}
            for row in result.data:
                month = row["created_at"][:7]  # YYYY-MM
                trend[month] = trend.get(month, 0) + 1

            trend_list = [{"month": m, "count": c} for m, c in sorted(trend.items())]
            await self.cache.set(
                cache_key, trend_list, ttl_seconds=3600
            )  # 1 hour cache
            return trend_list
        except Exception as e:
            logger.error(f"Failed to get case trend: {str(e)}")
            return []

    async def count_hospital_cases(self, hospital_id: str) -> int:
        """Count cases for a hospital."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to count hospital cases: {str(e)}")
            return 0

    async def count_hospital_files(self, hospital_id: str) -> int:
        """Count files for a hospital."""
        client = await self._get_client()
        try:
            case_ids = await self._get_hospital_case_ids(hospital_id)
            if not case_ids:
                return 0
            result = await (
                client.table("medical_files")
                .select("id", count="exact")
                .in_("case_id", case_ids)
                .eq("is_deleted", False)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to count hospital files: {str(e)}")
            return 0

    async def get_hospital_cases_by_status(self, hospital_id: str) -> Dict[str, int]:
        """Get hospital cases grouped by status."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("status")
                .eq("hospital_id", hospital_id)
                .execute()
            )
            counts: dict[str, int] = {}
            for row in result.data:
                status = row.get("status", "unknown")
                counts[status] = counts.get(status, 0) + 1
            return counts
        except Exception as e:
            logger.error(f"Failed to get hospital cases by status: {str(e)}")
            return {}

    async def get_hospital_files_by_type(self, hospital_id: str) -> Dict[str, int]:
        """Get hospital files grouped by type."""
        client = await self._get_client()
        try:
            case_ids = await self._get_hospital_case_ids(hospital_id)
            if not case_ids:
                return {}
            result = await (
                client.table("medical_files")
                .select("file_type")
                .in_("case_id", case_ids)
                .eq("is_deleted", False)
                .execute()
            )
            counts: dict[str, int] = {}
            for row in result.data:
                ftype = row.get("file_type", "unknown")
                counts[ftype] = counts.get(ftype, 0) + 1
            return counts
        except Exception as e:
            logger.error(f"Failed to get hospital files by type: {str(e)}")
            return {}

    async def get_hospital_case_trend(self, hospital_id: str) -> List[Dict[str, Any]]:
        """Get hospital case trend."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("created_at")
                .eq("hospital_id", hospital_id)
                .execute()
            )
            trend: dict[str, int] = {}
            for row in result.data:
                month = row["created_at"][:7]
                trend[month] = trend.get(month, 0) + 1
            return [{"month": m, "count": c} for m, c in sorted(trend.items())]
        except Exception as e:
            logger.error(f"Failed to get hospital case trend: {str(e)}")
            return []

    async def get_doctor_patients(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Get unique patients for a doctor."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("patient_id")
                .eq("assigned_doctor_id", doctor_id)
                .execute()
            )
            patient_ids = list(
                {
                    row["patient_id"]
                    for row in (result.data or [])
                    if row.get("patient_id")
                }
            )
            if not patient_ids:
                return []
            patients_result = await (
                client.table("patients")
                .select("id, mrn, first_name, last_name")
                .in_("id", patient_ids)
                .execute()
            )
            return patients_result.data or []
        except Exception as e:
            logger.error(f"Failed to get doctor patients: {str(e)}")
            return []

    async def get_doctor_cases(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Get cases for a doctor."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("*")
                .eq("assigned_doctor_id", doctor_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get doctor cases: {str(e)}")
            return []

    async def get_doctor_appointments(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Get appointments for a doctor."""
        try:
            return await self._list_follow_up_appointments(
                "assigned_doctor_id", doctor_id
            )
        except Exception as e:
            logger.error(f"Failed to get doctor appointments: {str(e)}")
            return []

    async def get_doctor_cases_by_status(self, doctor_id: str) -> Dict[str, int]:
        """Get doctor cases by status."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("status")
                .eq("assigned_doctor_id", doctor_id)
                .execute()
            )
            counts: dict[str, int] = {}
            for row in result.data:
                status = row.get("status", "unknown")
                counts[status] = counts.get(status, 0) + 1
            return counts
        except Exception as e:
            logger.error(f"Failed to get doctor cases by status: {str(e)}")
            return {}

    async def get_patient_cases(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get cases for a patient."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get patient cases: {str(e)}")
            return []

    async def get_patient_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get appointments for a patient."""
        try:
            return await self._list_follow_up_appointments("patient_id", patient_id)
        except Exception as e:
            logger.error(f"Failed to get patient appointments: {str(e)}")
            return []

    async def get_patient_files(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get files for a patient."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_files")
                .select(
                    "id, case_id, patient_id, uploaded_by, file_type, file_name, file_path, file_size, mime_type, storage_bucket, description, metadata, is_analyzed, analyzed_at, is_deleted, deleted_at, deleted_by, created_at, updated_at"
                )
                .eq("patient_id", patient_id)
                .eq("is_deleted", False)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get patient files: {str(e)}")
            return []

    async def get_patient_cases_by_status(self, patient_id: str) -> Dict[str, int]:
        """Get patient cases by status."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("status")
                .eq("patient_id", patient_id)
                .execute()
            )
            counts: dict[str, int] = {}
            for row in result.data:
                status = row.get("status", "unknown")
                counts[status] = counts.get(status, 0) + 1
            return counts
        except Exception as e:
            logger.error(f"Failed to get patient cases by status: {str(e)}")
            return {}

    async def get_patient_files_by_type(self, patient_id: str) -> Dict[str, int]:
        """Get patient files by type."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_files")
                .select("file_type")
                .eq("patient_id", patient_id)
                .eq("is_deleted", False)
                .execute()
            )
            counts: dict[str, int] = {}
            for row in result.data:
                ftype = row.get("file_type", "unknown")
                counts[ftype] = counts.get(ftype, 0) + 1
            return counts
        except Exception as e:
            logger.error(f"Failed to get patient files by type: {str(e)}")
            return {}

    # â”پâ”پâ”پâ”پ MEDICAL FILES â”پâ”پâ”پâ”پ

    @async_retry(max_retries=3)
    async def create_medical_file(
        self, file_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a medical file record."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("medical_files", file_data)
            result = await client.table("medical_files").insert(payload).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create medical file: {str(e)}")
            raise

    async def get_medical_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get medical file by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_files")
                .select("*")
                .eq("id", file_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get medical file {file_id}: {str(e)}")
            raise

    async def list_medical_files(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List medical files with filtering."""
        client = await self._get_client()
        try:
            query = client.table("medical_files").select("*").eq("is_deleted", False)

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list medical files: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_medical_file(
        self, file_id: str, file_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update medical file."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("medical_files", file_data)
            result = await (
                client.table("medical_files")
                .update(payload)
                .eq("id", file_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update medical file {file_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_medical_file(
        self, file_id: str, deleted_by: str, reason: Optional[str] = None
    ) -> bool:
        """Delete a medical file."""
        client = await self._get_client()
        try:
            data = {
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "deleted_by": deleted_by,
            }
            if reason:
                data["notes"] = reason
            payload = sanitize_for_table("medical_files", data)

            result = await (
                client.table("medical_files")
                .update(payload)
                .eq("id", file_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete medical file {file_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ ECG SIGNALS â”پâ”پâ”پâ”پ

    @async_retry(max_retries=3)
    async def create_ecg_signal(
        self, signal_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create ECG signal record."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("ecg_signals", signal_data)
            result = await client.table("ecg_signals").insert(payload).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create ECG signal: {str(e)}")
            raise

    async def get_ecg_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get ECG signal by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("ecg_signals")
                .select("*")
                .eq("id", signal_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get ECG signal {signal_id}: {str(e)}")
            raise

    async def list_ecg_signals(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List ECG signals with filtering."""
        client = await self._get_client()
        try:
            query = client.table("ecg_signals").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list ECG signals: {str(e)}")
            raise

    async def delete_ecg_signal(self, signal_id: str) -> bool:
        """Delete ECG signal."""
        client = await self._get_client()
        try:
            result = await (
                client.table("ecg_signals").delete().eq("id", signal_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete ECG signal {signal_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ ECG RESULTS â”پâ”پâ”پâ”پ

    @async_retry(max_retries=3)
    async def create_ecg_result(
        self, result_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create ECG analysis result."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("ecg_results", result_data)
            result = await client.table("ecg_results").insert(payload).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create ECG result: {str(e)}")
            raise

    async def get_ecg_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get ECG result by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("ecg_results")
                .select("*")
                .eq("id", result_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get ECG result {result_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_ecg_result(
        self, result_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update ECG result (for review)."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("ecg_results", data)
            result = await (
                client.table("ecg_results")
                .update(payload)
                .eq("id", result_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update ECG result {result_id}: {str(e)}")
            raise

    async def list_ecg_results(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List ECG results with filtering."""
        client = await self._get_client()
        try:
            query = client.table("ecg_results").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list ECG results: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_ecg_result(self, result_id: str) -> bool:
        """Delete ECG result."""
        client = await self._get_client()
        try:
            result = await (
                client.table("ecg_results").delete().eq("id", result_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete ECG result {result_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ MRI SCANS â”پâ”پâ”پâ”پ

    @async_retry(max_retries=3)
    async def create_mri_scan(
        self, scan_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create MRI scan record."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("mri_scans", scan_data)
            result = await client.table("mri_scans").insert(payload).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create MRI scan: {str(e)}")
            raise

    async def get_mri_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get MRI scan by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("mri_scans")
                .select("*")
                .eq("id", scan_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get MRI scan {scan_id}: {str(e)}")
            raise

    async def list_mri_scans(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List MRI scans with filtering."""
        client = await self._get_client()
        try:
            query = client.table("mri_scans").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list MRI scans: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_mri_scan(self, scan_id: str) -> bool:
        """Delete MRI scan."""
        client = await self._get_client()
        try:
            result = (
                await client.table("mri_scans").delete().eq("id", scan_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete MRI scan {scan_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ MRI SEGMENTATION RESULTS â”پâ”پâ”پâ”پ

    async def create_mri_result(
        self, result_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create MRI segmentation result."""
        client = await self._get_client()
        try:
            payload = build_mri_result_payload(result_data)
            result = await (
                client.table("mri_segmentation_results").insert(payload).execute()
            )
            return (
                normalize_mri_result_record(result.data[0]) if result.data else None
            )
        except Exception as e:
            logger.error(f"Failed to create MRI result: {str(e)}")
            raise

    async def get_mri_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get MRI result by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("mri_segmentation_results")
                .select("*")
                .eq("id", result_id)
                .single()
                .execute()
            )
            return normalize_mri_result_record(result.data)
        except Exception as e:
            logger.error(f"Failed to get MRI result {result_id}: {str(e)}")
            raise

    async def update_mri_result(
        self, result_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update MRI result (for review)."""
        client = await self._get_client()
        try:
            payload = build_mri_result_payload(data)
            result = await (
                client.table("mri_segmentation_results")
                .update(payload)
                .eq("id", result_id)
                .execute()
            )
            return (
                normalize_mri_result_record(result.data[0]) if result.data else None
            )
        except Exception as e:
            logger.error(f"Failed to update MRI result {result_id}: {str(e)}")
            raise

    async def list_mri_results(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List MRI results with filtering."""
        client = await self._get_client()
        try:
            query = client.table("mri_segmentation_results").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return [
                normalize_mri_result_record(record) for record in (result.data or [])
            ]
        except Exception as e:
            logger.error(f"Failed to list MRI results: {str(e)}")
            raise

    async def delete_mri_result(self, result_id: str) -> bool:
        """Delete MRI result."""
        client = await self._get_client()
        try:
            result = await (
                client.table("mri_segmentation_results")
                .delete()
                .eq("id", result_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete MRI result {result_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ GENERATED REPORTS â”پâ”پâ”پâ”پ

    async def create_report(
        self, report_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a generated report."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("generated_reports", report_data)
            result = await client.table("generated_reports").insert(payload).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create report: {str(e)}")
            raise

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("generated_reports")
                .select("*")
                .eq("id", report_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {str(e)}")
            raise

    async def update_report(
        self, report_id: str, report_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update report."""
        client = await self._get_client()
        try:
            payload = sanitize_for_table("generated_reports", report_data)
            result = await (
                client.table("generated_reports")
                .update(payload)
                .eq("id", report_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {str(e)}")
            raise

    async def list_reports(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List reports with filtering."""
        client = await self._get_client()
        try:
            query = client.table("generated_reports").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list reports: {str(e)}")
            raise

    async def approve_report(
        self,
        report_id: str,
        approved_by_doctor_id: str,
        approval_notes: Optional[str] = None,
    ) -> bool:
        """Approve a report."""
        client = await self._get_client()
        try:
            data = {
                "status": "approved",
                "approved_by_doctor_id": approved_by_doctor_id,
                "approved_at": datetime.now(timezone.utc).isoformat(),
            }
            if approval_notes:
                data["approval_notes"] = approval_notes

            result = await (
                client.table("generated_reports")
                .update(data)
                .eq("id", report_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to approve report {report_id}: {str(e)}")
            raise

    async def delete_report(self, report_id: str) -> bool:
        """Delete a report."""
        client = await self._get_client()
        try:
            result = await (
                client.table("generated_reports").delete().eq("id", report_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ PATIENT HISTORY â”پâ”پâ”پâ”پ

    async def get_patient_history(self, patient_id: str) -> Dict[str, Any]:
        """Get complete patient medical history in parallel (Performance Optimized)."""
        import asyncio

        client = await self._get_client()
        try:
            # Prepare independent queries
            t1 = (
                client.table("medical_cases")
                .select(
                    "id, case_number, status, priority, patient_id, hospital_id, assigned_doctor_id, created_at"
                )
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
            )

            t2 = (
                client.table("ecg_results")
                .select(
                    "id, rhythm_classification, rhythm_confidence, analysis_status, created_at"
                )
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .limit(10)
            )

            t3 = (
                client.table("mri_segmentation_results")
                .select(
                    "id, analysis_status, detected_abnormalities, measurements, severity_score, created_at"
                )
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .limit(10)
            )

            # Parallel Execution
            res_cases, res_ecg, res_mri = await asyncio.gather(
                t1.execute(), t2.execute(), t3.execute(), return_exceptions=True
            )

            # Error Handling helper
            def get_data(res, name):
                if isinstance(res, Exception):
                    logger.error(f"Failed to fetch {name}: {res}")
                    return []
                return res.data or []

            return {
                "cases": get_data(res_cases, "cases"),
                "ecg_results": [
                    normalize_ecg_result_record(record)
                    for record in get_data(res_ecg, "ecg_results")
                ],
                "mri_results": [
                    normalize_mri_result_record(record)
                    for record in get_data(res_mri, "mri_results")
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get patient history for {patient_id}: {str(e)}")
            raise

