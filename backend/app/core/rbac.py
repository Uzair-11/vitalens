from typing import List, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import decode_access_token, oauth2_scheme
from app.models.user import User
from app.models.appointment import Appointment
from app.models.consent import Consent
from app.models.doctor import Doctor
from app.services.user_service import get_user_profile

async def get_current_user_obj(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extracts and verifies current user from bearer token."""
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user_id = payload["sub"]
    user = await get_user_profile(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists."
        )
    if not getattr(user, "is_active", True) or getattr(user, "is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been suspended or deactivated."
        )
    return user

def require_role(*allowed_roles: str) -> Callable:
    """
    Role-Based Access Control (RBAC) route dependency.
    Example: Depends(require_role("ADMIN", "SUPER_ADMIN"))
    """
    async def role_checker(current_user: User = Depends(get_current_user_obj)) -> User:
        user_role = (current_user.role or "PATIENT").upper()
        allowed = [r.upper() for r in allowed_roles]
        
        # SUPER_ADMIN has god-mode across all roles
        if "SUPER_ADMIN" in allowed and user_role == "SUPER_ADMIN":
            return current_user
        if user_role not in allowed and "SUPER_ADMIN" != user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of [{', '.join(allowed)}] roles."
            )
        return current_user
    return role_checker

async def verify_doctor_patient_relationship(
    db: AsyncSession,
    doctor_user_id: str,
    patient_id: str
) -> bool:
    """
    Resource-level authorization check:
    Verifies that a Doctor has an active or completed consultation appointment
    with the target patient before permitting medical data access.
    """
    # 1. Fetch doctor entity linked to user
    doc_q = select(Doctor).where(Doctor.user_id == doctor_user_id)
    doc_res = await db.execute(doc_q)
    doctor = doc_res.scalars().first()
    if not doctor:
        return False

    # 2. Check appointment link
    appt_q = select(Appointment).where(
        Appointment.doctor_id == doctor.id,
        Appointment.user_id == patient_id
    )
    appt_res = await db.execute(appt_q)
    has_appointment = appt_res.scalars().first() is not None
    return has_appointment

async def check_user_consent(
    db: AsyncSession,
    user_id: str,
    consent_type: str
) -> bool:
    """
    Checks if an active, unrevoked consent record exists for the given user.
    """
    q = select(Consent).where(
        Consent.user_id == user_id,
        Consent.consent_type == consent_type,
        Consent.granted == True,
        Consent.revoked_at == None
    )
    res = await db.execute(q)
    return res.scalars().first() is not None
