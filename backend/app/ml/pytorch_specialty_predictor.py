"""
PyTorch Specialty Predictor for VitaLens API.
Loads the custom-trained VitaLensSpecialtyNet model and feature pipeline
to perform real-time multi-class inference on patient symptoms and lab biomarkers.
"""

import os
import sys
import json
import torch
import numpy as np
from typing import List, Dict, Any, Optional

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "training"))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from app.ml.models.specialty_network import VitaLensSpecialtyNet
from app.ml.training.feature_pipeline import ClinicalFeaturePipeline, CANONICAL_BIOMARKERS, FLAG_ENCODING

_MODEL_INSTANCE: Optional[VitaLensSpecialtyNet] = None
_PIPELINE_INSTANCE: Optional[ClinicalFeaturePipeline] = None
_METADATA: Optional[Dict[str, Any]] = None

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "specialty_model.pt")
PIPELINE_PATH = os.path.join(MODEL_DIR, "feature_pipeline.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")

def load_pytorch_specialty_model():
    """Loads model weights, pipeline, and metadata into memory (cached)."""
    global _MODEL_INSTANCE, _PIPELINE_INSTANCE, _METADATA
    
    if _MODEL_INSTANCE is not None and _PIPELINE_INSTANCE is not None:
        return _MODEL_INSTANCE, _PIPELINE_INSTANCE, _METADATA
        
    if not os.path.exists(MODEL_PATH) or not os.path.exists(PIPELINE_PATH):
        return None, None, None

    # Load Feature Pipeline
    _PIPELINE_INSTANCE = ClinicalFeaturePipeline.load(PIPELINE_PATH)

    # Load Model Weights
    checkpoint = torch.load(MODEL_PATH, map_location=torch.device("cpu"), weights_only=False)
    input_dim = checkpoint.get("input_dim", 298)
    num_classes = checkpoint.get("num_classes", 10)
    hidden_dims = checkpoint.get("hidden_dims", (256, 128, 64))
    dropout_rate = checkpoint.get("dropout_rate", 0.25)
    
    model = VitaLensSpecialtyNet(
        input_dim=input_dim,
        num_classes=num_classes,
        hidden_dims=hidden_dims,
        dropout_rate=dropout_rate
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    _MODEL_INSTANCE = model

    # Load Metadata
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            _METADATA = json.load(f)
    else:
        _METADATA = {"classes": checkpoint.get("classes", [])}

    return _MODEL_INSTANCE, _PIPELINE_INSTANCE, _METADATA

CANONICAL_NAME_TO_MODEL_FEATURE = {
    # Glucose / Diabetes
    "fasting_blood_glucose": "glucose_fasting",
    "glucose_fasting": "glucose_fasting",
    "fasting_glucose": "glucose_fasting",
    "fbs": "glucose_fasting",
    "blood_sugar": "glucose_fasting",
    "glucose": "glucose_fasting",
    
    # HbA1c
    "glycated_hemoglobin_(hba1c)": "hba1c",
    "glycated_hemoglobin": "hba1c",
    "hba1c": "hba1c",
    "a1c": "hba1c",

    # Lipids
    "total_cholesterol": "total_cholesterol",
    "serum_cholesterol": "total_cholesterol",
    "cholesterol,_total": "total_cholesterol",
    "cholesterol_total": "total_cholesterol",
    "cholesterol": "total_cholesterol",
    "ldl_cholesterol": "ldl_cholesterol",
    "cholesterol,_ldl": "ldl_cholesterol",
    "cholesterol_ldl": "ldl_cholesterol",
    "ldl": "ldl_cholesterol",
    "ldl_c": "ldl_cholesterol",
    "hdl_cholesterol": "hdl_cholesterol",
    "cholesterol,_hdl": "hdl_cholesterol",
    "cholesterol_hdl": "hdl_cholesterol",
    "hdl": "hdl_cholesterol",
    "hdl_c": "hdl_cholesterol",
    "triglycerides": "triglycerides",
    "tg": "triglycerides",

    # CBC
    "hemoglobin": "hemoglobin",
    "hemoglobin_(hb)": "hemoglobin",
    "hb": "hemoglobin",
    "white_blood_cell_count": "wbc_count",
    "white_blood_cell_count_(wbc)": "wbc_count",
    "wbc": "wbc_count",
    "wbc_count": "wbc_count",
    "platelets": "platelet_count",
    "platelet_count": "platelet_count",
    "plt": "platelet_count",

    # Liver
    "alanine_aminotransferase_(alt)": "alt_sgpt",
    "alanine_aminotransferase": "alt_sgpt",
    "alt": "alt_sgpt",
    "alt_(sgpt)": "alt_sgpt",
    "alt_sgpt": "alt_sgpt",
    "sgpt": "alt_sgpt",
    "aspartate_aminotransferase_(ast)": "ast_sgot",
    "aspartate_aminotransferase": "ast_sgot",
    "ast": "ast_sgot",
    "ast_(sgot)": "ast_sgot",
    "ast_sgot": "ast_sgot",
    "sgot": "ast_sgot",
    "bilirubin,_total": "total_bilirubin",
    "total_bilirubin": "total_bilirubin",
    "serum_bilirubin": "total_bilirubin",
    "bilirubin": "total_bilirubin",
    "bilirubin_total": "total_bilirubin",
    "bilirubin_total_(mg/dl)": "total_bilirubin",
    "total_serum_bilirubin": "total_bilirubin",
    "serum_total_bilirubin": "total_bilirubin",
    "t_bilirubin": "total_bilirubin",
    "t._bilirubin": "total_bilirubin",

    # Renal
    "serum_creatinine": "serum_creatinine",
    "creatinine": "serum_creatinine",
    "sr_creatinine": "serum_creatinine",
    "blood_urea_nitrogen_(bun)": "bun",
    "blood_urea_nitrogen": "bun",
    "bun": "bun",
    "estimated_glomerular_filtration_rate_(egfr)": "egfr",
    "estimated_glomerular_filtration_rate": "egfr",
    "egfr": "egfr",
    "gfr": "egfr",
    "uric_acid,_serum": "uric_acid",
    "uric_acid": "uric_acid",
    "serum_uric_acid": "uric_acid",

    # Thyroid
    "thyroid_stimulating_hormone_(tsh)": "tsh",
    "thyroid_stimulating_hormone": "tsh",
    "tsh": "tsh",
    "free_t4": "free_t4",
    "ft4": "free_t4",
    "free_thyroxine": "free_t4",

    # Inflammatory
    "c-reactive_protein_(crp)": "crp",
    "c-reactive_protein": "crp",
    "crp": "crp",
    "hs-crp": "crp",
    "erythrocyte_sedimentation_rate_(esr)": "esr",
    "erythrocyte_sedimentation_rate": "esr",
    "esr": "esr"
}

def normalize_biomarker_for_model(raw_name: str) -> str:
    cleaned = raw_name.lower().strip().replace(" ", "_").replace("-", "_")
    if cleaned in CANONICAL_NAME_TO_MODEL_FEATURE:
        return CANONICAL_NAME_TO_MODEL_FEATURE[cleaned]
    alphanumeric_clean = "".join(c if (c.isalnum() or c == "_") else "_" for c in cleaned)
    while "__" in alphanumeric_clean:
        alphanumeric_clean = alphanumeric_clean.replace("__", "_")
    alphanumeric_clean = alphanumeric_clean.strip("_")
    if alphanumeric_clean in CANONICAL_NAME_TO_MODEL_FEATURE:
        return CANONICAL_NAME_TO_MODEL_FEATURE[alphanumeric_clean]
    return CANONICAL_NAME_TO_MODEL_FEATURE.get(alphanumeric_clean, cleaned)

DEFAULT_NORMAL_MIDPOINTS = {
    "glucose_fasting": 84.5,
    "hba1c": 4.8,
    "total_cholesterol": 162.0,
    "ldl_cholesterol": 74.5,
    "hdl_cholesterol": 50.0,
    "triglycerides": 99.5,
    "hemoglobin": 14.5,
    "wbc_count": 7500.0,
    "platelet_count": 275000.0,
    "alt_sgpt": 25.0,
    "ast_sgot": 22.5,
    "total_bilirubin": 0.6,
    "serum_creatinine": 0.85,
    "bun": 12.5,
    "egfr": 105.0,
    "tsh": 2.2,
    "free_t4": 1.3,
    "uric_acid": 5.15,
    "crp": 1.3,
    "esr": 8.5
}

def predict_specialty_pytorch(
    primary_concern: str,
    symptoms_list: List[str],
    body_region: str,
    abnormal_biomarkers: List[Dict[str, Any]],
    severity_score: int = 5,
    duration_days: int = 7,
    return_trace_telemetry: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Executes inference using custom PyTorch VitaLensSpecialtyNet.
    Returns predicted specialty, probability scores, top-3 candidates, explainable rationale,
    and optional technical telemetry for Super Admin AI tracing.
    """
    import time
    model, pipeline, metadata = load_pytorch_specialty_model()
    if model is None or pipeline is None:
        return None

    classes = metadata.get("classes", [
        "Cardiology", "Endocrinology", "Hematology", "Gastroenterology",
        "Nephrology", "Pulmonology", "Dermatology", "Neurology",
        "Orthopedics", "General Medicine"
    ])

    # Construct single sample input dictionary
    symptoms_text = ", ".join(symptoms_list) if symptoms_list else primary_concern
    full_text = f"Primary Concern: {primary_concern}. Symptoms: {symptoms_text}. Affected Area: {body_region}."

    row = {
        "primary_concern": primary_concern,
        "symptoms": symptoms_text,
        "body_region": body_region,
        "full_text": full_text,
        "severity_score": severity_score,
        "duration_days": duration_days
    }

    # Map input biomarkers to canonical model features
    biomarker_map = {}
    unmapped_list = []
    for b in abnormal_biomarkers:
        raw_test_name = b.get("test_name") or ""
        raw_canonical = b.get("canonical_name") or raw_test_name
        feat_name = normalize_biomarker_for_model(raw_canonical)
        if feat_name not in CANONICAL_BIOMARKERS and raw_test_name:
            feat_name = normalize_biomarker_for_model(raw_test_name)

        val = b.get("value_numeric")
        flag = b.get("flag", "NORMAL")
        unit = b.get("unit", "")
        if val is not None:
            if feat_name in CANONICAL_BIOMARKERS:
                biomarker_map[feat_name] = (float(val), flag, raw_canonical, raw_test_name, unit)
            else:
                unmapped_list.append({
                    "canonical_feature": feat_name,
                    "source_name": raw_canonical,
                    "source_test_name": raw_test_name,
                    "value": float(val),
                    "unit": unit,
                    "flag": flag,
                    "status": "UNMAPPED_EXCLUDED_FROM_SCHEMA",
                    "reason": "Biomarker is not part of the model's fixed 20-feature training schema"
                })

    # Populate all 20 canonical biomarkers required by ClinicalFeaturePipeline
    for b_name in CANONICAL_BIOMARKERS:
        if b_name in biomarker_map:
            val = biomarker_map[b_name][0]
            flag = biomarker_map[b_name][1]
            row[f"val_{b_name}"] = val
            row[f"flag_{b_name}"] = flag
        else:
            row[f"val_{b_name}"] = DEFAULT_NORMAL_MIDPOINTS.get(b_name, 0.0)
            row[f"flag_{b_name}"] = "NORMAL"

    # Transform through feature pipeline
    feature_vector = pipeline.transform([row])  # Shape: (1, 298)
    tensor_input = torch.tensor(feature_vector, dtype=torch.float32)

    # Model inference with precise timing
    t_start = time.perf_counter()
    with torch.no_grad():
        logits = model(tensor_input)
        probs = torch.softmax(logits, dim=-1).numpy()[0]
    inference_duration_ms = (time.perf_counter() - t_start) * 1000.0

    top_idx = int(np.argmax(probs))
    predicted_specialty = classes[top_idx]
    confidence_score = float(probs[top_idx])

    # Top 3 Candidates
    sorted_indices = np.argsort(probs)[::-1]
    top_3 = [
        {"specialty": classes[i], "probability": round(float(probs[i]), 4)}
        for i in sorted_indices[:3]
    ]

    # Explainable Rationale Synthesis
    abnormal_names = [b.get("test_name") for b in abnormal_biomarkers if b.get("test_name")]
    if abnormal_names:
        rationale = (
            f"Based on your reported symptoms and laboratory flags in "
            f"({', '.join(abnormal_names)}), {predicted_specialty} may be a relevant "
            f"specialist to consult. This is a suggestion to help guide your next step, "
            f"not a diagnosis — please confirm with a healthcare professional."
        )
    else:
        rationale = (
            f"Based on your reported symptoms and health concerns, {predicted_specialty} may be a relevant "
            f"specialist to consult. This is a suggestion to help guide your next step, "
            f"not a diagnosis — please confirm with a healthcare professional."
        )

    response_dict = {
        "recommended_specialty_name": predicted_specialty,
        "confidence_score": round(confidence_score, 2),
        "rationale": rationale,
        "model_used": "VitaLensSpecialtyNet (Custom PyTorch MLP)",
        "top_3_specialties": top_3,
        "all_probabilities": {classes[i]: round(float(probs[i]), 4) for i in range(len(classes))}
    }

    if return_trace_telemetry:
        # Extract detailed technical telemetry for AI Trace
        mapping_table = []
        for dense_idx, b_name in enumerate(CANONICAL_BIOMARKERS):
            if b_name in biomarker_map:
                val, flag, orig_canonical, orig_test, unit = biomarker_map[b_name]
                mapping_table.append({
                    "model_dense_index": dense_idx,
                    "canonical_feature": b_name,
                    "source_name": orig_canonical,
                    "source_test_name": orig_test,
                    "value": val,
                    "unit": unit,
                    "flag": flag,
                    "status": "MAPPED_FROM_REPORT"
                })
            else:
                mapping_table.append({
                    "model_dense_index": dense_idx,
                    "canonical_feature": b_name,
                    "source_name": None,
                    "source_test_name": None,
                    "value": DEFAULT_NORMAL_MIDPOINTS.get(b_name, 0.0),
                    "unit": None,
                    "flag": "NORMAL",
                    "status": "DEFAULTED_NORMAL_MIDPOINT"
                })
        mapping_table.extend(unmapped_list)

        matched_terms = []
        try:
            feature_names = pipeline.vectorizer.get_feature_names_out()
            row_tfidf = feature_vector[0, :pipeline.max_tfidf_features]
            non_zero_indices = np.where(row_tfidf > 0)[0]
            matched_terms = [str(feature_names[idx]) for idx in non_zero_indices]
        except Exception:
            pass

        dense_breakdown = []
        try:
            dense_unscaled = pipeline._extract_biomarker_features([row])[0]
            dense_scaled = pipeline.scaler.transform([dense_unscaled])[0]
            for j, b_name in enumerate(CANONICAL_BIOMARKERS):
                raw_v = float(dense_unscaled[j * 2])
                raw_f = float(dense_unscaled[j * 2 + 1])
                sc_v = round(float(dense_scaled[j * 2]), 4)
                sc_f = round(float(dense_scaled[j * 2 + 1]), 4)
                dense_breakdown.append({
                    "feature": b_name,
                    "raw_value": raw_v,
                    "raw_flag_encoded": raw_f,
                    "scaled_value": sc_v,
                    "scaled_flag": sc_f
                })
        except Exception:
            pass

        response_dict["trace_telemetry"] = {
            "full_text": full_text,
            "mapping_table": mapping_table,
            "matched_tfidf_terms": matched_terms,
            "dense_breakdown": dense_breakdown,
            "inference_duration_ms": round(inference_duration_ms, 2),
            "input_feature_count": int(feature_vector.shape[1]),
            "text_features_dim": int(pipeline.max_tfidf_features),
            "dense_features_dim": int(len(CANONICAL_BIOMARKERS) * 2 + 2),
            "all_probabilities_sorted": [
                {"specialty": classes[i], "probability": round(float(probs[i]), 4)}
                for i in sorted_indices
            ]
        }

    return response_dict
