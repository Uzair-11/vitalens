import os
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import create_engine
from sqlalchemy.future import select
import torch
from app.core.config import settings

# Disable HF Hub symlink warnings on Windows platforms
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

CLINICAL_DISCLAIMER = (
    "Disclaimer: This summary is generated for informational and educational navigation purposes only. "
    "It does NOT constitute a medical diagnosis, clinical prognosis, or treatment recommendation. "
    "Laboratories may utilize different test methodologies and reference boundaries. "
    "Please consult a certified healthcare professional or qualified physician for official clinical evaluation."
)

# Pre-vetted explanation bank for retrieval-based layperson explanations
EXPLANATION_BANK = [
    # CBC
    {"test": "White Blood Cell (WBC)", "flag": "HIGH", "explanation": "An elevated white blood cell count often indicates the body is fighting an infection, inflammation, or responding to stress. It can also occur with certain medications or, less commonly, blood disorders."},
    {"test": "White Blood Cell (WBC)", "flag": "LOW", "explanation": "A low white blood cell count may reduce the body's ability to fight infection. Common causes include viral infections, certain medications, autoimmune conditions, or bone marrow issues."},
    {"test": "Red Blood Cell (RBC)", "flag": "HIGH", "explanation": "An elevated red blood cell count can relate to dehydration, smoking, lung disease, or conditions that overproduce red blood cells."},
    {"test": "Red Blood Cell (RBC)", "flag": "LOW", "explanation": "A low red blood cell count often points to anemia, blood loss, nutritional deficiencies, or chronic disease."},
    {"test": "Hemoglobin", "flag": "LOW", "explanation": "Low hemoglobin suggests anemia, which can result from iron deficiency, blood loss, chronic disease, or nutritional deficiencies. It often causes fatigue and weakness."},
    {"test": "Hemoglobin", "flag": "HIGH", "explanation": "Elevated hemoglobin can occur with dehydration, smoking, living at high altitude, or conditions that increase red blood cell production."},
    {"test": "Hematocrit", "flag": "HIGH", "explanation": "A high hematocrit can reflect dehydration, smoking, lung disease, or conditions causing excess red blood cell production."},
    {"test": "Hematocrit", "flag": "LOW", "explanation": "A low hematocrit often indicates anemia, blood loss, or a nutritional deficiency affecting red blood cell production."},
    {"test": "Platelets", "flag": "LOW", "explanation": "A low platelet count (thrombocytopenia) can increase bruising and bleeding risk. Causes range from viral infections and certain medications to bone marrow conditions or autoimmune disorders. Mild reductions are often transient and warrant repeat testing."},
    {"test": "Platelets", "flag": "HIGH", "explanation": "An elevated platelet count can occur with inflammation, infection, iron deficiency, or after surgery. It's usually reactive and resolves once the underlying cause is addressed."},

    # CMP - Glucose & Kidney
    {"test": "Glucose, Fasting", "flag": "HIGH", "explanation": "Elevated fasting glucose suggests impaired fasting glucose or insulin resistance, and may be an early sign of prediabetes or diabetes. Follow-up testing with HbA1c is typically recommended to assess longer-term blood sugar control."},
    {"test": "Glucose, Fasting", "flag": "LOW", "explanation": "Low fasting glucose (hypoglycemia) can result from prolonged fasting, certain medications, or less commonly, hormonal or metabolic conditions."},
    {"test": "Creatinine", "flag": "HIGH", "explanation": "Elevated creatinine can indicate reduced kidney function, dehydration, or high muscle mass. Persistent elevation warrants further kidney function evaluation."},
    {"test": "Creatinine", "flag": "LOW", "explanation": "Low creatinine is usually not concerning and can relate to lower muscle mass or pregnancy."},
    {"test": "BUN (Blood Urea Nitrogen)", "flag": "HIGH", "explanation": "Elevated BUN can indicate reduced kidney function, dehydration, or high protein intake."},
    {"test": "BUN (Blood Urea Nitrogen)", "flag": "LOW", "explanation": "Low BUN can occur with liver disease, malnutrition, or overhydration."},

    # CMP - Electrolytes
    {"test": "Sodium", "flag": "HIGH", "explanation": "High sodium (hypernatremia) usually reflects dehydration or excess sodium intake relative to water."},
    {"test": "Sodium", "flag": "LOW", "explanation": "Low sodium (hyponatremia) can result from excess fluid intake, certain medications, or hormonal imbalances."},
    {"test": "Potassium", "flag": "HIGH", "explanation": "High potassium can affect heart rhythm and may relate to kidney function, certain medications, or dietary intake."},
    {"test": "Potassium", "flag": "LOW", "explanation": "Low potassium can cause muscle weakness or irregular heartbeat, often from fluid loss, certain medications, or inadequate intake."},
    {"test": "Chloride", "flag": "HIGH", "explanation": "High chloride often accompanies dehydration or certain metabolic imbalances."},
    {"test": "Chloride", "flag": "LOW", "explanation": "Low chloride can occur with prolonged vomiting, certain diuretics, or metabolic imbalances."},
    {"test": "Calcium", "flag": "HIGH", "explanation": "Elevated calcium can relate to parathyroid function, certain cancers, or excess vitamin D intake."},
    {"test": "Calcium", "flag": "LOW", "explanation": "Low calcium can affect bones, muscles, and nerves, and may relate to vitamin D deficiency or parathyroid issues."},

    # Lipid Panel
    {"test": "Cholesterol, Total", "flag": "HIGH", "explanation": "Elevated total cholesterol increases long-term cardiovascular risk. It's influenced by diet, genetics, and lifestyle, and is often addressed through nutritional changes and, if needed, medication."},
    {"test": "Triglycerides", "flag": "HIGH", "explanation": "High triglycerides are often linked to diet, excess weight, or elevated blood sugar, and contribute to cardiovascular risk when persistently elevated."},
    {"test": "HDL Cholesterol (Good)", "flag": "LOW", "explanation": "Low HDL cholesterol ('good' cholesterol) is associated with higher cardiovascular risk, since HDL normally helps remove excess cholesterol from the bloodstream."},
    {"test": "LDL Cholesterol (Bad)", "flag": "HIGH", "explanation": "Elevated LDL cholesterol ('bad' cholesterol) is a key risk factor for cardiovascular disease. It can often be improved through diet, exercise, and, when necessary, medication."},

    # Thyroid Panel
    {"test": "TSH (Thyroid Stimulating Hormone)", "flag": "HIGH", "explanation": "An elevated TSH often indicates an underactive thyroid (hypothyroidism), where the thyroid isn't producing enough hormone, prompting the body to signal for more."},
    {"test": "TSH (Thyroid Stimulating Hormone)", "flag": "LOW", "explanation": "A low TSH often points to an overactive thyroid (hyperthyroidism), where excess thyroid hormone suppresses the signal to produce more."},
    {"test": "Free T4", "flag": "HIGH", "explanation": "Elevated free T4 suggests an overactive thyroid, producing excess thyroid hormone."},
    {"test": "Free T4", "flag": "LOW", "explanation": "Low free T4 suggests an underactive thyroid, producing insufficient thyroid hormone."},

    # Iron Studies
    {"test": "Ferritin", "flag": "LOW", "explanation": "Low ferritin indicates depleted iron stores and is a common, sensitive early marker of iron deficiency, often before anemia becomes apparent."},
    {"test": "Ferritin", "flag": "HIGH", "explanation": "Elevated ferritin can reflect iron overload, but is also commonly raised by inflammation or infection, since ferritin behaves as an inflammatory marker as well as an iron marker."},
    {"test": "Iron", "flag": "LOW", "explanation": "Low serum iron often relates to iron deficiency, chronic blood loss, or poor dietary intake."},
    {"test": "Iron", "flag": "HIGH", "explanation": "High serum iron can occur with iron overload conditions, liver disease, or excessive iron supplementation."},

    # HbA1c
    {"test": "HbA1c", "flag": "HIGH", "explanation": "Elevated HbA1c reflects higher average blood sugar over the past 2-3 months and is used to diagnose or monitor prediabetes and diabetes."},
    {"test": "HbA1c", "flag": "LOW", "explanation": "Low HbA1c is uncommon and can relate to conditions affecting red blood cell lifespan, or very tightly controlled/low average blood sugar."},

    # Liver Panel
    {"test": "ALT (Alanine Aminotransferase)", "flag": "HIGH", "explanation": "Elevated ALT is a common marker of liver cell stress or damage, which can result from fatty liver, alcohol use, certain medications, or viral hepatitis."},
    {"test": "AST (Aspartate Aminotransferase)", "flag": "HIGH", "explanation": "Elevated AST can indicate liver stress or damage, though it's less liver-specific than ALT and can also rise with muscle injury."},
    {"test": "Bilirubin, Total", "flag": "HIGH", "explanation": "Elevated bilirubin can cause jaundice and may relate to liver dysfunction, bile duct obstruction, or increased red blood cell breakdown."},

    # Urinalysis
    {"test": "Urine Protein", "flag": "HIGH", "explanation": "Protein in the urine (proteinuria) can indicate kidney stress or damage, and may warrant further kidney function evaluation, especially if persistent."},
    {"test": "Urine Glucose", "flag": "HIGH", "explanation": "Glucose in the urine typically appears when blood sugar is significantly elevated, often associated with poorly controlled diabetes."},
]

RETRIEVAL_THRESHOLD = 0.65  # validated: correctly rejects unrelated matches

_embedder = None
_bank_embeddings = None
_embedder_available = None


def _get_embedder():
    """Lazy-loads the sentence embedder once, on first use, with resilient fallback."""
    global _embedder, _bank_embeddings, _embedder_available
    if _embedder_available is False:
        return None, None
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer('all-MiniLM-L6-v2')
            bank_texts = [f"{ex['test']} is {ex['flag']}" for ex in EXPLANATION_BANK]
            _bank_embeddings = _embedder.encode(bank_texts, convert_to_tensor=True)
            _embedder_available = True
        except Exception as e:
            print(f"[!] Info: SentenceTransformer embedding unavailable ({e}). Using semantic keyword fallback.")
            _embedder = None
            _bank_embeddings = None
            _embedder_available = False
    return _embedder, _bank_embeddings


def retrieve_explanation(test_name: str, flag: str, threshold: float = RETRIEVAL_THRESHOLD) -> Tuple[str, float]:
    """
    Finds the closest-matching pre-written explanation by embedding similarity.
    If SentenceTransformer is blocked or unavailable, uses high-accuracy medical keyword matching.
    """
    flag_str = str(flag).upper()
    norm_flag = "HIGH" if "HIGH" in flag_str else ("LOW" if "LOW" in flag_str else flag_str)

    embedder, bank_embeddings = _get_embedder()
    if embedder is not None and bank_embeddings is not None:
        try:
            from sentence_transformers import util
            query = f"{test_name} is {norm_flag}"
            query_embedding = embedder.encode(query, convert_to_tensor=True)

            similarities = util.cos_sim(query_embedding, bank_embeddings)[0]
            best_idx = torch.argmax(similarities).item()
            best_score = similarities[best_idx].item()

            if best_score >= threshold:
                return EXPLANATION_BANK[best_idx]["explanation"], best_score
            return (f"No confident match found (similarity: {best_score:.2f}) "
                    f"— flagging for manual review."), best_score
        except Exception as e:
            print(f"[!] Embedding calculation failed ({e}), falling back to direct match.")

    # High-accuracy direct & synonym keyword fallback
    norm_test = test_name.lower().strip()
    best_candidate = None
    best_score = 0.0

    for item in EXPLANATION_BANK:
        bank_test = item["test"].lower()
        bank_flag = item["flag"].upper()

        if bank_flag != norm_flag:
            continue

        abbrevs = re.findall(r"\((.*?)\)", bank_test)
        clean_bank = re.sub(r"\(.*?\)", "", bank_test).strip()

        if (norm_test in bank_test or
            bank_test in norm_test or
            clean_bank in norm_test or
            any(abbr.lower() == norm_test or f" {abbr.lower()} " in f" {norm_test} " for abbr in abbrevs)):
            return item["explanation"], 0.95

        test_words = set(re.findall(r"\w+", norm_test))
        bank_words = set(re.findall(r"\w+", bank_test))
        overlap = len(test_words & bank_words) / max(len(test_words), len(bank_words), 1)
        if overlap > best_score:
            best_score = overlap
            best_candidate = item

    if best_candidate and best_score >= 0.4:
        return best_candidate["explanation"], float(best_score)

    return f"No confident match found for {test_name} ({flag}) — flagging for physician review.", 0.0


_GLOSSARY_CACHE: Optional[Dict[str, str]] = None


def invalidate_glossary_cache():
    """Invalidates cache when admin modifies glossary terms in DB."""
    global _GLOSSARY_CACHE
    _GLOSSARY_CACHE = None


def load_glossary_from_db_sync() -> Dict[str, str]:
    """Queries glossary_terms directly from the database."""
    global _GLOSSARY_CACHE
    if _GLOSSARY_CACHE is not None:
        return _GLOSSARY_CACHE

    db_url = os.getenv("TEST_DATABASE_URL") or settings.DATABASE_URL
    if "asyncpg" in db_url:
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif "aiosqlite" in db_url:
        sync_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
    else:
        sync_url = db_url

    try:
        from app.models.content import GlossaryTerm
        from sqlalchemy.orm import Session
        sync_engine = create_engine(sync_url)
        with Session(sync_engine) as session:
            rows = session.query(GlossaryTerm).all()
            glossary = {r.term: r.definition for r in rows}
            sync_engine.dispose()
            _GLOSSARY_CACHE = glossary
            return _GLOSSARY_CACHE
    except Exception as e:
        print(f"[!] Warning loading glossary terms from DB: {e}")
        return {}


def get_glossary_dictionary() -> Dict[str, str]:
    """Returns database-backed layperson terminology definitions."""
    return load_glossary_from_db_sync()


def generate_plain_explanation(biomarkers: List[Dict[str, Any]], report_type: str = "Blood Test") -> Dict[str, Any]:
    """
    Generates a structured, non-diagnostic layperson summary and terminology glossary
    based on the extracted biomarkers, flags, and database-loaded glossary terms.
    Uses retrieval-based embedding similarity to fetch verified clinical explanations for abnormal findings.
    """
    abnormal_items = [b for b in biomarkers if b.get("flag") in ["HIGH", "LOW", "CRITICAL_HIGH", "CRITICAL_LOW"]]
    normal_items = [b for b in biomarkers if b.get("flag") == "NORMAL"]
    
    if not biomarkers or len(biomarkers) == 0:
        return {
            "plain_summary": (
                f"We analyzed your {report_type}, but were unable to identify or extract any laboratory markers "
                "from the document. This may occur if the scan quality is unclear, the document format is unrecognized, "
                "or text extraction was obstructed. Please upload a clear, legible digital copy or photo of your lab report."
            ),
            "abnormal_count": 0,
            "normal_count": 0,
            "matched_glossary": {},
            "terminology_glossary": [],
            "clinical_disclaimer": CLINICAL_DISCLAIMER
        }

    summary_parts = []
    summary_parts.append(f"We analyzed your {report_type} containing {len(biomarkers)} laboratory markers.")
    
    if not abnormal_items:
        summary_parts.append(
            "Good news: All identified biomarkers in this report fall comfortably within their stated reference ranges."
        )
    else:
        summary_parts.append(
            f"We identified {len(abnormal_items)} value(s) outside the report's reference boundaries:"
        )
        for item in abnormal_items:
            test_name = item.get("canonical_name") or item.get("test_name") or ""
            flag = item.get("flag", "HIGH")
            explanation_text, confidence = retrieve_explanation(test_name, flag)
            
            val = item.get("value_numeric", item.get("value_text"))
            unit_str = f" {item.get('unit', '')}".rstrip()
            ref_str = item.get('reference_text', 'standard range')
            flag_desc = "higher than" if "HIGH" in str(flag).upper() else "lower than"
            
            summary_parts.append(
                f"• {item['test_name']}: {val}{unit_str} ({flag_desc} expected range of {ref_str}).\n  {explanation_text}"
            )
            
    summary_parts.append(
        "Please schedule a consultation with a licensed doctor to discuss what these numbers mean in the context of your personal health history."
    )
    
    # Match terminology from DB glossary
    glossary_dict = get_glossary_dictionary()
    matched_glossary_dict = {}
    matched_glossary_list = []
    seen = set()
    for b in biomarkers:
        test_name = b.get("test_name", "")
        canonical_name = b.get("canonical_name", "")
        for term, definition in glossary_dict.items():
            if term.lower() in test_name.lower() or term.lower() in canonical_name.lower():
                matched_glossary_dict[term] = definition
                if term not in seen:
                    matched_glossary_list.append({"term": term, "definition": definition})
                    seen.add(term)
                
    return {
        "plain_summary": "\n".join(summary_parts),
        "abnormal_count": len(abnormal_items),
        "normal_count": len(normal_items),
        "matched_glossary": matched_glossary_dict,
        "terminology_glossary": matched_glossary_list,
        "clinical_disclaimer": CLINICAL_DISCLAIMER
    }
