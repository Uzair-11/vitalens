from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import get_current_user_obj
from app.models.user import User
from app.models.report import MedicalReport
from app.integrations.abdm.fhir_mapper import map_report_to_fhir_bundle
from app.integrations.abdm.abha_client import abha_client

router = APIRouter()

@router.get("/fhir/reports/{report_id}")
async def get_report_as_fhir_bundle(
    report_id: str,
    current_user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db)
):
    """
    Transforms a patient's medical report and extracted biomarkers into a standard
    HL7 FHIR R4 Bundle for EHR / ABDM interoperability. Scoped strictly to the requesting user.
    """
    # 1. Query for the report belonging to the current user
    q = select(MedicalReport).where(
        MedicalReport.id == report_id,
        MedicalReport.user_id == current_user.id
    ).options(
        selectinload(MedicalReport.biomarkers),
        selectinload(MedicalReport.analysis)
    )
    res = await db.execute(q)
    report = res.scalars().first()

    if not report:
        # Cross-tenant check: if report exists under another user, return 403 Forbidden
        report_exists = (await db.execute(select(MedicalReport).where(MedicalReport.id == report_id))).scalars().first()
        if report_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot access another user's health report."
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    fhir_bundle = map_report_to_fhir_bundle(report, report.biomarkers, current_user)
    return fhir_bundle

@router.post("/abdm/verify-abha")
async def verify_patient_abha(
    payload: dict,
    current_user: User = Depends(get_current_user_obj)
):
    """Initiates ABHA ID validation and simulated OTP dispatch via ABDM gateway stub."""
    abha_num = payload.get("abha_number", "")
    return await abha_client.verify_abha_number(abha_num)
