import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class SymptomLog(Base):
    __tablename__ = "symptom_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="SET NULL"), nullable=True)
    primary_concern = Column(String(255), nullable=False)
    symptoms_list = Column(JSON, default=list)  # list of strings
    duration_days = Column(Integer, default=1)
    severity_score = Column(Integer, default=5)  # 1-10 scale
    body_region = Column(String(100), default="Whole Body")
    additional_notes = Column(Text, nullable=True)
    logged_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    user = relationship("User", back_populates="symptoms")
    report = relationship("MedicalReport", back_populates="symptom_logs")
    specialty_recommendations = relationship("SpecialtyRecommendation", back_populates="symptom_log", cascade="all, delete-orphan")
