# PyTorch Specialty Predictor for VitaLens API
"""
Loads the custom-trained VitaLensSpecialtyNet model and feature pipeline
to perform real-time multi-class inference on patient symptoms and lab biomarkers.
"""

import os
import sys
import json
import torch
import logging
import uuid
import numpy as np
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Ensure backend and training packages are on PYTHONPATH
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
training_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "training"))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from app.ml.models.specialty_network import VitaLensSpecialtyNet
from app.ml.training.feature_pipeline import ClinicalFeaturePipeline, CANONICAL_BIOMARKERS, FLAG_ENCODING
from app.ml.training.feature_pipeline_v2 import ClinicalFeaturePipelineV2, CANONICAL_BIOMARKERS_V2, FLAG_ENCODING as FLAG_ENCODING_V2

# ---------------------------------------------------------------------------
# Biomarker Name Normalization and Aliases
# ---------------------------------------------------------------------------
ALIAS_MAP: Dict[str, str] = {
    # Glucose aliases
    "fasting_blood_glucose": "glucose_fasting",
    "fasting glucose": "glucose_fasting",
    "fasting_glucose": "glucose_fasting",
    "glucose_fasting": "glucose_fasting",
    "glucose, fasting": "glucose_fasting",
    "fbs": "glucose_fasting",
    # TSH aliases
    "thyroid_stimulating_hormone": "tsh",
    "thyroid stimulating hormone": "tsh",
    "tsh": "tsh",
    "thyroid_stimulating_hormone_tsh": "tsh",
    # HbA1c aliases
    "glycated_hemoglobin_(hba1c)": "hba1c",
    "glycated hemoglobin (hba1c)": "hba1c",
    "a1c": "hba1c",
    # Bilirubin aliases
    "bilirubin_total": "total_bilirubin",
    "bilirubintotal": "total_bilirubin",
    "total_bilirubin": "total_bilirubin",
    "bilirubin,total": "total_bilirubin",
    "bilirubin_total_(mg/dl)": "total_bilirubin",
    "serum_bilirubin": "total_bilirubin",
    "total_serum_bilirubin": "total_bilirubin",
    "serum_total_bilirubin": "total_bilirubin",
    "t_bilirubin": "total_bilirubin",
    "bilirubin": "total_bilirubin",
    "ft4": "free_t4",
    "glycated_hemoglobin_hba1c": "hba1c",
    "bilirubin_total_mg/dl": "total_bilirubin",

    # LDL cholesterol aliases
    "ldl": "ldl_cholesterol",
    "ldl_cholesterol": "ldl_cholesterol",
    "cholesterol, ldl": "ldl_cholesterol",
    "cholesterol_ldl": "ldl_cholesterol",
    # HDL cholesterol aliases
    "hdl": "hdl_cholesterol",
    "hdl_cholesterol": "hdl_cholesterol",
    "cholesterol, hdl": "hdl_cholesterol",
    # Triglyceride aliases
    "triglycerides": "triglycerides",
    "triglyceride": "triglycerides",
    "tg": "triglycerides",
    "free_thyroxine": "free_t4",
    # WBC aliases
    "wbc": "wbc_count",
    "wbc_count": "wbc_count",
    "white_blood_cell_count": "wbc_count",
    "white_blood_cell_count_wbc": "wbc_count",
    "platelets": "platelet_count",
    "plt": "platelet_count",
}

# V2-specific canonical aliases (anemia & CBC panel extensions)
ALIAS_MAP_V2: Dict[str, str] = {
    **ALIAS_MAP,
    "hemoglobin_hb": "hemoglobin",
    "hemoglobin_(hb)": "hemoglobin",
    "red_blood_cell_count_rbc": "rbc_count",
    "red_blood_cell_count_(rbc)": "rbc_count",
    "hematocrit_pcv": "hematocrit",
    "hematocrit_(pcv)": "hematocrit",
    "blood_urea_nitrogen_bun": "bun",
    "blood_urea_nitrogen": "bun",
    "estimated_glomerular_filtration_rate_egfr": "egfr",
    "estimated_glomerular_filtration_rate": "egfr",
    "uric_acid_serum": "uric_acid",
    # Liver enzyme and inflammatory marker canonical aliases
    "alanine_aminotransferase_alt": "alt_sgpt",
    "alanine_aminotransferase_(alt)": "alt_sgpt",
    "alanine_aminotransferase": "alt_sgpt",
    "alt": "alt_sgpt",
    "sgpt": "alt_sgpt",
    "aspartate_aminotransferase_ast": "ast_sgot",
    "aspartate_aminotransferase_(ast)": "ast_sgot",
    "aspartate_aminotransferase": "ast_sgot",
    "ast": "ast_sgot",
    "sgot": "ast_sgot",
    "c-reactive_protein_crp": "crp",
    "c_reactive_protein_crp": "crp",
    "c-reactive_protein_(crp)": "crp",
    "c_reactive_protein_(crp)": "crp",
    "c-reactive_protein": "crp",
    "c_reactive_protein": "crp",
    "crp": "crp",
    "erythrocyte_sedimentation_rate_esr": "esr",
    "erythrocyte_sedimentation_rate_(esr)": "esr",
    "erythrocyte_sedimentation_rate": "esr",
    "esr": "esr",
}

def normalize_biomarker_for_model(name: str, alias_map: Optional[Dict[str, str]] = None) -> str:
    """Normalize biomarker names to canonical feature keys used in the model.
    Handles whitespace, commas, parentheses, case, and known alias mappings.
    """
    key = (
        name.strip()
        .lower()
        .replace(" ", "_")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
    )
    mapping = alias_map if alias_map is not None else ALIAS_MAP
    return mapping.get(key, key)

# ---------------------------------------------------------------------------
# Version Configuration and Isolated Caches
# ---------------------------------------------------------------------------
DEFAULT_MODEL_VERSION = "v1"
MODEL_VERSION = os.getenv("VITALENS_MODEL_VERSION", DEFAULT_MODEL_VERSION).strip().lower()

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
MODEL_DIR = os.path.join(REPO_ROOT, "models")

VERSION_CONFIG: Dict[str, Dict[str, Any]] = {
    "v1": {
        "pipeline_class": ClinicalFeaturePipeline,
        "canonical_biomarkers": CANONICAL_BIOMARKERS,
        "flag_encoding": FLAG_ENCODING,
        "alias_map": ALIAS_MAP,
        "model_path": os.path.join(MODEL_DIR, "specialty_model.pt"),
        "pipeline_path": os.path.join(MODEL_DIR, "feature_pipeline.joblib"),
        "metadata_path": os.path.join(MODEL_DIR, "model_metadata.json"),
        "expected_input_dim": 298,
    },
    "v2": {
        "pipeline_class": ClinicalFeaturePipelineV2,
        "canonical_biomarkers": CANONICAL_BIOMARKERS_V2,
        "flag_encoding": FLAG_ENCODING_V2,
        "alias_map": ALIAS_MAP_V2,
        "model_path": os.path.join(MODEL_DIR, "v2", "specialty_model_v2.pt"),
        "pipeline_path": os.path.join(MODEL_DIR, "v2", "feature_pipeline_v2.joblib"),
        "metadata_path": os.path.join(MODEL_DIR, "v2", "model_metadata_v2.json"),
        "expected_input_dim": 306,
    },
}

# Module-level defaults for backward compatibility
if MODEL_VERSION == "v2":
    PIPELINE_CLASS = ClinicalFeaturePipelineV2
    CANONICAL_BIOMARKERS_USED = CANONICAL_BIOMARKERS_V2
    FLAG_ENCODING_USED = FLAG_ENCODING_V2
else:
    PIPELINE_CLASS = ClinicalFeaturePipeline
    CANONICAL_BIOMARKERS_USED = CANONICAL_BIOMARKERS
    FLAG_ENCODING_USED = FLAG_ENCODING

# Isolated cached instances per version
_MODEL_CACHE: Dict[str, VitaLensSpecialtyNet] = {}
_PIPELINE_CACHE: Dict[str, object] = {}
_METADATA_CACHE: Dict[str, Dict[str, Any]] = {}


def resolve_model_version(requested_version: Optional[str] = None) -> str:
    """Resolve the active model version.

    Precedence:
    1. Explicit requested_version parameter if provided.
    2. Environment variable VITALENS_MODEL_VERSION if set.
    3. Default 'v1'.
    """
    if requested_version:
        ver = str(requested_version).strip().lower()
    else:
        ver = os.getenv("VITALENS_MODEL_VERSION", DEFAULT_MODEL_VERSION).strip().lower()
    return ver


def load_pytorch_specialty_model(version: Optional[str] = None):
    """Load model, pipeline and metadata for the specified version (cached per version).

    There is NO automatic fallback: if the requested version fails to load,
    returns (None, None, None) so callers can fail explicitly.
    """
    ver = resolve_model_version(version)
    if ver not in VERSION_CONFIG:
        logger.error("Unsupported model version requested: %s", ver)
        return None, None, None

    if ver in _MODEL_CACHE and ver in _PIPELINE_CACHE:
        return _MODEL_CACHE[ver], _PIPELINE_CACHE[ver], _METADATA_CACHE.get(ver, {})

    cfg = VERSION_CONFIG[ver]
    model_path = cfg["model_path"]
    pipeline_path = cfg["pipeline_path"]
    metadata_path = cfg["metadata_path"]
    pipeline_class = cfg["pipeline_class"]

    if not os.path.exists(model_path) or not os.path.exists(pipeline_path):
        logger.error(
            "Model or pipeline file missing for %s (model_path=%s, pipeline_path=%s)",
            ver,
            model_path,
            pipeline_path,
        )
        return None, None, None

    try:
        pipeline = pipeline_class.load(pipeline_path)
    except Exception as e:
        logger.exception("Failed to load pipeline for %s: %s", ver, e)
        return None, None, None

    try:
        checkpoint = torch.load(model_path, map_location=torch.device("cpu"), weights_only=False)
        input_dim = checkpoint.get("input_dim", cfg["expected_input_dim"])
        num_classes = checkpoint.get("num_classes", 10)
        hidden_dims = checkpoint.get("hidden_dims", (256, 128, 64))
        dropout_rate = checkpoint.get("dropout_rate", 0.25)
        model = VitaLensSpecialtyNet(
            input_dim=input_dim,
            num_classes=num_classes,
            hidden_dims=hidden_dims,
            dropout_rate=dropout_rate,
        )
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()
    except Exception as e:
        logger.exception("Failed to load model for %s: %s", ver, e)
        return None, None, None

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {"classes": checkpoint.get("classes", [])}
    else:
        metadata = {"classes": checkpoint.get("classes", [])}

    _MODEL_CACHE[ver] = model
    _PIPELINE_CACHE[ver] = pipeline
    _METADATA_CACHE[ver] = metadata
    return model, pipeline, metadata


# ---------------------------------------------------------------------------
# Main prediction function
# ---------------------------------------------------------------------------
def predict_specialty_pytorch(
    primary_concern: str,
    symptoms_list: List[str],
    body_region: str,
    abnormal_biomarkers: List[Dict[str, Any]],
    severity_score: int = 5,
    duration_days: int = 7,
    return_trace_telemetry: bool = False,
    model_version: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Execute inference and return a structured response.

    Resolves model_version explicitly at prediction time (precedence: parameter ->
    environment variable VITALENS_MODEL_VERSION -> default 'v1').
    Errors are returned as JSON objects containing ``error``, ``model_version`` and ``request_id``.
    There is NO automatic fallback between versions.
    """
    active_version = resolve_model_version(model_version)
    request_id = uuid.uuid4().hex

    if active_version not in VERSION_CONFIG:
        return {
            "error": f"Invalid model version '{active_version}'. Supported versions are 'v1' and 'v2'.",
            "model_version": active_version,
            "request_id": request_id,
        }

    # Basic sanity checks – return a structured error instead of raising
    if not primary_concern or symptoms_list is None or not body_region or abnormal_biomarkers is None:
        return {
            "error": "Malformed request: missing required fields",
            "model_version": active_version,
            "request_id": request_id,
        }

    # Load model / pipeline / metadata (cached per version, no fallback)
    model, pipeline, metadata = load_pytorch_specialty_model(active_version)
    if model is None or pipeline is None:
        return {
            "error": "Model or pipeline failed to load",
            "model_version": active_version,
            "request_id": request_id,
        }

    cfg = VERSION_CONFIG[active_version]
    canonical_biomarkers = cfg["canonical_biomarkers"]
    expected_dim = cfg["expected_input_dim"]
    active_alias_map = cfg.get("alias_map", ALIAS_MAP)

    classes = metadata.get("classes", [
        "Cardiology", "Endocrinology", "Hematology", "Gastroenterology",
        "Nephrology", "Pulmonology", "Dermatology", "Neurology",
        "Orthopedics", "General Medicine",
    ])

    # Assemble row for the pipeline
    symptoms_text = ", ".join(symptoms_list) if symptoms_list else primary_concern
    full_text = f"Primary Concern: {primary_concern}. Symptoms: {symptoms_text}. Affected Area: {body_region}."
    row = {
        "primary_concern": primary_concern,
        "symptoms": symptoms_text,
        "body_region": body_region,
        "full_text": full_text,
        "severity_score": severity_score,
        "duration_days": duration_days,
    }

    # Map biomarkers to the canonical set for this version
    biomarker_map = {}
    unmapped_list = []
    for b in abnormal_biomarkers:
        test_name = b.get("test_name") or ""
        canonical_name = b.get("canonical_name") or test_name
        feat_name = normalize_biomarker_for_model(canonical_name, alias_map=active_alias_map)
        if feat_name not in canonical_biomarkers and test_name:
            feat_name = normalize_biomarker_for_model(test_name, alias_map=active_alias_map)
        val = b.get("value_numeric")
        flag = b.get("flag", "NORMAL")
        unit = b.get("unit", "")
        if val is not None:
            if feat_name in canonical_biomarkers:
                biomarker_map[feat_name] = (float(val), flag, canonical_name, test_name, unit)
            else:
                unmapped_list.append({
                    "canonical_feature": feat_name,
                    "source_name": canonical_name,
                    "source_test_name": test_name,
                    "value": float(val),
                    "unit": unit,
                    "flag": flag,
                    "status": "UNMAPPED_EXCLUDED_FROM_SCHEMA",
                    "reason": "Biomarker not part of model schema",
                })

    # Populate all required biomarker fields (default normal values)
    for i, b_name in enumerate(canonical_biomarkers):
        if b_name in biomarker_map:
            val, flag, _, _, _ = biomarker_map[b_name]
            row[f"val_{b_name}"] = val
            row[f"flag_{b_name}"] = flag
        else:
            if active_version == "v2" and hasattr(pipeline, "scaler") and hasattr(pipeline.scaler, "mean_"):
                row[f"val_{b_name}"] = float(pipeline.scaler.mean_[i * 2])
            else:
                row[f"val_{b_name}"] = 0.0  # placeholder normal midpoint
            row[f"flag_{b_name}"] = "NORMAL"

    # Transform to feature vector
    feature_vector = pipeline.transform([row])
    actual_dim = int(feature_vector.shape[1])
    if metadata:
        meta_dim = metadata.get("input_dimensions") or metadata.get("feature_dimensions", {}).get("total_input_dim")
        if meta_dim is not None:
            expected_dim = int(meta_dim)
    if actual_dim != expected_dim:
        logger.error(
            "Feature dimension mismatch for %s: %s vs expected %s", active_version, actual_dim, expected_dim
        )
        return {
            "error": "Feature dimension mismatch",
            "model_version": active_version,
            "request_id": request_id,
        }

    tensor_input = torch.tensor(feature_vector, dtype=torch.float32)

    # Inference with timing
    t_start = time.perf_counter()
    try:
        with torch.no_grad():
            logits = model(tensor_input)
            probs = torch.softmax(logits, dim=-1).numpy()[0]
    except Exception as e:
        logger.exception("Model inference failed for request %s (version=%s)", request_id, active_version)
        return {"error": "Model inference failed", "model_version": active_version, "request_id": request_id}
    inference_duration_ms = (time.perf_counter() - t_start) * 1000.0

    top_idx = int(np.argmax(probs))
    predicted_specialty = classes[top_idx]
    confidence_score = float(probs[top_idx])
    sorted_indices = np.argsort(probs)[::-1]
    top_3 = [{"specialty": classes[i], "confidence": round(float(probs[i]), 4)} for i in sorted_indices[:3]]

    # Simple rationale
    abnormal_names = [b.get("test_name") for b in abnormal_biomarkers if b.get("test_name")]
    if abnormal_names:
        rationale = f"Based on your reported symptoms and laboratory flags ({', '.join(abnormal_names)}), {predicted_specialty} may be relevant."
    else:
        rationale = f"Based on your reported symptoms, {predicted_specialty} may be relevant."

    response_dict = {
        "recommended_specialty_name": predicted_specialty,
        "confidence_score": round(confidence_score, 2),
        "rationale": rationale,
        "model_used": "VitaLensSpecialtyNet",
        "top_3_specialties": top_3,
        "all_probabilities": {classes[i]: round(float(probs[i]), 4) for i in range(len(classes))},
        "model_version": active_version,
        "feature_schema_version": active_version,
        "request_id": request_id,
    }

    if return_trace_telemetry:
        mapping_table = []
        for dense_idx, b_name in enumerate(canonical_biomarkers):
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
                    "status": "MAPPED_FROM_REPORT",
                })
            else:
                mapping_table.append({
                    "model_dense_index": dense_idx,
                    "canonical_feature": b_name,
                    "source_name": None,
                    "source_test_name": None,
                    "value": 0.0,
                    "unit": None,
                    "flag": "NORMAL",
                    "status": "DEFAULTED_NORMAL_MIDPOINT",
                })
        mapping_table.extend(unmapped_list)

        # 1. Sorted specialty probabilities
        all_probabilities_sorted = [
            {"specialty": classes[i], "probability": round(float(probs[i]), 4)}
            for i in sorted_indices
        ]

        # 2. Matched TF-IDF symptom terms
        matched_tfidf_terms = []
        if hasattr(pipeline, "vectorizer") and hasattr(pipeline.vectorizer, "get_feature_names_out"):
            try:
                vocab = pipeline.vectorizer.get_feature_names_out()
                tfidf_vec = feature_vector[0, :len(vocab)]
                nz_indices = np.where(tfidf_vec > 0)[0]
                sorted_nz = nz_indices[np.argsort(tfidf_vec[nz_indices])[::-1]]
                matched_tfidf_terms = [str(vocab[idx]) for idx in sorted_nz]
            except Exception as e:
                logger.warning("Could not extract matched_tfidf_terms: %s", e)

        # 3. Dense features breakdown (biomarkers + clinical metadata)
        dense_features_dim = len(canonical_biomarkers) * 2 + 2
        text_features_dim = actual_dim - dense_features_dim
        scaled_dense = feature_vector[0, text_features_dim:]
        flag_encoding = cfg.get("flag_encoding", {})
        dense_breakdown = []
        for j, b_name in enumerate(canonical_biomarkers):
            raw_val = float(row.get(f"val_{b_name}", 0.0))
            raw_flag = str(row.get(f"flag_{b_name}", "NORMAL")).upper()
            raw_flag_enc = flag_encoding.get(raw_flag, 0.0)
            scaled_val = round(float(scaled_dense[j * 2]), 4)
            scaled_flag = round(float(scaled_dense[j * 2 + 1]), 4)
            dense_breakdown.append({
                "feature": b_name,
                "raw_value": round(raw_val, 2),
                "raw_flag_encoded": raw_flag_enc,
                "scaled_value": scaled_val,
                "scaled_flag": scaled_flag,
            })
        dense_breakdown.append({
            "feature": "severity_score",
            "raw_value": round(float(severity_score), 2),
            "raw_flag_encoded": 0.0,
            "scaled_value": round(float(scaled_dense[-2]), 4),
            "scaled_flag": 0.0,
        })
        dense_breakdown.append({
            "feature": "duration_days",
            "raw_value": round(float(duration_days), 2),
            "raw_flag_encoded": 0.0,
            "scaled_value": round(float(scaled_dense[-1]), 4),
            "scaled_flag": 0.0,
        })

        response_dict["trace_telemetry"] = {
            "full_text": full_text,
            "mapping_table": mapping_table,
            "inference_duration_ms": round(inference_duration_ms, 2),
            "input_feature_count": actual_dim,
            "text_features_dim": text_features_dim,
            "dense_features_dim": dense_features_dim,
            "matched_tfidf_terms": matched_tfidf_terms,
            "dense_breakdown": dense_breakdown,
            "all_probabilities_sorted": all_probabilities_sorted,
        }

    return response_dict
