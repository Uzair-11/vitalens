from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, distinct
from app.core.database import get_db
from app.core.rbac import require_role
from app.models.user import User
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.schemas.doctor_portal_schema import DoctorMeResponse, DoctorStatsToday

router = APIRouter()

@router.get("/me", response_model=DoctorMeResponse)
async def get_doctor_profile_me(
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves authenticated doctor's profile and operational stats.
    Resolved securely via current_user.id (never accepts doctor ID from client).
    """
    # 1. Fetch Doctor record linked to user
    doc_q = select(Doctor).where(Doctor.user_id == current_user.id).options(selectinload(Doctor.specialty))
    doc_res = await db.execute(doc_q)
    doctor = doc_res.scalars().first()

    if not doctor:
        # If super_admin is testing, resolve first doctor for preview or raise
        if current_user.role == "SUPER_ADMIN":
            first_doc_q = select(Doctor).options(selectinload(Doctor.specialty))
            first_doc_res = await db.execute(first_doc_q)
            doctor = first_doc_res.scalars().first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for this user account. Please contact an administrator."
        )

    today = date.today()

    # 2. Compute today's operational stats
    # Today's appointments count
    today_q = select(func.count(Appointment.id)).where(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == today,
        Appointment.status != "CANCELLED"
    )
    today_count = (await db.execute(today_q)).scalar() or 0

    # Completed today
    completed_today_q = select(func.count(Appointment.id)).where(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == today,
        Appointment.status == "COMPLETED"
    )
    completed_today = (await db.execute(completed_today_q)).scalar() or 0

    # Total consultations completed
    total_completed_q = select(func.count(Appointment.id)).where(
        Appointment.doctor_id == doctor.id,
        Appointment.status == "COMPLETED"
    )
    total_completed = (await db.execute(total_completed_q)).scalar() or 0

    # Pending requests
    pending_q = select(func.count(Appointment.id)).where(
        Appointment.doctor_id == doctor.id,
        Appointment.status == "PENDING"
    )
    pending_count = (await db.execute(pending_q)).scalar() or 0

    # Distinct active patients
    patients_q = select(func.count(distinct(Appointment.user_id))).where(
        Appointment.doctor_id == doctor.id,
        Appointment.status.in_(["CONFIRMED", "COMPLETED"])
    )
    active_patients = (await db.execute(patients_q)).scalar() or 0

    stats = DoctorStatsToday(
        today_appointments_count=today_count,
        pending_requests_count=pending_count,
        completed_today_count=completed_today,
        total_consultations_completed=total_completed,
        active_patients_count=active_patients
    )

    return DoctorMeResponse(
        doctor_id=doctor.id,
        user_id=current_user.id,
        full_name=doctor.full_name,
        email=current_user.email,
        specialty_id=doctor.specialty_id,
        specialty_name=doctor.specialty.name if doctor.specialty else "General",
        qualification=doctor.qualification,
        experience_years=doctor.experience_years,
        clinic_name=doctor.clinic_name,
        address=doctor.address,
        city=doctor.city,
        consultation_fee=float(doctor.consultation_fee),
        rating=doctor.rating,
        review_count=doctor.review_count,
        verification_status=doctor.verification_status,
        is_active=doctor.is_active,
        today_stats=stats
    )
