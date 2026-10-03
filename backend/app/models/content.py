import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime, JSON, Boolean
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class BiomarkerReference(Base):
    __tablename__ = "biomarker_references"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_name = Column(String(255), nullable=False, unique=True, index=True)
    canonical_name = Column(String(255), nullable=False, index=True)
    synonyms = Column(JSON, default=list, nullable=True)
    category = Column(String(100), default="General Panel")
    default_unit = Column(String(50), nullable=True)
    ref_min = Column(Float, nullable=True)
    ref_max = Column(Float, nullable=True)
    critical_low = Column(Float, nullable=True)
    critical_high = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    term = Column(String(100), nullable=False, unique=True, index=True)
    definition = Column(Text, nullable=False)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
