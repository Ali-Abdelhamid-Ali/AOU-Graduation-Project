"""Real-Time Monitoring Middleware - FastAPI request/response monitoring with structured logging."""
import time
import uuid
import psutil
import threading
import os
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from datetime import UTC  # Python 3.11+
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.observability.logger import get_logger, set_correlation_id
from src.services.domain.execution_tracker import execution_manager

logger = get_logger("middleware.real_time_monitor")

class RealTimeMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Real-time monitoring middleware that captures request/response data
    with structured logging, performance metrics, and error categorization.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.process = psutil.Process()
        self._queue: list[Dict[str, Any]] = []
        self._queue_lock = threading.Lock()
        self._processing_thread = None
        self._start_queue_processor()
    
    def _start_queue_processor(self):
        """Start async queue processor for log persistence."""
        def process_queue():
            while True:
                try:
                    if self._queue:
                        with self._queue_lock:
                            batch = self._queue[:100]  # Process in batches
                            self._queue = self._queue[100:]
                        
                        if batch:
                            self._persist_batch(batch)
                    
                    time.sleep(0.05)  # Process every 50ms for better responsiveness
                except Exception as e:
                    logger.error(f"Queue processor error: {e}")
        
        self._processing_thread = threading.Thread(target=process_queue, daemon=True)
        self._processing_thread.start()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with monitoring."""
        start_time = time.time()
        correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get(
            "X-Correlation-ID", str(uuid.uuid4())
        )

        # Keep correlation context aligned with upstream middleware.
        set_correlation_id(correlation_id)
        
        # Start execution tracking
        execution_manager.start_execution(
            request_id=correlation_id,
            user_id=None  # Will be populated if user is authenticated
        )
        
        # Collect request data
        request_data = self._collect_request_data(request)
        
        # Process request
        response = None
        error_info = None
        caught_error = None
        
        try:
            response = await call_next(request)
            response = self._enhance_response(response, correlation_id)
            
        except Exception as e:
            caught_error = e
            error_info = self._categorize_error(e, request)
        
        finally:
            # Collect response data
            response_data = self._collect_response_data(response if response else Response(), error_info)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                start_time, request, response if response else Response(), error_info
            )
            
            # Create execution log entry
            log_entry = self._create_log_entry(
                correlation_id, request_data, response_data, 
                performance_metrics, error_info
            )
            
            # Queue for persistence (async)
            self._queue_log_entry(log_entry)
            
            # Output to terminal (synchronous for immediate feedback)
            self._output_to_terminal(log_entry)
            
            # End execution tracking
            execution_manager.end_execution(correlation_id)

        if caught_error is not None:
            raise caught_error

        return response
    
    def _collect_request_data(self, request: Request) -> Dict[str, Any]:
        """Collect structured request data."""
        headers = self._redact_headers(dict(request.headers))
        return {
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "headers": headers,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_length": request.headers.get("content-length"),
            "content_type": request.headers.get("content-type")
        }

    @staticmethod
    def _redact_headers(headers: Dict[str, Any]) -> Dict[str, Any]:
        sensitive = {
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "x-auth-token",
            "x-access-token",
            "proxy-authorization",
        }
        sanitized: Dict[str, Any] = {}
        for key, value in headers.items():
            sanitized[key] = "[REDACTED]" if key.lower() in sensitive else value
        return sanitized
    
    def _collect_response_data(self, response: Response, error_info: Optional[Dict]) -> Dict[str, Any]:
        """Collect structured response data."""
        if hasattr(response, 'status_code'):
            status_code = response.status_code
        elif isinstance(response, JSONResponse):
            status_code = response.status_code
        else:
            status_code = 200
        
        return {
            "status_code": status_code,
            "headers": dict(response.headers) if hasattr(response, 'headers') else {},
            "content_length": response.headers.get("content-length") if hasattr(response, 'headers') else None,
            "error": error_info
        }
    
    def _categorize_error(self, error: Exception, request: Request) -> Dict[str, Any]:
        """Categorize error by type, category, and priority."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Determine error category and priority
        if hasattr(error, 'status_code'):
            status_code = error.status_code
        else:
            status_code = 500
        
        category, priority = self._classify_error_by_status(status_code, error_type, error_message)
        
        return {
            "type": error_type,
            "message": error_message,
            "category": category,
            "priority": priority,
            "status_code": status_code,
            "stack_trace": self._get_stack_trace(error),
            "request_path": str(request.url.path),
            "request_method": request.method
        }
    
    def _classify_error_by_status(self, status_code: int, error_type: str, message: str) -> tuple:
        """Classify error by HTTP status code and type."""
        # Medical domain specific error patterns
        medical_patterns = {
            'patient': ['patient', 'medical record', 'clinical', 'diagnosis'],
            'authentication': ['auth', 'token', 'login', 'permission'],
            'validation': ['validation', 'required', 'invalid', 'format'],
            'database': ['database', 'sql', 'query', 'connection'],
            'network': ['network', 'timeout', 'dns', 'connection refused'],
            'file': ['file', 'upload', 'download', 'storage'],
            'clinical_workflow': ['workflow', 'process', 'step', 'sequence']
        }
        
        # Priority mapping
        priority_map = {
            'critical': ['500', '502', '503', '504', 'OutOfMemory', 'SystemExit'],
            'high': ['401', '403', 'timeout', 'ConnectionError'],
            'medium': ['400', '422', '429', 'ValidationError'],
            'low': ['404', '409', 'FileNotFoundError']
        }
        
        # Determine category based on status code and error type
        if 500 <= status_code < 600:
            category = 'server_error'
        elif 400 <= status_code < 500:
            if status_code == 401:
                category = 'authentication'
            elif status_code == 403:
                category = 'authorization'
            elif status_code == 422:
                category = 'validation'
            else:
                category = 'client_error'
        elif status_code < 400:
            category = 'success'
        else:
            category = 'unknown'
        
        # Check for medical domain patterns
        message_lower = message.lower()
        for med_category, patterns in medical_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                category = f"medical_{med_category}"
                break
        
        # Determine priority
        priority = 'low'  # Default
        for prio, indicators in priority_map.items():
            if (str(status_code) in indicators or 
                error_type in indicators or 
                any(indicator in message_lower for indicator in indicators)):
                priority = prio
                break
        
        return category, priority
    
    def _calculate_performance_metrics(self, start_time: float, request: Request, 
                                     response: Response, error_info: Optional[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Get current memory usage
        memory_info = self.process.memory_info()
        
        # Get CPU usage
        cpu_percent = self.process.cpu_percent()
        
        metrics = {
            "total_duration_ms": round(duration, 2),
            "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
            "cpu_percent": round(cpu_percent, 2),
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Add error-specific metrics
        if error_info:
            metrics["error_occurred"] = True
            metrics["error_category"] = error_info["category"]
            metrics["error_priority"] = error_info["priority"]
        else:
            metrics["error_occurred"] = False
        
        # Add response status metrics
        if hasattr(response, 'status_code'):
            status_code = response.status_code
            metrics["status_code"] = status_code
            metrics["success"] = 200 <= status_code < 400
        
        return metrics
    
    def _create_log_entry(self, correlation_id: str, request_data: Dict[str, Any], 
                         response_data: Dict[str, Any], performance_metrics: Dict[str, Any],
                         error_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create structured log entry."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "request": request_data,
            "response": response_data,
            "performance": performance_metrics,
            "execution_summary": self._get_execution_summary(correlation_id)
        }
        
        if error_info:
            log_entry["error"] = error_info
        
        return log_entry
    
    def _get_execution_summary(self, correlation_id: str) -> Dict[str, Any]:
        """Get execution summary from execution tracker."""
        try:
            # This would integrate with the existing execution tracker
            return {
                "operations_count": 0,
                "side_effects_count": 0,
                "database_queries_count": 0,
                "external_calls_count": 0,
                "violations": []
            }
        except Exception as e:
            logger.warning(f"Failed to get execution summary: {e}")
            return {}
    
    def _queue_log_entry(self, log_entry: Dict[str, Any]):
        """Queue log entry for async persistence."""
        with self._queue_lock:
            self._queue.append(log_entry)
    
    def _persist_batch(self, batch: list):
        """Persist batch of log entries to Supabase."""
        try:
            # Convert to format expected by Supabase
            supabase_data = []
            for entry in batch:
                supabase_data.append({
                    'correlation_id': entry['correlation_id'],
                    'timestamp': entry['timestamp'],
                    'request_method': entry['request']['method'],
                    'request_path': entry['request']['path'],
                    'status_code': entry['response']['status_code'],
                    'duration_ms': entry['performance']['total_duration_ms'],
                    'memory_usage_mb': entry['performance']['memory_usage_mb'],
                    'cpu_percent': entry['performance']['cpu_percent'],
                    'error_category': entry['performance'].get('error_category'),
                    'error_priority': entry['performance'].get('error_priority'),
                    'success': entry['performance']['success'],
                    'raw_data': entry  # Store full data as JSON
                })
            
            # Insert batch into Supabase (this would need to be implemented)
            # For now, we'll log the data
            logger.info(f"Persisting {len(supabase_data)} log entries")
            
        except Exception as e:
            logger.error(f"Failed to persist log batch: {e}")
    
    def _output_to_terminal(self, log_entry: Dict[str, Any]):
        """Output formatted log entry without ANSI color codes."""
        try:
            timestamp = log_entry['timestamp']
            correlation_id = log_entry['correlation_id']
            method = log_entry['request']['method']
            path = log_entry['request']['path']
            status_code = log_entry['response']['status_code']
            duration = log_entry['performance']['total_duration_ms']

            status_symbol = "[OK]" if log_entry["performance"]["success"] else "[FAIL]"
            output = (
                f"[{timestamp}][{status_symbol}] {method} {path} "
                f"(id: {correlation_id[:8]}) - {status_code} - {duration}ms"
            )
            logger.info(output)
            
        except Exception as e:
            logger.error(f"Failed to output to terminal: {e}")
    
    def _enhance_response(self, response: Response, correlation_id: str) -> Response:
        """Enhance response with correlation ID header."""
        if hasattr(response, 'headers'):
            response.headers['X-Correlation-ID'] = correlation_id
        return response
    
    async def _handle_error(self, request: Request, error: Exception, correlation_id: str) -> JSONResponse:
        """Handle errors with structured response."""
        safe_error_message = "An internal server error occurred"
        if os.getenv("ENVIRONMENT", "development").lower() == "development":
            safe_error_message = str(error)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": safe_error_message,
                "error_type": type(error).__name__,
                "correlation_id": correlation_id,
                "timestamp": datetime.now(UTC).isoformat()
            }
        )
    
    def _get_stack_trace(self, error: Exception) -> str:
        """Get formatted stack trace."""
        import traceback
        
        # Get the full traceback
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        stack_trace = ''.join(tb)
        
        # Limit stack trace length for performance
        if len(stack_trace) > 2000:
            stack_trace = stack_trace[:2000] + "\n... (truncated)"
        
        return stack_trace

