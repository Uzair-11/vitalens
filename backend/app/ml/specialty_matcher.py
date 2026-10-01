import re
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Emergency red flag keywords requiring immediate urgent care guidance
EMERGENCY_SYMPTOMS = [
    "chest pain", "crushing pressure", "shortness of breath", "difficulty breathing",
    "sudden numbness", "facial droop", "slurred speech", "loss of consciousness",
    "coughing blood", "severe sudden headache", "anaphylaxis", "severe allergic reaction"
]

SPECIALTY_TAXONOMY = {
    "Cardiology": [
        "chest pain", "palpitations", "heart racing", "shortness of breath on exertion",
        "high cholesterol", "elevated ldl", "hypertension", "high blood pressure",
        "triglycerides", "irregular heartbeat", "dizziness on standing"
    ],
    "Endocrinology": [
        "frequent urination", "excessive thirst", "high blood sugar", "elevated glucose",
        "high hba1c", "thyroid", "elevated tsh", "low tsh", "unexplained weight loss",
        "fatigue", "hormonal imbalance", "heat intolerance", "cold intolerance"
    ],
    "Hematology": [
        "anemia", "low hemoglobin", "pale skin", "easy bruising", "excessive bleeding",
        "low platelets", "high wbc", "low wbc", "chronic fatigue", "iron deficiency"
    ],
    "Gastroenterology": [
        "stomach pain", "abdominal cramps", "acid reflux", "heartburn", "nausea",
        "elevated alt", "elevated ast", "high bilirubin", "jaundice", "bloating",
        "constipation", "chronic diarrhea", "liver enzyme elevation"
    ],
    "Nephrology": [
        "elevated creatinine", "high bun", "low egfr", "swelling in legs", "edema",
        "foamy urine", "decreased urine output", "kidney pain", "flank pain"
    ],
    "Pulmonology": [
        "chronic cough", "wheezing", "asthma", "bronchitis", "chest congestion",
        "shortness of breath", "sputum", "lung infection"
    ],
    "Dermatology": [
        "skin rash", "itching", "eczema", "acne", "mole change", "psoriasis",
        "hives", "skin lesion", "hair loss", "flaky skin"
    ],
    "Neurology": [
        "frequent headaches", "migraine", "dizziness", "tingling sensation",
        "tremor", "memory lapse", "vertigo", "nerve pain", "weakness in limbs"
    ],
    "Orthopedics": [
        "joint pain", "knee pain", "back pain", "shoulder stiffness", "swollen joint",
        "bone fracture", "muscle sprain", "arthritis", "limited mobility"
    ],
    "General Medicine": [
        "mild fever", "general weakness", "body ache", "malaise", "head cold",
        "seasonal allergies", "annual checkup", "routine wellness"
    ]
}

def check_emergency(symptoms_text: str, abnormal_biomarkers: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """Checks for emergency red flags in symptoms and critical biomarker flags."""
    text_lower = symptoms_text.lower()
    for red_flag in EMERGENCY_SYMPTOMS:
        if red_flag in text_lower:
            return True, f"You reported experiencing '{red_flag}'. Please seek immediate emergency medical care (dial 911/112 or visit nearest emergency room) rather than waiting for an outpatient appointment."
            
    critical_biomarkers = [b for b in abnormal_biomarkers if b.get("flag") == "CRITICAL"]
    if critical_biomarkers:
        names = ", ".join([b.get("test_name", "") for b in critical_biomarkers])
        return True, f"Your report shows critical biomarker values ({names}). We strongly advise immediate clinical evaluation at an urgent care or emergency facility."
        
    return False, None

def detect_emergency_red_flags(text: str) -> List[str]:
    """Returns matching emergency red flag terms found in the provided text."""
    text_lower = text.lower()
    return [flag for flag in EMERGENCY_SYMPTOMS if flag in text_lower]

def recommend_specialty(
    primary_concern: str,
    symptoms_list: List[str],
    body_region: str,
    abnormal_biomarkers: List[Dict[str, Any]],
    severity_score: int = 5,
    duration_days: int = 7
) -> Dict[str, Any]:
    """
    Executes specialty recommendation:
    1. Emergency Red-Flag Screening (Immediate Urgent Intercept).
    2. Primary Inference: Custom PyTorch Deep Neural Network (VitaLensSpecialtyNet).
    3. Fallback Inference: Rule-based heuristic + TF-IDF semantic matcher.
    """
    all_symptoms = " ".join([primary_concern] + symptoms_list + [body_region])
    
    # Step 1: Emergency Red-Flag Check
    is_emergency, emergency_msg = check_emergency(all_symptoms, abnormal_biomarkers)
    
    # Step 2: Try PyTorch Deep Learning Model Inference
    try:
        from app.ml.pytorch_specialty_predictor import predict_specialty_pytorch
        pytorch_res = predict_specialty_pytorch(
            primary_concern=primary_concern,
            symptoms_list=symptoms_list,
            body_region=body_region,
            abnormal_biomarkers=abnormal_biomarkers,
            severity_score=severity_score,
            duration_days=duration_days
        )
        if pytorch_res is not None:
            pytorch_res["is_emergency_flagged"] = is_emergency
            pytorch_res["emergency_message"] = emergency_msg
            pytorch_res["abnormal_biomarkers_considered"] = [b.get("test_name", "") for b in abnormal_biomarkers]
            pytorch_res["symptoms_considered"] = [primary_concern] + symptoms_list
            return pytorch_res
    except Exception as e:
        print(f"[!] PyTorch specialty predictor fallback: {e}")

    # Step 3: Fallback Rule-based evaluation on abnormal biomarkers
    rule_matched_specialty = None
    rule_rationale_parts = []
    
    abnormal_canonical = {b.get("canonical_name", "").lower(): b for b in abnormal_biomarkers}
    
    for name, item in abnormal_canonical.items():
        flag = item.get("flag")
        if "cholesterol" in name or "ldl" in name or "triglycerides" in name:
            rule_matched_specialty = "Cardiology"
            rule_rationale_parts.append(f"Elevated lipid marker ({item.get('test_name')}: {item.get('value_numeric')} {item.get('unit')})")
        elif "glucose" in name or "hba1c" in name or "tsh" in name or "thyroid" in name:
            rule_matched_specialty = "Endocrinology"
            rule_rationale_parts.append(f"Abnormal metabolic/hormonal marker ({item.get('test_name')}: {item.get('value_numeric')} {item.get('unit')})")
        elif "hemoglobin" in name or "platelet" in name or "wbc" in name:
            rule_matched_specialty = "Hematology"
            rule_rationale_parts.append(f"Abnormal blood count marker ({item.get('test_name')}: {item.get('value_numeric')} {item.get('unit')})")
        elif "alt" in name or "ast" in name or "bilirubin" in name:
            rule_matched_specialty = "Gastroenterology"
            rule_rationale_parts.append(f"Elevated liver enzyme ({item.get('test_name')}: {item.get('value_numeric')} {item.get('unit')})")
        elif "creatinine" in name or "bun" in name or "egfr" in name:
            rule_matched_specialty = "Nephrology"
            rule_rationale_parts.append(f"Abnormal renal marker ({item.get('test_name')}: {item.get('value_numeric')} {item.get('unit')})")

    # Step 4: Semantic similarity fallback on symptom text
    specialty_names = list(SPECIALTY_TAXONOMY.keys())
    corpus = [" ".join(SPECIALTY_TAXONOMY[spec]) for spec in specialty_names]
    corpus.append(all_symptoms)
    
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
    
    best_idx = similarities.argmax()
    best_sim_score = float(similarities[best_idx])
    semantic_specialty = specialty_names[best_idx]
    
    if rule_matched_specialty and best_sim_score > 0.15 and semantic_specialty == rule_matched_specialty:
        final_specialty = rule_matched_specialty
        confidence = min(0.95, 0.70 + best_sim_score)
        rationale = (
            f"Based on your reported symptoms and laboratory findings "
            f"({'; '.join(rule_rationale_parts)}), {final_specialty} may be a relevant "
            f"specialist to consult. This is a suggestion to help guide your next step, "
            f"not a diagnosis — please confirm with a healthcare professional."
        )
    elif rule_matched_specialty and best_sim_score <= 0.10:
        final_specialty = rule_matched_specialty
        confidence = 0.88
        rationale = (
            f"Based on your laboratory findings ({'; '.join(rule_rationale_parts)}), "
            f"{final_specialty} may be a relevant specialist to consult. "
            f"This is a suggestion to help guide your next step, not a diagnosis — "
            f"please confirm with a healthcare professional."
        )
    elif best_sim_score > 0.20:
        final_specialty = semantic_specialty
        confidence = min(0.92, 0.60 + best_sim_score)
        rationale = (
            f"Based on your reported concern ('{primary_concern}' and associated symptoms), "
            f"{final_specialty} may be a relevant specialist to consult. "
            f"This is a suggestion to help guide your next step, not a diagnosis — "
            f"please confirm with a healthcare professional."
        )
    else:
        final_specialty = "General Medicine"
        confidence = 0.80
        rationale = (
            f"Based on your symptoms and findings, a General Physician or Internal Medicine specialist "
            f"may be a helpful starting point. This is a suggestion to help guide your next step, "
            f"not a diagnosis — please confirm with a healthcare professional."
        )

    return {
        "recommended_specialty_name": final_specialty,
        "confidence_score": round(confidence, 2),
        "rationale": rationale,
        "is_emergency_flagged": is_emergency,
        "emergency_message": emergency_msg,
        "abnormal_biomarkers_considered": [b.get("test_name", "") for b in abnormal_biomarkers],
        "symptoms_considered": [primary_concern] + symptoms_list,
        "model_used": "Heuristic Rule & TF-IDF Fallback"
    }
