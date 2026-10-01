import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class ConsultationNote(Base):
    __tablename__ = "consultation_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String(36), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    diagnosis = Column(String(255), nullable=True)
    clinical_notes = Column(Text, nullable=False)
    prescriptions = Column(Text, nullable=True)
    follow_up_recommendation = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    appointment = relationship("Appointment", back_populates="consultation_note")
    doctor = relationship("Doctor", back_populates="consultation_notes")
