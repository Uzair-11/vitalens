import secrets
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import require_role
from app.core.audit import record_audit_log
from app.core.security import get_password_hash, async_get_password_hash
from app.models.user import User
from app.models.doctor import Doctor
from app.models.specialty import MedicalSpecialty

router = APIRouter()

class CreateDoctorAdminRequest(BaseModel):
    email: EmailStr
    temporary_password: Optional[str] = None
    full_name: str
    phone: Optional[str] = None
    registration_number: Optional[str] = None
    registration_council: Optional[str] = None
    state_code: Optional[str] = None
    specialty_id: str
    qualification: str
    experience_years: int
    clinic_name: str
    address: str
    city: str
    consultation_fee: float = 800.0
    bio: Optional[str] = None
    languages: List[str] = ["English"]
    credential_documents: List[str] = []

class UpdateDoctorAdminRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    registration_number: Optional[str] = None
    registration_council: Optional[str] = None
    state_code: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    clinic_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    consultation_fee: Optional[float] = None
    bio: Optional[str] = None
    languages: Optional[List[str]] = None
    credential_documents: Optional[List[str]] = None

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_doctor_account(
    data: CreateDoctorAdminRequest,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin creates a doctor profile and associated login user account in a single transaction."""
    # Check if user already exists
    user_q = select(User).where(User.email == data.email)
    res = await db.execute(user_q)
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="User account with this email already exists.")

    # Validate specialty exists
    spec_q = select(MedicalSpecialty).where(MedicalSpecialty.id == data.specialty_id)
    spec_res = await db.execute(spec_q)
    if not spec_res.scalars().first():
        raise HTTPException(status_code=404, detail="Selected medical specialty not found.")

    # Generate temporary password if not provided
    temp_password = data.temporary_password or secrets.token_urlsafe(10)

    # 1. Create DOCTOR user account
    hashed_pwd = await async_get_password_hash(temp_password)
    doctor_user = User(
        email=data.email,
        hashed_password=hashed_pwd,
        role="DOCTOR",
        full_name=data.full_name,
        phone=data.phone,
        is_active=True
    )
    db.add(doctor_user)
    await db.flush()  # Populates doctor_user.id

    # 2. Create Doctor profile linked to user account
    doctor = Doctor(
        user_id=doctor_user.id,
        specialty_id=data.specialty_id,
        full_name=data.full_name,
        qualification=data.qualification,
        registration_number=data.registration_number,
        registration_council=data.registration_council,
        state_code=data.state_code,
        email=data.email,
        phone=data.phone,
        experience_years=data.experience_years,
        clinic_name=data.clinic_name,
        address=data.address,
        city=data.city,
        consultation_fee=data.consultation_fee,
        bio=data.bio,
        languages=data.languages,
        credential_documents=data.credential_documents,
        verification_status="PENDING",
        is_active=True
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    await db.refresh(doctor_user)

    # 3. Record Audit Log
    await record_audit_log(
        db, action="CREATE_DOCTOR", resource_type="Doctor", resource_id=doctor.id,
        actor_user_id=current_admin.id, metadata={"email": data.email, "doctor_id": doctor.id, "user_id": doctor_user.id}
    )

    return {
        "status": "SUCCESS",
        "doctor_id": doctor.id,
        "user_id": doctor_user.id,
        "email": doctor_user.email,
        "phone": doctor.phone,
        "registration_number": doctor.registration_number,
        "full_name": doctor.full_name,
        "verification_status": doctor.verification_status,
        "temporary_password": temp_password if not data.temporary_password else "[USER_PROVIDED]",
        "message": "Doctor profile and login credentials created successfully. Verification pending."
    }

@router.get("/")
async def list_doctors_admin(
    name: Optional[str] = Query(None, description="Search doctor by name"),
    specialty_id: Optional[str] = Query(None, description="Filter by specialty ID"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin lists all doctors with search and filtering."""
    q = select(Doctor).options(selectinload(Doctor.specialty), selectinload(Doctor.user))
    if name:
        q = q.where(Doctor.full_name.ilike(f"%{name}%"))
    if specialty_id:
        q = q.where(Doctor.specialty_id == specialty_id)
    if verification_status:
        q = q.where(Doctor.verification_status == verification_status.upper())
    if is_active is not None:
        q = q.where(Doctor.is_active == is_active)

    res = await db.execute(q)
    doctors = res.scalars().all()
    return [
        {
            "id": d.id,
            "user_id": d.user_id,
            "full_name": d.full_name,
            "email": d.email or (d.user.email if d.user else None),
            "phone": d.phone or (d.user.phone if d.user else None),
            "registration_number": d.registration_number,
            "registration_council": d.registration_council,
            "state_code": d.state_code,
            "specialty_id": d.specialty_id,
            "specialty_name": d.specialty.name if d.specialty else None,
            "qualification": d.qualification,
            "experience_years": d.experience_years,
            "clinic_name": d.clinic_name,
            "address": d.address,
            "city": d.city,
            "consultation_fee": d.consultation_fee,
            "bio": d.bio,
            "languages": d.languages,
            "verification_status": d.verification_status,
            "credential_documents": d.credential_documents,
            "is_active": d.is_active,
            "rating": d.rating,
            "review_count": d.review_count,
            "created_at": d.created_at
        }
        for d in doctors
    ]

@router.patch("/{doctor_id}")
async def update_doctor_profile(
    doctor_id: str,
    data: UpdateDoctorAdminRequest,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin edits doctor profile fields and credentials."""
    q = select(Doctor).where(Doctor.id == doctor_id)
    res = await db.execute(q)
    doctor = res.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    update_data = data.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(doctor, field, val)

    await db.commit()
    await db.refresh(doctor)

    await record_audit_log(
        db, action="UPDATE_DOCTOR", resource_type="Doctor", resource_id=doctor.id,
        actor_user_id=current_admin.id, metadata={"updated_fields": list(update_data.keys())}
    )
    return {"doctor_id": doctor.id, "status": "UPDATED", "doctor": doctor}

@router.patch("/{doctor_id}/verify")
async def verify_doctor(
    doctor_id: str,
    verification_status: str = Query(..., pattern="^(VERIFIED|REJECTED|PENDING)$"),
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin sets verification status to VERIFIED or REJECTED."""
    q = select(Doctor).where(Doctor.id == doctor_id)
    res = await db.execute(q)
    doctor = res.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    doctor.verification_status = verification_status
    await db.commit()
    await record_audit_log(
        db, action="VERIFY_DOCTOR", resource_type="Doctor", resource_id=doctor.id,
        actor_user_id=current_admin.id, metadata={"verification_status": verification_status}
    )
    return {"doctor_id": doctor.id, "verification_status": doctor.verification_status}

@router.patch("/{doctor_id}/status")
async def toggle_doctor_status(
    doctor_id: str,
    is_active: bool,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin activates or deactivates a doctor profile (soft update)."""
    q = select(Doctor).where(Doctor.id == doctor_id)
    res = await db.execute(q)
    doctor = res.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    doctor.is_active = is_active
    await db.commit()
    await record_audit_log(
        db, action="TOGGLE_DOCTOR_STATUS", resource_type="Doctor", resource_id=doctor.id,
        actor_user_id=current_admin.id, metadata={"is_active": is_active}
    )
    return {"doctor_id": doctor.id, "is_active": doctor.is_active}

@router.delete("/{doctor_id}")
async def delete_doctor(
    doctor_id: str,
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Admin removes doctor profile record."""
    q = select(Doctor).where(Doctor.id == doctor_id)
    res = await db.execute(q)
    doctor = res.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    user_id = doctor.user_id
    doctor_name = doctor.full_name
    await db.delete(doctor)

    if user_id:
        user_res = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalars().first()
        if user_obj and user_obj.role == "DOCTOR":
            user_obj.is_active = False
            user_obj.is_deleted = True

    await db.commit()
    await record_audit_log(
        db, action="DELETE_DOCTOR", resource_type="Doctor", resource_id=doctor_id,
        actor_user_id=current_admin.id, metadata={"doctor_name": doctor_name, "user_id": user_id}
    )
    return {"status": "SUCCESS", "message": f"Doctor {doctor_name} removed successfully."}
