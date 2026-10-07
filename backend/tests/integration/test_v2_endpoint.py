import os
import pytest

# Import the predictor function
from app.ml.pytorch_specialty_predictor import predict_specialty_pytorch


def _run_predict(version, monkeypatch=None):
    if monkeypatch is not None:
        monkeypatch.setenv("VITALENS_MODEL_VERSION", version)
    else:
        os.environ["VITALENS_MODEL_VERSION"] = version
    # Minimal valid request (no biomarkers, minimal symptoms)
    result = predict_specialty_pytorch(
        primary_concern="Abdominal pain",
        symptoms_list=["nausea"],
        body_region="abdomen",
        abnormal_biomarkers=[],
        severity_score=5,
        duration_days=7,
        return_trace_telemetry=False,
    )
    return result


def test_v1_version_selection(monkeypatch):
    result = _run_predict("v1", monkeypatch=monkeypatch)
    # When V1 model files are present, a normal response contains 'recommended_specialty_name'
    # If files are missing, we still expect a structured error containing the version
    assert isinstance(result, dict)
    assert result.get("model_version") == "v1"


def test_v2_version_selection(monkeypatch):
    result = _run_predict("v2", monkeypatch=monkeypatch)
    assert isinstance(result, dict)
    assert result.get("model_version") == "v2"


def test_missing_biomarkers_handling(monkeypatch):
    # Provide a biomarker that does not exist in the schema
    monkeypatch.setenv("VITALENS_MODEL_VERSION", "v2")
    result = predict_specialty_pytorch(
        primary_concern="Fatigue",
        symptoms_list=["tiredness"],
        body_region="general",
        abnormal_biomarkers=[{"test_name": "unknown_test", "value_numeric": 123, "flag": "HIGH"}],
        severity_score=5,
        duration_days=7,
        return_trace_telemetry=True,
    )
    assert isinstance(result, dict)
    # Should contain a mapping table entry with status "UNMAPPED_EXCLUDED_FROM_SCHEMA"
    trace = result.get("trace_telemetry", {})
    unmapped = [m for m in trace.get("mapping_table", []) if m.get("status") == "UNMAPPED_EXCLUDED_FROM_SCHEMA"]
    assert len(unmapped) >= 1


def test_malformed_request_returns_error(monkeypatch):
    monkeypatch.setenv("VITALENS_MODEL_VERSION", "v2")
    # Pass None for required fields to simulate malformed request
    result = predict_specialty_pytorch(
        primary_concern=None,
        symptoms_list=None,
        body_region=None,
        abnormal_biomarkers=None,
        severity_score=None,
        duration_days=None,
        return_trace_telemetry=False,
    )
    # The function should not raise but return an error dict
    assert isinstance(result, dict)
    assert "error" in result
    assert result.get("model_version") == "v2"
