from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, time, datetime

class AppointmentCreate(BaseModel):
    doctor_id: str
    appointment_date: date
    appointment_time: time
    report_id: Optional[str] = None
    visit_reason: Optional[str] = "Routine Consultation"
    patient_notes: Optional[str] = None

class AppointmentCancelRequest(BaseModel):
    cancellation_reason: str = "Patient requested cancellation"

class AppointmentRescheduleRequest(BaseModel):
    new_date: date
    new_time: time

class AppointmentResponse(BaseModel):
    id: str
    user_id: str
    doctor_id: str
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    doctor_clinic: Optional[str] = None
    doctor_address: Optional[str] = None
    doctor_photo: Optional[str] = None
    consultation_fee: Optional[float] = None
    report_id: Optional[str] = None
    report_name: Optional[str] = None
    appointment_date: date
    appointment_time: time
    status: str
    payment_status: Optional[str] = "PAID"
    payment_id: Optional[str] = None
    payment_order_id: Optional[str] = None
    payment_amount: Optional[str] = None
    payment_currency: Optional[str] = "INR"
    visit_reason: Optional[str] = None
    patient_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
