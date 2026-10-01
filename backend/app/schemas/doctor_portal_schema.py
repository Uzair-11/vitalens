from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import date, time, datetime

class WorkingHoursItem(BaseModel):
    day_of_week: int  # 0=Monday, ..., 6=Sunday
    start_time: str   # "09:00"
    end_time: str     # "17:00"
    slot_duration_minutes: int = 30
    is_active: bool = True

class SetWorkingHoursRequest(BaseModel):
    working_hours: List[WorkingHoursItem]

class ScheduleBlockCreateRequest(BaseModel):
    block_date: date
    start_time: Optional[str] = None  # e.g. "14:00" or None for whole day
    end_time: Optional[str] = None
    reason: Optional[str] = None

class ScheduleBlockResponse(BaseModel):
    id: str
    doctor_id: str
    block_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DoctorWorkingHoursResponse(BaseModel):
    id: str
    doctor_id: str
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class DoctorScheduleOverviewResponse(BaseModel):
    doctor_id: str
    recurring_hours: List[DoctorWorkingHoursResponse]
    schedule_blocks: List[ScheduleBlockResponse]
    active_available_slots_count: int

class DoctorStatsToday(BaseModel):
    today_appointments_count: int
    pending_requests_count: int
    completed_today_count: int
    total_consultations_completed: int
    active_patients_count: int

class DoctorMeResponse(BaseModel):
    doctor_id: str
    user_id: str
    full_name: str
    email: str
    specialty_id: str
    specialty_name: str
    qualification: str
    experience_years: int
    clinic_name: str
    address: str
    city: str
    consultation_fee: float
    rating: float
    review_count: int
    verification_status: str
    is_active: bool
    today_stats: DoctorStatsToday

class DoctorAppointmentItemResponse(BaseModel):
    id: str
    user_id: str
    patient_name: str
    patient_email: str
    patient_phone: Optional[str] = None
    appointment_date: date
    appointment_time: time
    status: str
    visit_reason: Optional[str] = None
    patient_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    report_id: Optional[str] = None
    has_consultation_notes: bool = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UpdateDoctorAppointmentStatusRequest(BaseModel):
    status: str  # CONFIRMED, COMPLETED, CANCELLED, NO_SHOW, RESCHEDULED
    cancellation_reason: Optional[str] = None

class ConsultationNoteRequest(BaseModel):
    diagnosis: Optional[str] = None
    clinical_notes: str
    prescriptions: Optional[str] = None
    follow_up_recommendation: Optional[str] = None

class ConsultationNoteResponse(BaseModel):
    id: str
    appointment_id: str
    doctor_id: str
    diagnosis: Optional[str] = None
    clinical_notes: str
    prescriptions: Optional[str] = None
    follow_up_recommendation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DoctorPatientDetailResponse(BaseModel):
    patient_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    biological_sex: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    appointments_with_doctor: List[DoctorAppointmentItemResponse]
    consultation_notes: List[ConsultationNoteResponse]
    shared_reports: List[Any] = []
