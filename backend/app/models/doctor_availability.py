import uuid
from sqlalchemy import Column, String, Date, Time, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class DoctorAvailability(Base):
    __tablename__ = "doctor_availabilities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    available_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=30)
    is_booked = Column(Boolean, default=False)
    booked_appointment_id = Column(String(36), nullable=True)

    # Relationships
    doctor = relationship("Doctor", back_populates="availability_slots")
