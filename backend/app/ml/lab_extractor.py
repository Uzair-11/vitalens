import os
import re
import asyncio
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.future import select
from app.core.config import settings

# In-memory dynamic biomarker cache loaded from database
_BIOMARKER_CACHE: Optional[Dict[str, Any]] = None

def invalidate_biomarker_cache():
    """Invalidates cache when admin updates biomarker references in DB."""
    global _BIOMARKER_CACHE
    _BIOMARKER_CACHE = None

SYNONYM_MAP = {
    "glucose": ["sugar", "blood sugar", "fasting blood sugar", "fbs", "glucose fasting", "glucose, fasting", "fasting glucose", "sugar fasting"],
    "hemoglobin": ["hb", "hgb", "total hemoglobin"],
    "white blood cell": ["wbc", "tlc", "total leucocyte count", "leukocytes", "white blood cell count"],
    "platelet": ["plt", "thrombocytes", "platelet count", "platelets"],
    "hematocrit": ["pcv", "packed cell volume", "hct"],
    "cholesterol": ["total cholesterol", "serum cholesterol", "cholesterol, total", "cholesterol total"],
    "creatinine": ["serum creatinine", "sr creatinine", "creatinine"],
    "tsh": ["thyroid stimulating hormone", "thyroid stimulating hormone (tsh)"],
    "free t4": ["ft4", "free thyroxine", "t4, free", "t4 free"],
    "ferritin": ["serum ferritin"],
    "iron": ["serum iron", "fe", "total iron"],
    "alt": ["alanine aminotransferase", "alanine aminotransferase (alt)", "sgpt"],
    "ast": ["aspartate aminotransferase", "aspartate aminotransferase (ast)", "sgot"],
    "bilirubin": ["total bilirubin", "bilirubin, total", "serum bilirubin", "bilirubin total"],
    "sodium": ["serum sodium", "na", "na+", "s. sodium"],
    "potassium": ["serum potassium", "k", "k+", "s. potassium"],
    "chloride": ["serum chloride", "cl", "cl-", "s. chloride"],
    "calcium": ["serum calcium", "ca", "total calcium", "ca++", "s. calcium"],
    "egfr": ["estimated glomerular filtration rate", "estimated gfr", "gfr", "egfr (ckd-epi)"],
    "uric acid": ["serum uric acid", "uric acid, serum", "s. uric acid"],
    "crp": ["c-reactive protein", "c-reactive protein (crp)", "hs-crp"],
    "esr": ["erythrocyte sedimentation rate", "erythrocyte sedimentation rate (esr)", "sed rate"],
}

DEFAULT_BIOMARKER_DEFINITIONS = {
    "hemoglobin": {
        "canonical_name": "Hemoglobin (Hb)",
        "category": "Complete Blood Count",
        "default_unit": "g/dL",
        "default_min": 12.0,
        "default_max": 17.5,
        "critical_low": 7.0,
        "critical_high": 20.0,
        "aliases": ["hemoglobin", "hemoglobin (hb)", "hb", "hgb", "total hemoglobin"]
    },
    "white_blood_cell_count": {
        "canonical_name": "White Blood Cell Count (WBC)",
        "category": "Complete Blood Count",
        "default_unit": "cells/mcL",
        "default_min": 4000.0,
        "default_max": 11000.0,
        "critical_low": 2000.0,
        "critical_high": 30000.0,
        "aliases": ["white blood cell count", "white blood cell count (wbc)", "wbc count", "wbc-count", "wbc", "tlc", "total leucocyte count", "leukocytes", "leukocyte count", "leucocyte count", "white blood cell"]
    },
    "red_blood_cell_count": {
        "canonical_name": "Red Blood Cell Count (RBC)",
        "category": "Complete Blood Count",
        "default_unit": "million/mcL",
        "default_min": 4.2,
        "default_max": 5.9,
        "critical_low": 2.5,
        "critical_high": 7.0,
        "aliases": ["red blood cell count", "red blood cell count (rbc)", "rbc count", "rbc-count", "rbc", "erythrocyte count", "red blood cell"]
    },
    "platelets": {
        "canonical_name": "Platelet Count",
        "category": "Complete Blood Count",
        "default_unit": "cells/mcL",
        "default_min": 150000.0,
        "default_max": 450000.0,
        "critical_low": 50000.0,
        "critical_high": 1000000.0,
        "aliases": ["platelets", "platelet count", "platelet-count", "plt", "thrombocytes", "platelet"]
    },
    "hematocrit": {
        "canonical_name": "Hematocrit (PCV)",
        "category": "Complete Blood Count",
        "default_unit": "%",
        "default_min": 36.0,
        "default_max": 50.0,
        "critical_low": 20.0,
        "critical_high": 60.0,
        "aliases": ["hematocrit", "hematocrit (pcv)", "pcv", "packed cell volume", "hct"]
    },
    "fasting_blood_glucose": {
        "canonical_name": "Fasting Blood Glucose",
        "category": "Diabetes & Metabolism",
        "default_unit": "mg/dL",
        "default_min": 70.0,
        "default_max": 99.0,
        "critical_low": 50.0,
        "critical_high": 350.0,
        "aliases": ["fasting blood glucose", "glucose fasting", "glucose, fasting", "fasting glucose", "fbs", "fasting blood sugar", "sugar fasting", "blood sugar", "sugar", "glucose"]
    },
    "hba1c": {
        "canonical_name": "Glycated Hemoglobin (HbA1c)",
        "category": "Diabetes & Metabolism",
        "default_unit": "%",
        "default_min": 4.0,
        "default_max": 5.6,
        "critical_low": 3.5,
        "critical_high": 14.0,
        "aliases": ["hba1c", "glycated hemoglobin (hba1c)", "glycated hemoglobin", "hemoglobin a1c", "hemoglobin a1c (hba1c)", "a1c"]
    },
    "total_cholesterol": {
        "canonical_name": "Total Cholesterol",
        "category": "Lipid Profile",
        "default_unit": "mg/dL",
        "default_min": 125.0,
        "default_max": 200.0,
        "critical_low": 80.0,
        "critical_high": 400.0,
        "aliases": ["total cholesterol", "serum cholesterol", "cholesterol, total", "cholesterol"]
    },
    "ldl_cholesterol": {
        "canonical_name": "LDL Cholesterol",
        "category": "Lipid Profile",
        "default_unit": "mg/dL",
        "default_min": 0.0,
        "default_max": 100.0,
        "critical_low": 0.0,
        "critical_high": 250.0,
        "aliases": ["ldl cholesterol", "ldl", "ldl-c", "cholesterol, ldl"]
    },
    "hdl_cholesterol": {
        "canonical_name": "HDL Cholesterol",
        "category": "Lipid Profile",
        "default_unit": "mg/dL",
        "default_min": 40.0,
        "default_max": 60.0,
        "critical_low": 20.0,
        "critical_high": 120.0,
        "aliases": ["hdl cholesterol", "hdl", "hdl-c", "cholesterol, hdl"]
    },
    "triglycerides": {
        "canonical_name": "Triglycerides",
        "category": "Lipid Profile",
        "default_unit": "mg/dL",
        "default_min": 0.0,
        "default_max": 150.0,
        "critical_low": 0.0,
        "critical_high": 500.0,
        "aliases": ["triglycerides", "tg", "triglyceride"]
    },
    "serum_creatinine": {
        "canonical_name": "Serum Creatinine",
        "category": "Renal Panel",
        "default_unit": "mg/dL",
        "default_min": 0.6,
        "default_max": 1.2,
        "critical_low": 0.2,
        "critical_high": 5.0,
        "aliases": ["serum creatinine", "sr creatinine", "creatinine, serum", "creatinine serum", "creatinine"]
    },
    "bun": {
        "canonical_name": "Blood Urea Nitrogen (BUN)",
        "category": "Renal Panel",
        "default_unit": "mg/dL",
        "default_min": 7.0,
        "default_max": 20.0,
        "critical_low": 2.0,
        "critical_high": 80.0,
        "aliases": ["bun", "blood urea nitrogen", "blood urea nitrogen (bun)", "b.u.n.", "b.u.n", "urea nitrogen"]
    },
    "alt": {
        "canonical_name": "Alanine Aminotransferase (ALT)",
        "category": "Liver Function",
        "default_unit": "U/L",
        "default_min": 7.0,
        "default_max": 56.0,
        "critical_low": 0.0,
        "critical_high": 500.0,
        "aliases": ["alt", "alanine aminotransferase", "alanine aminotransferase (alt)", "sgpt"]
    },
    "ast": {
        "canonical_name": "Aspartate Aminotransferase (AST)",
        "category": "Liver Function",
        "default_unit": "U/L",
        "default_min": 10.0,
        "default_max": 40.0,
        "critical_low": 0.0,
        "critical_high": 500.0,
        "aliases": ["ast", "aspartate aminotransferase", "aspartate aminotransferase (ast)", "sgot"]
    },
    "tsh": {
        "canonical_name": "Thyroid Stimulating Hormone (TSH)",
        "category": "Thyroid Panel",
        "default_unit": "uIU/mL",
        "default_min": 0.4,
        "default_max": 4.0,
        "critical_low": 0.05,
        "critical_high": 20.0,
        "aliases": ["tsh", "thyroid stimulating hormone", "thyroid stimulating hormone (tsh)"]
    },
    "free_t4": {
        "canonical_name": "Free T4",
        "category": "Thyroid Panel",
        "default_unit": "ng/dL",
        "default_min": 0.8,
        "default_max": 1.8,
        "critical_low": 0.3,
        "critical_high": 3.5,
        "aliases": ["free t4", "ft4", "free thyroxine", "t4, free", "t4 free"]
    },
    "ferritin": {
        "canonical_name": "Ferritin",
        "category": "Iron Studies",
        "default_unit": "ng/mL",
        "default_min": 15.0,
        "default_max": 150.0,
        "critical_low": 5.0,
        "critical_high": 1000.0,
        "aliases": ["ferritin", "serum ferritin"]
    },
    "iron": {
        "canonical_name": "Iron",
        "category": "Iron Studies",
        "default_unit": "ug/dL",
        "default_min": 50.0,
        "default_max": 170.0,
        "critical_low": 20.0,
        "critical_high": 300.0,
        "aliases": ["iron", "serum iron", "fe", "total iron"]
    },
    "total_bilirubin": {
        "canonical_name": "Bilirubin, Total",
        "category": "Liver Function",
        "default_unit": "mg/dL",
        "default_min": 0.1,
        "default_max": 1.2,
        "critical_low": 0.0,
        "critical_high": 15.0,
        "aliases": ["bilirubin, total", "total bilirubin", "bilirubin total", "serum bilirubin", "bilirubin"]
    },
    "sodium": {
        "canonical_name": "Sodium",
        "category": "Comprehensive Metabolic Panel",
        "default_unit": "mEq/L",
        "default_min": 135.0,
        "default_max": 145.0,
        "critical_low": 120.0,
        "critical_high": 160.0,
        "aliases": ["sodium", "serum sodium", "na", "na+", "s. sodium"]
    },
    "potassium": {
        "canonical_name": "Potassium",
        "category": "Comprehensive Metabolic Panel",
        "default_unit": "mEq/L",
        "default_min": 3.5,
        "default_max": 5.1,
        "critical_low": 2.8,
        "critical_high": 6.2,
        "aliases": ["potassium", "serum potassium", "k", "k+", "s. potassium"]
    },
    "chloride": {
        "canonical_name": "Chloride",
        "category": "Comprehensive Metabolic Panel",
        "default_unit": "mEq/L",
        "default_min": 96.0,
        "default_max": 106.0,
        "critical_low": 80.0,
        "critical_high": 120.0,
        "aliases": ["chloride", "serum chloride", "cl", "cl-", "s. chloride"]
    },
    "calcium": {
        "canonical_name": "Calcium",
        "category": "Comprehensive Metabolic Panel",
        "default_unit": "mg/dL",
        "default_min": 8.5,
        "default_max": 10.2,
        "critical_low": 6.5,
        "critical_high": 13.0,
        "aliases": ["calcium", "serum calcium", "ca", "total calcium", "ca++", "s. calcium"]
    },
    "urine_protein": {
        "canonical_name": "Urine Protein",
        "category": "Urinalysis",
        "default_unit": "mg/dL",
        "default_min": 0.0,
        "default_max": 14.0,
        "critical_low": None,
        "critical_high": 300.0,
        "aliases": ["urine protein", "protein urine", "protein, urine", "urinary protein", "urine albumin"]
    },
    "urine_glucose": {
        "canonical_name": "Urine Glucose",
        "category": "Urinalysis",
        "default_unit": "mg/dL",
        "default_min": 0.0,
        "default_max": 15.0,
        "critical_low": None,
        "critical_high": 500.0,
        "aliases": ["urine glucose", "glucose urine", "glucose, urine", "urinary glucose", "urine sugar"]
    },
    "egfr": {
        "canonical_name": "Estimated Glomerular Filtration Rate (eGFR)",
        "category": "Renal Panel",
        "default_unit": "mL/min/1.73m2",
        "default_min": 90.0,
        "default_max": None,
        "critical_low": 15.0,
        "critical_high": None,
        "aliases": ["egfr", "estimated glomerular filtration rate", "estimated glomerular filtration rate (egfr)", "gfr", "estimated gfr", "egfr (ckd-epi)", "gfr estimated"]
    },
    "uric_acid": {
        "canonical_name": "Uric Acid, Serum",
        "category": "Renal Panel",
        "default_unit": "mg/dL",
        "default_min": 3.5,
        "default_max": 7.2,
        "critical_low": 1.5,
        "critical_high": 12.0,
        "aliases": ["uric acid", "serum uric acid", "uric acid, serum", "s. uric acid"]
    },
    "crp": {
        "canonical_name": "C-Reactive Protein (CRP)",
        "category": "Inflammatory Markers",
        "default_unit": "mg/L",
        "default_min": 0.0,
        "default_max": 3.0,
        "critical_low": None,
        "critical_high": 50.0,
        "aliases": ["crp", "c-reactive protein", "c-reactive protein (crp)", "hs-crp", "high sensitivity crp"]
    },
    "esr": {
        "canonical_name": "Erythrocyte Sedimentation Rate (ESR)",
        "category": "Inflammatory Markers",
        "default_unit": "mm/hr",
        "default_min": 0.0,
        "default_max": 20.0,
        "critical_low": None,
        "critical_high": 100.0,
        "aliases": ["esr", "erythrocyte sedimentation rate", "erythrocyte sedimentation rate (esr)", "sed rate", "westergren esr"]
    }
}

def _generate_aliases_for_name(test_name: str, canonical_name: str) -> List[str]:
    """Generates regex search aliases from database test names and abbreviations."""
    aliases = set()
    for name in [test_name, canonical_name]:
        if not name:
            continue
        cleaned = name.lower().strip()
        aliases.add(cleaned)
        # Extract abbreviation in parentheses e.g. "Hemoglobin (Hb)" -> "hb"
        abbrev_match = re.findall(r"\((.*?)\)", cleaned)
        for ab in abbrev_match:
            if len(ab.strip()) >= 2:
                aliases.add(ab.strip().lower())
        # Strip parentheses
        no_parens = re.sub(r"\(.*?\)", "", cleaned).strip()
        if no_parens:
            aliases.add(no_parens)
            # Invert comma formats like "cholesterol, total" -> "total cholesterol" and "glucose, fasting" -> "fasting glucose"
            if "," in no_parens:
                parts = [p.strip() for p in no_parens.split(",") if p.strip()]
                if len(parts) == 2:
                    aliases.add(f"{parts[1]} {parts[0]}")
                    aliases.add(f"{parts[0]} {parts[1]}")
            else:
                words = no_parens.split()
                if len(words) == 2:
                    aliases.add(f"{words[1]}, {words[0]}")
                    aliases.add(f"{words[0]}, {words[1]}")

    # Expand standard clinical terminology synonyms using strict word-boundary matching
    for root, syns in SYNONYM_MAP.items():
        pattern = r"\b" + re.escape(root) + r"\b"
        if any(re.search(pattern, a) for a in list(aliases)):
            for s in syns:
                aliases.add(s)

    # Sort descending by length so longer specific aliases match before generic ones
    return sorted(list(aliases), key=len, reverse=True)

def load_biomarkers_from_db_sync() -> Dict[str, Any]:
    """Queries biomarker_references table directly from the database and constructs the lookup library."""
    global _BIOMARKER_CACHE
    if _BIOMARKER_CACHE is not None:
        return _BIOMARKER_CACHE

    # Initialize with default baseline library so canonical tests are always available
    library = {k: dict(v) for k, v in DEFAULT_BIOMARKER_DEFINITIONS.items()}

    db_url = os.getenv("TEST_DATABASE_URL") or settings.DATABASE_URL
    if "asyncpg" in db_url:
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif "aiosqlite" in db_url:
        sync_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
    else:
        sync_url = db_url

    try:
        from app.models.content import BiomarkerReference
        from sqlalchemy.orm import Session
        sync_engine = create_engine(sync_url)
        with Session(sync_engine) as session:
            rows = session.query(BiomarkerReference).all()
            for r in rows:
                key = r.test_name.lower().replace(" ", "_")
                aliases = _generate_aliases_for_name(r.test_name, r.canonical_name)
                # Merge with default aliases and database-stored synonyms if existing
                existing_aliases = library.get(key, {}).get("aliases", [])
                db_synonyms = [s.lower().strip() for s in (r.synonyms or []) if isinstance(s, str)]
                combined_aliases = sorted(list(set(aliases + existing_aliases + db_synonyms)), key=len, reverse=True)

                library[key] = {
                    "id": r.id,
                    "canonical_name": r.canonical_name or r.test_name,
                    "aliases": combined_aliases,
                    "category": r.category or "General Panel",
                    "default_unit": r.default_unit or "",
                    "default_min": r.ref_min,
                    "default_max": r.ref_max,
                    "critical_low": r.critical_low,
                    "critical_high": r.critical_high,
                    "description": r.description or ""
                }
            sync_engine.dispose()
    except Exception as e:
        print(f"[!] Warning loading biomarker references from DB: {e}")

    _BIOMARKER_CACHE = library
    return _BIOMARKER_CACHE

def get_canonical_biomarkers(custom_biomarkers: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Returns database-loaded canonical biomarker definitions merged with any custom ones."""
    base_library = load_biomarkers_from_db_sync()
    merged = dict(base_library)

    if custom_biomarkers and isinstance(custom_biomarkers, list):
        for b in custom_biomarkers:
            if not isinstance(b, dict):
                continue
            key = b.get("test_name", "").lower().replace(" ", "_")
            if key:
                c_name = b.get("canonical_name", b.get("test_name"))
                aliases = _generate_aliases_for_name(b.get("test_name", ""), c_name)
                merged[key] = {
                    "canonical_name": c_name,
                    "aliases": aliases,
                    "category": b.get("category", "Custom"),
                    "default_unit": b.get("default_unit", ""),
                    "default_min": b.get("ref_min"),
                    "default_max": b.get("ref_max"),
                    "critical_low": b.get("critical_low"),
                    "critical_high": b.get("critical_high")
                }
    return merged

def evaluate_flag(val: float, ref_min: Optional[float], ref_max: Optional[float], critical_low: Optional[float] = None, critical_high: Optional[float] = None) -> str:
    """Evaluates the clinical status flag of a numerical biomarker value against reference ranges."""
    if critical_low is not None and val <= critical_low:
        return "CRITICAL_LOW"
    if critical_high is not None and val >= critical_high:
        return "CRITICAL_HIGH"
    if ref_min is not None and val < ref_min:
        return "LOW"
    if ref_max is not None and val > ref_max:
        return "HIGH"
    return "NORMAL"

def parse_range_string(range_str: str) -> tuple[Optional[float], Optional[float]]:
    """Parses a reference range text string like '12.0 - 17.5' or '< 200' into min and max floats."""
    if not range_str:
        return None, None
    
    cleaned = range_str.replace("–", "-").replace("—", "-").strip()
    cleaned = re.sub(r"(\d+),(\d{3})", r"\1\2", cleaned)
    
    # Pattern: 12.0 - 17.5
    dash_match = re.search(r"([\d\.]+)\s*-\s*([\d\.]+)", cleaned)
    if dash_match:
        try:
            return float(dash_match.group(1)), float(dash_match.group(2))
        except ValueError:
            pass
            
    # Pattern: < 200 or <= 200
    less_match = re.search(r"(?:<=|[<≤])\s*([\d\.]+)", cleaned)
    if less_match:
        try:
            return None, float(less_match.group(1))
        except ValueError:
            pass

    # Pattern: > 50 or >= 50
    greater_match = re.search(r"(?:>=|[>≥])\s*([\d\.]+)", cleaned)
    if greater_match:
        try:
            return float(greater_match.group(1)), None
        except ValueError:
            pass
            
    return None, None

NON_LAB_SECTION_PATTERNS = [
    r"^\s*(?:\d+[\.\)]\s*)?(?:subjective\s+findings|patient\s+history|history\s+of\s+present\s+illness|past\s+medical\s+history|chief\s+complaint)\b",
    r"^\s*(?:\d+[\.\)]\s*)?(?:objective\s+findings|physical\s+exam(?:ination)?|vital\s+signs)\b",
    r"^\s*(?:\d+[\.\)]\s*)?(?:assessment\s*(?:&|and)?\s*clinical\s+diagnosis|assessment\b|clinical\s+diagnosis|impression)\b",
    r"^\s*(?:\d+[\.\)]\s*)?(?:management\s*(?:&|and)?\s*treatment\s+plan|treatment\s+plan|management\s+plan|pharmacotherapy|prescriptions?|medications?|current\s+medications?)\b",
    r"^\s*(?:\d+[\.\)]\s*)?(?:clinical\s+coordination|follow-up\s+screening|follow-up\s+plan|advice|doctor\'?s\s+advice|recommendations?)\b",
    r"^\s*(?:electronic\s+signature|disclaimer|for\s+informational\s+purposes)\b"
]

LAB_SECTION_PATTERNS = [
    r"^\s*(?:\d+[\.\)]\s*)?(?:diagnostic\s+investigations|laboratory\s+results|lab\s+results|laboratory\s+investigations|investigations|test\s+results|biochemistry|hematology|serology|endocrinology|pathology|urinalysis|blood\s+work|metabolic\s+panel|lipid\s+panel|lipid\s+profile|thyroid\s+panel|thyroid\s+function|renal\s+function|renal\s+panel|liver\s+function|complete\s+blood\s+count|cbc\b|iron\s+studies|inflammatory\s+markers|diabetes\s*(?:&|and)?\s*metabolism)\b"
]

def is_medication_or_non_lab_line(line_lower: str) -> bool:
    """Detects whether a text line is a prescription, medication administration instruction, or narrative comment."""
    med_indicators = [
        r"\b(?:initiate|initiated|prescribe|prescribed|discontinue|take|taken|administer|administered)\b",
        r"\b(?:orally|daily|once daily|twice daily|bid|tid|qid|sublingually?|empty stomach|before breakfast|after meals|before food|with meals)\b",
        r"\b(?:tablets?|capsules?|syrups?|injections?|drops?|infusions?|dosage|titrations?)\b"
    ]
    return any(re.search(pattern, line_lower) for pattern in med_indicators)

def is_drug_compound(line_lower: str, match_start: int, alias: str) -> bool:
    """Checks whether the matched mineral/biomarker is part of a pharmaceutical salt (e.g. Levothyroxine Sodium)."""
    prefix = line_lower[:match_start].strip()
    if prefix:
        words = re.findall(r"[a-z0-9]+", prefix)
        if words:
            last_word = words[-1]
            if alias in ["sodium", "potassium", "calcium", "chloride", "iron", "magnesium", "zinc"]:
                drug_prefixes = {
                    "levothyroxine", "warfarin", "docusate", "valproate", "divalproex",
                    "heparin", "diclofenac", "naproxen", "ceftriaxone", "ampicillin",
                    "colistimethate", "bacteriostatic", "supplement", "supplements",
                    "ferrous", "elemental"
                }
                if last_word in drug_prefixes:
                    return True
    return False

def clean_unit_string(unit: str) -> str:
    """Sanitizes extracted unit string, preventing flags, dosing narrative, or punctuation from polluting units."""
    if not unit:
        return ""
    # Strip full flag words, not single letters like 'L' which can stand for Liter (e.g. U/L, cells/mcL)
    u = re.sub(
        r"\b(CRITICAL[\s_]HIGH|CRITICAL[\s_]LOW|HIGH|LOW|NORMAL|CRIT[\s_]HIGH|CRIT[\s_]LOW|ELEVATED|DECREASED)\b",
        "",
        unit,
        flags=re.I
    ).strip()

    # Strip narrative dosing instructions or non-unit words
    u = re.split(
        r"\b(orally|daily|morning|evening|strictly|empty|stomach|before|after|breakfast|take|taken|tablet|tablets|capsule|capsules|patient|every|hours?|weeks?|days?|months?|od|bid|tid|qid|prn)\b",
        u,
        flags=re.I
    )[0].strip()

    u = u.strip(":=- (),")

    # Match valid medical unit patterns: e.g. mg/dL, uIU/mL, %, g/dL, mEq/L, mmol/L, U/L, ng/dL, cells/mcL, x10^3/uL, mm/hr, etc.
    m = re.match(r"^([a-zA-Z0-9%µμ°\^/\*\-]+(?:\s*[a-zA-Z0-9%µμ°\^/\*\-]+){0,2})", u)
    if m:
        candidate = m.group(1).strip()
        common_words = {"in", "on", "at", "to", "for", "and", "or", "the", "is", "was", "with", "by", "from", "of"}
        if candidate.lower() not in common_words:
            u = candidate
        else:
            u = ""
    else:
        u = ""

    return u[:30]

def parse_line_biomarker(line: str, biomarker_library: Dict[str, Any], found_keys: set) -> Optional[Dict[str, Any]]:
    """
    Parses a single line of laboratory report text for biomarker names, numerical results,
    explicit or evaluated flags, reference ranges, and units.
    """
    line_clean = line.strip()
    if not line_clean:
        return None
    # Pre-normalize comma thousands separators in numbers (e.g. 8,700 -> 8700, 235,000 -> 235000, 4,000 -> 4000)
    line_clean = re.sub(r"(\d+),(\d{3})", r"\1\2", line_clean)
    line_lower = line_clean.lower()

    # Skip lines that are known commentary, section headers, or signatures
    skip_prefixes = [
        "alert:", "thyroid alert", "iron alert", "liver alert",
        "electronically signed", "report status", "patient name",
        "ordering physician", "specimen id", "date of birth",
        "test component", "laboratory comments", "this is for informational",
        "pharmacotherapy", "treatment plan", "management plan", "prescription",
        "follow-up", "clinical coordination", "subjective findings",
        "chief complaint", "history of present illness", "past medical history",
        "vital signs", "physical exam", "doctor's advice", "advice:"
    ]
    if any(line_lower.startswith(p) or f"{p}:" in line_lower for p in skip_prefixes):
        return None

    if is_medication_or_non_lab_line(line_lower):
        return None

    best_match = None
    best_key = None
    best_meta = None
    best_len = 0

    for key, meta in biomarker_library.items():
        if key in found_keys:
            continue
        for alias in meta.get("aliases", []):
            if not alias:
                continue
            # Regex match alias as a word/phrase, optionally followed by parenthetical acronym/expansion
            # e.g. "TSH (Thyroid Stimulating Hormone)" or "ALT (Alanine Aminotransferase)"
            pattern = r"(?:^|[\s,;])(" + re.escape(alias) + r"(?:\s*\([^)]*\))?)(\s*[:=-]?\s*)"
            m = re.search(pattern, line_lower)
            if m:
                if is_drug_compound(line_lower, m.start(1), alias):
                    continue
                match_text = m.group(1)
                if len(match_text) > best_len:
                    best_len = len(match_text)
                    best_match = m
                    best_key = key
                    best_meta = meta

    if not best_match or not best_meta:
        return None

    # Slice everything after the matched test name
    rest = line_clean[best_match.end():].strip()
    if not rest:
        return None

    # Strip descriptor suffixes like "count", "counts", "level", "value", etc.
    rest = re.sub(r"^(?:count|counts|level|levels|concentration|value|result|index|total)\b\s*[:=-]?\s*", "", rest, flags=re.I).strip()
    # Strip visual table leaders (dot leaders, dashes, equals, or separator characters e.g. "....... 162" or "---- 162")
    rest = re.sub(r"^(\.{2,}|[_\-=:|>~]{1,})\s*", "", rest).strip()
    if not rest:
        return None

    # Match the numerical result value or qualitative indicator (Negative, Nil, Normal, Trace, Positive, 1+, 2+, 3+, 4+)
    val = None
    qualitative_flag = None
    val_text = None

    val_match = re.match(r"^([\d,]+(?:\.\d+)?)", rest)
    if val_match:
        raw_num = val_match.group(1).replace(",", "")
        try:
            val = float(raw_num)
            val_text = raw_num
        except ValueError:
            val = None
    else:
        # Check qualitative indicators
        neg_match = re.match(r"^(negative|nil|normal|non-reactive|absent)\b", rest, flags=re.I)
        if neg_match:
            val = 0.0
            val_text = neg_match.group(1).capitalize()
            qualitative_flag = "NORMAL"
            val_match = neg_match
        else:
            trace_match = re.match(r"^(trace)\b", rest, flags=re.I)
            if trace_match:
                val = 15.0
                val_text = "Trace"
                qualitative_flag = "NORMAL"
                val_match = trace_match
            else:
                pos_match = re.match(r"^(positive|present|reactive|[1-4]\+)\b", rest, flags=re.I)
                if pos_match:
                    val = 30.0
                    val_text = pos_match.group(1).upper()
                    qualitative_flag = "HIGH"
                    val_match = pos_match

    if val is None or not val_match:
        return None

    after_val = rest[val_match.end():].strip()

    # Detect explicit flag (HIGH, LOW, CRITICAL, NORMAL)
    explicit_flag = None
    flag_match = re.search(
        r"\b(CRITICAL[\s_]HIGH|CRITICAL[\s_]LOW|HIGH|LOW|NORMAL|CRIT[\s_]HIGH|CRIT[\s_]LOW)\b",
        after_val,
        flags=re.I
    )
    if flag_match:
        explicit_flag = flag_match.group(1).upper().replace(" ", "_")

    # Detect reference range: e.g. "0.4 - 4.0", "15 - 150", "< 200", ">= 90", "> 50"
    range_match = re.search(
        r"(\(?\s*[\d\.]+\s*[-–—]\s*[\d\.]+\s*\)?)|((?:<=|[<≤])\s*[\d\.]+)|((?:>=|[>≥])\s*[\d\.]+)",
        after_val
    )

    ref_min = None
    ref_max = None
    ref_text = ""
    unit = ""

    if range_match:
        range_str = range_match.group(0).strip("()").strip()
        ref_min, ref_max = parse_range_string(range_str)
        ref_text = range_str

        before_range = after_val[:range_match.start()].strip()
        after_range = after_val[range_match.end():].strip()

        cleaned_after = clean_unit_string(after_range)
        cleaned_before = clean_unit_string(before_range)
        if cleaned_after:
            unit = cleaned_after
        elif cleaned_before:
            unit = cleaned_before
    else:
        unit = clean_unit_string(after_val)
        ref_min = best_meta.get("default_min")
        ref_max = best_meta.get("default_max")
        ref_text = f"{ref_min} - {ref_max}" if (ref_min is not None and ref_max is not None) else ""

    if not unit:
        unit = best_meta.get("default_unit", "")

    # Fall back to default library range if no range was stated in the document
    if ref_min is None or ref_max is None:
        if ref_min is None:
            ref_min = best_meta.get("default_min")
        if ref_max is None:
            ref_max = best_meta.get("default_max")
        if not ref_text and ref_min is not None and ref_max is not None:
            ref_text = f"{ref_min} - {ref_max}"
        elif not ref_text and ref_min is not None and ref_max is None:
            ref_text = f">= {ref_min}"

    # Critical thresholds: ignore if out of scale with this report's reference boundaries
    crit_low = best_meta.get("critical_low")
    crit_high = best_meta.get("critical_high")
    if ref_max is not None and crit_low is not None and crit_low > ref_max:
        crit_low = None
    if ref_min is not None and crit_high is not None and crit_high < ref_min:
        crit_high = None

    if qualitative_flag:
        eval_flag = qualitative_flag
    else:
        eval_flag = evaluate_flag(val, ref_min, ref_max, crit_low, crit_high)

    # If explicit flag was printed on the report, respect it; otherwise use evaluated
    if explicit_flag in ["HIGH", "CRITICAL_HIGH", "LOW", "CRITICAL_LOW"]:
        final_flag = explicit_flag
    elif eval_flag != "NORMAL":
        final_flag = eval_flag
    else:
        final_flag = explicit_flag or "NORMAL"

    return {
        "key": best_key,
        "test_name": best_meta["canonical_name"],
        "canonical_name": best_meta["canonical_name"],
        "value_numeric": val,
        "value_text": val_text or str(val),
        "unit": unit,
        "reference_min": ref_min,
        "reference_max": ref_max,
        "reference_text": ref_text,
        "flag": final_flag,
        "category": best_meta.get("category", "General Panel")
    }

def extract_biomarkers_from_text(
    raw_text: str,
    tables_or_custom: Optional[Any] = None,
    custom_biomarkers: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Extracts structured biomarker records from OCR raw text and extracted tables
    using DB-loaded biomarker library and canonical fallback rules.
    """
    tables = None
    if tables_or_custom:
        if isinstance(tables_or_custom, list) and len(tables_or_custom) > 0:
            if isinstance(tables_or_custom[0], dict):
                custom_biomarkers = tables_or_custom
            elif isinstance(tables_or_custom[0], list):
                tables = tables_or_custom
        elif isinstance(tables_or_custom, list):
            tables = tables_or_custom

    biomarker_library = get_canonical_biomarkers(custom_biomarkers)
    extracted = []
    found_keys = set()

    # Pass 1: Parse structured lines
    raw_lines = raw_text.splitlines()
    in_lab_section = True  # Default to extracting lab lines until a non-lab section is encountered
    parsed_line_indices = set()

    for idx, line in enumerate(raw_lines):
        line_clean = line.strip()
        if not line_clean:
            continue
        line_lower = line_clean.lower()

        if any(re.search(lp, line_lower) for lp in LAB_SECTION_PATTERNS):
            in_lab_section = True
            continue
        if any(re.search(nlp, line_lower) for nlp in NON_LAB_SECTION_PATTERNS):
            in_lab_section = False
            continue

        if not in_lab_section:
            continue

        res = parse_line_biomarker(line, biomarker_library, found_keys)
        if res:
            parsed_line_indices.add(idx)
            found_keys.add(res["key"])
            record = dict(res)
            record.pop("key", None)
            extracted.append(record)

    # Pass 2: Tabular whitespace column alignment fallback for remaining unextracted markers
    for idx, line in enumerate(raw_lines):
        if idx in parsed_line_indices:
            continue
        line_clean = line.strip()
        if not line_clean:
            continue
        line_lower = line_clean.lower()
        if is_medication_or_non_lab_line(line_lower):
            continue
        parts = [p.strip() for p in re.split(r"\s{2,}|\t+", line_clean) if p.strip()]
        if len(parts) >= 2:
            row_header = parts[0].lower()
            for key, meta in biomarker_library.items():
                if key in found_keys:
                    continue
                for alias in meta.get("aliases", []):
                    if alias and (alias == row_header or re.search(r"\b" + re.escape(alias) + r"\b", row_header)):
                        if is_drug_compound(line_lower, line_lower.find(alias), alias):
                            continue
                        numbers = []
                        for col in parts[1:]:
                            found_nums = re.findall(r"[\d\.]+", col)
                            numbers.extend(found_nums)
                        if numbers:
                            try:
                                val = float(numbers[0])
                                ref_min, ref_max = meta.get("default_min"), meta.get("default_max")
                                if len(numbers) >= 3:
                                    ref_min = float(numbers[1])
                                    ref_max = float(numbers[2])
                                ref_text = f"{ref_min} - {ref_max}"
                                
                                crit_low = meta.get("critical_low")
                                crit_high = meta.get("critical_high")
                                if ref_max is not None and crit_low is not None and crit_low > ref_max:
                                    crit_low = None
                                if ref_min is not None and crit_high is not None and crit_high < ref_min:
                                    crit_high = None
                                
                                flag = evaluate_flag(val, ref_min, ref_max, crit_low, crit_high)
                                extracted.append({
                                    "test_name": meta["canonical_name"],
                                    "canonical_name": meta["canonical_name"],
                                    "value_numeric": val,
                                    "value_text": str(val),
                                    "unit": meta.get("default_unit", ""),
                                    "reference_min": ref_min,
                                    "reference_max": ref_max,
                                    "reference_text": ref_text,
                                    "flag": flag,
                                    "category": meta["category"]
                                })
                                found_keys.add(key)
                                break
                            except (ValueError, IndexError):
                                pass

    # Pass 3: Process table structures if available (e.g. from pdfplumber)
    if tables and isinstance(tables, list):
        for table in tables:
            if not isinstance(table, list):
                continue
            for row in table:
                if not isinstance(row, list) or len(row) < 2:
                    continue
                joined_row = "  ".join(str(c) for c in row if c)
                res = parse_line_biomarker(joined_row, biomarker_library, found_keys)
                if res:
                    found_keys.add(res["key"])
                    record = dict(res)
                    record.pop("key", None)
                    extracted.append(record)

    return extracted
