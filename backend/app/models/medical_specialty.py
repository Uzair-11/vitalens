import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class MedicalSpecialty(Base):
    __tablename__ = "medical_specialties"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon_name = Column(String(50), default="stethoscope")
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    doctors = relationship("Doctor", back_populates="specialty")
    recommendations = relationship("SpecialtyRecommendation", back_populates="recommended_specialty")
