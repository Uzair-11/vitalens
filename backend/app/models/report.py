import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Date, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    report_type = Column(String(100), default="Blood / Laboratory Test")
    report_date = Column(Date, default=lambda: datetime.now(timezone.utc).date())
    status = Column(String(50), default="PENDING")  # PENDING, ANALYZING, COMPLETED, FAILED
    file_hash_sha256 = Column(String(64), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    user = relationship("User", back_populates="reports")
    biomarkers = relationship("Biomarker", back_populates="report", cascade="all, delete-orphan")
    analysis = relationship("ReportAnalysis", back_populates="report", uselist=False, cascade="all, delete-orphan")
    symptom_logs = relationship("SymptomLog", back_populates="report")
    appointments = relationship("Appointment", back_populates="report")
