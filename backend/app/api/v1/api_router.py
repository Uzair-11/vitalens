from fastapi import APIRouter
from app.api.v1.endpoints import auth, reports, ai, doctors, appointments, history, integrations, privacy, payments

from app.api.v1.endpoints.admin import (
    doctors as admin_doctors,
    users as admin_users,
    appointments as admin_appointments,
    content as admin_content,
    analytics as admin_analytics,
    ai_review as admin_ai_review,
    ai_trace as admin_ai_trace
)
from app.api.v1.endpoints.doctor import (
    me as doctor_me,
    schedule as doctor_schedule,
    appointments as doctor_appointments,
    patients as doctor_patients
)

api_router = APIRouter()

# Patient & Core Endpoints (Existing & Extended)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Profile"])
api_router.include_router(privacy.router, prefix="/me", tags=["Privacy & Consent Center"])
api_router.include_router(privacy.router, prefix="/auth/me", tags=["Privacy & Consent Center"], include_in_schema=False)
api_router.include_router(reports.router, prefix="/reports", tags=["Medical Reports"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Healthcare Navigation & Q&A"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctors & Specialties"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointment Booking"])
api_router.include_router(payments.router, prefix="/appointments", tags=["Appointment Payments"])
api_router.include_router(history.router, prefix="/history", tags=["Longitudinal Trends & Comparison"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["EHR & ABDM Interoperability"])


# Admin Portal Subrouters
api_router.include_router(admin_analytics.router, prefix="/admin/analytics", tags=["Admin Analytics"])
api_router.include_router(admin_doctors.router, prefix="/admin/doctors", tags=["Admin Doctor Management"])
api_router.include_router(admin_users.router, prefix="/admin/users", tags=["Admin User Management"])
api_router.include_router(admin_appointments.router, prefix="/admin/appointments", tags=["Admin Appointment Oversight"])
api_router.include_router(admin_content.router, prefix="/admin/content", tags=["Admin Content & Thresholds"])
api_router.include_router(admin_ai_review.router, prefix="/admin/ai-review", tags=["Admin AI Recommendation Review"])
api_router.include_router(admin_ai_trace.router, prefix="/admin/ai-trace", tags=["Super Admin AI Trace & Observability"])

# Doctor Portal Subrouters
api_router.include_router(doctor_me.router, prefix="/doctor", tags=["Doctor Dashboard & Profile"])
api_router.include_router(doctor_schedule.router, prefix="/doctor", tags=["Doctor Schedule & Availability"])
api_router.include_router(doctor_appointments.router, prefix="/doctor", tags=["Doctor Appointments & Clinical Notes"])
api_router.include_router(doctor_patients.router, prefix="/doctor", tags=["Doctor Consented Patient Records"])

