from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.consent import Consent
from app.models.report import MedicalReport
from app.models.symptom_log import SymptomLog
from app.models.appointment import Appointment
from app.models.consultation_note import ConsultationNote
from app.models.refresh_token import RefreshToken
from app.core.audit import record_audit_log

router = APIRouter()

STANDARD_CONSENT_TYPES = [
    "REPORT_ANALYSIS",
    "AI_PROCESSING",
    "DOCTOR_DATA_ACCESS",
    "NOTIFICATIONS",
    "MARKETING"
]

class ToggleConsentRequest(BaseModel):
    granted: bool

@router.get("/consents")
@router.get("/me/consents", include_in_schema=False)
async def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists current privacy and processing consents for the authenticated user."""
    q = select(Consent).where(Consent.user_id == current_user.id)
    res = await db.execute(q)
    user_consents = {c.consent_type: c for c in res.scalars().all()}

    results = []
    for c_type in STANDARD_CONSENT_TYPES:
        if c_type in user_consents:
            c = user_consents[c_type]
            results.append({
                "id": c.id,
                "consent_type": c.consent_type,
                "granted": c.granted,
                "granted_at": c.granted_at,
                "revoked_at": c.revoked_at
            })
        else:
            # Default unseeded
            results.append({
                "id": None,
                "consent_type": c_type,
                "granted": False,
                "granted_at": None,
                "revoked_at": None
            })

    return results

@router.patch("/consents/{consent_type}")
@router.patch("/me/consents/{consent_type}", include_in_schema=False)
async def toggle_consent(
    consent_type: str,
    granted: Optional[bool] = Query(None),
    body: Optional[ToggleConsentRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates consent status for a specific DPDP purpose (accepts query param or JSON body)."""
    target_granted = granted if granted is not None else (body.granted if body is not None else True)

    q = select(Consent).where(
        Consent.user_id == current_user.id,
        Consent.consent_type == consent_type
    )
    res = await db.execute(q)
    consent = res.scalars().first()

    now = datetime.now(timezone.utc)
    action_name = "GRANT_CONSENT" if target_granted else "REVOKE_CONSENT"

    if not consent:
        consent = Consent(
            user_id=current_user.id,
            consent_type=consent_type,
            granted=target_granted,
            granted_at=now if target_granted else None,
            revoked_at=now if not target_granted else None
        )
        db.add(consent)
    else:
        consent.granted = target_granted
        if target_granted:
            consent.granted_at = now
            consent.revoked_at = None
        else:
            consent.revoked_at = now

    await db.commit()
    await db.refresh(consent)

    await record_audit_log(
        db,
        action=action_name,
        resource_type="Consent",
        resource_id=consent.id,
        actor_user_id=current_user.id,
        metadata={"consent_type": consent_type, "granted": target_granted}
    )

    return {
        "id": consent.id,
        "consent_type": consent_type,
        "granted": consent.granted,
        "granted_at": consent.granted_at,
        "revoked_at": consent.revoked_at,
        "updated_at": now
    }

@router.get("/data-export")
@router.get("/me/data-export", include_in_schema=False)
async def export_patient_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    DPDP Article & Digital Personal Data Protection compliant full data export.
    Returns structured JSON of profile, medical reports, biomarkers, symptom logs,
    appointments, consultation notes, and consent history strictly scoped to current user.
    """
    # 1. Fetch user profile
    profile_data = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "date_of_birth": str(current_user.date_of_birth) if current_user.date_of_birth else None,
        "biological_sex": current_user.biological_sex,
        "blood_group": current_user.blood_group,
        "emergency_contact": current_user.emergency_contact,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
    }

    # 2. Fetch medical reports + biomarkers + AI analysis
    rep_q = select(MedicalReport).where(
        MedicalReport.user_id == current_user.id
    ).options(selectinload(MedicalReport.biomarkers), selectinload(MedicalReport.analysis))
    reports = (await db.execute(rep_q)).scalars().all()

    reports_data = []
    for r in reports:
        reports_data.append({
            "id": r.id,
            "file_name": r.file_name,
            "report_type": r.report_type,
            "report_date": str(r.report_date) if r.report_date else None,
            "status": r.status,
            "uploaded_at": r.created_at.isoformat() if r.created_at else None,
            "biomarkers": [
                {
                    "test_name": b.test_name,
                    "canonical_name": b.canonical_name,
                    "value": b.value_numeric if b.value_numeric is not None else b.value_text,
                    "unit": b.unit,
                    "reference_min": b.reference_min,
                    "reference_max": b.reference_max,
                    "reference_text": b.reference_text,
                    "flag": b.flag
                }
                for b in r.biomarkers
            ],
            "ai_analysis": {
                "plain_summary": r.analysis.plain_summary if r.analysis else None,
                "terminology_glossary": r.analysis.terminology_glossary if r.analysis else [],
                "clinical_disclaimer": r.analysis.clinical_disclaimer if r.analysis else None,
                "generated_at": r.analysis.generated_at.isoformat() if (r.analysis and r.analysis.generated_at) else None
            } if r.analysis else None

        })

    # 3. Fetch symptom logs
    sym_q = select(SymptomLog).where(SymptomLog.user_id == current_user.id)
    syms = (await db.execute(sym_q)).scalars().all()
    symptoms_data = [
        {
            "id": s.id,
            "report_id": s.report_id,
            "primary_concern": s.primary_concern,
            "symptoms_list": s.symptoms_list,
            "duration_days": s.duration_days,
            "severity_score": s.severity_score,
            "body_region": s.body_region,
            "additional_notes": s.additional_notes,
            "logged_at": s.logged_at.isoformat() if s.logged_at else None
        }
        for s in syms
    ]

    # 4. Fetch appointments & consultation notes
    app_q = select(Appointment).where(
        Appointment.user_id == current_user.id
    ).options(selectinload(Appointment.doctor), selectinload(Appointment.consultation_note))
    appts = (await db.execute(app_q)).scalars().all()

    appointments_data = []
    consultation_notes_data = []
    for a in appts:
        appointments_data.append({
            "id": a.id,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.full_name if a.doctor else None,
            "appointment_date": str(a.appointment_date),
            "appointment_time": str(a.appointment_time),
            "status": a.status,
            "visit_reason": a.visit_reason,
            "patient_notes": a.patient_notes,
            "cancellation_reason": a.cancellation_reason
        })
        if a.consultation_note:
            cn = a.consultation_note
            consultation_notes_data.append({
                "id": cn.id,
                "appointment_id": a.id,
                "doctor_id": cn.doctor_id,
                "diagnosis": cn.diagnosis,
                "clinical_notes": cn.clinical_notes,
                "prescriptions": cn.prescriptions,
                "follow_up_recommendation": cn.follow_up_recommendation,
                "created_at": cn.created_at.isoformat() if cn.created_at else None
            })

    # 5. Fetch consent history
    con_q = select(Consent).where(Consent.user_id == current_user.id)
    cons = (await db.execute(con_q)).scalars().all()
    consent_history_data = [
        {
            "id": c.id,
            "consent_type": c.consent_type,
            "granted": c.granted,
            "granted_at": c.granted_at.isoformat() if c.granted_at else None,
            "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None
        }
        for c in cons
    ]

    now_iso = datetime.now(timezone.utc).isoformat()
    export_payload = {
        "export_metadata": {
            "platform": "VitaLens Health Platform",
            "version": "1.0",
            "compliance_standard": "Digital Personal Data Protection (DPDP) Act",
            "exported_at": now_iso,
            "user_id": current_user.id
        },
        "profile": profile_data,
        "reports_count": len(reports_data),
        "reports": reports_data,
        "medical_reports_count": len(reports_data),
        "medical_reports": reports_data,
        "symptom_logs_count": len(symptoms_data),
        "symptom_logs": symptoms_data,
        "appointments_count": len(appointments_data),
        "appointments": appointments_data,
        "consultation_notes_count": len(consultation_notes_data),
        "consultation_notes": consultation_notes_data,
        "consent_history": consent_history_data
    }


    # Record audit log
    await record_audit_log(
        db,
        action="EXPORT_USER_DATA",
        resource_type="User",
        resource_id=current_user.id,
        actor_user_id=current_user.id,
        metadata={"reports_count": len(reports_data), "appointments_count": len(appointments_data)}
    )

    return export_payload

@router.post("/delete-account")
@router.post("/me/delete-account", include_in_schema=False)
async def delete_patient_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    DPDP Right to Erasure: Soft-deletes user account, deactivates login,
    and immediately revokes all active refresh tokens.
    """
    current_user.is_active = False
    current_user.is_deleted = True

    # Revoke all active refresh tokens for this user
    now = datetime.now(timezone.utc)
    token_q = select(RefreshToken).where(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked_at.is_(None)
    )
    tokens = (await db.execute(token_q)).scalars().all()
    for tok in tokens:
        tok.revoked_at = now

    await db.commit()

    # Record audit log
    await record_audit_log(
        db,
        action="DELETE_ACCOUNT_REQUESTED",
        resource_type="User",
        resource_id=current_user.id,
        actor_user_id=current_user.id,
        metadata={"revoked_tokens_count": len(tokens), "scheduled_hard_delete": True}
    )

    return {
        "status": "SUCCESS",
        "message": "Your account has been deactivated and scheduled for permanent erasure. All active sessions have been terminated."
    }

@router.post("/abha/link")
@router.post("/me/abha/link", include_in_schema=False)
async def link_abha_number(
    payload: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Simulated ABHA linking endpoint:
    Validates 14-digit format and links ABHA number to current user profile without contacting real ABDM servers.
    """
    abha_number = payload.get("abha_number", "")
    clean_num = str(abha_number).replace("-", "").strip()
    if len(clean_num) != 14 or not clean_num.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ABHA number format. Must be 14 digits (e.g. 91-1234-5678-9012 or 91123456789012)."
        )

    formatted_abha = f"{clean_num[0:2]}-{clean_num[2:6]}-{clean_num[6:10]}-{clean_num[10:14]}"
    current_user.abha_number = formatted_abha
    await db.commit()
    await db.refresh(current_user)

    await record_audit_log(
        db,
        action="ABHA_NUMBER_LINKED",
        resource_type="User",
        resource_id=current_user.id,
        actor_user_id=current_user.id,
        metadata={"abha_number": formatted_abha, "simulation_mode": True}
    )

    return {
        "status": "LINKED",
        "message": "ABHA number linked successfully (simulated/mock).",
        "abha_number": formatted_abha,
        "user_id": current_user.id
    }

