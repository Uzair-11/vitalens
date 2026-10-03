import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.medical_specialty import MedicalSpecialty

def utc_now():
    return datetime.now(timezone.utc)

class SpecialtyRecommendation(Base):
    __tablename__ = "specialty_recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_analysis_id = Column(String(36), ForeignKey("report_analyses.id", ondelete="CASCADE"), nullable=True)
    symptom_log_id = Column(String(36), ForeignKey("symptom_logs.id", ondelete="CASCADE"), nullable=False)
    recommended_specialty_id = Column(String(36), ForeignKey("medical_specialties.id", ondelete="CASCADE"), nullable=False)
    rationale = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.85)
    is_emergency_flagged = Column(Boolean, default=False)
    review_status = Column(String(50), default="UNREVIEWED", index=True)  # UNREVIEWED, APPROVED, FLAGGED, OVERRIDDEN
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    report_analysis = relationship("ReportAnalysis", back_populates="specialty_recommendations")
    symptom_log = relationship("SymptomLog", back_populates="specialty_recommendations")
    recommended_specialty = relationship("MedicalSpecialty", back_populates="recommendations")
