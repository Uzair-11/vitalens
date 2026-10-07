import os
import pytest
from unittest.mock import patch, MagicMock

from app.ml.specialty_matcher import recommend_specialty, check_emergency
from app.ml.tracer import AITracer
from app.schemas.ai_schema import SpecialtyRecommendationResponse


@pytest.fixture
def mock_tracer():
    tracer = AITracer(
        endpoint="/api/v1/ai/recommend-specialty",
        operation="SPECIALTY_TRIAGE",
        user_id="test-user-uuid",
        user_role="PATIENT"
    )
    return tracer


def test_v2_successful_inference_provenance(mock_tracer):
    """
    On successful V2 inference:
    - fallback_used = False
    - prediction_source = "ai_model"
    - model_version = "specialty-net-v2.0.0"
    - confidence_score > 0
    - trace records AI_MODEL_CONFIRMED with specialty-net-v2.0.0
    - schema validates cleanly
    """
    abnormal_biomarkers = [
        {"test_name": "TSH", "canonical_name": "tsh", "value_numeric": 7.5, "unit": "mIU/L", "flag": "HIGH"},
        {"test_name": "Free T4", "canonical_name": "free_t4", "value_numeric": 0.5, "unit": "ng/dL", "flag": "LOW"},
    ]
    rec = recommend_specialty(
        primary_concern="Frequent urination and fatigue",
        symptoms_list=["Frequent urination", "Fatigue"],
        body_region="General",
        abnormal_biomarkers=abnormal_biomarkers,
        severity_score=5,
        duration_days=3,
        tracer=mock_tracer,
        model_version="v2"
    )

    assert rec["fallback_used"] is False
    assert rec["prediction_source"] == "ai_model"
    assert rec["model_version"] == "specialty-net-v2.0.0"
    assert rec["confidence_score"] > 0.0
    assert rec["recommended_specialty_name"] == "Endocrinology"
    assert rec["is_emergency_flagged"] is False

    # Check tracer telemetry
    assert mock_tracer.status == "SUCCESS"
    assert mock_tracer.model_version == "specialty-net-v2.0.0"
    step_10 = next((s for s in mock_tracer.steps if s["step_number"] == 10), None)
    assert step_10 is not None
    assert step_10["details"]["fallback_used"] is False
    assert step_10["details"]["decision_status"] == "AI_MODEL_CONFIRMED"

    # Schema validation
    validated = SpecialtyRecommendationResponse(
        recommended_specialty_id="spec-id-123",
        **rec
    )
    assert validated.fallback_used is False
    assert validated.prediction_source == "ai_model"
    assert validated.model_version == "specialty-net-v2.0.0"


def test_v2_inference_failure_safe_general_medicine_default(mock_tracer):
    """
    On V2 inference exception:
    - Do NOT use heuristic rule prediction (no specific specialty guessing)
    - Do NOT invoke V1
    - Return safe structured General Medicine default
    - confidence_score = 0.0
    - fallback_used = True
    - prediction_source = "primary_care_safe_default"
    - model_version = None
    - tracer status = "MODEL_UNAVAILABLE"
    """
    abnormal_biomarkers = [
        {"test_name": "TSH", "canonical_name": "tsh", "value_numeric": 7.5, "unit": "mIU/L", "flag": "HIGH"},
    ]
    with patch("app.ml.pytorch_specialty_predictor.predict_specialty_pytorch", side_effect=RuntimeError("Simulated V2 CUDA/Pipeline crash")):
        rec = recommend_specialty(
            primary_concern="Frequent urination and fatigue",
            symptoms_list=["Frequent urination", "Fatigue"],
            body_region="General",
            abnormal_biomarkers=abnormal_biomarkers,
            severity_score=5,
            duration_days=3,
            tracer=mock_tracer,
            model_version="v2"
        )

    # Must be General Medicine, NOT Endocrinology from heuristic rules!
    assert rec["recommended_specialty_name"] == "General Medicine"
    assert rec["confidence_score"] == 0.0
    assert rec["fallback_used"] is True
    assert rec["prediction_source"] == "primary_care_safe_default"
    assert rec["model_version"] is None
    assert "temporarily unavailable" in rec["rationale"]
    assert "General Physician or Primary Care Doctor" in rec["rationale"]

    # Check tracer telemetry
    assert mock_tracer.status == "MODEL_UNAVAILABLE"
    assert mock_tracer.model_version is None
    step_10 = next((s for s in mock_tracer.steps if s["step_number"] == 10), None)
    assert step_10 is not None
    assert step_10["details"]["fallback_used"] is True
    assert step_10["details"]["decision_status"] == "MODEL_UNAVAILABLE"

    # Schema validation
    validated = SpecialtyRecommendationResponse(
        recommended_specialty_id="spec-id-gen-med",
        **rec
    )
    assert validated.fallback_used is True
    assert validated.prediction_source == "primary_care_safe_default"
    assert validated.model_version is None
    assert validated.confidence_score == 0.0


def test_v2_inference_failure_with_emergency_alert(mock_tracer):
    """
    When emergency symptoms exist AND V2 fails:
    - Emergency red flag is preserved
    - Emergency message is preserved
    - Falls back to General Medicine safe default with confidence 0.0
    - fallback_used = True, prediction_source = "primary_care_safe_default"
    """
    with patch("app.ml.pytorch_specialty_predictor.predict_specialty_pytorch", side_effect=RuntimeError("Simulated pipeline failure")):
        rec = recommend_specialty(
            primary_concern="I have sudden crushing chest pain and shortness of breath",
            symptoms_list=["chest pain", "shortness of breath"],
            body_region="Chest",
            abnormal_biomarkers=[],
            severity_score=10,
            duration_days=1,
            tracer=mock_tracer,
            model_version="v2"
        )

    assert rec["is_emergency_flagged"] is True
    assert rec["emergency_message"] is not None
    assert "emergency" in rec["emergency_message"].lower()
    assert rec["recommended_specialty_name"] == "General Medicine"
    assert rec["confidence_score"] == 0.0
    assert rec["fallback_used"] is True
    assert rec["prediction_source"] == "primary_care_safe_default"
    assert rec["model_version"] is None
    assert "CRITICAL MEDICAL ALERT" in rec["rationale"]

    # Schema validation
    validated = SpecialtyRecommendationResponse(
        recommended_specialty_id="spec-id-gen-med",
        **rec
    )
    assert validated.is_emergency_flagged is True
    assert validated.fallback_used is True


def test_v2_failure_structured_error_dict(mock_tracer):
    """
    When predict_specialty_pytorch returns a structured error dict (e.g. dimension mismatch):
    - Cleanly handled by Option B safe default
    """
    error_dict = {"error": "Feature dimension mismatch: 300 vs 306", "model_version": "v2"}
    with patch("app.ml.pytorch_specialty_predictor.predict_specialty_pytorch", return_value=error_dict):
        rec = recommend_specialty(
            primary_concern="Fatigue",
            symptoms_list=[],
            body_region="General",
            abnormal_biomarkers=[],
            tracer=mock_tracer,
            model_version="v2"
        )

    assert rec["recommended_specialty_name"] == "General Medicine"
    assert rec["confidence_score"] == 0.0
    assert rec["fallback_used"] is True
    assert rec["prediction_source"] == "primary_care_safe_default"
    assert rec["model_version"] is None


def test_v2_failure_v1_isolation(mock_tracer):
    """
    Confirms that V1 is NEVER invoked or loaded when V2 fails.
    """
    with patch("app.ml.pytorch_specialty_predictor.predict_specialty_pytorch", side_effect=RuntimeError("V2 failure")) as mock_predict:
        rec = recommend_specialty(
            primary_concern="Fatigue",
            symptoms_list=[],
            body_region="General",
            abnormal_biomarkers=[],
            tracer=mock_tracer,
            model_version="v2"
        )
        # Verify predict_specialty_pytorch was only called once, and with model_version="v2"
        assert mock_predict.call_count == 1
        assert mock_predict.call_args[1].get("model_version") == "v2"
        assert rec["fallback_used"] is True
        assert rec["model_version"] is None


def test_v1_success_provenance(mock_tracer):
    """
    On V1 success:
    - fallback_used = False
    - prediction_source = "ai_model"
    - model_version = "specialty-net-v1.0.0"
    """
    rec = recommend_specialty(
        primary_concern="Mild chest tightness",
        symptoms_list=["palpitations"],
        body_region="Chest",
        abnormal_biomarkers=[],
        tracer=mock_tracer,
        model_version="v1"
    )
    assert rec["fallback_used"] is False
    assert rec["prediction_source"] == "ai_model"
    assert rec["model_version"] == "specialty-net-v1.0.0"
    assert rec["confidence_score"] > 0.0
