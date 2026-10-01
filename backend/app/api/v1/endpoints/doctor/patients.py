from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import require_role, verify_doctor_patient_relationship
from app.core.audit import record_audit_log
from app.core.consent import verify_user_consent
from app.models.user import User
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.report import MedicalReport
from app.models.consultation_note import ConsultationNote
from app.schemas.doctor_portal_schema import (
    DoctorPatientDetailResponse, DoctorAppointmentItemResponse, ConsultationNoteResponse
)

router = APIRouter()

async def get_doctor_for_user(db: AsyncSession, user_id: str) -> Doctor:
    doc_q = select(Doctor).where(Doctor.user_id == user_id)
    doc = (await db.execute(doc_q)).scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for authenticated user."
        )
    return doc

@router.get("/patients", response_model=List[dict])
@router.get("/patients/", response_model=List[dict], include_in_schema=False)
async def list_doctor_assigned_patients(
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Lists distinct patients who have scheduled consultations with this doctor."""
    doctor = await get_doctor_for_user(db, current_user.id)

    appts_q = select(Appointment).where(
        Appointment.doctor_id == doctor.id
    ).options(selectinload(Appointment.user))
    appts = (await db.execute(appts_q)).scalars().all()

    seen_patient_ids = set()
    patients = []
    for a in appts:
        if a.user_id not in seen_patient_ids and a.user:
            seen_patient_ids.add(a.user_id)
            if search:
                s_low = search.lower()
                if s_low not in a.user.full_name.lower() and s_low not in a.user.email.lower():
                    continue
            patients.append({
                "patient_id": a.user.id,
                "full_name": a.user.full_name,
                "email": a.user.email,
                "phone": a.user.phone,
                "last_appointment_date": a.appointment_date,
                "status": a.status
            })
    return patients

@router.get("/patients/{patient_id}", response_model=DoctorPatientDetailResponse)
async def get_patient_clinical_chart(
    patient_id: str,
    current_user: User = Depends(require_role("DOCTOR", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves consented patient chart.
    Enforces resource-level doctor-patient relationship guard: returns 403 Forbidden
    if no active/completed consultation exists with this doctor.
    """
    # 1. Resource-level relationship authorization guard
    if current_user.role == "DOCTOR":
        has_relationship = await verify_doctor_patient_relationship(db, current_user.id, patient_id)
        if not has_relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: No active or completed appointment exists between you and this patient."
            )

        # 2. Patient consent guard: DOCTOR_DATA_ACCESS
        has_consent = await verify_user_consent(db, patient_id, "DOCTOR_DATA_ACCESS")
        if not has_consent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consent required: Patient has revoked or not granted 'DOCTOR_DATA_ACCESS' consent."
            )

    doctor = await get_doctor_for_user(db, current_user.id)


    # 2. Record audit log
    await record_audit_log(
        db,
        action="VIEW_PATIENT_CHART",
        resource_type="PATIENT",
        resource_id=patient_id,
        actor_user_id=current_user.id,
        metadata={"doctor_id": doctor.id}
    )


    # 3. Fetch patient profile
    pat_q = select(User).where(User.id == patient_id)
    patient = (await db.execute(pat_q)).scalars().first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found.")

    # 4. Fetch appointments with this doctor
    appts_q = select(Appointment).where(
        Appointment.doctor_id == doctor.id,
        Appointment.user_id == patient_id
    ).options(selectinload(Appointment.consultation_note)).order_by(Appointment.appointment_date.desc())
    appts = (await db.execute(appts_q)).scalars().all()

    # 5. Fetch consultation notes
    notes_q = select(ConsultationNote).where(
        ConsultationNote.doctor_id == doctor.id,
        ConsultationNote.appointment_id.in_([a.id for a in appts])
    ).order_by(ConsultationNote.created_at.desc())
    notes = (await db.execute(notes_q)).scalars().all()

    # 6. Fetch shared reports
    reports_q = select(MedicalReport).where(
        MedicalReport.user_id == patient_id
    ).options(selectinload(MedicalReport.biomarkers), selectinload(MedicalReport.analysis)).order_by(MedicalReport.created_at.desc())
    reports = (await db.execute(reports_q)).scalars().all()

    reports_data = []
    for r in reports:
        reports_data.append({
            "id": r.id,
            "report_title": r.report_title,
            "report_type": r.report_type,
            "report_date": r.report_date,
            "overall_status": r.overall_status,
            "biomarkers_count": len(r.biomarkers),
            "biomarkers": [
                {
                    "test_name": b.test_name,
                    "value_numeric": b.value_numeric,
                    "value_text": b.value_text,
                    "unit": b.unit,
                    "reference_text": b.reference_text,
                    "flag": b.flag
                }
                for b in r.biomarkers
            ],
            "analysis_summary": r.analysis.summary if r.analysis else None
        })

    appts_data = [
        DoctorAppointmentItemResponse(
            id=a.id,
            user_id=a.user_id,
            patient_name=patient.full_name,
            patient_email=patient.email,
            patient_phone=patient.phone,
            appointment_date=a.appointment_date,
            appointment_time=a.appointment_time,
            status=a.status,
            visit_reason=a.visit_reason,
            patient_notes=a.patient_notes,
            cancellation_reason=a.cancellation_reason,
            report_id=a.report_id,
            has_consultation_notes=a.consultation_note is not None,
            created_at=a.created_at
        )
        for a in appts
    ]

    return DoctorPatientDetailResponse(
        patient_id=patient.id,
        full_name=patient.full_name,
        email=patient.email,
        phone=patient.phone,
        date_of_birth=patient.date_of_birth,
        biological_sex=patient.biological_sex,
        blood_group=patient.blood_group,
        emergency_contact=patient.emergency_contact,
        appointments_with_doctor=appts_data,
        consultation_notes=notes,
        shared_reports=reports_data
    )
