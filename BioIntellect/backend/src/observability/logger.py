import json
import logging
import os
import uuid
from contextvars import ContextVar
from typing import Any

correlation_id_ctx: ContextVar[str] = ContextVar(
    "correlation_id", default=str(uuid.uuid4())
)


class RedactionFilter(logging.Filter):
    """Redacts common secrets from log records."""

    SECRET_PATTERNS = (
        "authorization",
        "token",
        "password",
        "secret",
        "api_key",
        "refresh_token",
        "access_token",
    )

    def _should_redact_key(self, key: str) -> bool:
        lowered = str(key).lower()
        return any(pattern in lowered for pattern in self.SECRET_PATTERNS)

    def _scrub_value(self, key: str, value: Any) -> Any:
        if self._should_redact_key(key):
            return "[REDACTED]"
        if isinstance(value, dict):
            return {
                nested_key: self._scrub_value(nested_key, nested_value)
                for nested_key, nested_value in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self._scrub_value(key, item) for item in value]
        return value

    def filter(self, record: logging.LogRecord) -> bool:
        message = str(record.getMessage())
        lowered = message.lower()
        if any(pattern in lowered for pattern in self.SECRET_PATTERNS):
            record.msg = "[REDACTED SENSITIVE LOG MESSAGE]"
            record.args = ()

        for key, value in list(record.__dict__.items()):
            if key.startswith("_"):
                continue
            if key not in {"msg", "message", "args"}:
                record.__dict__[key] = self._scrub_value(key, value)
        return True


class JsonFormatter(logging.Formatter):
    """Structured JSON formatter for production logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "correlation_id": correlation_id_ctx.get(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }

        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=True)


def setup_logging() -> None:
    """Configure root logger once."""
    root_logger = logging.getLogger()
    if getattr(root_logger, "_biointellect_configured", False):
        return
    root_logger.handlers.clear()

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    environment = os.getenv("ENVIRONMENT", "development").lower()
    use_json = environment == "production"

    root_logger.setLevel(level)
    redaction_filter = RedactionFilter()

    stream_handler = logging.StreamHandler()
    stream_handler.addFilter(redaction_filter)
    if use_json:
        stream_handler.setFormatter(JsonFormatter())
    else:
        stream_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    root_logger.addHandler(stream_handler)

    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(
        os.path.join(log_dir, "app.log"), mode="a", encoding="utf-8"
    )
    file_handler.addFilter(redaction_filter)
    if use_json:
        file_handler.setFormatter(JsonFormatter())
    else:
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    root_logger.addHandler(file_handler)

    # Let framework loggers propagate to root handlers to avoid duplicated lines.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        framework_logger = logging.getLogger(logger_name)
        framework_logger.handlers.clear()
        framework_logger.propagate = True
        framework_logger.setLevel(level)

    setattr(root_logger, "_biointellect_configured", True)


def get_logger(name: str) -> logging.Logger:
    """Return named logger."""
    return logging.getLogger(name)


def set_correlation_id(cid: str | None) -> None:
    """Set/generate correlation id for current context."""
    correlation_id_ctx.set(cid or str(uuid.uuid4()))


def get_correlation_id() -> str:
    """Retrieve current correlation id."""
    return correlation_id_ctx.get()
