from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date

class DataPoint(BaseModel):
    date: str
    value: float
    unit: str
    flag: str
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    report_id: str

class BiomarkerTrendSeries(BaseModel):
    canonical_name: str
    category: str
    data_points: List[DataPoint] = []

class ComparisonItem(BaseModel):
    canonical_name: str
    test_name: str
    unit: str
    report_1_value: Optional[float] = None
    report_1_flag: Optional[str] = None
    report_2_value: Optional[float] = None
    report_2_flag: Optional[str] = None
    delta: Optional[float] = None
    status_change: str  # "IMPROVED", "WORSENED", "STABLE", "NEW"
    explanation: str

class ReportComparisonResponse(BaseModel):
    report_1_id: str
    report_1_date: date
    report_2_id: str
    report_2_date: date
    items: List[ComparisonItem] = []
    clinical_disclaimer: str
