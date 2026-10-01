from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict, Union
from datetime import datetime

class SymptomIntakeRequest(BaseModel):
    report_id: Optional[str] = None
    primary_concern: str
    symptoms_list: List[str] = []
    duration_days: int = 1
    severity_score: int = 5  # 1-10
    body_region: str = "Whole Body"
    additional_notes: Optional[str] = None

class SymptomLogResponse(BaseModel):
    id: str
    user_id: str
    report_id: Optional[str] = None
    primary_concern: str
    symptoms_list: List[str] = []
    duration_days: int
    severity_score: int
    body_region: str
    additional_notes: Optional[str] = None
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SpecialtyRecommendationRequest(BaseModel):
    report_id: Optional[str] = None
    symptom_log_id: str

class SpecialtyRecommendationResponse(BaseModel):
    recommended_specialty_id: str
    recommended_specialty_name: str
    confidence_score: float
    rationale: str
    is_emergency_flagged: bool
    emergency_message: Optional[str] = None
    abnormal_biomarkers_considered: List[str] = []
    symptoms_considered: List[str] = []

class ReportQARequest(BaseModel):
    report_id: Optional[str] = None
    question: str

class ReportQAResponse(BaseModel):
    question: str
    answer: str
    citations: List[Any] = []
    confidence_score: float = 1.0
    is_emergency_flagged: bool = False
    review_status: str = "VERIFIED"
    model_provider: str = "deterministic-clinical-rules"
    disclaimer: str
