"""
FHIR R4 Mapper for VitaLens Medical Reports and Biomarkers.
Converts internal relational domain models into standard HL7 FHIR R4 DiagnosticReport and Observation resources.

Standard Reference: HL7 FHIR Release 4 (v4.0.1)
- DiagnosticReport: http://hl7.org/fhir/R4/diagnosticreport.html
- Observation: http://hl7.org/fhir/R4/observation.html
- Bundle: http://hl7.org/fhir/R4/bundle.html
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Standard LOINC mapping table for VitaLens canonical clinical biomarkers
CANONICAL_LOINC_MAP: Dict[str, str] = {
    # Complete Blood Count (CBC)
    "hemoglobin": "718-7",
    "hemoglobin (hb)": "718-7",
    "hgb": "718-7",
    "white blood cell count": "6690-2",
    "white blood cell count (wbc)": "6690-2",
    "wbc": "6690-2",
    "red blood cell count": "789-8",
    "red blood cell count (rbc)": "789-8",
    "rbc": "789-8",
    "platelets": "777-3",
    "platelet count": "777-3",
    "hematocrit": "4544-3",
    "hematocrit (pcv)": "4544-3",
    "pcv": "4544-3",

    # Diabetes & Metabolism
    "fasting blood glucose": "1558-6",
    "fasting blood sugar": "1558-6",
    "fasting glucose": "1558-6",
    "glucose, fasting": "1558-6",
    "blood glucose": "2345-7",
    "glucose": "2345-7",
    "hba1c": "4548-4",
    "glycated hemoglobin (hba1c)": "4548-4",
    "glycated hemoglobin": "4548-4",

    # Lipid Profile
    "total cholesterol": "2093-3",
    "cholesterol, total": "2093-3",
    "cholesterol": "2093-3",
    "ldl cholesterol": "13457-7",
    "ldl": "13457-7",
    "hdl cholesterol": "2085-9",
    "hdl": "2085-9",
    "triglycerides": "2571-8",
    "triglyceride": "2571-8",

    # Renal Panel / Kidney Function (KFT)
    "serum creatinine": "2160-0",
    "creatinine": "2160-0",
    "bun": "3094-0",
    "blood urea nitrogen": "3094-0",
    "blood urea nitrogen (bun)": "3094-0",
    "urea": "3094-0",
    "egfr": "33914-3",
    "estimated gfr": "33914-3",

    # Liver Function (LFT)
    "alt": "1742-6",
    "alanine aminotransferase (alt)": "1742-6",
    "sgpt": "1742-6",
    "ast": "1920-8",
    "aspartate aminotransferase (ast)": "1920-8",
    "sgot": "1920-8",
    "total bilirubin": "1975-2",
    "bilirubin total": "1975-2",
    "direct bilirubin": "1968-7",
    "alkaline phosphatase": "6768-6",
    "alp": "6768-6",

    # Thyroid Panel
    "tsh": "3016-3",
    "thyroid stimulating hormone (tsh)": "3016-3",
    "thyroid stimulating hormone": "3016-3",
    "free t3": "3051-2",
    "free t4": "3024-7",

    # Electrolytes & Minerals
    "serum calcium": "17861-6",
    "calcium": "17861-6",
    "serum potassium": "2823-3",
    "potassium": "2823-3",
    "serum sodium": "2951-2",
    "sodium": "2951-2",
    "serum chloride": "2075-0",
    "chloride": "2075-0",
}

def resolve_loinc_code(biomarker: Dict[str, Any]) -> str:
    """
    Resolves standard LOINC code from:
    1. Direct `loinc_code` property (if set)
    2. Canonical name lookup in CANONICAL_LOINC_MAP
    3. Raw test name lookup in CANONICAL_LOINC_MAP
    4. Partial keyword match against canonical registry
    5. Fallback to 'unknown'
    """
    if biomarker.get("loinc_code"):
        return str(biomarker["loinc_code"])

    canonical = (biomarker.get("canonical_name") or "").lower().strip()
    if canonical in CANONICAL_LOINC_MAP:
        return CANONICAL_LOINC_MAP[canonical]

    test_name = (biomarker.get("test_name") or "").lower().strip()
    if test_name in CANONICAL_LOINC_MAP:
        return CANONICAL_LOINC_MAP[test_name]

    # Keyword / substring search
    for key, code in CANONICAL_LOINC_MAP.items():
        if key in canonical or (len(key) > 3 and key in test_name):
            return code

    return "unknown"


def map_biomarker_to_fhir_observation(biomarker: Dict[str, Any], patient_id: str, report_date: str) -> Dict[str, Any]:
    """
    Maps an internal Biomarker record into an HL7 FHIR R4 Observation resource.
    Ensures structural compliance with HL7 FHIR R4 JSON schema:
    - resourceType: Observation
    - status: final
    - category: laboratory
    - code: CodeableConcept (Standard LOINC coding + display text)
    - subject: Reference(Patient)
    - valueQuantity / valueString
    - referenceRange: low/high Quantity
    - interpretation: ObservationInterpretation coding
    """
    flag = (biomarker.get("flag") or "NORMAL").upper()
    flag_code = "N"
    flag_text = "Normal"
    if flag == "HIGH":
        flag_code = "H"
        flag_text = "High"
    elif flag == "LOW":
        flag_code = "L"
        flag_text = "Low"
    elif flag in ("CRITICAL", "PANIC"):
        flag_code = "AA"
        flag_text = "Critical Abnormal"

    canonical = biomarker.get("canonical_name") or biomarker.get("test_name") or "Laboratory Test"
    test_name = biomarker.get("test_name") or canonical
    loinc_code = resolve_loinc_code(biomarker)

    obs: Dict[str, Any] = {
        "resourceType": "Observation",
        "id": f"obs-{biomarker.get('id', 'unknown')}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory"
                    }
                ],
                "text": "Laboratory"
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": loinc_code,
                    "display": canonical
                }
            ],
            "text": test_name
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": report_date,
        "interpretation": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": flag_code,
                        "display": flag_text
                    }
                ],
                "text": flag_text
            }
        ]
    }

    unit_str = biomarker.get("unit") or ""

    if biomarker.get("value_numeric") is not None:
        obs["valueQuantity"] = {
            "value": float(biomarker["value_numeric"]),
            "unit": unit_str,
            "system": "http://unitsofmeasure.org",
            "code": unit_str
        }
    elif biomarker.get("value_text"):
        obs["valueString"] = str(biomarker["value_text"])

    ref_min = biomarker.get("reference_min")
    ref_max = biomarker.get("reference_max")
    if ref_min is not None or ref_max is not None:
        ref_range: Dict[str, Any] = {}
        if ref_min is not None:
            ref_range["low"] = {
                "value": float(ref_min),
                "unit": unit_str,
                "system": "http://unitsofmeasure.org",
                "code": unit_str
            }
        if ref_max is not None:
            ref_range["high"] = {
                "value": float(ref_max),
                "unit": unit_str,
                "system": "http://unitsofmeasure.org",
                "code": unit_str
            }
        obs["referenceRange"] = [ref_range]

    return obs


def map_report_to_fhir_bundle(report: Any, biomarkers: List[Any], patient: Any) -> Dict[str, Any]:
    """
    Assembles a complete HL7 FHIR R4 Bundle containing a DiagnosticReport and child Observation resources.
    The domain models (MedicalReport, Biomarker, User) remain untouched; mapping happens exclusively here.
    """
    patient_id = getattr(patient, "id", None) or str(patient)
    patient_name = getattr(patient, "full_name", None)

    if hasattr(report, "report_date") and report.report_date:
        report_date_str = str(report.report_date)
    else:
        report_date_str = datetime.now(timezone.utc).date().isoformat()

    observations: List[Dict[str, Any]] = []
    obs_entries: List[Dict[str, Any]] = []

    for b in biomarkers:
        b_dict = {
            "id": getattr(b, "id", "unknown"),
            "test_name": getattr(b, "test_name", ""),
            "canonical_name": getattr(b, "canonical_name", ""),
            "value_numeric": getattr(b, "value_numeric", None),
            "value_text": getattr(b, "value_text", None),
            "unit": getattr(b, "unit", None),
            "reference_min": getattr(b, "reference_min", None),
            "reference_max": getattr(b, "reference_max", None),
            "flag": getattr(b, "flag", "NORMAL"),
            "loinc_code": getattr(b, "loinc_code", None)
        }
        fhir_obs = map_biomarker_to_fhir_observation(b_dict, patient_id, report_date_str)
        observations.append(fhir_obs)
        obs_entries.append({
            "fullUrl": f"urn:uuid:{fhir_obs['id']}",
            "resource": fhir_obs
        })

    report_type = getattr(report, "report_type", "Laboratory Report") or "Laboratory Report"
    analysis_obj = getattr(report, "analysis", None)
    plain_summary = getattr(analysis_obj, "plain_summary", None) if analysis_obj else None

    diagnostic_report: Dict[str, Any] = {
        "resourceType": "DiagnosticReport",
        "id": f"report-{getattr(report, 'id', 'unknown')}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "LAB",
                        "display": "Laboratory"
                    }
                ],
                "text": "Laboratory"
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": report_type
                }
            ],
            "text": report_type
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "display": patient_name
        },
        "effectiveDateTime": report_date_str,
        "issued": datetime.now(timezone.utc).isoformat(),
        "result": [
            {
                "reference": f"Observation/{o['id']}",
                "display": o.get("code", {}).get("text")
            }
            for o in observations
        ],
        "conclusion": plain_summary or "Laboratory analysis complete."
    }

    bundle: Dict[str, Any] = {
        "resourceType": "Bundle",
        "id": f"bundle-{getattr(report, 'id', 'unknown')}",
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": [
            {
                "fullUrl": f"urn:uuid:{diagnostic_report['id']}",
                "resource": diagnostic_report
            },
            *obs_entries
        ]
    }
    return bundle
