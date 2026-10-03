import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class BiomarkerExplanation(Base):
    """
    Database-backed clinical explanation bank for out-of-range lab markers.
    Used for retrieval-based layperson explanations with clinical review metadata.
    """
    __tablename__ = "biomarker_explanations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False, index=True)
    flag = Column(String(20), nullable=False, index=True)  # HIGH, LOW, NORMAL, CRITICAL, ABNORMAL
    explanation_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
