from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.history_schema import BiomarkerTrendSeries, ReportComparisonResponse
from app.services.history_service import get_biomarker_trends, compare_two_reports

router = APIRouter()

@router.get("/trends", response_model=List[BiomarkerTrendSeries])
async def get_trends(
    canonical_names: List[str] = Query(default=["Glucose", "Hemoglobin", "Cholesterol", "Creatinine", "TSH"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves time-series data for tracked biomarkers across the user's historical reports."""
    return await get_biomarker_trends(db, current_user.id, canonical_names)

@router.get("/compare", response_model=ReportComparisonResponse)
async def compare_reports(
    report_1_id: str = Query(...),
    report_2_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates side-by-side comparative biomarker delta analysis between two reports."""
    return await compare_two_reports(db, current_user.id, report_1_id, report_2_id)
