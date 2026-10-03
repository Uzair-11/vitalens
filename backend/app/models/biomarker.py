import uuid
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Biomarker(Base):
    __tablename__ = "biomarkers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False, index=True)  # e.g., "Glucose, Fasting", "Hemoglobin"
    value_numeric = Column(Float, nullable=True)
    value_text = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    reference_min = Column(Float, nullable=True)
    reference_max = Column(Float, nullable=True)
    reference_text = Column(String(100), nullable=True)
    flag = Column(String(20), default="NORMAL", index=True, nullable=False)  # NORMAL, HIGH, LOW, CRITICAL, ABNORMAL
    category = Column(String(100), default="General Panel")  # Hematology, Lipid Profile, Liver Function, etc.

    # Relationships
    report = relationship("MedicalReport", back_populates="biomarkers")

    @property
    def clinical_interpretation(self):
        if self.flag and str(self.flag).upper() not in ["NORMAL"]:
            try:
                from app.ml.explainer_ai import retrieve_explanation
                explanation_text, conf = retrieve_explanation(self.canonical_name or self.test_name, self.flag)
                if conf >= 0.4 and not explanation_text.startswith("No confident match found"):
                    return explanation_text
            except Exception:
                pass
        return None
