from typing import Optional, List
import uuid
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import require_role
from app.core.audit import record_audit_log
from app.core.security import async_get_password_hash
from app.models.user import User, UserRole
from app.models.appointment import Appointment

router = APIRouter()

class CreateUserAdminRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "ADMIN"
    phone: Optional[str] = None

class UpdateUserRoleRequest(BaseModel):
    role: str

@router.get("/")
async def list_users_admin(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    current_user: User = Depends(require_role("ADMIN", "SUPER_ADMIN", "SUPPORT_STAFF")),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists and searches patient and user accounts with pagination.
    Accessible to SUPPORT_STAFF (read-only), ADMIN, and SUPER_ADMIN.
    """
    q = select(User).options(
        selectinload(User.reports),
        selectinload(User.appointments)
    )
    if role:
        q = q.where(User.role == role.upper())
    if is_active is not None:
        q = q.where(User.is_active == is_active)
    if search:
        search_pattern = f"%{search.strip()}%"
        q = q.where(
            User.full_name.ilike(search_pattern) | 
            User.email.ilike(search_pattern) | 
            User.phone.ilike(search_pattern)
        )

    q = q.order_by(User.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(q)
    users = res.scalars().all()

    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role,
            "phone": u.phone,
            "avatar_url": u.avatar_url,
            "date_of_birth": u.date_of_birth,
            "biological_sex": u.biological_sex,
            "blood_group": u.blood_group,
            "emergency_contact": u.emergency_contact,
            "city": u.city,
            "state": u.state,
            "postal_code": u.postal_code,
            "country": u.country,
            "abha_number": u.abha_number,
            "is_verified": u.is_verified,
            "is_active": u.is_active,
            "is_deleted": u.is_deleted,
            "last_login_at": u.last_login_at,
            "appointments_count": len(u.appointments) if u.appointments else 0,
            "reports_count": len(u.reports) if u.reports else 0,
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
    Operational detailed view: returns complete user profile, address, security metadata,
    and aggregate clinical records (appointments, reports, symptoms).
    """
    q = select(User).where(User.id == user_id).options(
        selectinload(User.reports),
        selectinload(User.appointments).selectinload(Appointment.doctor),
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
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "date_of_birth": user.date_of_birth,
        "biological_sex": user.biological_sex,
        "blood_group": user.blood_group,
        "emergency_contact": user.emergency_contact,
        "abha_number": user.abha_number,
        "address_line1": user.address_line1,
        "address_line2": user.address_line2,
        "city": user.city,
        "state": user.state,
        "postal_code": user.postal_code,
        "country": user.country,
        "registration_ip": user.registration_ip,
        "last_login_ip": user.last_login_ip,
        "is_verified": user.is_verified,
        "verified_at": user.verified_at,
        "phone_verified": user.phone_verified,
        "email_verified": user.email_verified,
        "last_login_at": user.last_login_at,
        "is_active": user.is_active,
        "is_deleted": user.is_deleted,
        "summary_metrics": {
            "reports_count": len(user.reports),
            "appointments_count": len(user.appointments),
            "symptom_logs_count": len(user.symptoms)
        },
        "recent_appointments": [
            {
                "id": a.id,
                "booking_reference": a.booking_reference,
                "doctor_name": a.doctor.full_name if a.doctor else "Assigned Practitioner",
                "clinic_name": a.doctor.clinic_name if a.doctor else "Partner Clinic",
                "appointment_date": a.appointment_date,
                "appointment_time": a.appointment_time.strftime("%H:%M") if a.appointment_time else None,
                "status": a.status,
                "payment_status": a.payment_status,
                "visit_reason": a.visit_reason
            }
            for a in (user.appointments or [])[:10]
        ],
        "recent_reports": [
            {
                "id": r.id,
                "file_name": r.file_name,
                "file_path": r.file_path,
                "file_size_bytes": r.file_size_bytes,
                "report_type": r.report_type,
                "report_date": r.report_date,
                "status": r.status,
                "created_at": r.created_at
            }
            for r in (user.reports or [])[:10]
        ],
        "recent_symptoms": [
            {
                "id": s.id,
                "symptoms": s.symptoms,
                "severity": s.severity,
                "duration_days": s.duration_days,
                "created_at": s.created_at
            }
            for s in (user.symptoms or [])[:10]
        ],
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.patch("/{user_id}/status")
async def toggle_user_active_status(
    user_id: str,
    is_active: bool = Query(..., description="Active status to set (True = active, False = suspended)"),
    reason: Optional[str] = Query(None, description="Administrative reason for status change"),
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
        actor_user_id=current_admin.id, metadata={"is_active": is_active, "target_email": user.email, "reason": reason}
    )

    return {
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "message": f"User account {'reactivated' if is_active else 'suspended'} successfully."
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    data: CreateUserAdminRequest,
    current_super_admin: User = Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new user account with a designated role (e.g. ADMIN, SUPPORT_STAFF, PATIENT, DOCTOR).
    Restricted strictly to SUPER_ADMIN.
    """
    target_role = data.role.upper()
    valid_roles = {r.value for r in UserRole}
    if target_role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{data.role}'. Allowed roles: {', '.join(valid_roles)}"
        )

    # Check for existing email
    q = select(User).where(User.email == data.email.lower().strip())
    res = await db.execute(q)
    if res.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="A user with this email address already exists."
        )

    hashed_pw = await async_get_password_hash(data.password)
    new_user = User(
        id=str(uuid.uuid4()),
        email=data.email.lower().strip(),
        hashed_password=hashed_pw,
        full_name=data.full_name.strip(),
        role=target_role,
        phone=data.phone.strip() if data.phone else None,
        is_active=True,
        is_verified=True,
        email_verified=True,
        phone_verified=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    await record_audit_log(
        db, action="CREATE_USER_ADMIN", resource_type="User", resource_id=new_user.id,
        actor_user_id=current_super_admin.id,
        metadata={"created_email": new_user.email, "assigned_role": new_user.role}
    )

    return {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "phone": new_user.phone,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at
    }

@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    data: UpdateUserRoleRequest,
    current_super_admin: User = Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Modifies a user's system role (e.g. promoting to ADMIN, demoting).
    Restricted strictly to SUPER_ADMIN.
    """
    target_role = data.role.upper()
    valid_roles = {r.value for r in UserRole}
    if target_role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{data.role}'. Allowed roles: {', '.join(valid_roles)}"
        )

    q = select(User).where(User.id == user_id)
    res = await db.execute(q)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    old_role = user.role
    user.role = target_role
    await db.commit()
    await db.refresh(user)

    await record_audit_log(
        db, action="UPDATE_USER_ROLE", resource_type="User", resource_id=user.id,
        actor_user_id=current_super_admin.id,
        metadata={"target_email": user.email, "old_role": old_role, "new_role": target_role}
    )

    return {
        "user_id": user.id,
        "email": user.email,
        "old_role": old_role,
        "new_role": user.role,
        "message": f"User role updated to {target_role} successfully."
    }

class UpdateUserAbhaRequest(BaseModel):
    abha_number: Optional[str] = None

@router.patch("/{user_id}/abha")
async def update_user_abha(
    user_id: str,
    data: UpdateUserAbhaRequest,
    current_admin: User = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates or links/unlinks a patient's ABHA Health ID.
    Restricted to ADMIN or SUPER_ADMIN.
    """
    q = select(User).where(User.id == user_id)
    res = await db.execute(q)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    if data.abha_number and data.abha_number.strip():
        clean_num = str(data.abha_number).replace("-", "").strip()
        if len(clean_num) != 14 or not clean_num.isdigit():
            raise HTTPException(
                status_code=400,
                detail="Invalid ABHA number format. Must be 14 numeric digits (e.g. 91-1234-5678-9012)."
            )
        formatted_abha = f"{clean_num[0:2]}-{clean_num[2:6]}-{clean_num[6:10]}-{clean_num[10:14]}"
        user.abha_number = formatted_abha
    else:
        user.abha_number = None

    await db.commit()
    await db.refresh(user)

    await record_audit_log(
        db,
        action="UPDATE_USER_ABHA",
        resource_type="User",
        resource_id=user.id,
        actor_user_id=current_admin.id,
        metadata={"target_email": user.email, "abha_number": user.abha_number}
    )

    return {
        "user_id": user.id,
        "email": user.email,
        "abha_number": user.abha_number,
        "message": "ABHA Health ID updated successfully."
    }


