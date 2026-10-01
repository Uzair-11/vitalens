from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class BiomarkerSchema(BaseModel):
    id: Optional[str] = None
    test_name: str
    canonical_name: str
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    reference_text: Optional[str] = None
    flag: str = "NORMAL"
    category: str = "General"

    model_config = ConfigDict(from_attributes=True)

class GlossaryItem(BaseModel):
    term: str
    definition: str

class ReportAnalysisSchema(BaseModel):
    id: Optional[str] = None
    plain_summary: str
    terminology_glossary: List[GlossaryItem] = []
    clinical_disclaimer: str
    generated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReportSummaryResponse(BaseModel):
    id: str
    file_name: str
    report_type: str
    report_date: date
    status: str
    created_at: datetime
    biomarker_count: Optional[int] = 0
    abnormal_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class ReportDetailResponse(BaseModel):
    id: str
    file_name: str
    report_type: str
    report_date: date
    status: str
    created_at: datetime
    biomarkers: List[BiomarkerSchema] = []
    analysis: Optional[ReportAnalysisSchema] = None

    model_config = ConfigDict(from_attributes=True)
