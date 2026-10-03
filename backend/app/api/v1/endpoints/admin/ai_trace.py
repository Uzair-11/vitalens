"""
Super Admin AI Trace & Observability Endpoints.
Provides technical visibility into the entire AI clinical recommendation pipeline,
including live telemetry stream, trace audit logs, search & filtering, and interactive simulation.
Restricted exclusively to SUPER_ADMIN role.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.rbac import require_role
from app.core.security import decode_access_token
from app.models.user import User
from app.models.ai_trace import AITrace
from app.ml.tracer import AITracer, trace_broadcaster
from app.ml.specialty_matcher import recommend_specialty
from app.services.user_service import get_user_profile

router = APIRouter()

# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------

class TraceSimulationRequest(BaseModel):
    primary_concern: str
    symptoms_list: List[str] = Field(default_factory=list)
    body_region: str = "Whole Body"
    severity_score: int = Field(5, ge=1, le=10)
    duration_days: int = Field(7, ge=1)
    biomarkers: List[Dict[str, Any]] = Field(default_factory=list)

class TraceSummaryItem(BaseModel):
    id: str
    trace_id: str
    created_at: datetime
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    endpoint: str
    operation: str
    status: str
    total_duration_ms: float
    primary_concern: Optional[str] = None
    top_specialty: Optional[str] = None
    confidence_score: Optional[float] = None
    is_emergency_flagged: bool
    step_count: int

class TraceListResponse(BaseModel):
    total: int
    items: List[TraceSummaryItem]

# -----------------------------------------------------------------------------
# SSE Authentication Helper
# -----------------------------------------------------------------------------

async def get_super_admin_sse_user(
    token: Optional[str] = Query(None),
    auth_header: Optional[str] = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Verifies SUPER_ADMIN privileges for SSE live stream via either query param or bearer header."""
    raw_token = token
    if not raw_token and auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header.split("Bearer ")[1].strip()
        
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required for live trace streaming."
        )
        
    payload = decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )
        
    user = await get_user_profile(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
        
    if user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Super Admin role required for AI trace observability."
        )
        
    return user

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("", response_model=TraceListResponse, include_in_schema=False)
@router.get("/", response_model=TraceListResponse)
async def list_ai_traces(
    search: Optional[str] = Query(None, description="Search by trace ID, primary concern, or specialty"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, WARNING, FAILED)"),
    specialty: Optional[str] = Query(None, description="Filter by top recommended specialty"),
    start_date: Optional[str] = Query(None, description="Filter from start date (ISO string)"),
    end_date: Optional[str] = Query(None, description="Filter to end date (ISO string)"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    current_user: User = Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Lists AI execution traces with multi-field search and technical status filters."""
    query = select(AITrace)
    count_query = select(func.count(AITrace.id))

    if status:
        query = query.where(AITrace.status == status.upper())
        count_query = count_query.where(AITrace.status == status.upper())

    if specialty:
        query = query.where(AITrace.top_specialty.ilike(f"%{specialty.strip()}%"))
        count_query = count_query.where(AITrace.top_specialty.ilike(f"%{specialty.strip()}%"))

    if search:
        search_term = f"%{search.strip()}%"
        search_filter = (
            AITrace.trace_id.ilike(search_term) |
            AITrace.primary_concern.ilike(search_term) |
            AITrace.top_specialty.ilike(search_term) |
            AITrace.endpoint.ilike(search_term)
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if start_date:
        try:
            dt_start = datetime.fromisoformat(start_date)
            query = query.where(AITrace.created_at >= dt_start)
            count_query = count_query.where(AITrace.created_at >= dt_start)
        except ValueError:
            pass

    if end_date:
        try:
            dt_end = datetime.fromisoformat(end_date)
            query = query.where(AITrace.created_at <= dt_end)
            count_query = count_query.where(AITrace.created_at <= dt_end)
        except ValueError:
            pass

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(desc(AITrace.created_at)).offset(skip).limit(limit)
    res = await db.execute(query)
    records = res.scalars().all()

    items = []
    for r in records:
        items.append(TraceSummaryItem(
            id=r.id,
            trace_id=r.trace_id,
            created_at=r.created_at,
            user_id=r.user_id,
            user_role=r.user_role,
            endpoint=r.endpoint,
            operation=r.operation,
            status=r.status,
            total_duration_ms=r.total_duration_ms or 0.0,
            primary_concern=r.primary_concern,
            top_specialty=r.top_specialty,
            confidence_score=r.confidence_score,
            is_emergency_flagged=bool(r.is_emergency_flagged),
            step_count=len(r.steps) if isinstance(r.steps, list) else 0
        ))

    return TraceListResponse(total=total, items=items)

@router.get("/stats")
async def get_ai_trace_stats(
    current_user: User = Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Returns aggregated performance and routing metrics across recent AI traces."""
    total_q = select(func.count(AITrace.id))
    total_res = await db.execute(total_q)
    total_traces = total_res.scalar() or 0

    # Status Breakdown
    status_q = select(AITrace.status, func.count(AITrace.id)).group_by(AITrace.status)
    status_res = await db.execute(status_q)
    status_breakdown = {s: count for s, count in status_res.all()}

    # Average Duration
    avg_q = select(func.avg(AITrace.total_duration_ms))
    avg_res = await db.execute(avg_q)
    avg_duration_ms = round(float(avg_res.scalar() or 0.0), 2)

    # Top Recommended Specialties
    spec_q = select(AITrace.top_specialty, func.count(AITrace.id)).where(
        AITrace.top_specialty.isnot(None)
    ).group_by(AITrace.top_specialty).order_by(desc(func.count(AITrace.id))).limit(10)
    spec_res = await db.execute(spec_q)
    top_specialties = {s: count for s, count in spec_res.all()}

    # Emergency Count
    emerg_q = select(func.count(AITrace.id)).where(AITrace.is_emergency_flagged == True)
    emerg_res = await db.execute(emerg_q)
    emergency_count = emerg_res.scalar() or 0

    return {
        "total_traces": total_traces,
        "status_breakdown": status_breakdown,
        "average_duration_ms": avg_duration_ms,
        "top_specialties": top_specialties,
        "emergency_intercepts": emergency_count
    }

@router.get("/stream/live")
async def stream_live_ai_traces(
    user: User = Depends(get_super_admin_sse_user)
):
    """
    Server-Sent Events (SSE) live stream broadcasting AI execution steps
    and completed traces in real time to the Super Admin console.
    """
    queue = trace_broadcaster.subscribe()

    async def event_generator():
        try:
            # Yield initial connection confirmation
            init_payload = json.dumps({
                "type": "CONNECTION_ESTABLISHED",
                "message": "Connected to VitaLens Live AI Trace Stream",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            yield f"data: {init_payload}\n\n"

            while True:
                try:
                    # Wait up to 15 seconds for an event before sending keepalive
                    event_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    # Send SSE keep-alive comment
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            trace_broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/simulate")
async def simulate_ai_pipeline(
    sim_in: TraceSimulationRequest,
    current_user: User = Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin Diagnostic Sandbox: Runs a full end-to-end trace simulation
    against the real production model and pipeline without altering any patient data.
    """
    tracer = AITracer(
        endpoint="/api/v1/admin/ai-trace/simulate",
        operation="TRACE_SIMULATION",
        user_id=str(current_user.id),
        user_role="SUPER_ADMIN"
    )

    # Step 1: Request Received
    tracer.record_step_1_request_received(
        client_ip="internal_admin_sandbox",
        metadata={
            "simulation": True,
            "biomarker_count": len(sim_in.biomarkers),
            "symptoms_count": len(sim_in.symptoms_list)
        }
    )

    # Step 2: User Input
    tracer.record_step_2_user_input(
        primary_concern=sim_in.primary_concern,
        symptoms_list=sim_in.symptoms_list,
        duration_days=sim_in.duration_days,
        severity_score=sim_in.severity_score,
        body_region=sim_in.body_region,
        additional_notes="Super Admin Diagnostic Simulation"
    )

    # Step 3: Report Data
    sanitized_biomarkers = []
    abnormal_biomarkers = []
    for b in sim_in.biomarkers:
        b_dict = {
            "test_name": b.get("test_name", ""),
            "canonical_name": b.get("canonical_name", b.get("test_name", "")),
            "value_numeric": b.get("value_numeric") if b.get("value_numeric") is not None else b.get("value"),
            "value_text": b.get("value_text"),
            "unit": b.get("unit", ""),
            "reference_min": b.get("reference_min"),
            "reference_max": b.get("reference_max"),
            "reference_text": b.get("reference_text"),
            "flag": b.get("flag", "NORMAL")
        }
        sanitized_biomarkers.append(b_dict)
        if b_dict["flag"] and b_dict["flag"] != "NORMAL":
            abnormal_biomarkers.append(b_dict)

    tracer.record_step_3_report_data(
        report_id="SIMULATED_REPORT",
        biomarkers=sanitized_biomarkers,
        extraction_status="SUCCESS"
    )

    # Step 4: Clinical Flagging
    tracer.record_step_4_clinical_flagging(sanitized_biomarkers)

    # Step 5 - 10: PyTorch Inference & Decision (via recommend_specialty)
    recommendation = recommend_specialty(
        primary_concern=sim_in.primary_concern,
        symptoms_list=sim_in.symptoms_list,
        body_region=sim_in.body_region,
        abnormal_biomarkers=abnormal_biomarkers,
        severity_score=sim_in.severity_score,
        duration_days=sim_in.duration_days,
        tracer=tracer
    )

    # Step 11: API Response
    sim_response = {
        "simulation": True,
        "trace_id": tracer.trace_id,
        "recommended_specialty_name": recommendation.get("recommended_specialty_name"),
        "confidence_score": recommendation.get("confidence_score"),
        "rationale": recommendation.get("rationale"),
        "is_emergency_flagged": recommendation.get("is_emergency_flagged"),
        "emergency_message": recommendation.get("emergency_message"),
        "abnormal_biomarkers_considered": recommendation.get("abnormal_biomarkers_considered", []),
        "symptoms_considered": recommendation.get("symptoms_considered", []),
        "model_used": recommendation.get("model_used")
    }
    tracer.record_step_11_api_response(http_status=200, response_body=sim_response)

    # Finalize & persist
    trace_record = await tracer.finalize(db)

    return {
        "trace_id": trace_record.trace_id,
        "created_at": trace_record.created_at,
        "status": trace_record.status,
        "total_duration_ms": trace_record.total_duration_ms,
        "model_metadata": {
            "model_name": trace_record.model_name,
            "model_version": trace_record.model_version,
            "preprocessing_version": trace_record.preprocessing_version
        },
        "recommendation": sim_response,
        "steps": trace_record.steps,
        "input_snapshot": trace_record.input_snapshot,
        "output_snapshot": trace_record.output_snapshot
    }

@router.get("/{trace_id}")
async def get_ai_trace_detail(
    trace_id: str,
    current_user: User = Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full technical telemetry and step-by-step breakdown for a specific AI trace."""
    query = select(AITrace).where(AITrace.trace_id == trace_id)
    res = await db.execute(query)
    trace = res.scalars().first()

    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI trace with ID '{trace_id}' not found."
        )

    return {
        "id": trace.id,
        "trace_id": trace.trace_id,
        "created_at": trace.created_at,
        "user_id": trace.user_id,
        "user_role": trace.user_role,
        "endpoint": trace.endpoint,
        "operation": trace.operation,
        "status": trace.status,
        "total_duration_ms": trace.total_duration_ms,
        "model_metadata": {
            "model_name": trace.model_name,
            "model_version": trace.model_version,
            "preprocessing_version": trace.preprocessing_version
        },
        "primary_concern": trace.primary_concern,
        "top_specialty": trace.top_specialty,
        "confidence_score": trace.confidence_score,
        "is_emergency_flagged": trace.is_emergency_flagged,
        "error_step": trace.error_step,
        "error_message": trace.error_message,
        "steps": trace.steps,
        "input_snapshot": trace.input_snapshot,
        "output_snapshot": trace.output_snapshot
    }
