from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import require_role
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability

router = APIRouter()

@router.get("/")
async def list_all_appointments_admin(
    status: Optional[str] = Query(None, description="Filter by status (CONFIRMED, COMPLETED, CANCELLED, NO_SHOW)"),
    doctor_id: Optional[str] = Query(None, description="Filter by doctor ID"),
    patient_id: Optional[str] = Query(None, description="Filter by patient user ID"),
    start_date: Optional[date] = Query(None, description="Filter by appointments on or after this date"),
    end_date: Optional[date] = Query(None, description="Filter by appointments on or before this date"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN", "SUPPORT_STAFF")),
    db: AsyncSession = Depends(get_db)
):
    """Admin and Support Staff view system-wide appointments with conflict resolution filters."""
    q = select(Appointment).options(
        selectinload(Appointment.doctor),
        selectinload(Appointment.user)
    ).order_by(Appointment.appointment_date.desc())

    if status:
        q = q.where(Appointment.status == status.upper())
    if doctor_id:
        q = q.where(Appointment.doctor_id == doctor_id)
    if patient_id:
        q = q.where(Appointment.user_id == patient_id)
    if start_date:
        q = q.where(Appointment.appointment_date >= start_date)
    if end_date:
        q = q.where(Appointment.appointment_date <= end_date)

    q = q.offset(skip).limit(limit)
    res = await db.execute(q)
    appts = res.scalars().all()

    return [
        {
            "id": a.id,
            "patient_id": a.user_id,
            "patient_name": a.user.full_name if a.user else "Unknown Patient",
            "patient_email": a.user.email if a.user else "",
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.full_name if a.doctor else "Unknown Doctor",
            "appointment_date": a.appointment_date,
            "appointment_time": str(a.appointment_time),
            "status": a.status,
            "visit_reason": a.visit_reason,
            "cancellation_reason": a.cancellation_reason,
            "created_at": a.created_at
        }
        for a in appts
    ]

@router.patch("/{appointment_id}/cancel")
async def cancel_appointment_admin(
    appointment_id: str,
    reason: str = Query("Cancelled by administrator for conflict resolution"),
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin manually cancels an appointment and releases the doctor's availability slot.
    Restricted to ADMIN and SUPER_ADMIN only.
    """
    q = select(Appointment).where(Appointment.id == appointment_id)
    res = await db.execute(q)
    appt = res.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if appt.status == "CANCELLED":
        return {"appointment_id": appt.id, "status": "CANCELLED", "message": "Appointment was already cancelled."}

    # 1. Update appointment status
    appt.status = "CANCELLED"
    appt.cancellation_reason = reason

    # 2. Release the doctor's availability slot
    slot_q = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == appt.doctor_id,
        DoctorAvailability.available_date == appt.appointment_date,
        DoctorAvailability.start_time == appt.appointment_time
    )
    slot_res = await db.execute(slot_q)
    slot = slot_res.scalars().first()
    if slot:
        slot.is_booked = False

    await db.commit()
    await db.refresh(appt)

    # 3. Record Audit Log
    await record_audit_log(
        db, action="ADMIN_CANCEL_APPOINTMENT", resource_type="Appointment", resource_id=appt.id,
        actor_user_id=current_admin.id, metadata={"reason": reason, "doctor_id": appt.doctor_id, "slot_released": slot is not None}
    )

    return {
        "appointment_id": appt.id,
        "status": "CANCELLED",
        "reason": reason,
        "slot_released": slot is not None,
        "message": "Appointment cancelled and doctor slot released successfully."
    }
