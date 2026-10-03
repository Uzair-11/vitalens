import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Boolean, JSON, DateTime, Integer
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class AITrace(Base):
    """
    Super Admin technical observability log for AI processing pipelines.
    Tracks every stage: raw input, report parsing, canonical mapping,
    symptom encoding, feature vectorization, PyTorch inference, and final decision.
    """
    __tablename__ = "ai_traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    user_role = Column(String(50), default="PATIENT")
    endpoint = Column(String(255), nullable=False)
    operation = Column(String(50), default="SPECIALTY_TRIAGE", index=True)
    status = Column(String(50), default="SUCCESS", index=True)  # SUCCESS, WARNING, FAILED
    total_duration_ms = Column(Float, default=0.0)

    # Model metadata
    model_name = Column(String(100), default="VitaLensSpecialtyNet")
    model_version = Column(String(50), default="specialty-net-v1.0.0")
    preprocessing_version = Column(String(50), default="feature-pipeline-v1.0")

    # High-level outputs for instant querying and filtering
    primary_concern = Column(Text, nullable=True)
    top_specialty = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)
    is_emergency_flagged = Column(Boolean, default=False, index=True)

    # Error tracking
    error_step = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    # Structured 11-step telemetry data
    steps = Column(JSON, nullable=False)
    input_snapshot = Column(JSON, nullable=True)
    output_snapshot = Column(JSON, nullable=True)
