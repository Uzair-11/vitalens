import uuid
from datetime import datetime, timezone, time
from sqlalchemy import Column, String, Date, Time, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class DoctorWorkingHours(Base):
    __tablename__ = "doctor_working_hours"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    doctor = relationship("Doctor", back_populates="working_hours")


class DoctorScheduleBlock(Base):
    __tablename__ = "doctor_schedule_blocks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    block_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=True)  # None = full day block
    end_time = Column(Time, nullable=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    doctor = relationship("Doctor", back_populates="schedule_blocks")
