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
    "glucose": ["sugar", "blood sugar", "fasting blood sugar", "fbs", "glucose fasting", "sugar fasting"],
    "hemoglobin": ["hb", "hgb", "total hemoglobin"],
    "white blood cell": ["wbc", "tlc", "total leucocyte count", "leukocytes", "white blood cell count"],
    "platelet": ["plt", "thrombocytes", "platelet count", "platelets"],
    "hematocrit": ["pcv", "packed cell volume", "hct"],
    "cholesterol": ["total cholesterol", "serum cholesterol"],
    "creatinine": ["serum creatinine", "sr creatinine"],
    "tsh": ["thyroid stimulating hormone", "thyroid stimulating hormone (tsh)"],
    "free t4": ["ft4", "free thyroxine", "t4, free", "t4 free"],
    "ferritin": ["serum ferritin"],
    "iron": ["serum iron", "fe", "total iron"],
    "alt": ["alanine aminotransferase", "alanine aminotransferase (alt)", "sgpt"],
    "ast": ["aspartate aminotransferase", "aspartate aminotransferase (ast)", "sgot"],
    "bilirubin": ["total bilirubin", "bilirubin, total", "serum bilirubin", "bilirubin total"],
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
        "aliases": ["white blood cell count", "white blood cell count (wbc)", "wbc", "tlc", "total leucocyte count", "leukocytes", "white blood cell"]
    },
    "red_blood_cell_count": {
        "canonical_name": "Red Blood Cell Count (RBC)",
        "category": "Complete Blood Count",
        "default_unit": "million/mcL",
        "default_min": 4.2,
        "default_max": 5.9,
        "critical_low": 2.5,
        "critical_high": 7.0,
        "aliases": ["red blood cell count", "red blood cell count (rbc)", "rbc", "red blood cell"]
    },
    "platelets": {
        "canonical_name": "Platelet Count",
        "category": "Complete Blood Count",
        "default_unit": "cells/mcL",
        "default_min": 150000.0,
        "default_max": 450000.0,
        "critical_low": 50000.0,
        "critical_high": 1000000.0,
        "aliases": ["platelets", "platelet count", "plt", "thrombocytes", "platelet"]
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
        "aliases": ["fasting blood glucose", "glucose fasting", "fbs", "fasting blood sugar", "sugar fasting", "blood sugar", "sugar", "glucose"]
    },
    "hba1c": {
        "canonical_name": "Glycated Hemoglobin (HbA1c)",
        "category": "Diabetes & Metabolism",
        "default_unit": "%",
        "default_min": 4.0,
        "default_max": 5.6,
        "critical_low": 3.5,
        "critical_high": 14.0,
        "aliases": ["hba1c", "glycated hemoglobin (hba1c)", "glycated hemoglobin", "a1c"]
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
        "aliases": ["serum creatinine", "sr creatinine", "creatinine"]
    },
    "bun": {
        "canonical_name": "Blood Urea Nitrogen (BUN)",
        "category": "Renal Panel",
        "default_unit": "mg/dL",
        "default_min": 7.0,
        "default_max": 20.0,
        "critical_low": 2.0,
        "critical_high": 80.0,
        "aliases": ["bun", "blood urea nitrogen", "blood urea nitrogen (bun)", "urea nitrogen"]
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

    # Expand standard clinical terminology synonyms
    for root, syns in SYNONYM_MAP.items():
        if any(root in a for a in list(aliases)):
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
                # Merge with default aliases if existing
                existing_aliases = library.get(key, {}).get("aliases", [])
                combined_aliases = sorted(list(set(aliases + existing_aliases)), key=len, reverse=True)

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
    
    # Pattern: 12.0 - 17.5
    dash_match = re.search(r"([\d\.]+)\s*-\s*([\d\.]+)", cleaned)
    if dash_match:
        try:
            return float(dash_match.group(1)), float(dash_match.group(2))
        except ValueError:
            pass
            
    # Pattern: < 200 or <= 200
    less_match = re.search(r"[<≤]\s*([\d\.]+)", cleaned)
    if less_match:
        try:
            return None, float(less_match.group(1))
        except ValueError:
            pass

    # Pattern: > 50 or >= 50
    greater_match = re.search(r"[>≥]\s*([\d\.]+)", cleaned)
    if greater_match:
        try:
            return float(greater_match.group(1)), None
        except ValueError:
            pass
            
    return None, None

def clean_unit_string(unit: str) -> str:
    """Sanitizes extracted unit string, preventing flags or punctuation from polluting units."""
    if not unit:
        return ""
    # Strip full flag words, not single letters like 'L' which can stand for Liter (e.g. U/L, cells/mcL)
    u = re.sub(
        r"\b(CRITICAL[\s_]HIGH|CRITICAL[\s_]LOW|HIGH|LOW|NORMAL|CRIT[\s_]HIGH|CRIT[\s_]LOW|ELEVATED|DECREASED)\b",
        "",
        unit,
        flags=re.I
    ).strip()
    u = u.strip(":=- (),")
    return u

def parse_line_biomarker(line: str, biomarker_library: Dict[str, Any], found_keys: set) -> Optional[Dict[str, Any]]:
    """
    Parses a single line of laboratory report text for biomarker names, numerical results,
    explicit or evaluated flags, reference ranges, and units.
    """
    line_clean = line.strip()
    if not line_clean:
        return None
    line_lower = line_clean.lower()

    # Skip lines that are known commentary, section headers, or signatures
    skip_prefixes = [
        "alert:", "thyroid alert", "iron alert", "liver alert",
        "electronically signed", "report status", "patient name",
        "ordering physician", "specimen id", "date of birth",
        "test component", "laboratory comments", "this is for informational"
    ]
    if any(line_lower.startswith(p) or f"{p}:" in line_lower for p in skip_prefixes):
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

    # Match the numerical result value at start of rest
    val_match = re.match(r"^([\d\.]+)", rest)
    if not val_match:
        return None

    try:
        val = float(val_match.group(1))
    except ValueError:
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

    # Detect reference range: e.g. "0.4 - 4.0", "15 - 150", "< 200", "> 50"
    range_match = re.search(
        r"(\(?\s*[\d\.]+\s*[-–—]\s*[\d\.]+\s*\)?)|([<≤]\s*[\d\.]+)|([>≥]\s*[\d\.]+)",
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
        ref_min = best_meta.get("default_min")
        ref_max = best_meta.get("default_max")
        if not ref_text and ref_min is not None and ref_max is not None:
            ref_text = f"{ref_min} - {ref_max}"

    # Critical thresholds: ignore if out of scale with this report's reference boundaries
    crit_low = best_meta.get("critical_low")
    crit_high = best_meta.get("critical_high")
    if ref_max is not None and crit_low is not None and crit_low > ref_max:
        crit_low = None
    if ref_min is not None and crit_high is not None and crit_high < ref_min:
        crit_high = None

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
        "value_text": str(val),
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
    for line in raw_lines:
        res = parse_line_biomarker(line, biomarker_library, found_keys)
        if res:
            found_keys.add(res["key"])
            record = dict(res)
            record.pop("key", None)
            extracted.append(record)

    # Pass 2: Tabular whitespace column alignment fallback for remaining unextracted markers
    for line in raw_lines:
        parts = [p.strip() for p in re.split(r"\s{2,}|\t+", line.strip()) if p.strip()]
        if len(parts) >= 2:
            row_header = parts[0].lower()
            for key, meta in biomarker_library.items():
                if key in found_keys:
                    continue
                for alias in meta.get("aliases", []):
                    if alias and (alias == row_header or re.search(r"\b" + re.escape(alias) + r"\b", row_header)):
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
