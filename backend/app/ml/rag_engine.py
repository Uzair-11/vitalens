"""
Clinical RAG Engine & Safety Guardrail Pipeline.

Features:
- Multi-report contextual chunk retrieval across patient history.
- Emergency red-flag safety interception before response delivery.
- Traceable grounded biomarker citations (zero ungrounded claims).
- Low-confidence (< 0.70) routing to clinical review queue / unreviewed labeling.
- Queryable audit trail persistence to `ai_interaction_logs`.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.report import MedicalReport
from app.models.biomarker import Biomarker
from app.models.report_embedding import ReportEmbedding
from app.models.ai_interaction_log import AIInteractionLog
from app.ml.specialty_matcher import detect_emergency_red_flags
from app.core.llm_provider import get_active_llm_provider

logger = logging.getLogger("vitalens.ai.rag")

CLINICAL_SAFETY_DISCLAIMER = (
    "Note: This AI-generated health insight is grounded in your uploaded laboratory reports "
    "and is intended for educational clarity only. It does not constitute medical diagnosis or treatment advice."
)

def answer_report_question(question: str, biomarkers: List[Dict[str, Any]], report_summary: str) -> Dict[str, Any]:
    """Synchronous helper for single-report biomarker QA queries."""
    q_lower = question.lower()
    citations = []
    answers = []
    for b in biomarkers:
        test_name = (b.get("test_name") or "").lower()
        canonical = (b.get("canonical_name") or "").lower()
        if (test_name and test_name in q_lower) or (canonical and canonical in q_lower):
            val = b.get("value_numeric") if b.get("value_numeric") is not None else b.get("value_text")
            unit = b.get("unit") or ""
            flag = b.get("flag", "NORMAL")
            citations.append(b.get("test_name"))
            answers.append(f"Regarding **{b.get('test_name')}**: your report indicates **{val} {unit}** (Flag: {flag}).")
    final_answer = "\n\n".join(answers) if answers else f"Summary: {report_summary}"
    return {
        "question": question,
        "answer": final_answer,
        "citations": citations,
        "disclaimer": CLINICAL_SAFETY_DISCLAIMER
    }


EMERGENCY_BANNER = (
    "🚨 **CRITICAL MEDICAL ALERT**: Your query mentions potential emergency symptoms. "
    "If you are experiencing chest pain, severe shortness of breath, sudden numbness, or acute distress, "
    "please contact emergency medical services (dial 112 / 911) or proceed to the nearest emergency room immediately.\n\n"
)

UNREVIEWED_LABEL = (
    "⚠️ **CLINICAL NOTICE: UNREVIEWED AI RESPONSE**\n"
    "This query has lower diagnostic confidence or ambiguous grounding in your current lab data. "
    "This item has been flagged for physician review in the clinical queue.\n\n"
)

async def execute_grounded_rag_qa(
    db: AsyncSession,
    user_id: str,
    question: str,
    report_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes grounded multi-report RAG query with safety guardrails.
    """
    # 1. Safety Guardrail Gate 1: Check Question for Acute Emergency Red Flags
    emergency_flags = detect_emergency_red_flags(question)
    is_emergency = len(emergency_flags) > 0

    # 2. Multi-Report Biomarker & Context Retrieval
    # If report_id is provided, search single report; else search all reports of user
    if report_id:
        report_q = select(MedicalReport).where(
            MedicalReport.id == report_id,
            MedicalReport.user_id == user_id
        ).options(selectinload(MedicalReport.biomarkers), selectinload(MedicalReport.analysis))
        reports = (await db.execute(report_q)).scalars().all()
    else:
        reports_q = select(MedicalReport).where(
            MedicalReport.user_id == user_id
        ).options(selectinload(MedicalReport.biomarkers), selectinload(MedicalReport.analysis))
        reports = (await db.execute(reports_q)).scalars().all()

    # Collect structured facts across all retrieved reports
    structured_biomarkers: List[Dict[str, Any]] = []
    context_chunks: List[str] = []

    for rep in reports:
        rep_date_str = str(rep.report_date) if rep.report_date else "Recent"
        if rep.analysis and rep.analysis.plain_summary:
            context_chunks.append(f"Report dated {rep_date_str} ({rep.report_type}): {rep.analysis.plain_summary}")

        for b in rep.biomarkers:
            structured_biomarkers.append({
                "id": b.id,
                "test_name": b.test_name,
                "canonical_name": b.canonical_name,
                "value_numeric": b.value_numeric,
                "value_text": b.value_text,
                "unit": b.unit,
                "reference_min": b.reference_min,
                "reference_max": b.reference_max,
                "reference_text": b.reference_text,
                "flag": b.flag,
                "report_id": rep.id,
                "report_date": rep_date_str
            })

    # 3. Invoke Deterministic Clinical RAG Provider
    provider = get_active_llm_provider()
    rag_result = await provider.generate_rag_response(question, context_chunks, structured_biomarkers)

    answer_text = rag_result["answer"]
    citations = rag_result.get("citations", [])
    confidence_score = rag_result.get("confidence_score", 1.0)
    model_provider = rag_result.get("provider", provider.provider_name)

    # 4. Safety Guardrail Gate 2: Low-Confidence Routing (< 0.70)
    if confidence_score < 0.70:
        review_status = "PENDING_REVIEW"
        answer_text = UNREVIEWED_LABEL + answer_text
    else:
        review_status = "VERIFIED"

    # 5. Safety Guardrail Gate 3: Prepend Emergency Warning if Flagged
    if is_emergency:
        answer_text = EMERGENCY_BANNER + answer_text

    # 6. Audit Logging: Persist queryable interaction record
    log_entry = AIInteractionLog(
        user_id=user_id,
        report_id=report_id,
        prompt=question,
        response_text=answer_text,
        confidence_score=confidence_score,
        citations=citations,
        is_emergency_flagged=is_emergency,
        review_status=review_status,
        model_provider=model_provider
    )
    db.add(log_entry)
    await db.commit()

    return {
        "question": question,
        "answer": answer_text,
        "citations": citations,
        "confidence_score": confidence_score,
        "is_emergency_flagged": is_emergency,
        "review_status": review_status,
        "model_provider": model_provider,
        "disclaimer": CLINICAL_SAFETY_DISCLAIMER
    }
