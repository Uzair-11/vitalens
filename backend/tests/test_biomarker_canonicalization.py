"""
Automated Test Suite for Biomarker Canonicalization & Mapping Telemetry.
Verifies that all biomarker alias variations (specifically including all Bilirubin formats)
correctly resolve to canonical model features, and that excluded biomarkers are gracefully tracked.
"""

import sys
import os
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

training_dir = os.path.abspath(os.path.join(backend_dir, "app", "ml", "training"))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from app.ml.pytorch_specialty_predictor import (
    normalize_biomarker_for_model,
    predict_specialty_pytorch,
    CANONICAL_BIOMARKERS
)

class TestBiomarkerCanonicalization(unittest.TestCase):
    def test_bilirubin_canonicalization_variations(self):
        """Verifies that all Bilirubin variations resolve to 'total_bilirubin'."""
        variations = [
            "bilirubin_total",
            "total_bilirubin",
            "Bilirubin, Total",
            "Bilirubin Total",
            "bilirubin, total",
            "bilirubin total",
            "Serum Bilirubin",
            "serum_bilirubin",
            "total_serum_bilirubin",
            "serum_total_bilirubin",
            "t_bilirubin",
            "bilirubin",
            "Bilirubin",
            "bilirubin_total_(mg/dl)",
        ]
        for var in variations:
            normalized = normalize_biomarker_for_model(var)
            self.assertEqual(
                normalized,
                "total_bilirubin",
                f"Failed to canonicalize '{var}' to 'total_bilirubin'. Got '{normalized}'"
            )
        self.assertIn("total_bilirubin", CANONICAL_BIOMARKERS)

    def test_metabolic_and_lipid_canonicalization(self):
        """Verifies glucose, HbA1c, and lipid profile alias resolutions."""
        glucose_vars = ["fasting_blood_glucose", "Fasting Blood Glucose", "glucose, fasting", "fbs", "glucose_fasting", "fasting glucose"]
        for g in glucose_vars:
            self.assertEqual(normalize_biomarker_for_model(g), "glucose_fasting", f"Failed for {g}")

        hba1c_vars = ["hba1c", "HbA1c", "glycated_hemoglobin_(hba1c)", "Glycated Hemoglobin (HbA1c)", "a1c"]
        for h in hba1c_vars:
            self.assertEqual(normalize_biomarker_for_model(h), "hba1c", f"Failed for {h}")

        ldl_vars = ["ldl_cholesterol", "LDL Cholesterol", "ldl", "cholesterol, ldl"]
        for l in ldl_vars:
            self.assertEqual(normalize_biomarker_for_model(l), "ldl_cholesterol", f"Failed for {l}")

    def test_cbc_and_thyroid_canonicalization(self):
        """Verifies CBC and Thyroid alias resolutions."""
        tsh_vars = ["tsh", "TSH", "thyroid_stimulating_hormone", "Thyroid Stimulating Hormone (TSH)"]
        for t in tsh_vars:
            self.assertEqual(normalize_biomarker_for_model(t), "tsh", f"Failed for {t}")

        t4_vars = ["free_t4", "Free T4", "ft4", "free_thyroxine"]
        for f in t4_vars:
            self.assertEqual(normalize_biomarker_for_model(f), "free_t4", f"Failed for {f}")

        wbc_vars = ["wbc_count", "wbc", "white_blood_cell_count", "White Blood Cell Count (WBC)"]
        for w in wbc_vars:
            self.assertEqual(normalize_biomarker_for_model(w), "wbc_count", f"Failed for {w}")

        plt_vars = ["platelet_count", "platelets", "Platelet Count", "plt"]
        for p in plt_vars:
            self.assertEqual(normalize_biomarker_for_model(p), "platelet_count", f"Failed for {p}")

    def test_unmapped_biomarkers_tracked_safely(self):
        """Verifies that non-schema biomarkers are gracefully captured as unmapped without throwing errors."""
        excluded_markers = [
            {"test_name": "Ferritin", "canonical_name": "Ferritin", "value_numeric": 9.0, "flag": "LOW"},
            {"test_name": "Iron", "canonical_name": "Iron", "value_numeric": 42.0, "flag": "LOW"},
            {"test_name": "Red Blood Cell Count (RBC)", "canonical_name": "Red Blood Cell Count (RBC)", "value_numeric": 3.78, "flag": "LOW"},
            {"test_name": "Hematocrit (PCV)", "canonical_name": "Hematocrit (PCV)", "value_numeric": 34.1, "flag": "LOW"},
        ]
        res = predict_specialty_pytorch(
            primary_concern="Checkup",
            symptoms_list=[],
            body_region="Whole Body",
            abnormal_biomarkers=excluded_markers,
            return_trace_telemetry=True
        )
        self.assertIsNotNone(res)
        telem = res.get("trace_telemetry", {})
        mapping_table = telem.get("mapping_table", [])
        
        # Verify 20 canonical biomarkers are defaulted
        defaulted = [m for m in mapping_table if m.get("status") == "DEFAULTED_NORMAL_MIDPOINT"]
        self.assertEqual(len(defaulted), 20)

        # Verify all 4 excluded biomarkers are identified as unmapped
        unmapped = [m for m in mapping_table if m.get("status") == "UNMAPPED_EXCLUDED_FROM_SCHEMA"]
        self.assertEqual(len(unmapped), 4)

    def test_report_2_bilirubin_now_maps_cleanly(self):
        """Confirms that Report #2's Bilirubin now maps to total_bilirubin cleanly."""
        report_2_sample = [
            {"test_name": "Bilirubin", "canonical_name": "bilirubin_total", "value_numeric": 1.4, "unit": "mg/dL", "flag": "HIGH"},
            {"test_name": "TSH", "canonical_name": "tsh", "value_numeric": 6.8, "unit": "mIU/L", "flag": "HIGH"},
        ]
        res = predict_specialty_pytorch(
            primary_concern="Checkup",
            symptoms_list=[],
            body_region="Whole Body",
            abnormal_biomarkers=report_2_sample,
            return_trace_telemetry=True
        )
        telem = res["trace_telemetry"]
        mapping_table = telem["mapping_table"]

        bili_entry = next((m for m in mapping_table if m.get("canonical_feature") == "total_bilirubin"), None)
        self.assertIsNotNone(bili_entry)
        self.assertEqual(bili_entry["status"], "MAPPED_FROM_REPORT")
        self.assertEqual(bili_entry["value"], 1.4)
        self.assertEqual(bili_entry["flag"], "HIGH")

if __name__ == "__main__":
    unittest.main()
