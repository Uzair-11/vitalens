from typing import List, Optional
from datetime import date, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.appointment import Appointment
from app.models.doctor_availability import DoctorAvailability
from app.models.doctor import Doctor
from app.models.report import MedicalReport
from app.schemas.appointment_schema import AppointmentCreate

async def book_appointment(db: AsyncSession, user_id: str, appt_in: AppointmentCreate) -> Appointment:
    # Verify doctor existence
    doc_query = select(Doctor).where(Doctor.id == appt_in.doctor_id).options(selectinload(Doctor.specialty))
    doc_res = await db.execute(doc_query)
    doctor = doc_res.scalars().first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected doctor not found.")

    # Check for slot availability and lock it
    slot_query = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == appt_in.doctor_id,
        DoctorAvailability.available_date == appt_in.appointment_date,
        DoctorAvailability.start_time == appt_in.appointment_time
    )
    slot_res = await db.execute(slot_query)
    slot = slot_res.scalars().first()
    
    if slot and slot.is_booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This appointment slot has already been booked. Please select another time."
        )

    if slot:
        slot.is_booked = True

    import os
    from app.core.config import settings
    from app.core.notifications import notification_service
    from app.models.user import User

    payments_enabled = (
        getattr(settings, "ENABLE_PAYMENTS", False)
        or getattr(settings, "PAYMENTS_ENABLED", False)
        or os.getenv("PAYMENTS_ENABLED", "false").lower() == "true"
    )

    fee_inr = float(doctor.consultation_fee) if doctor and doctor.consultation_fee else 800.0
    initial_status = "PENDING_PAYMENT" if payments_enabled else "CONFIRMED"
    initial_payment_status = "PENDING" if payments_enabled else "PAID"

    appointment = Appointment(
        user_id=user_id,
        doctor_id=appt_in.doctor_id,
        report_id=appt_in.report_id,
        appointment_date=appt_in.appointment_date,
        appointment_time=appt_in.appointment_time,
        status=initial_status,
        payment_status=initial_payment_status,
        payment_amount=str(fee_inr),
        payment_currency="INR",
        visit_reason=appt_in.visit_reason,
        patient_notes=appt_in.patient_notes
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    # Fetch report name if report_id provided
    report_name = None
    if appt_in.report_id:
        rep_res = await db.execute(select(MedicalReport).where(MedicalReport.id == appt_in.report_id))
        rep_obj = rep_res.scalars().first()
        if rep_obj:
            report_name = rep_obj.file_name

    # Attach doctor and report metadata to appointment instance for Pydantic response serialization
    appointment.doctor_name = doctor.full_name if doctor else "Specialist"
    appointment.doctor_specialty = doctor.specialty.name if doctor and doctor.specialty else "General Medicine"
    appointment.doctor_clinic = doctor.clinic_name if doctor else "Clinic"
    appointment.doctor_address = doctor.address if doctor else "Address"
    appointment.doctor_photo = doctor.profile_photo_url if doctor else None
    appointment.consultation_fee = float(doctor.consultation_fee) if doctor and doctor.consultation_fee else float(fee_inr)
    appointment.report_name = report_name

    # If payments disabled, trigger confirmed notification immediately
    if not payments_enabled:
        user_res = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalars().first()
        if user_obj:
            await notification_service.notify_appointment_confirmed(
                db=db,
                appointment=appointment,
                user=user_obj,
                doctor_name=doctor.full_name
            )

    return appointment

async def list_user_appointments(db: AsyncSession, user_id: str, status_filter: Optional[str] = None) -> List[dict]:
    query = select(Appointment).where(Appointment.user_id == user_id).options(
        selectinload(Appointment.doctor).selectinload(Doctor.specialty),
        selectinload(Appointment.report)
    )
    if status_filter:
        query = query.where(Appointment.status == status_filter.upper())
        
    query = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
    result = await db.execute(query)
    appts = result.scalars().all()
    
    response = []
    for a in appts:
        response.append({
            "id": a.id,
            "user_id": a.user_id,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.full_name if a.doctor else "Specialist",
            "doctor_specialty": a.doctor.specialty.name if a.doctor and a.doctor.specialty else "General",
            "doctor_clinic": a.doctor.clinic_name if a.doctor else "Clinic",
            "doctor_address": a.doctor.address if a.doctor else "Address",
            "doctor_photo": a.doctor.profile_photo_url if a.doctor else None,
            "consultation_fee": float(a.doctor.consultation_fee) if a.doctor else 0.0,
            "report_id": a.report_id,
            "report_name": a.report.file_name if a.report else None,
            "appointment_date": a.appointment_date,
            "appointment_time": a.appointment_time,
            "status": a.status,
            "payment_status": a.payment_status,
            "payment_id": a.payment_id,
            "payment_order_id": a.payment_order_id,
            "payment_amount": a.payment_amount,
            "payment_currency": a.payment_currency,
            "visit_reason": a.visit_reason,
            "patient_notes": a.patient_notes,
            "cancellation_reason": a.cancellation_reason,
            "created_at": a.created_at
        })
    return response

async def cancel_appointment(db: AsyncSession, user_id: str, appt_id: str, reason: str) -> Appointment:
    query = select(Appointment).where(Appointment.id == appt_id, Appointment.user_id == user_id).options(
        selectinload(Appointment.doctor).selectinload(Doctor.specialty),
        selectinload(Appointment.user),
        selectinload(Appointment.report)
    )
    result = await db.execute(query)
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
        
    appt.status = "CANCELLED"
    appt.cancellation_reason = reason
    
    # Release slot back to availability
    slot_query = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == appt.doctor_id,
        DoctorAvailability.available_date == appt.appointment_date,
        DoctorAvailability.start_time == appt.appointment_time
    )
    slot_res = await db.execute(slot_query)
    slot = slot_res.scalars().first()
    if slot:
        slot.is_booked = False
        
    await db.commit()
    await db.refresh(appt)

    # Attach metadata for serialization
    if appt.doctor:
        appt.doctor_name = appt.doctor.full_name
        appt.doctor_specialty = appt.doctor.specialty.name if appt.doctor.specialty else "General Medicine"
        appt.doctor_clinic = appt.doctor.clinic_name
        appt.doctor_address = appt.doctor.address
        appt.doctor_photo = appt.doctor.profile_photo_url
        appt.consultation_fee = float(appt.doctor.consultation_fee) if appt.doctor.consultation_fee else 0.0
    if appt.report:
        appt.report_name = appt.report.file_name

    # Trigger cancellation notification (consent-gated)
    from app.core.notifications import notification_service
    if appt.user:
        doc_name = appt.doctor.full_name if appt.doctor else "Doctor"
        await notification_service.notify_appointment_cancelled(
            db=db,
            appointment=appt,
            user=appt.user,
            doctor_name=doc_name,
            reason=reason
        )

    return appt

async def reschedule_appointment(db: AsyncSession, user_id: str, appt_id: str, new_date: date, new_time: time) -> Appointment:
    query = select(Appointment).where(Appointment.id == appt_id, Appointment.user_id == user_id).options(
        selectinload(Appointment.doctor).selectinload(Doctor.specialty),
        selectinload(Appointment.report)
    )
    result = await db.execute(query)
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    # Free old slot
    old_slot_q = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == appt.doctor_id,
        DoctorAvailability.available_date == appt.appointment_date,
        DoctorAvailability.start_time == appt.appointment_time
    )
    old_res = await db.execute(old_slot_q)
    old_slot = old_res.scalars().first()
    if old_slot:
        old_slot.is_booked = False

    # Claim new slot
    new_slot_q = select(DoctorAvailability).where(
        DoctorAvailability.doctor_id == appt.doctor_id,
        DoctorAvailability.available_date == new_date,
        DoctorAvailability.start_time == new_time
    )
    new_res = await db.execute(new_slot_q)
    new_slot = new_res.scalars().first()
    if new_slot and new_slot.is_booked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The requested new slot is already booked.")
    if new_slot:
        new_slot.is_booked = True

    appt.appointment_date = new_date
    appt.appointment_time = new_time
    appt.status = "RESCHEDULED"
    await db.commit()
    await db.refresh(appt)

    # Attach metadata for serialization
    if appt.doctor:
        appt.doctor_name = appt.doctor.full_name
        appt.doctor_specialty = appt.doctor.specialty.name if appt.doctor.specialty else "General Medicine"
        appt.doctor_clinic = appt.doctor.clinic_name
        appt.doctor_address = appt.doctor.address
        appt.doctor_photo = appt.doctor.profile_photo_url
        appt.consultation_fee = float(appt.doctor.consultation_fee) if appt.doctor.consultation_fee else 0.0
    if appt.report:
        appt.report_name = appt.report.file_name

    return appt
