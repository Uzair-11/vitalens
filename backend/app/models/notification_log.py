import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    recipient = Column(String(255), nullable=False)
    notification_type = Column(String(50), nullable=False)  # EMAIL, PUSH, SMS
    event_type = Column(String(100), nullable=False, index=True)  # APPOINTMENT_CONFIRMED, APPOINTMENT_CANCELLED, REPORT_ANALYSIS_COMPLETE
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, index=True)  # SENT, FAILED, SKIPPED_NO_CONSENT
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    user = relationship("User", back_populates="notification_logs")
