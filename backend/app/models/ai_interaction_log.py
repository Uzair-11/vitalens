import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class AIInteractionLog(Base):
    """
    Queryable audit log for all clinical AI and RAG interactions.
    Records safety flags, confidence scores, source citations, and human review status.
    """
    __tablename__ = "ai_interaction_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    prompt = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False, default=1.0)
    citations = Column(JSON, nullable=True)  # List of grounded biomarker references
    is_emergency_flagged = Column(Boolean, default=False, nullable=False, index=True)
    review_status = Column(String(50), default="VERIFIED", nullable=False, index=True)  # VERIFIED, UNREVIEWED, PENDING_REVIEW, REVIEWED_APPROVED
    model_provider = Column(String(100), default="deterministic-clinical-rules", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    user = relationship("User", backref="ai_logs")
    report = relationship("MedicalReport", backref="ai_logs")
