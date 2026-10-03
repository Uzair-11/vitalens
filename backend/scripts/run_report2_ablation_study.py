"""
VitaLens Report #2 Ablation Study & Baseline Diagnostic Script.
Runs the exact database records for Test A, Test B, and Test C through the production
PyTorch VitaLensSpecialtyNet pipeline under 6 controlled biomarker ablation conditions:
  1. All Abnormalities
  2. Bilirubin Removed (Bilirubin = Normal)
  3. Thyroid Removed (TSH, Free T4 = Normal)
  4. Hematology Removed (Hemoglobin, WBC, Platelets, Ferritin, Iron, RBC, Hematocrit = Normal)
  5. Thyroid Only (Only TSH, Free T4 abnormal)
  6. Currently-Supported Hematology Only (Only Hemoglobin, WBC, Platelet abnormal)

Outputs all 10 specialty probabilities for every run to establish a clean, reproducible V1 baseline.
"""

import sys
import os
import json

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

training_dir = os.path.abspath(os.path.join(backend_dir, "app", "ml", "training"))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from app.ml.pytorch_specialty_predictor import predict_specialty_pytorch

# Exact 11 abnormal biomarkers from Report #2 in production database
FULL_REPORT_2_BIOMARKERS = [
    {"test_name": "Bilirubin, Total", "canonical_name": "Bilirubin, Total", "value_numeric": 1.4, "unit": "mg/dL", "flag": "HIGH"},
    {"test_name": "Thyroid Stimulating Hormone (TSH)", "canonical_name": "Thyroid Stimulating Hormone (TSH)", "value_numeric": 6.8, "unit": "mIU/L", "flag": "HIGH"},
    {"test_name": "Free T4", "canonical_name": "Free T4", "value_numeric": 0.72, "unit": "ng/dL", "flag": "LOW"},
    {"test_name": "Ferritin", "canonical_name": "Ferritin", "value_numeric": 9.0, "unit": "ng/mL", "flag": "LOW"},
    {"test_name": "Iron", "canonical_name": "Iron", "value_numeric": 42.0, "unit": "ug/dL", "flag": "LOW"},
    {"test_name": "Hemoglobin (Hb)", "canonical_name": "Hemoglobin (Hb)", "value_numeric": 11.2, "unit": "g/dL", "flag": "LOW"},
    {"test_name": "White Blood Cell Count (WBC)", "canonical_name": "White Blood Cell Count (WBC)", "value_numeric": 12400.0, "unit": "cells/mcL", "flag": "HIGH"},
    {"test_name": "Red Blood Cell Count (RBC)", "canonical_name": "Red Blood Cell Count (RBC)", "value_numeric": 3.78, "unit": "million/mcL", "flag": "LOW"},
    {"test_name": "Platelet Count", "canonical_name": "Platelet Count", "value_numeric": 472000.0, "unit": "cells/mcL", "flag": "HIGH"},
    {"test_name": "Hematocrit (PCV)", "canonical_name": "Hematocrit (PCV)", "value_numeric": 34.1, "unit": "%", "flag": "LOW"},
    {"test_name": "LDL Cholesterol", "canonical_name": "LDL Cholesterol", "value_numeric": 112.0, "unit": "mg/dL", "flag": "HIGH"}
]

# Exact DB records from symptom_logs table
DB_TEST_CASES = [
    {
        "test_code": "TEST A",
        "description": "Feeling unusually tired and dizzy (Fatigue + Dizziness + Headache)",
        "concern": "Feeling unusually tired and dizzy",
        "symptoms": ["Dizziness", "Headache", "Fatigue"],
        "region": "General",
        "severity": 5,
        "duration": 7
    },
    {
        "test_code": "TEST B",
        "description": "Neck swelling and feeling unusually tired",
        "concern": "Neck swelling and feeling unusually tired",
        "symptoms": [],
        "region": "General",
        "severity": 5,
        "duration": 7
    },
    {
        "test_code": "TEST C",
        "description": "Routine follow-up for abnormal laboratory results (No significant symptoms)",
        "concern": "Routine follow-up for abnormal laboratory results",
        "symptoms": [],
        "region": "General",
        "severity": 5,
        "duration": 7
    }
]

def get_ablation_biomarkers(condition_name: str):
    """Filters Report #2 biomarkers according to the experimental ablation condition."""
    if condition_name == "1. All Abnormalities":
        return list(FULL_REPORT_2_BIOMARKERS)

    elif condition_name == "2. Bilirubin Removed":
        return [b for b in FULL_REPORT_2_BIOMARKERS if "bilirubin" not in b["canonical_name"].lower()]

    elif condition_name == "3. Thyroid Removed":
        return [b for b in FULL_REPORT_2_BIOMARKERS if "tsh" not in b["canonical_name"].lower() and "free t4" not in b["canonical_name"].lower()]

    elif condition_name == "4. Hematology Removed":
        hematology_keys = ["hemoglobin", "wbc", "platelet", "rbc", "hematocrit", "ferritin", "iron"]
        return [b for b in FULL_REPORT_2_BIOMARKERS if not any(k in b["canonical_name"].lower() for k in hematology_keys)]

    elif condition_name == "5. Thyroid-Only":
        return [b for b in FULL_REPORT_2_BIOMARKERS if "tsh" in b["canonical_name"].lower() or "free t4" in b["canonical_name"].lower()]

    elif condition_name == "6. Currently-Supported Hematology-Only":
        supported_keys = ["hemoglobin", "white blood cell count", "platelet count"]
        return [b for b in FULL_REPORT_2_BIOMARKERS if any(k in b["canonical_name"].lower() for k in supported_keys)]

    else:
        raise ValueError(f"Unknown condition: {condition_name}")

ABLATION_CONDITIONS = [
    "1. All Abnormalities",
    "2. Bilirubin Removed",
    "3. Thyroid Removed",
    "4. Hematology Removed",
    "5. Thyroid-Only",
    "6. Currently-Supported Hematology-Only"
]

def run_study():
    print("=" * 100)
    print("VITALENS SPECIALTY MODEL — REPORT #2 CONTROLLED ABLATION STUDY")
    print("Framework: PyTorch VitaLensSpecialtyNet (298 Features, 10 Classes, Fixed V1 Baseline)")
    print("=" * 100)

    summary_matrix = {}

    for test_case in DB_TEST_CASES:
        t_code = test_case["test_code"]
        summary_matrix[t_code] = {}
        print(f"\n" + "#" * 100)
        print(f"PATIENT SCENARIO: {t_code} — {test_case['description']}")
        print(f"Inputs: Concern='{test_case['concern']}', Symptoms={test_case['symptoms']}, Region='{test_case['region']}'")
        print("#" * 100)

        for cond in ABLATION_CONDITIONS:
            biomarkers = get_ablation_biomarkers(cond)
            res = predict_specialty_pytorch(
                primary_concern=test_case["concern"],
                symptoms_list=test_case["symptoms"],
                body_region=test_case["region"],
                abnormal_biomarkers=biomarkers,
                severity_score=test_case["severity"],
                duration_days=test_case["duration"],
                return_trace_telemetry=True
            )

            winner = res["recommended_specialty_name"]
            conf = res["confidence_score"]
            probs_list = res["trace_telemetry"]["all_probabilities_sorted"]
            summary_matrix[t_code][cond] = {
                "winner": winner,
                "confidence": conf,
                "probabilities": {p["specialty"]: p["probability"] for p in probs_list}
            }

            print(f"\n>>> Condition: {cond} ({len(biomarkers)} active markers)")
            print(f"    WINNER: >>> {winner} <<< (Confidence: {conf*100:.2f}%)")
            print("    Complete Probability Distribution (All 10 Specialties):")
            for p in probs_list:
                spec = p["specialty"]
                prob = p["probability"]
                is_win = spec == winner
                indicator = "==>" if is_win else "   "
                bar = "#" * int(prob * 35)
                print(f"    {indicator} {spec:25s}: {prob*100:6.2f}% | {bar}")

    # Summary Comparison Grid
    print("\n" + "=" * 100)
    print("ABLATION STUDY SUMMARY MATRIX — WINNER & CONFIDENCE ACROSS ALL RUNS")
    print("=" * 100)
    header = f"{'Condition':40s} | {'Test A (Fatigue/Dizzy/Headache)':28s} | {'Test B (Neck Swelling)':28s} | {'Test C (Routine Follow-up)':28s}"
    print(header)
    print("-" * 135)
    for cond in ABLATION_CONDITIONS:
        res_a = summary_matrix["TEST A"][cond]
        res_b = summary_matrix["TEST B"][cond]
        res_c = summary_matrix["TEST C"][cond]
        str_a = f"{res_a['winner']} ({res_a['confidence']*100:.1f}%)"
        str_b = f"{res_b['winner']} ({res_b['confidence']*100:.1f}%)"
        str_c = f"{res_c['winner']} ({res_c['confidence']*100:.1f}%)"
        print(f"{cond:40s} | {str_a:28s} | {str_b:28s} | {str_c:28s}")
    print("=" * 100)

    # Save machine-readable JSON results
    output_json_path = os.path.join(os.path.dirname(__file__), "ablation_results.json")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_matrix, f, indent=2)
    print(f"\n[OK] Machine-readable results saved to: {output_json_path}")

if __name__ == "__main__":
    run_study()
