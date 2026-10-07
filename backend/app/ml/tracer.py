"""
VitaLens AI Observability & Tracing Engine.
Provides comprehensive end-to-end telemetry for clinical AI processing,
recording every transformation step from user input to PyTorch inference and final routing.
Includes in-memory Server-Sent Events (SSE) broadcasting for Super Admin real-time monitoring.
"""

import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai_trace import AITrace

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

def generate_trace_id() -> str:
    """Generates standard trace ID format: VL-YYYYMMDD-XXXXXX (e.g. VL-20261003-8F42A1)."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"VL-{date_str}-{short_uuid}"

class TraceEventBroadcaster:
    """In-memory pub/sub for streaming live AI trace events to Super Admin SSE listeners."""
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)

    async def broadcast(self, event_data: Dict[str, Any]):
        dead_queues = set()
        for q in list(self._subscribers):
            try:
                q.put_nowait(event_data)
            except asyncio.QueueFull:
                dead_queues.add(q)
            except Exception:
                dead_queues.add(q)
        for dq in dead_queues:
            self._subscribers.discard(dq)

# Global singleton broadcaster
trace_broadcaster = TraceEventBroadcaster()

class AITracer:
    """
    Stateful tracer instance managing a single AI pipeline execution session.
    Records structured events for all 11 lifecycle stages.
    """
    def __init__(
        self,
        endpoint: str,
        operation: str = "SPECIALTY_TRIAGE",
        user_id: Optional[str] = None,
        user_role: str = "PATIENT",
        trace_id: Optional[str] = None
    ):
        self.trace_id = trace_id or generate_trace_id()
        self.endpoint = endpoint
        self.operation = operation
        self.user_id = user_id
        self.user_role = user_role
        self.created_at = datetime.now(timezone.utc)
        self.start_perf_time = time.perf_counter()
        
        self.status = "SUCCESS"
        self.total_duration_ms = 0.0
        self.model_name = "VitaLensSpecialtyNet"
        self.model_version = "specialty-net-v1.0.0"
        self.preprocessing_version = "feature-pipeline-v1.0"
        
        self.primary_concern: Optional[str] = None
        self.top_specialty: Optional[str] = None
        self.confidence_score: Optional[float] = None
        self.is_emergency_flagged: bool = False
        
        self.error_step: Optional[str] = None
        self.error_message: Optional[str] = None
        
        self.steps: List[Dict[str, Any]] = []
        self.input_snapshot: Dict[str, Any] = {}
        self.output_snapshot: Dict[str, Any] = {}

    def _add_step(
        self,
        step_number: int,
        step_name: str,
        status: str,
        duration_ms: float,
        details: Dict[str, Any],
        error: Optional[str] = None
    ):
        step_data = {
            "step_number": step_number,
            "step_name": step_name,
            "status": status,
            "started_at": utc_now_iso(),
            "completed_at": utc_now_iso(),
            "duration_ms": round(duration_ms, 2),
            "details": details,
            "error": error
        }
        self.steps.append(step_data)
        
        if status == "FAILED":
            self.status = "FAILED"
            self.error_step = step_name
            self.error_message = error
        elif status == "MODEL_UNAVAILABLE" and self.status != "FAILED":
            self.status = "MODEL_UNAVAILABLE"
        elif status == "WARNING" and self.status not in ["FAILED", "MODEL_UNAVAILABLE"]:
            self.status = "WARNING"

        # Emit asynchronous SSE broadcast
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(trace_broadcaster.broadcast({
                "type": "STEP_UPDATE",
                "trace_id": self.trace_id,
                "step": step_data,
                "timestamp": utc_now_iso()
            }))
        except RuntimeError:
            pass

    # =========================================================================
    # 11 Structured Pipeline Steps
    # =========================================================================

    def record_step_1_request_received(self, client_ip: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """STEP 1 — REQUEST RECEIVED"""
        t0 = time.perf_counter()
        details = {
            "trace_id": self.trace_id,
            "endpoint": self.endpoint,
            "operation": self.operation,
            "authenticated_role": self.user_role,
            "user_reference": self.user_id or "anonymous",
            "client_ip": client_ip,
            "metadata": metadata or {}
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(1, "REQUEST_RECEIVED", "SUCCESS", dur, details)

    def record_step_2_user_input(
        self,
        primary_concern: str,
        symptoms_list: List[str],
        duration_days: int,
        severity_score: int,
        body_region: str,
        additional_notes: Optional[str] = None
    ):
        """STEP 2 — USER INPUT"""
        t0 = time.perf_counter()
        self.primary_concern = primary_concern
        self.input_snapshot = {
            "primary_concern": primary_concern,
            "symptoms_list": symptoms_list,
            "duration_days": duration_days,
            "severity_score": severity_score,
            "body_region": body_region,
            "additional_notes": additional_notes
        }
        details = {
            "main_concern": primary_concern,
            "selected_symptoms": symptoms_list,
            "duration_days": duration_days,
            "severity_score": f"{severity_score}/10",
            "body_region": body_region,
            "has_additional_notes": bool(additional_notes)
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(2, "USER_INPUT", "SUCCESS", dur, details)

    def record_step_3_report_data(
        self,
        report_id: Optional[str],
        biomarkers: List[Dict[str, Any]],
        extraction_status: str = "SUCCESS",
        error_msg: Optional[str] = None
    ):
        """STEP 3 — REPORT DATA"""
        t0 = time.perf_counter()
        sanitized_biomarkers = [
            {
                "test_name": b.get("test_name"),
                "canonical_name": b.get("canonical_name"),
                "value": b.get("value_numeric") if b.get("value_numeric") is not None else b.get("value_text"),
                "unit": b.get("unit"),
                "reference_min": b.get("reference_min"),
                "reference_max": b.get("reference_max"),
                "reference_text": b.get("reference_text"),
                "flag": b.get("flag", "NORMAL")
            }
            for b in biomarkers
        ]
        status = "SUCCESS" if extraction_status == "SUCCESS" else "WARNING"
        if not report_id:
            status = "SKIPPED"
        details = {
            "report_id": report_id or "NONE_PROVIDED",
            "biomarker_count": len(sanitized_biomarkers),
            "biomarkers": sanitized_biomarkers,
            "extraction_status": extraction_status
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(3, "REPORT_DATA", status, dur, details, error=error_msg)

    def record_step_4_clinical_flagging(self, biomarkers: List[Dict[str, Any]]):
        """STEP 4 — CLINICAL FLAGGING"""
        t0 = time.perf_counter()
        high_list = []
        low_list = []
        critical_list = []
        normal_list = []

        for b in biomarkers:
            flag = str(b.get("flag", "NORMAL")).upper()
            val = b.get("value_numeric") if b.get("value_numeric") is not None else b.get("value_text")
            ref = b.get("reference_text") or f"{b.get('reference_min')} - {b.get('reference_max')}"
            unit = b.get("unit") or ""
            entry = {
                "test_name": b.get("test_name"),
                "value": f"{val} {unit}".strip(),
                "reference_range": ref,
                "flag": flag
            }
            if "CRITICAL" in flag:
                critical_list.append(entry)
            elif "HIGH" in flag:
                high_list.append(entry)
            elif "LOW" in flag:
                low_list.append(entry)
            else:
                normal_list.append(entry)

        status = "WARNING" if critical_list else "SUCCESS"
        details = {
            "total_evaluated": len(biomarkers),
            "critical_count": len(critical_list),
            "high_count": len(high_list),
            "low_count": len(low_list),
            "normal_count": len(normal_list),
            "critical_biomarkers": critical_list,
            "high_biomarkers": high_list,
            "low_biomarkers": low_list,
            "normal_biomarkers": normal_list
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(4, "CLINICAL_FLAGGING", status, dur, details)

    def record_step_5_canonical_feature_mapping(self, mapping_table: List[Dict[str, Any]]):
        """STEP 5 — CANONICAL FEATURE MAPPING"""
        t0 = time.perf_counter()
        mapped_count = sum(1 for m in mapping_table if m.get("status") in ["MAPPED_FROM_REPORT", "MAPPED"])
        defaulted_count = sum(1 for m in mapping_table if m.get("status") in ["DEFAULTED_NORMAL_MIDPOINT", "DEFAULTED"])
        unmapped_count = sum(1 for m in mapping_table if m.get("status") in ["UNMAPPED", "UNMAPPED_EXCLUDED_FROM_SCHEMA"])

        status = "WARNING" if unmapped_count > 0 else "SUCCESS"
        details = {
            "canonical_features_required": len(mapping_table),
            "mapped_from_report_count": mapped_count,
            "defaulted_midpoint_count": defaulted_count,
            "unmapped_count": unmapped_count,
            "mapping_table": mapping_table
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(5, "CANONICAL_FEATURE_MAPPING", status, dur, details)

    def record_step_6_symptom_encoding(
        self,
        full_text: str,
        matched_tfidf_terms: List[str],
        severity_normalized: float,
        duration_normalized: float
    ):
        """STEP 6 — SYMPTOM ENCODING"""
        t0 = time.perf_counter()
        details = {
            "full_text_input": full_text,
            "matched_tfidf_terms": matched_tfidf_terms,
            "matched_term_count": len(matched_tfidf_terms),
            "severity_normalized": severity_normalized,
            "duration_normalized": duration_normalized
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(6, "SYMPTOM_ENCODING", "SUCCESS", dur, details)

    def record_step_7_final_feature_vector(
        self,
        feature_count: int,
        text_features_dim: int,
        dense_features_dim: int,
        dense_breakdown: List[Dict[str, Any]],
        preprocessing_success: bool = True
    ):
        """STEP 7 — FINAL FEATURE VECTOR"""
        t0 = time.perf_counter()
        status = "SUCCESS" if preprocessing_success else "FAILED"
        details = {
            "total_feature_count": feature_count,
            "text_features_dim": text_features_dim,
            "dense_features_dim": dense_features_dim,
            "preprocessing_version": self.preprocessing_version,
            "scaler_applied": True,
            "dense_features_breakdown": dense_breakdown
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(7, "FINAL_FEATURE_VECTOR", status, dur, details)

    def record_step_8_model_inference(
        self,
        model_name: str,
        model_version: str,
        input_feature_count: int,
        inference_duration_ms: float,
        inference_status: str = "SUCCESS",
        error_msg: Optional[str] = None
    ):
        """STEP 8 — MODEL INFERENCE"""
        self.model_name = model_name
        self.model_version = model_version
        details = {
            "model_name": model_name,
            "model_version": model_version,
            "input_feature_count": input_feature_count,
            "device": "CPU",
            "inference_duration_ms": round(inference_duration_ms, 2)
        }
        self._add_step(8, "MODEL_INFERENCE", inference_status, inference_duration_ms, details, error=error_msg)

    def record_step_9_model_output(
        self,
        all_probabilities_sorted: List[Dict[str, Any]],
        top_prediction: str,
        confidence_score: float
    ):
        """STEP 9 — MODEL OUTPUT"""
        t0 = time.perf_counter()
        self.top_specialty = top_prediction
        self.confidence_score = confidence_score
        details = {
            "top_prediction": top_prediction,
            "confidence_score": round(confidence_score, 4),
            "confidence_percentage": f"{confidence_score * 100:.2f}%",
            "all_specialty_probabilities": all_probabilities_sorted
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(9, "MODEL_OUTPUT", "SUCCESS", dur, details)

    def record_step_10_final_decision(
        self,
        model_top_class: str,
        specialty_mapping: str,
        final_specialty_name: str,
        is_emergency: bool,
        emergency_message: Optional[str] = None,
        fallback_used: bool = False,
        decision_status: Optional[str] = None
    ):
        """STEP 10 — FINAL DECISION"""
        t0 = time.perf_counter()
        self.is_emergency_flagged = is_emergency
        status = "MODEL_UNAVAILABLE" if decision_status == "MODEL_UNAVAILABLE" else ("WARNING" if is_emergency or fallback_used else "SUCCESS")
        details = {
            "model_top_class": model_top_class,
            "specialty_name_mapping": specialty_mapping,
            "final_specialty": final_specialty_name,
            "is_emergency_flagged": is_emergency,
            "emergency_message": emergency_message,
            "fallback_used": fallback_used,
            "decision_status": decision_status or ("INTERCEPTED_EMERGENCY" if is_emergency else ("FALLBACK_RULE_BASED" if fallback_used else "AI_MODEL_CONFIRMED"))
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(10, "FINAL_DECISION", status, dur, details)

    def record_step_11_api_response(
        self,
        http_status: int,
        response_body: Dict[str, Any]
    ):
        """STEP 11 — API RESPONSE"""
        t0 = time.perf_counter()
        self.output_snapshot = response_body
        status = "SUCCESS" if http_status < 400 else "FAILED"
        details = {
            "http_status": http_status,
            "response_body": response_body
        }
        dur = (time.perf_counter() - t0) * 1000.0
        self._add_step(11, "API_RESPONSE", status, dur, details)

    # =========================================================================
    # Finalize & Database Persistence
    # =========================================================================

    async def finalize(self, db: AsyncSession) -> AITrace:
        """Calculates total processing duration, persists to ai_traces table, and broadcasts completion."""
        self.total_duration_ms = round((time.perf_counter() - self.start_perf_time) * 1000.0, 2)
        
        trace_record = AITrace(
            trace_id=self.trace_id,
            user_id=self.user_id,
            user_role=self.user_role,
            endpoint=self.endpoint,
            operation=self.operation,
            status=self.status,
            total_duration_ms=self.total_duration_ms,
            model_name=self.model_name,
            model_version=self.model_version,
            preprocessing_version=self.preprocessing_version,
            primary_concern=self.primary_concern,
            top_specialty=self.top_specialty,
            confidence_score=self.confidence_score,
            is_emergency_flagged=self.is_emergency_flagged,
            error_step=self.error_step,
            error_message=self.error_message,
            steps=self.steps,
            input_snapshot=self.input_snapshot,
            output_snapshot=self.output_snapshot
        )
        
        try:
            db.add(trace_record)
            await db.commit()
            await db.refresh(trace_record)
        except Exception as e:
            print(f"[!] Warning: Failed to persist AITrace {self.trace_id} to database: {e}")
            await db.rollback()

        # Emit final completion event to SSE stream
        try:
            await trace_broadcaster.broadcast({
                "type": "TRACE_COMPLETED",
                "trace_id": self.trace_id,
                "operation": self.operation,
                "status": self.status,
                "top_specialty": self.top_specialty,
                "confidence_score": self.confidence_score,
                "total_duration_ms": self.total_duration_ms,
                "timestamp": utc_now_iso()
            })
        except Exception as broadcast_err:
            pass

        return trace_record
