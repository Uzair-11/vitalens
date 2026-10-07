"""
VitaLens Pipeline Regression & Validation Test Corpus Harness.

This test suite executes the end-to-end medical report regression corpus:
  Layer 1: Document Extraction (PDF / text parsing)
  Layer 2: Biomarker Canonicalization & Normalization
  Layer 3: Abnormality Classification (Source reference range priority)
  Layer 4: Feature Vector Construction (306-dim V2 integrity)
  Layer 5: Specialty Recommendation (Probabilities and acceptable specialties)
  Layer 6: Architecture Isolation (V1 vs V2 independence)

Every discovered bug in VitaLens must be encoded in manifest.json and verified here.
"""

import os
import json
import pytest
from typing import Dict, Any, List

from app.ml.document_parser import extract_text_and_tables_from_file
from app.ml.lab_extractor import extract_biomarkers_from_text
from app.ml.pytorch_specialty_predictor import (
    predict_specialty_pytorch,
    normalize_biomarker_for_model,
    load_pytorch_specialty_model,
    ALIAS_MAP,
    ALIAS_MAP_V2,
    CANONICAL_BIOMARKERS,
    VERSION_CONFIG
)
from app.ml.training.feature_pipeline_v2 import CANONICAL_BIOMARKERS_V2, FLAG_ENCODING as FLAG_ENCODING_V2

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "corpus")
MANIFEST_PATH = os.path.join(CORPUS_DIR, "manifest.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    MANIFEST = json.load(f)

TEXT_CASES = MANIFEST.get("text_cases", [])
PDF_CASES = MANIFEST.get("pdf_cases", [])


class PipelineLayerFailure(AssertionError):
    """Custom assertion error attributing failures to exact pipeline layers."""
    def __init__(self, layer_num: int, layer_name: str, test_id: str, message: str):
        self.layer_num = layer_num
        self.layer_name = layer_name
        self.test_id = test_id
        formatted = (
            f"\n"
            f"======================================================================\n"
            f"PIPELINE FAILURE AT LAYER {layer_num} [{layer_name.upper()}]\n"
            f"Test Case: {test_id}\n"
            f"Details: {message}\n"
            f"======================================================================\n"
        )
        super().__init__(formatted)


# ============================================================================
# Layer 6: Architecture & Vector Isolation Tests
# ============================================================================

def test_v1_v2_architecture_and_feature_isolation():
    """Verifies complete architectural isolation and vector sizing between V1 and V2."""
    # V1 dimension integrity
    assert len(CANONICAL_BIOMARKERS) == 20, "V1 canonical biomarkers must be exactly 20"
    v1_config = VERSION_CONFIG["v1"]
    assert v1_config["expected_input_dim"] == 298, "V1 input dimension must be 298"

    # V2 dimension integrity
    assert len(CANONICAL_BIOMARKERS_V2) == 24, "V2 canonical biomarkers must be exactly 24"
    v2_config = VERSION_CONFIG["v2"]
    assert v2_config["expected_input_dim"] == 306, "V2 input dimension must be 306"

    # Verify model assets load cleanly
    m, v2_pipe, v2_meta = load_pytorch_specialty_model("v2")
    assert m is not None, "V2 model must load"
    assert v2_pipe is not None, "V2 pipeline must load"

    # Verify dummy vector transform shape
    sample_record = {
        "full_text": "Patient has severe fatigue and creatinine 1.7",
        "val_serum_creatinine": 1.7,
        "flag_serum_creatinine": "HIGH",
        "severity_score": 5.0,
        "duration_days": 7.0
    }
    vec = v2_pipe.transform([sample_record])
    assert vec.shape == (1, 306), f"V2 feature vector shape must be (1, 306), got {vec.shape}"


# ============================================================================
# Text Cases (Layers 1 to 5)
# ============================================================================

@pytest.mark.parametrize("case", TEXT_CASES, ids=[c["id"] for c in TEXT_CASES])
def test_text_report_pipeline(case: Dict[str, Any]):
    test_id = case["id"]
    file_rel = case["file"]
    filepath = os.path.join(CORPUS_DIR, file_rel)
    assert os.path.exists(filepath), f"File not found: {filepath}"

    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # ------------------------------------------------------------------------
    # LAYER 1: Document Extraction
    # ------------------------------------------------------------------------
    extracted = extract_biomarkers_from_text(raw_text)
    expected_bios = case.get("expected_biomarkers", [])

    if not extracted and expected_bios:
        raise PipelineLayerFailure(
            1, "Document Extraction", test_id,
            f"Extraction returned 0 biomarkers from '{file_rel}', expected {len(expected_bios)}."
        )

    # ------------------------------------------------------------------------
    # LAYER 2 & 3: Canonicalization & Abnormality Flagging
    # ------------------------------------------------------------------------
    extracted_by_name = {}
    extracted_by_canon = {}
    for b in extracted:
        t_name = (b.get("test_name") or b.get("canonical_name") or "").lower()
        extracted_by_name[t_name] = b
        norm_key = normalize_biomarker_for_model(b.get("canonical_name") or b.get("test_name") or "", ALIAS_MAP_V2)
        extracted_by_canon[norm_key] = b

    for expected in expected_bios:
        exp_name = expected["name"]
        exp_canon = expected.get("canonical_v2")
        exp_val = expected["value"]
        exp_flag = expected.get("expected_flag")

        # Find matching extracted biomarker
        match = None
        for name_key, b_obj in extracted_by_name.items():
            if exp_name.lower() in name_key or name_key in exp_name.lower():
                match = b_obj
                break

        if not match and exp_canon and exp_canon in extracted_by_canon:
            match = extracted_by_canon[exp_canon]

        if not match:
            raise PipelineLayerFailure(
                1, "Document Extraction", test_id,
                f"Biomarker '{exp_name}' was not extracted from text. Available extracted: {list(extracted_by_name.keys())}"
            )

        # Value comparison
        actual_val = match.get("value_numeric")
        if actual_val is None or abs(actual_val - exp_val) > 0.1:
            raise PipelineLayerFailure(
                1, "Document Extraction", test_id,
                f"Biomarker '{exp_name}' value mismatch: expected {exp_val}, got {actual_val}"
            )

        # Canonical key verification
        if exp_canon:
            actual_canon = normalize_biomarker_for_model(match.get("canonical_name") or match.get("test_name"), ALIAS_MAP_V2)
            if actual_canon != exp_canon:
                raise PipelineLayerFailure(
                    2, "Biomarker Canonicalization", test_id,
                    f"Biomarker '{match.get('test_name')}' mapped to '{actual_canon}', expected canonical '{exp_canon}'"
                )

        # Flag verification (Ground truth reference range compliance)
        if exp_flag:
            actual_flag = match.get("flag")
            if actual_flag != exp_flag:
                raise PipelineLayerFailure(
                    3, "Abnormality Classification", test_id,
                    f"Biomarker '{match.get('test_name')}' flag mismatch: expected {exp_flag}, got {actual_flag}. Ref: {match.get('reference_text')}"
                )

    # ------------------------------------------------------------------------
    # LAYER 4 & 5: Feature Construction & Specialty Recommendation
    # ------------------------------------------------------------------------
    patient_ctx = case.get("patient_context", {})
    symptoms = patient_ctx.get("symptoms", [])
    main_concern = patient_ctx.get("main_concern") or (symptoms[0] if symptoms else "Checkup")
    duration = 7
    severity = patient_ctx.get("severity", 5)

    predictor_bios = [
        {
            "test_name": b.get("test_name"),
            "canonical_name": b.get("canonical_name"),
            "value_numeric": b.get("value_numeric"),
            "unit": b.get("unit"),
            "flag": b.get("flag", "NORMAL"),
            "reference_range": b.get("reference_text")
        }
        for b in extracted
    ]

    prediction = predict_specialty_pytorch(
        primary_concern=main_concern,
        symptoms_list=symptoms,
        body_region="general",
        abnormal_biomarkers=predictor_bios,
        severity_score=severity,
        duration_days=duration,
        model_version="v2"
    )

    primary_specialty = prediction.get("recommended_specialty_name") or prediction.get("primary_specialty")
    fallback_used = prediction.get("fallback_used", False)
    all_scores = prediction.get("all_probabilities") or prediction.get("all_specialty_scores", {})
    sorted_specialties = sorted(all_scores.keys(), key=lambda k: all_scores[k], reverse=True)
    top_2 = sorted_specialties[:2]

    expected_spec = case.get("expected_specialty", {})
    acceptable_primary = expected_spec.get("acceptable_primary", [])
    acceptable_top2 = expected_spec.get("acceptable_top2", [])
    disallowed_primary = expected_spec.get("disallowed_primary", [])

    if disallowed_primary and primary_specialty in disallowed_primary:
        raise PipelineLayerFailure(
            5, "Specialty Recommendation", test_id,
            f"Primary specialty '{primary_specialty}' is in disallowed list {disallowed_primary}. Full scores: {all_scores}"
        )

    if acceptable_primary and primary_specialty not in acceptable_primary:
        raise PipelineLayerFailure(
            5, "Specialty Recommendation", test_id,
            f"Primary specialty '{primary_specialty}' not in acceptable list {acceptable_primary}. Top 2: {top_2}, Full scores: {all_scores}"
        )

    if acceptable_top2 and not any(s in acceptable_top2 for s in top_2):
        raise PipelineLayerFailure(
            5, "Specialty Recommendation", test_id,
            f"Top 2 specialties {top_2} do not contain any of {acceptable_top2}."
        )


# ============================================================================
# PDF Ingestion Cases (Golden Inventory Ground Truth)
# ============================================================================

@pytest.mark.parametrize("case", PDF_CASES, ids=[c["id"] for c in PDF_CASES])
def test_pdf_report_pipeline(case: Dict[str, Any]):
    test_id = case["id"]
    file_rel = case["file"]
    filepath = os.path.join(CORPUS_DIR, file_rel)
    assert os.path.exists(filepath), f"PDF file not found: {filepath}"

    # ------------------------------------------------------------------------
    # LAYER 1: Document & Table Extraction from PDF
    # ------------------------------------------------------------------------
    parsed = extract_text_and_tables_from_file(filepath)
    raw_text = parsed.get("raw_text", "")
    tables = parsed.get("tables", [])

    biomarkers = extract_biomarkers_from_text(raw_text, tables)
    expected_inventory = case.get("expected_biomarkers_inventory", [])

    if not biomarkers and expected_inventory:
        raise PipelineLayerFailure(
            1, "Document Extraction (PDF)", test_id,
            f"Zero biomarkers extracted from PDF '{file_rel}'. Expected inventory count: {len(expected_inventory)}."
        )

    # ------------------------------------------------------------------------
    # LAYER 1, 2, 3: Inventory Completeness & No Silent Drops
    # ------------------------------------------------------------------------
    extracted_canonical = {}
    extracted_names = []
    for b in biomarkers:
        c_name = normalize_biomarker_for_model(b.get("canonical_name") or b.get("test_name"), ALIAS_MAP_V2)
        extracted_canonical[c_name] = b
        extracted_names.append((b.get("test_name") or "").lower())

    missing_from_pdf = []
    for exp in expected_inventory:
        exp_name = exp["name"]
        exp_canon = exp.get("canonical_v2")
        exp_val = exp.get("value")
        exp_flag = exp.get("expected_flag")

        match = None
        if exp_canon and exp_canon in extracted_canonical:
            match = extracted_canonical[exp_canon]
        else:
            for b in biomarkers:
                b_name = (b.get("test_name") or "").lower()
                b_canon = (b.get("canonical_name") or "").lower()
                if exp_name.lower() in b_name or exp_name.lower() in b_canon:
                    match = b
                    break

        if not match:
            missing_from_pdf.append(exp_name)
            continue

        # Check value accuracy if specified
        if exp_val is not None:
            actual_val = match.get("value_numeric")
            if actual_val is None or abs(actual_val - exp_val) > 0.1:
                raise PipelineLayerFailure(
                    1, "Document Extraction (PDF Value Mismatch)", test_id,
                    f"Biomarker '{exp_name}' value mismatch: expected {exp_val}, got {actual_val}"
                )

        # Check flag accuracy if specified
        if exp_flag is not None:
            actual_flag = match.get("flag")
            if actual_flag != exp_flag:
                raise PipelineLayerFailure(
                    3, "Abnormality Classification (PDF)", test_id,
                    f"Biomarker '{exp_name}' flag mismatch: expected {exp_flag}, got {actual_flag}. Ref text: {match.get('reference_text')}"
                )

    if missing_from_pdf:
        raise PipelineLayerFailure(
            1, "Document Extraction (PDF Dropped Biomarkers)", test_id,
            f"PDF inventory failed! The following {len(missing_from_pdf)} biomarkers were silently dropped: {missing_from_pdf}."
        )

    # ------------------------------------------------------------------------
    # LAYER 5: Specialty Recommendation from PDF
    # ------------------------------------------------------------------------
    patient_ctx = case.get("patient_context", {})
    symptoms = patient_ctx.get("symptoms", [])
    main_concern = patient_ctx.get("main_concern") or (symptoms[0] if symptoms else "Checkup")
    duration = 7
    severity = patient_ctx.get("severity", 5)

    # Map biomarkers to format expected by specialty predictor
    predictor_bios = [
        {
            "test_name": b.get("test_name"),
            "canonical_name": b.get("canonical_name"),
            "value_numeric": b.get("value_numeric"),
            "unit": b.get("unit"),
            "flag": b.get("flag", "NORMAL"),
            "reference_range": b.get("reference_text")
        }
        for b in biomarkers
    ]

    prediction = predict_specialty_pytorch(
        primary_concern=main_concern,
        symptoms_list=symptoms,
        body_region="general",
        abnormal_biomarkers=predictor_bios,
        severity_score=severity,
        duration_days=duration,
        model_version="v2"
    )

    primary_specialty = prediction.get("recommended_specialty_name") or prediction.get("primary_specialty")
    all_scores = prediction.get("all_probabilities") or prediction.get("all_specialty_scores", {})
    expected_spec = case.get("expected_specialty", {})
    acceptable_primary = expected_spec.get("acceptable_primary", [])
    disallowed_primary = expected_spec.get("disallowed_primary", [])

    if disallowed_primary and primary_specialty in disallowed_primary:
        raise PipelineLayerFailure(
            5, "Specialty Recommendation (PDF)", test_id,
            f"Primary specialty '{primary_specialty}' is in disallowed list {disallowed_primary}."
        )

    if acceptable_primary and primary_specialty not in acceptable_primary:
        raise PipelineLayerFailure(
            5, "Specialty Recommendation (PDF)", test_id,
            f"Primary specialty '{primary_specialty}' not in acceptable list {acceptable_primary}. Scores: {all_scores}"
        )
