from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.report import MedicalReport
from app.models.symptom_log import SymptomLog
from app.models.specialty import MedicalSpecialty, SpecialtyRecommendation
from app.schemas.ai_schema import (
    SymptomIntakeRequest, SymptomLogResponse,
    SpecialtyRecommendationRequest, SpecialtyRecommendationResponse,
    ReportQARequest, ReportQAResponse
)
from app.ml.specialty_matcher import recommend_specialty
from app.ml.rag_engine import answer_report_question
from app.core.consent import enforce_user_consent
from app.ml.tracer import AITracer

router = APIRouter()

@router.post("/symptoms", response_model=SymptomLogResponse, status_code=status.HTTP_201_CREATED)
async def log_user_symptoms(
    symptom_in: SymptomIntakeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logs patient-reported symptoms and concerns."""
    await enforce_user_consent(
        db,
        current_user.id,
        "AI_PROCESSING",
        "log symptoms and receive AI-driven health guidance"
    )
    symptom_log = SymptomLog(
        user_id=current_user.id,
        report_id=symptom_in.report_id,
        primary_concern=symptom_in.primary_concern,
        symptoms_list=symptom_in.symptoms_list,
        duration_days=symptom_in.duration_days,
        severity_score=symptom_in.severity_score,
        body_region=symptom_in.body_region,
        additional_notes=symptom_in.additional_notes
    )
    db.add(symptom_log)
    await db.commit()
    await db.refresh(symptom_log)
    return symptom_log

@router.post("/recommend-specialty", response_model=SpecialtyRecommendationResponse)
async def get_specialty_recommendation(
    rec_in: SpecialtyRecommendationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes hybrid AI specialty recommendation combining extracted report anomalies
    and patient health concerns. Telemetry captured in full for Super Admin AI Trace.
    """
    tracer = AITracer(
        endpoint="/api/v1/ai/recommend-specialty",
        operation="SPECIALTY_TRIAGE",
        user_id=str(current_user.id),
        user_role=str(getattr(current_user, "role", "PATIENT"))
    )
    
    client_ip = request.client.host if request.client else None
    tracer.record_step_1_request_received(
        client_ip=client_ip,
        metadata={"report_id": rec_in.report_id, "symptom_log_id": rec_in.symptom_log_id}
    )

    try:
        await enforce_user_consent(
            db,
            current_user.id,
            "AI_PROCESSING",
            "generate AI medical specialty recommendations"
        )

        # 1. Fetch symptom log
        symptom_q = select(SymptomLog).where(SymptomLog.id == rec_in.symptom_log_id, SymptomLog.user_id == current_user.id)
        symptom_res = await db.execute(symptom_q)
        symptom_log = symptom_res.scalars().first()
        if not symptom_log:
            tracer.record_step_2_user_input("UNKNOWN", [], 0, 0, "UNKNOWN")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symptom log record not found.")

        tracer.record_step_2_user_input(
            primary_concern=symptom_log.primary_concern,
            symptoms_list=symptom_log.symptoms_list or [],
            duration_days=symptom_log.duration_days or 1,
            severity_score=symptom_log.severity_score or 5,
            body_region=symptom_log.body_region or "Whole Body",
            additional_notes=symptom_log.additional_notes
        )

        # 2. Fetch report biomarkers if report_id is provided
        all_biomarkers = []
        abnormal_biomarkers = []
        if rec_in.report_id:
            report_q = select(MedicalReport).where(
                MedicalReport.id == rec_in.report_id,
                MedicalReport.user_id == current_user.id
            ).options(selectinload(MedicalReport.biomarkers), selectinload(MedicalReport.analysis))
            report_res = await db.execute(report_q)
            report = report_res.scalars().first()
            if report and report.biomarkers:
                for b in report.biomarkers:
                    b_dict = {
                        "test_name": b.test_name,
                        "canonical_name": b.canonical_name,
                        "value_numeric": b.value_numeric,
                        "value_text": getattr(b, "value_text", None),
                        "unit": b.unit,
                        "reference_min": getattr(b, "reference_min", None),
                        "reference_max": getattr(b, "reference_max", None),
                        "reference_text": getattr(b, "reference_text", None),
                        "flag": b.flag or "NORMAL"
                    }
                    all_biomarkers.append(b_dict)
                    if b.flag and b.flag != "NORMAL":
                        abnormal_biomarkers.append(b_dict)

        tracer.record_step_3_report_data(
            report_id=rec_in.report_id,
            biomarkers=all_biomarkers,
            extraction_status="SUCCESS" if all_biomarkers or not rec_in.report_id else "WARNING"
        )
        tracer.record_step_4_clinical_flagging(all_biomarkers)

        # 3. Execute PyTorch deep learning recommendation engine
        recommendation = recommend_specialty(
            primary_concern=symptom_log.primary_concern,
            symptoms_list=symptom_log.symptoms_list or [],
            body_region=symptom_log.body_region or "Whole Body",
            abnormal_biomarkers=abnormal_biomarkers,
            severity_score=symptom_log.severity_score or 5,
            duration_days=symptom_log.duration_days or 7,
            tracer=tracer
        )

        # 4. Map recommendation to database MedicalSpecialty
        spec_name = recommendation["recommended_specialty_name"]
        spec_q = select(MedicalSpecialty).where(MedicalSpecialty.name.ilike(f"%{spec_name}%"))
        spec_res = await db.execute(spec_q)
        specialty_obj = spec_res.scalars().first()

        if not specialty_obj:
            # Fallback to General Medicine
            gen_q = select(MedicalSpecialty).where(MedicalSpecialty.name == "General Medicine")
            gen_res = await db.execute(gen_q)
            specialty_obj = gen_res.scalars().first()

        specialty_id = specialty_obj.id if specialty_obj else "gen-med-default-id"
        specialty_title = specialty_obj.name if specialty_obj else spec_name

        # 5. Persist recommendation record
        rec_record = SpecialtyRecommendation(
            symptom_log_id=symptom_log.id,
            recommended_specialty_id=specialty_id,
            rationale=recommendation["rationale"],
            confidence_score=recommendation["confidence_score"],
            is_emergency_flagged=recommendation["is_emergency_flagged"]
        )
        db.add(rec_record)
        await db.commit()

        response_payload = {
            "recommended_specialty_id": specialty_id,
            "recommended_specialty_name": specialty_title,
            "confidence_score": recommendation["confidence_score"],
            "rationale": recommendation["rationale"],
            "is_emergency_flagged": recommendation["is_emergency_flagged"],
            "emergency_message": recommendation["emergency_message"],
            "abnormal_biomarkers_considered": recommendation["abnormal_biomarkers_considered"],
            "symptoms_considered": recommendation["symptoms_considered"],
            "trace_id": tracer.trace_id
        }
        tracer.record_step_11_api_response(http_status=200, response_body=response_payload)
        return response_payload
    except Exception as exc:
        if tracer.status != "FAILED":
            tracer.status = "FAILED"
            tracer.error_step = "EXECUTION_EXCEPTION"
            tracer.error_message = str(exc)
        raise exc
    finally:
        await tracer.finalize(db)

@router.post("/qa", response_model=ReportQAResponse)
async def ask_report_question(
    qa_in: ReportQARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Answers patient questions grounded across multi-report laboratory context
    with safety guardrails, citation verification, and emergency interception.
    """
    await enforce_user_consent(
        db,
        current_user.id,
        "AI_PROCESSING",
        "query AI interactive report insights"
    )

    if qa_in.report_id:
        report_q = select(MedicalReport).where(
            MedicalReport.id == qa_in.report_id,
            MedicalReport.user_id == current_user.id
        )
        report_res = await db.execute(report_q)
        report = report_res.scalars().first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    from app.ml.rag_engine import execute_grounded_rag_qa
    return await execute_grounded_rag_qa(
        db=db,
        user_id=current_user.id,
        question=qa_in.question,
        report_id=qa_in.report_id
    )
