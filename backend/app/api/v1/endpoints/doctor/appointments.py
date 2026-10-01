import uuid
from typing import List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import require_role
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.doctor_availability import DoctorAvailability
from app.models.consultation_note import ConsultationNote
from app.schemas.doctor_portal_schema import (
    DoctorAppointmentItemResponse, UpdateDoctorAppointmentStatusRequest,
    ConsultationNoteRequest, ConsultationNoteResponse
)

router = APIRouter()

async def get_doctor_for_user(db: AsyncSession, user_id: str) -> Doctor:
    """Resolves Doctor record from authenticated user_id."""
    doc_q = select(Doctor).where(Doctor.user_id == user_id)
    doc = (await db.execute(doc_q)).scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for authenticated user."
        )
    return doc

@router.get("/appointments", response_model=List[DoctorAppointmentItemResponse])
@router.get("/appointments/", response_model=List[DoctorAppointmentItemResponse], include_in_schema=False)
async def list_doctor_appointments(
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Lists appointments belonging exclusively to the authenticated doctor."""
    doctor = await get_doctor_for_user(db, current_user.id)

    query = select(Appointment).where(
        Appointment.doctor_id == doctor.id
    ).options(
        selectinload(Appointment.user),
        selectinload(Appointment.consultation_note)
    )

    if status_filter:
        query = query.where(Appointment.status == status_filter.upper())
    if start_date:
        query = query.where(Appointment.appointment_date >= start_date)
    if end_date:
        query = query.where(Appointment.appointment_date <= end_date)

    query = query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
    result = await db.execute(query)
    appointments = result.scalars().all()

    response = []
    for a in appointments:
        response.append(DoctorAppointmentItemResponse(
            id=a.id,
            user_id=a.user_id,
            patient_name=a.user.full_name if a.user else "Anonymous Patient",
            patient_email=a.user.email if a.user else "",
            patient_phone=a.user.phone if a.user else None,
            appointment_date=a.appointment_date,
            appointment_time=a.appointment_time,
            status=a.status,
            visit_reason=a.visit_reason,
            patient_notes=a.patient_notes,
            cancellation_reason=a.cancellation_reason,
            report_id=a.report_id,
            has_consultation_notes=a.consultation_note is not None,
            created_at=a.created_at
        ))
    return response

@router.patch("/appointments/{appointment_id}/status", response_model=DoctorAppointmentItemResponse)
async def update_appointment_status(
    appointment_id: str,
    status_in: UpdateDoctorAppointmentStatusRequest,
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts/rejects pending requests, marks appointments completed or no-show.
    Cancelling or rejecting releases the doctor's availability slot.
    """
    doctor = await get_doctor_for_user(db, current_user.id)

    appt_q = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.doctor_id == doctor.id
    ).options(selectinload(Appointment.user), selectinload(Appointment.consultation_note))
    appt = (await db.execute(appt_q)).scalars().first()

    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or does not belong to this doctor."
        )

    target_status = status_in.status.upper()
    valid_statuses = ["CONFIRMED", "COMPLETED", "CANCELLED", "NO_SHOW", "RESCHEDULED"]
    if target_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    previous_status = appt.status
    appt.status = target_status
    if status_in.cancellation_reason:
        appt.cancellation_reason = status_in.cancellation_reason

    # If appointment is being cancelled or rejected, release doctor availability slot
    if target_status == "CANCELLED":
        slot_q = select(DoctorAvailability).where(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.available_date == appt.appointment_date,
            DoctorAvailability.start_time == appt.appointment_time
        )
        slot = (await db.execute(slot_q)).scalars().first()
        if slot:
            slot.is_booked = False

    await db.commit()
    await db.refresh(appt)

    # Audit log
    await record_audit_log(
        db,
        action="DOCTOR_UPDATE_APPOINTMENT_STATUS",
        resource_type="APPOINTMENT",
        resource_id=appt.id,
        actor_user_id=current_user.id,
        metadata={
            "doctor_id": doctor.id,
            "previous_status": previous_status,
            "new_status": target_status,
            "cancellation_reason": status_in.cancellation_reason
        }
    )


    return DoctorAppointmentItemResponse(
        id=appt.id,
        user_id=appt.user_id,
        patient_name=appt.user.full_name if appt.user else "Anonymous Patient",
        patient_email=appt.user.email if appt.user else "",
        patient_phone=appt.user.phone if appt.user else None,
        appointment_date=appt.appointment_date,
        appointment_time=appt.appointment_time,
        status=appt.status,
        visit_reason=appt.visit_reason,
        patient_notes=appt.patient_notes,
        cancellation_reason=appt.cancellation_reason,
        report_id=appt.report_id,
        has_consultation_notes=appt.consultation_note is not None,
        created_at=appt.created_at
    )

@router.post("/appointments/{appointment_id}/notes", response_model=ConsultationNoteResponse)
async def save_consultation_notes(
    appointment_id: str,
    note_in: ConsultationNoteRequest,
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Creates or updates clinical consultation notes for an appointment."""
    doctor = await get_doctor_for_user(db, current_user.id)

    # Verify doctor owns appointment
    appt_q = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.doctor_id == doctor.id
    )
    appt = (await db.execute(appt_q)).scalars().first()
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or does not belong to this doctor."
        )

    # Check if note already exists
    note_q = select(ConsultationNote).where(ConsultationNote.appointment_id == appointment_id)
    note = (await db.execute(note_q)).scalars().first()

    if note:
        note.diagnosis = note_in.diagnosis
        note.clinical_notes = note_in.clinical_notes
        note.prescriptions = note_in.prescriptions
        note.follow_up_recommendation = note_in.follow_up_recommendation
        note.updated_at = datetime.now(timezone.utc)
    else:
        note = ConsultationNote(
            appointment_id=appointment_id,
            doctor_id=doctor.id,
            diagnosis=note_in.diagnosis,
            clinical_notes=note_in.clinical_notes,
            prescriptions=note_in.prescriptions,
            follow_up_recommendation=note_in.follow_up_recommendation
        )
        db.add(note)

    await db.commit()
    await db.refresh(note)

    # Record audit log
    await record_audit_log(
        db,
        action="SAVE_CONSULTATION_NOTE",
        resource_type="CONSULTATION_NOTE",
        resource_id=note.id,
        actor_user_id=current_user.id,
        metadata={"appointment_id": appointment_id, "doctor_id": doctor.id}
    )


    return note

@router.get("/appointments/{appointment_id}/notes", response_model=ConsultationNoteResponse)
async def get_consultation_notes(
    appointment_id: str,
    current_user: User = Depends(require_role("DOCTOR", "PATIENT", "ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves consultation notes for an appointment."""
    note_q = select(ConsultationNote).where(
        ConsultationNote.appointment_id == appointment_id
    ).options(selectinload(ConsultationNote.appointment))
    note = (await db.execute(note_q)).scalars().first()

    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation notes not found.")

    # Role-based authorization
    if current_user.role == "DOCTOR":
        doc_q = select(Doctor).where(Doctor.user_id == current_user.id)
        doctor = (await db.execute(doc_q)).scalars().first()
        if not doctor or note.doctor_id != doctor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this consultation note.")
    elif current_user.role == "PATIENT":
        if note.appointment.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this consultation note.")

    return note
