import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    specialty_id = Column(String(36), ForeignKey("medical_specialties.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    qualification = Column(String(255), nullable=False)
    experience_years = Column(Integer, default=0)
    clinic_name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    consultation_fee = Column(Float, default=800.0)
    rating = Column(Float, default=5.0)
    review_count = Column(Integer, default=0)
    profile_photo_url = Column(String(500), nullable=True)
    languages = Column(JSON, default=list)  # list of strings e.g. ["English", "Hindi"]
    bio = Column(Text, nullable=True)
    verification_status = Column(String(50), default="VERIFIED", nullable=False, index=True)  # PENDING, VERIFIED, REJECTED
    credential_documents = Column(JSON, default=list)  # list of strings/doc URLs
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="doctor_profile")
    specialty = relationship("MedicalSpecialty", back_populates="doctors")
    availability_slots = relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    working_hours = relationship("DoctorWorkingHours", back_populates="doctor", cascade="all, delete-orphan")
    schedule_blocks = relationship("DoctorScheduleBlock", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
    consultation_notes = relationship("ConsultationNote", back_populates="doctor", cascade="all, delete-orphan")
