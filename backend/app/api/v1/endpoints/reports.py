from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.report_schema import ReportSummaryResponse, ReportDetailResponse
from app.services.report_service import (
    save_uploaded_report, analyze_report, list_user_reports, get_report_detail, delete_report
)

from app.core.consent import enforce_user_consent

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_medical_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a PDF or Image medical report."""
    report = await save_uploaded_report(db, current_user.id, file)
    return {
        "report_id": report.id,
        "file_name": report.file_name,
        "status": report.status,
        "message": "Report uploaded successfully. Ready for AI analysis."
    }

@router.post("/{report_id}/analyze", response_model=ReportDetailResponse)
async def trigger_report_analysis(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Triggers OCR, biomarker extraction, range evaluation, and plain-English explanation."""
    # Enforce active consent for REPORT_ANALYSIS
    await enforce_user_consent(
        db,
        current_user.id,
        "REPORT_ANALYSIS",
        "extract biomarkers and analyze medical reports"
    )
    return await analyze_report(db, current_user.id, report_id)


@router.get("", response_model=List[ReportSummaryResponse], include_in_schema=False)
@router.get("/", response_model=List[ReportSummaryResponse])
async def get_all_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists all uploaded reports for the current user."""
    return await list_user_reports(db, current_user.id)

@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_single_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches details, extracted biomarkers, and explanation for a specific report."""
    return await get_report_detail(db, current_user.id, report_id)

@router.delete("/{report_id}")
async def remove_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a report and its extracted records."""
    await delete_report(db, current_user.id, report_id)
    return {"status": "DELETED", "message": "Report removed successfully."}
