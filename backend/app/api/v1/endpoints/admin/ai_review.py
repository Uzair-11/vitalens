from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.rbac import require_role
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.specialty import SpecialtyRecommendation, MedicalSpecialty
from app.models.symptom_log import SymptomLog

router = APIRouter()

class AIReviewActionRequest(BaseModel):
    action: str  # "APPROVE", "FLAG", "OVERRIDE"
    override_specialty_id: Optional[str] = None
    reviewer_notes: Optional[str] = None

@router.get("/")
async def list_ai_recommendations_for_review(
    status_filter: Optional[str] = Query(None, description="Filter by review status (UNREVIEWED, APPROVED, FLAGGED, OVERRIDDEN)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN", "SUPPORT_STAFF")),
    db: AsyncSession = Depends(get_db)
):
    """Clinical reviewer lists AI specialty recommendations with symptom context and confidence scores."""
    q = select(SpecialtyRecommendation).options(
        selectinload(SpecialtyRecommendation.recommended_specialty),
        selectinload(SpecialtyRecommendation.symptom_log)
    ).order_by(SpecialtyRecommendation.created_at.desc())

    if status_filter:
        q = q.where(SpecialtyRecommendation.review_status == status_filter.upper())

    q = q.offset(skip).limit(limit)
    res = await db.execute(q)
    items = res.scalars().all()

    return [
        {
            "id": r.id,
            "symptom_log_id": r.symptom_log_id,
            "primary_concern": r.symptom_log.primary_concern if r.symptom_log else None,
            "recommended_specialty_id": r.recommended_specialty_id,
            "specialty_name": r.recommended_specialty.name if r.recommended_specialty else "Unknown",
            "confidence_score": r.confidence_score,
            "is_emergency_flagged": r.is_emergency_flagged,
            "rationale": r.rationale,
            "review_status": r.review_status,
            "reviewed_by": r.reviewed_by,
            "reviewed_at": r.reviewed_at,
            "created_at": r.created_at
        }
        for r in items
    ]

@router.patch("/{recommendation_id}")
async def review_ai_recommendation(
    recommendation_id: str,
    data: Optional[AIReviewActionRequest] = None,
    action: Optional[str] = Query(None, description="Action query fallback (APPROVE, FLAG, OVERRIDE)"),
    override_specialty_id: Optional[str] = Query(None, description="Specialty ID to assign on OVERRIDE"),
    current_admin: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin/Clinician approves, flags, or overrides an AI specialty recommendation.
    Records reviewer name, timestamp, and audit trail.
    """
    q = select(SpecialtyRecommendation).where(SpecialtyRecommendation.id == recommendation_id)
    res = await db.execute(q)
    rec = res.scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="AI Recommendation record not found.")

    chosen_action = (data.action if data else action or "APPROVE").upper()
    if chosen_action not in ["APPROVE", "FLAG", "OVERRIDDEN", "OVERRIDE"]:
        raise HTTPException(status_code=400, detail="Invalid review action. Must be APPROVE, FLAG, or OVERRIDE.")

    status_map = {
        "APPROVE": "APPROVED",
        "FLAG": "FLAGGED",
        "OVERRIDE": "OVERRIDDEN",
        "OVERRIDDEN": "OVERRIDDEN"
    }
    rec.review_status = status_map.get(chosen_action, "APPROVED")
    rec.reviewed_by = current_admin.full_name or current_admin.email
    rec.reviewed_at = datetime.now(timezone.utc)

    override_id = (data.override_specialty_id if data else None) or override_specialty_id
    if rec.review_status == "OVERRIDDEN" and override_id:
        # Validate target specialty
        spec_q = select(MedicalSpecialty).where(MedicalSpecialty.id == override_id)
        spec_res = await db.execute(spec_q)
        if not spec_res.scalars().first():
            raise HTTPException(status_code=404, detail="Target override medical specialty not found.")
        rec.recommended_specialty_id = override_id

    await db.commit()
    await db.refresh(rec)

    # Record Audit Log
    await record_audit_log(
        db, action=f"AI_REVIEW_{rec.review_status}", resource_type="SpecialtyRecommendation",
        resource_id=rec.id, actor_user_id=current_admin.id, metadata={"action": chosen_action, "override_id": override_id}
    )

    return {
        "id": rec.id,
        "review_status": rec.review_status,
        "reviewed_by": rec.reviewed_by,
        "reviewed_at": rec.reviewed_at,
        "recommended_specialty_id": rec.recommended_specialty_id,
        "message": f"AI recommendation marked as {rec.review_status}."
    }
