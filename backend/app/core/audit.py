from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.core.logging_config import get_request_id

async def record_audit_log(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Persists an immutable audit log entry for regulatory compliance and security tracking.
    Automatically correlates with active request_id.
    """
    meta = metadata.copy() if metadata else {}
    if "request_id" not in meta:
        meta["request_id"] = get_request_id()

    log_entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=meta,
        ip_address=ip_address
    )
    db.add(log_entry)
    await db.commit()
    return log_entry
