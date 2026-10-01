from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import require_role
from app.core.audit import record_audit_log
from app.models.user import User

router = APIRouter()

@router.get("/")
async def list_users_admin(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    current_user: User = Depends(require_role("ADMIN", "SUPER_ADMIN", "SUPPORT_STAFF")),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists and searches patient and user accounts with pagination.
    Accessible to SUPPORT_STAFF (read-only), ADMIN, and SUPER_ADMIN.
    """
    q = select(User)
    if role:
        q = q.where(User.role == role.upper())
    if search:
        search_pattern = f"%{search.strip()}%"
        q = q.where(User.full_name.ilike(search_pattern) | User.email.ilike(search_pattern))

    q = q.order_by(User.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(q)
    users = res.scalars().all()

    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "phone": u.phone,
            "date_of_birth": u.date_of_birth,
            "biological_sex": u.biological_sex,
            "blood_group": u.blood_group,
            "is_active": u.is_active,
            "is_deleted": u.is_deleted,
            "created_at": u.created_at
        }
        for u in users
    ]

@router.get("/{user_id}")
async def get_user_admin_detail(
    user_id: str,
    current_user: User = Depends(require_role("ADMIN", "SUPER_ADMIN", "SUPPORT_STAFF")),
    db: AsyncSession = Depends(get_db)
):
    """
    Operational summary view: returns user profile and aggregate activity counts.
    Does NOT dump full clinical biomarkers/notes (preserves DPDP clinical isolation).
    """
    q = select(User).where(User.id == user_id).options(
        selectinload(User.reports),
        selectinload(User.appointments),
        selectinload(User.symptoms)
    )
    res = await db.execute(q)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone,
        "date_of_birth": user.date_of_birth,
        "biological_sex": user.biological_sex,
        "blood_group": user.blood_group,
        "is_active": user.is_active,
        "is_deleted": user.is_deleted,
        "summary_metrics": {
            "reports_count": len(user.reports),
            "appointments_count": len(user.appointments),
            "symptom_logs_count": len(user.symptoms)
        },
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.patch("/{user_id}/status")
async def toggle_user_active_status(
    user_id: str,
    is_active: bool = Query(..., description="Active status to set (True = active, False = suspended)"),
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin suspends or reactivates a user account.
    Restricted strictly to ADMIN and SUPER_ADMIN (SUPPORT_STAFF gets 403 Forbidden).
    """
    q = select(User).where(User.id == user_id)
    res = await db.execute(q)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    user.is_active = is_active
    await db.commit()
    await db.refresh(user)

    await record_audit_log(
        db, action="TOGGLE_USER_STATUS", resource_type="User", resource_id=user.id,
        actor_user_id=current_admin.id, metadata={"is_active": is_active, "target_email": user.email}
    )

    return {
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "message": f"User account {'reactivated' if is_active else 'suspended'} successfully."
    }
