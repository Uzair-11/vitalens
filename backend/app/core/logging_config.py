import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

def get_request_id() -> str:
    """Returns the current request correlation ID from contextvars."""
    req_id = request_id_ctx.get()
    return req_id if req_id else "system"

def set_request_id(req_id: str) -> None:
    """Sets the request correlation ID for the active async execution context."""
    request_id_ctx.set(req_id)

class StructuredJsonFormatter(logging.Formatter):
    """
    Standard JSON log formatter that includes request correlation IDs and ISO-8601 timestamps.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include structured extra fields if provided
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj["data"] = record.extra_data

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that generates or extracts X-Request-ID, binds it to contextvars,
    captures unhandled exceptions, and attaches X-Request-ID to the HTTP response headers.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        set_request_id(req_id)
        
        try:
            response = await call_next(request)
        except Exception as exc:
            from app.core.errors import unhandled_exception_handler
            response = await unhandled_exception_handler(request, exc)

        response.headers["X-Request-ID"] = req_id
        return response

def setup_structured_logging(log_level: str = "INFO"):
    """Configures root logger with JSON formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)

    # Quieten overly verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
