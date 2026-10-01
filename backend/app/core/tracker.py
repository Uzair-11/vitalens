import os
import sys
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.logging_config import get_request_id

logger = logging.getLogger("vitalens.errors")

class ErrorTracker:
    """
    Lightweight, production-grade error tracking and diagnostics engine.
    Supports local JSON telemetry and plug-and-play Sentry forwarding via SENTRY_DSN.
    """
    def __init__(self):
        self.sentry_enabled = False
        self._recent_errors: List[Dict[str, Any]] = []
        self._max_recent = 50

        # Check for optional Sentry DSN configuration
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastApiIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[FastApiIntegration(), SqlalchemyIntegration()],
                    traces_sample_rate=1.0,
                    environment=os.getenv("ENVIRONMENT", "development")
                )
                self.sentry_enabled = True
                logger.info("Sentry error tracking integration initialized.")
            except ImportError:
                logger.warning("SENTRY_DSN is configured but 'sentry-sdk' is not installed. Operating in structured log mode.")

    def capture_exception(
        self,
        exc: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Captures an exception, records structured context, formats stack trace,
        and logs with correlated request_id.
        """
        req_id = get_request_id()
        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        error_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": req_id,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
            "user_id": user_id,
            "path": path,
            "context": context or {},
            "traceback": tb_str
        }

        # Store in circular diagnostic buffer
        self._recent_errors.append(error_event)
        if len(self._recent_errors) > self._max_recent:
            self._recent_errors.pop(0)

        # Log structured error
        logger.error(
            f"Exception captured: {exc.__class__.__name__}: {str(exc)} [Request: {req_id}]",
            exc_info=exc,
            extra={"extra_data": error_event}
        )

        # Forward to Sentry if active
        if self.sentry_enabled:
            try:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    scope.set_tag("request_id", req_id)
                    if user_id:
                        scope.user = {"id": user_id}
                    if path:
                        scope.set_tag("path", path)
                    if context:
                        for k, v in context.items():
                            scope.set_extra(k, v)
                    sentry_sdk.capture_exception(exc)
            except Exception as e:
                logger.warning(f"Failed to forward exception to Sentry: {e}")

        return error_event

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns the most recent captured error events for diagnostic inspection."""
        return self._recent_errors[-limit:]

    def clear_recent_errors(self) -> None:
        """Clears recent errors."""
        self._recent_errors.clear()

error_tracker = ErrorTracker()
