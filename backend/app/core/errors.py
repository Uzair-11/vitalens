from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging_config import get_request_id
from app.core.tracker import error_tracker

async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats HTTPException into standard VitaLens error envelope with request_id correlation."""
    req_id = get_request_id()
    if exc.status_code >= 500:
        error_tracker.capture_exception(exc, path=str(request.url.path))
    
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": msg,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": msg,
                "path": str(request.url.path),
                "request_id": req_id
            }
        },
        headers=getattr(exc, "headers", None)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic validation errors into standard VitaLens error envelope with request_id."""
    req_id = get_request_id()
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = f"{first_error.get('loc', ['field'])[-1]}: {first_error.get('msg', 'Validation error')}"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": msg,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": msg,
                "details": exc.errors(),
                "path": str(request.url.path),
                "request_id": req_id
            }
        }
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catches unhandled server exceptions, logs to error tracker with trace, and returns safe envelope."""
    req_id = get_request_id()
    error_tracker.capture_exception(exc, path=str(request.url.path))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "path": str(request.url.path),
                "request_id": req_id
            }
        }
    )
