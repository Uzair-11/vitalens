from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from app.core.database import get_db
from app.core.rbac import require_role
from app.models.user import User
from app.models.doctor import Doctor
from app.models.report import MedicalReport
from app.models.appointment import Appointment
from app.models.specialty import SpecialtyRecommendation

router = APIRouter()

@router.get("/dashboard")
async def get_admin_dashboard_analytics(
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN", "SUPPORT_STAFF")),
    db: AsyncSession = Depends(get_db)
):
    """
    Computes live aggregate analytics from real database tables.
    Accessible to SUPPORT_STAFF (read-only), ADMIN, and SUPER_ADMIN.
    """
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # 1. User Signups
    total_users_q = select(func.count(User.id))
    recent_users_q = select(func.count(User.id)).where(User.created_at >= week_ago)
    patients_q = select(func.count(User.id)).where(User.role == "PATIENT")

    total_users = (await db.execute(total_users_q)).scalar() or 0
    recent_users = (await db.execute(recent_users_q)).scalar() or 0
    patient_count = (await db.execute(patients_q)).scalar() or 0

    # 2. Doctor Verification Metrics
    total_docs = (await db.execute(select(func.count(Doctor.id)))).scalar() or 0
    verified_docs = (await db.execute(select(func.count(Doctor.id)).where(Doctor.verification_status == "VERIFIED", Doctor.is_active == True))).scalar() or 0
    pending_docs = (await db.execute(select(func.count(Doctor.id)).where(Doctor.verification_status == "PENDING"))).scalar() or 0
    rejected_docs = (await db.execute(select(func.count(Doctor.id)).where(Doctor.verification_status == "REJECTED"))).scalar() or 0

    # 3. Medical Report Processing
    total_reports = (await db.execute(select(func.count(MedicalReport.id)))).scalar() or 0
    completed_reports = (await db.execute(select(func.count(MedicalReport.id)).where(MedicalReport.status == "COMPLETED"))).scalar() or 0
    failed_reports = (await db.execute(select(func.count(MedicalReport.id)).where(MedicalReport.status == "FAILED"))).scalar() or 0

    # 4. Appointment Oversight & Rates
    total_appts = (await db.execute(select(func.count(Appointment.id)))).scalar() or 0
    confirmed_appts = (await db.execute(select(func.count(Appointment.id)).where(Appointment.status == "CONFIRMED"))).scalar() or 0
    completed_appts = (await db.execute(select(func.count(Appointment.id)).where(Appointment.status == "COMPLETED"))).scalar() or 0
    cancelled_appts = (await db.execute(select(func.count(Appointment.id)).where(Appointment.status == "CANCELLED"))).scalar() or 0
    noshow_appts = (await db.execute(select(func.count(Appointment.id)).where(Appointment.status == "NO_SHOW"))).scalar() or 0

    cancellation_rate = round((cancelled_appts / total_appts * 100), 1) if total_appts > 0 else 0.0
    completion_rate = round((completed_appts / total_appts * 100), 1) if total_appts > 0 else 0.0
    noshow_rate = round((noshow_appts / total_appts * 100), 1) if total_appts > 0 else 0.0

    return {
        "user_metrics": {
            "total_registered_users": total_users,
            "signups_this_week": recent_users,
            "patient_accounts": patient_count
        },
        "doctor_metrics": {
            "total_doctors": total_docs,
            "active_verified_doctors": verified_docs,
            "pending_verification": pending_docs,
            "rejected_doctors": rejected_docs,
            "verification_rate_pct": round((verified_docs / total_docs * 100), 1) if total_docs > 0 else 0.0
        },
        "report_metrics": {
            "total_reports_processed": total_reports,
            "successfully_analyzed": completed_reports,
            "failed_reports": failed_reports
        },
        "appointment_metrics": {
            "total_bookings": total_appts,
            "active_confirmed": confirmed_appts,
            "completed_consultations": completed_appts,
            "cancelled_bookings": cancelled_appts,
            "no_show_bookings": noshow_appts,
            "cancellation_rate_pct": cancellation_rate,
            "completion_rate_pct": completion_rate,
            "no_show_rate_pct": noshow_rate
        }
    }
