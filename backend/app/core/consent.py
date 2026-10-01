from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.consent import Consent

async def verify_user_consent(db: AsyncSession, user_id: str, consent_type: str) -> bool:
    """
    Checks whether a user has granted an active, unrevoked consent for a given purpose.
    Returns True if consent is explicitly granted and not revoked.
    Returns False otherwise.
    """
    query = select(Consent).where(
        Consent.user_id == user_id,
        Consent.consent_type == consent_type,
        Consent.granted == True,
        Consent.revoked_at.is_(None)
    )
    result = await db.execute(query)
    consent = result.scalars().first()
    return consent is not None

async def enforce_user_consent(
    db: AsyncSession,
    user_id: str,
    consent_type: str,
    action_description: Optional[str] = None
) -> None:
    """
    Enforces active user consent for a clinical or processing action.
    Raises HTTP 403 Forbidden with a clear, actionable message if missing or revoked.
    """
    has_consent = await verify_user_consent(db, user_id, consent_type)
    if not has_consent:
        desc = action_description or f"perform {consent_type}"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Consent required: Active '{consent_type}' consent is required to {desc}. Please update your preferences in Profile > Privacy & Consent."
        )
