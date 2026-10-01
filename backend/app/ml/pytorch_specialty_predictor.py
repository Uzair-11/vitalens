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

def predict_specialty_pytorch(
    primary_concern: str,
    symptoms_list: List[str],
    body_region: str,
    abnormal_biomarkers: List[Dict[str, Any]],
    severity_score: int = 5,
    duration_days: int = 7
) -> Optional[Dict[str, Any]]:
    """
    Executes inference using custom PyTorch VitaLensSpecialtyNet.
    Returns predicted specialty, probability scores, top-3 candidates, and explainable rationale.
    """
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

    # Map extracted abnormal biomarkers into canonical columns
    abnormal_map = {}
    for b in abnormal_biomarkers:
        name_clean = (b.get("canonical_name") or b.get("test_name") or "").lower().replace(" ", "_")
        val = b.get("value_numeric", 0.0)
        flag = b.get("flag", "NORMAL")
        abnormal_map[name_clean] = (val, flag)

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

    for b_name in CANONICAL_BIOMARKERS:
        if b_name in abnormal_map:
            val, flag = abnormal_map[b_name]
            row[f"val_{b_name}"] = val
            row[f"flag_{b_name}"] = flag
        else:
            row[f"val_{b_name}"] = DEFAULT_NORMAL_MIDPOINTS.get(b_name, 0.0)
            row[f"flag_{b_name}"] = "NORMAL"

    # Transform through feature pipeline
    feature_vector = pipeline.transform([row])  # Shape: (1, 298)
    tensor_input = torch.tensor(feature_vector, dtype=torch.float32)

    # Model inference
    with torch.no_grad():
        logits = model(tensor_input)
        probs = torch.softmax(logits, dim=-1).numpy()[0]

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

    return {
        "recommended_specialty_name": predicted_specialty,
        "confidence_score": round(confidence_score, 2),
        "rationale": rationale,
        "model_used": "VitaLensSpecialtyNet (Custom PyTorch MLP)",
        "top_3_specialties": top_3,
        "all_probabilities": {classes[i]: round(float(probs[i]), 4) for i in range(len(classes))}
    }
