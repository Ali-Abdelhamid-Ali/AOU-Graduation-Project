"""Execution Tracker - Ensures One Operation = One Execution = One Side Effect."""

from typing import Optional, Dict, Any, List, Set
from src.observability.logger import get_logger
from src.security.auth_middleware import get_correlation_id
import time
import threading
from contextvars import ContextVar

logger = get_logger("service.execution_tracker")


class ExecutionContext:
    """
    Tracks execution context for a single request.
    Ensures: one logical operation = exactly one execution = exactly one side effect.
    """

    def __init__(self, request_id: str, user_id: Optional[str] = None):
        self.request_id = request_id
        self.user_id = user_id
        self.start_time = time.time()
        self.operations: List[Dict[str, Any]] = []
        self.side_effects: List[Dict[str, Any]] = []
        self.database_queries: List[Dict[str, Any]] = []
        self.external_calls: List[Dict[str, Any]] = []
        self.permissions_checked: Set[str] = set()
        self.lock = threading.Lock()

    def record_operation(
        self,
        operation_type: str,
        operation_id: str,
        details: Dict[str, Any | None] | None = None,
    ):
        """Record a logical operation."""
        with self.lock:
            operation = {
                "type": operation_type,
                "id": operation_id,
                "details": details or {},
                "timestamp": time.time(),
                "correlation_id": get_correlation_id(),
            }
            self.operations.append(operation)
            logger.debug(f"Operation recorded: {operation_type} - {operation_id}")

    def record_side_effect(
        self,
        effect_type: str,
        resource: str,
        details: Dict[str, Any | None] | None = None,
    ):
        """Record a side effect."""
        with self.lock:
            # Check for duplicate side effects
            duplicate = any(
                se["type"] == effect_type
                and se["resource"] == resource
                and abs(se["timestamp"] - time.time()) < 1.0  # Within 1 second
                for se in self.side_effects
            )

            if duplicate:
                logger.warning(
                    f"Duplicate side effect detected: {effect_type} on {resource}"
                )
                return False

            side_effect = {
                "type": effect_type,
                "resource": resource,
                "details": details or {},
                "timestamp": time.time(),
                "correlation_id": get_correlation_id(),
            }
            self.side_effects.append(side_effect)
            logger.debug(f"Side effect recorded: {effect_type} on {resource}")
            return True

    def record_database_query(
        self, table: str, query_type: str, filters: Dict[str, Any | None] | None = None
    ):
        """Record a database query."""
        with self.lock:
            query = {
                "table": table,
                "type": query_type,
                "filters": filters or {},
                "timestamp": time.time(),
                "correlation_id": get_correlation_id(),
            }
            self.database_queries.append(query)

            # Check for duplicate queries
            duplicate_count = sum(
                1
                for q in self.database_queries
                if q["table"] == table
                and q["type"] == query_type
                and q["filters"] == filters
                and abs(q["timestamp"] - query["timestamp"]) < 0.1
            )  # Within 100ms

            if duplicate_count > 1:
                logger.warning(
                    f"Duplicate database query detected: {query_type} on {table}"
                )

            logger.debug(f"Database query recorded: {query_type} on {table}")

    def record_external_call(
        self, service: str, endpoint: str, details: Dict[str, Any | None] | None = None
    ):
        """Record an external service call."""
        with self.lock:
            external_call = {
                "service": service,
                "endpoint": endpoint,
                "details": details or {},
                "timestamp": time.time(),
                "correlation_id": get_correlation_id(),
            }
            self.external_calls.append(external_call)

            # Check for duplicate external calls
            duplicate_count = sum(
                1
                for call in self.external_calls
                if call["service"] == service
                and call["endpoint"] == endpoint
                and abs(call["timestamp"] - external_call["timestamp"]) < 1.0
            )

            if duplicate_count > 1:
                logger.warning(
                    f"Duplicate external call detected: {service} - {endpoint}"
                )

            logger.debug(f"External call recorded: {service} - {endpoint}")

    def record_permission_check(self, permission: str):
        """Record a permission check."""
        with self.lock:
            self.permissions_checked.add(permission)
            logger.debug(f"Permission check recorded: {permission}")

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary for the request."""
        with self.lock:
            duration = time.time() - self.start_time

            summary = {
                "request_id": self.request_id,
                "user_id": self.user_id,
                "duration_seconds": duration,
                "operation_count": len(self.operations),
                "side_effect_count": len(self.side_effects),
                "database_query_count": len(self.database_queries),
                "external_call_count": len(self.external_calls),
                "permission_checks": list(self.permissions_checked),
                "operations": self.operations,
                "side_effects": self.side_effects,
                "database_queries": self.database_queries,
                "external_calls": self.external_calls,
                "correlation_id": get_correlation_id(),
            }

            # Check for violations
            violations = []

            # Check for multiple side effects of same type
            side_effect_types = {}
            for se in self.side_effects:
                key = f"{se['type']}:{se['resource']}"
                if key in side_effect_types:
                    violations.append(
                        f"Multiple side effects of type {se['type']} on resource {se['resource']}"
                    )
                side_effect_types[key] = True

            # Check for duplicate database queries
            query_signatures = {}
            for q in self.database_queries:
                key = f"{q['table']}:{q['type']}:{str(q['filters'])}"
                if key in query_signatures:
                    violations.append(
                        f"Duplicate database query: {q['type']} on {q['table']}"
                    )
                query_signatures[key] = True

            # Check for duplicate external calls
            call_signatures = {}
            for call in self.external_calls:
                key = f"{call['service']}:{call['endpoint']}"
                if key in call_signatures:
                    violations.append(
                        f"Duplicate external call: {call['service']} - {call['endpoint']}"
                    )
                call_signatures[key] = True

            summary["violations"] = violations
            summary["execution_valid"] = len(violations) == 0

            return summary

    def validate_execution_purity(self) -> bool:
        """Validate that execution follows purity principles."""
        summary = self.get_execution_summary()
        return summary["execution_valid"]


class RequestExecutionManager:
    """
    Manages execution context for requests.
    Ensures execution determinism and tracks all operations.
    """

    def __init__(self):
        self._execution_contexts: ContextVar[Optional[ExecutionContext]] = ContextVar(
            "execution_context", default=None
        )
        self._active_requests: Dict[str, ExecutionContext] = {}
        self._lock = threading.Lock()

    def start_execution(
        self, request_id: str, user_id: Optional[str] = None
    ) -> ExecutionContext:
        """Start execution tracking for a request."""
        with self._lock:
            context = ExecutionContext(request_id, user_id)
            self._execution_contexts.set(context)
            self._active_requests[request_id] = context
            logger.info(f"Execution started for request: {request_id}")
            return context

    def get_execution_context(self) -> Optional[ExecutionContext]:
        """Get current execution context."""
        return self._execution_contexts.get()

    def end_execution(self, request_id: str) -> Dict[str, Any]:
        """End execution tracking and return summary."""
        with self._lock:
            context = self._active_requests.pop(request_id, None)
            if context:
                summary = context.get_execution_summary()
                logger.info(
                    f"Execution ended for request: {request_id} - Valid: {summary['execution_valid']}"
                )

                # Log violations if any
                if summary["violations"]:
                    logger.error(
                        f"Execution violations for request {request_id}: {summary['violations']}"
                    )

                return summary
            else:
                logger.warning(f"No execution context found for request: {request_id}")
                return {"request_id": request_id, "error": "No execution context found"}

    def record_operation(
        self,
        operation_type: str,
        operation_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Record an operation in current execution context."""
        context = self.get_execution_context()
        if context:
            context.record_operation(operation_type, operation_id, details)

    def record_side_effect(
        self,
        effect_type: str,
        resource: str,
        details: Dict[str, Any | None] | None = None,
    ) -> bool:
        """Record a side effect in current execution context."""
        context = self.get_execution_context()
        if context:
            return context.record_side_effect(effect_type, resource, details)
        return False

    def record_database_query(
        self, table: str, query_type: str, filters: Dict[str, Any | None] | None = None
    ):
        """Record a database query in current execution context."""
        context = self.get_execution_context()
        if context:
            context.record_database_query(table, query_type, filters)

    def record_external_call(
        self, service: str, endpoint: str, details: Dict[str, Any | None] | None = None
    ):
        """Record an external call in current execution context."""
        context = self.get_execution_context()
        if context:
            context.record_external_call(service, endpoint, details)

    def record_permission_check(self, permission: str):
        """Record a permission check in current execution context."""
        context = self.get_execution_context()
        if context:
            context.record_permission_check(permission)

    def validate_current_execution(self) -> bool:
        """Validate current execution context."""
        context = self.get_execution_context()
        if context:
            return context.validate_execution_purity()
        return True  # No context means no violations


# Global execution manager
execution_manager = RequestExecutionManager()


