import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, Time, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="SET NULL"), nullable=True)
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(Time, nullable=False)
    status = Column(String(50), default="CONFIRMED", nullable=False, index=True)  # CONFIRMED, COMPLETED, CANCELLED, RESCHEDULED, NO_SHOW, PENDING_PAYMENT
    payment_status = Column(String(50), default="PAID", nullable=False, index=True)  # PENDING, PAID, FAILED, REFUNDED
    payment_id = Column(String(100), nullable=True, index=True)
    payment_order_id = Column(String(100), nullable=True, index=True)
    payment_amount = Column(String(50), nullable=True)
    payment_currency = Column(String(10), default="INR", nullable=True)
    visit_reason = Column(String(255), nullable=True)
    patient_notes = Column(Text, nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    report = relationship("MedicalReport", back_populates="appointments")
    consultation_note = relationship("ConsultationNote", back_populates="appointment", uselist=False, cascade="all, delete-orphan")
