import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class ReportAnalysis(Base):
    __tablename__ = "report_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False, unique=True)
    plain_summary = Column(Text, nullable=False)
    terminology_glossary = Column(JSON, default=list)  # list of {"term": "...", "definition": "..."}
    clinical_disclaimer = Column(Text, nullable=False)
    model_version = Column(String(100), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    report = relationship("MedicalReport", back_populates="analysis")
    specialty_recommendations = relationship("SpecialtyRecommendation", back_populates="report_analysis", cascade="all, delete-orphan")
