import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class ReportEmbedding(Base):
    """
    Stores text chunks and vector embeddings of patient medical reports for multi-report RAG retrieval.
    Designed for seamless future migration to native pgvector VECTOR column type upon cloud deployment.
    """
    __tablename__ = "report_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_type = Column(String(50), default="BIOMARKERS_SUMMARY")  # BIOMARKERS_SUMMARY, PLAIN_EXPLANATION, CLINICAL_NOTE
    content_chunk = Column(Text, nullable=False)
    embedding_json = Column(JSON, nullable=True)  # Stores float array vector embedding
    metadata_json = Column(JSON, nullable=True)   # Structured search attributes (dates, biomarker names, flags)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    report = relationship("MedicalReport", backref="embeddings")
    user = relationship("User", backref="report_embeddings")
