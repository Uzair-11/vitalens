import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Consent(Base):
    __tablename__ = "consents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    # Types: REPORT_ANALYSIS, AI_PROCESSING, DOCTOR_DATA_ACCESS, NOTIFICATIONS, MARKETING
    consent_type = Column(String(50), nullable=False, index=True)
    consent_version = Column(String(20), default='1.0', nullable=False)
    purpose = Column(String(255), nullable=True)
    granted = Column(Boolean, default=True, nullable=False)
    granted_at = Column(DateTime(timezone=True), default=utc_now)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="consents")
