"""
Medical Specialty Dataset Generator for VitaLens AI Model.
Synthesizes a comprehensive clinical dataset of patient symptoms,
severity, duration, body region, and biomarker anomaly patterns mapped to 10 specialties.
Uses pure Python standard library (csv, random).
"""

import os
import csv
import random

SPECIALTIES = [
    "Cardiology",
    "Endocrinology",
    "Hematology",
    "Gastroenterology",
    "Nephrology",
    "Pulmonology",
    "Dermatology",
    "Neurology",
    "Orthopedics",
    "General Medicine"
]

CANONICAL_BIOMARKERS = [
    "glucose_fasting", "hba1c", "total_cholesterol", "ldl_cholesterol",
    "hdl_cholesterol", "triglycerides", "hemoglobin", "wbc_count",
    "platelet_count", "alt_sgpt", "ast_sgot", "total_bilirubin",
    "serum_creatinine", "bun", "egfr", "tsh", "free_t4",
    "uric_acid", "crp", "esr"
]

CLINICAL_PROFILES = {
    "Cardiology": {
        "concerns": [
            "Chest tightness during morning brisk walking",
            "Frequent heart fluttering and palpitations at rest",
            "High blood pressure and shortness of breath when climbing stairs",
            "Pressure behind the sternum and rapid heart rate",
            "Severe fatigue, dizzy spells, and swollen ankles",
            "Elevated lipid profile with recurrent chest discomfort",
            "Irregular heartbeat and breathlessness upon exertion",
            "Chest heaviness radiating towards left shoulder",
            "Elevated cholesterol and hypertension follow-up",
            "Heart pounding in chest during minimal physical activity"
        ],
        "symptoms": [
            ["chest pain", "shortness of breath", "palpitations"],
            ["heart fluttering", "dizziness", "fatigue"],
            ["high blood pressure", "chest tightness", "sweating"],
            ["palpitations", "rapid heartbeat", "breathlessness"],
            ["ankle swelling", "fatigue", "irregular pulse"],
            ["elevated cholesterol", "chest heaviness", "dyspnea"],
            ["left shoulder discomfort", "chest pressure", "fatigue"],
            ["dizziness on standing", "irregular heartbeat", "short breath"]
        ],
        "body_regions": ["Chest", "Heart", "Upper Body", "Left Arm"],
        "abnormal_markers": {
            "total_cholesterol": ("HIGH", 220, 310),
            "ldl_cholesterol": ("HIGH", 140, 210),
            "triglycerides": ("HIGH", 170, 380),
            "hdl_cholesterol": ("LOW", 25, 38),
            "crp": ("HIGH", 3.5, 12.0)
        }
    },
    "Endocrinology": {
        "concerns": [
            "Unexplained weight loss despite ravenous appetite and constant thirst",
            "High fasting blood sugar and frequent urination during night",
            "Extreme chronic fatigue, cold intolerance, and sluggishness",
            "Heat intolerance, trembling hands, and rapid weight loss",
            "Elevated HbA1c in routine screening with extreme lethargy",
            "Swelling in the anterior neck and throat fullness",
            "Hormonal imbalance with sudden weight gain and mood swings",
            "Excessive thirst, dry mouth, and blurred vision episodes",
            "Uncontrolled blood glucose levels with tingling in feet",
            "Thyroid enlargement and sudden changes in energy levels"
        ],
        "symptoms": [
            ["excessive thirst", "frequent urination", "weight loss"],
            ["high blood sugar", "fatigue", "blurred vision"],
            ["cold intolerance", "weight gain", "dry skin", "constipation"],
            ["heat intolerance", "hand tremors", "rapid pulse", "weight loss"],
            ["elevated hba1c", "frequent urination", "lethargy"],
            ["neck swelling", "difficulty swallowing", "hoarseness"],
            ["polyuria", "polydipsia", "unexplained fatigue"],
            ["tingling in toes", "high fasting sugar", "dry mouth"]
        ],
        "body_regions": ["Neck", "General / Systemic", "Endocrine", "Abdomen"],
        "abnormal_markers": {
            "glucose_fasting": ("HIGH", 130, 260),
            "hba1c": ("HIGH", 6.8, 11.5),
            "tsh": ("HIGH", 5.5, 22.0),
            "free_t4": ("LOW", 0.4, 0.75)
        }
    },
    "Hematology": {
        "concerns": [
            "Severe persistent fatigue, pale skin, and brittle nails",
            "Unexplained easy bruising on arms and legs without injury",
            "Low hemoglobin diagnosed during blood donation screening",
            "Spontaneous bleeding from gums and frequent petechial spots",
            "Chronic lightheadedness and feeling out of breath after walking 10 steps",
            "Abnormal complete blood count with severely low platelets",
            "Swollen lymph nodes in neck and recurring low-grade fevers",
            "Iron deficiency anemia causing extreme exhaustion and spoon-shaped nails",
            "Elevated white blood cell count found on routine lab check",
            "Persistent weakness, pale conjunctiva, and rapid heart rate"
        ],
        "symptoms": [
            ["severe fatigue", "pale skin", "shortness of breath", "cold hands"],
            ["easy bruising", "petechiae", "gum bleeding", "weakness"],
            ["low hemoglobin", "lightheadedness", "brittle nails", "exhaustion"],
            ["low platelets", "unprovoked bruising", "fatigue"],
            ["high wbc count", "recurrent infections", "night sweats"],
            ["spoon nails", "pale conjunctiva", "dizziness on standing"],
            ["chronic anemia", "breathlessness", "rapid heart rate"]
        ],
        "body_regions": ["Blood / Systemic", "Arms and Legs", "Neck", "General"],
        "abnormal_markers": {
            "hemoglobin": ("LOW", 6.5, 10.5),
            "platelet_count": ("LOW", 45000, 130000),
            "wbc_count": ("HIGH", 12500, 28000),
            "esr": ("HIGH", 35, 90)
        }
    },
    "Gastroenterology": {
        "concerns": [
            "Persistent burning sensation in chest and severe acid reflux after eating",
            "Severe upper abdominal pain radiating to the back",
            "Yellowish discoloration of eyes and skin with dark tea-colored urine",
            "Chronic bloating, irregular bowel movements, and abdominal cramps",
            "Elevated liver enzymes (SGPT/SGOT) found in health checkup",
            "Recurrent nausea, vomiting, and loss of appetite for three weeks",
            "Stomach ulcer pain that worsens on an empty stomach",
            "Fatty liver grade 2 with persistent right upper quadrant heaviness",
            "Chronic diarrhea alternating with constipation and gas",
            "Digestive issues, indigestion, and burning pain behind breastbone"
        ],
        "symptoms": [
            ["acid reflux", "heartburn", "stomach burning", "indigestion"],
            ["abdominal cramps", "bloating", "nausea", "loss of appetite"],
            ["jaundice", "yellow eyes", "dark urine", "pale stools"],
            ["elevated sgpt", "elevated sgot", "liver pain", "fatigue"],
            ["stomach pain", "vomiting after food", "belching"],
            ["right upper quadrant ache", "bloating", "fatty liver"],
            ["chronic diarrhea", "gas", "abdominal distension"]
        ],
        "body_regions": ["Abdomen", "Stomach", "Digestive System", "Upper Abdomen"],
        "abnormal_markers": {
            "alt_sgpt": ("HIGH", 55, 240),
            "ast_sgot": ("HIGH", 50, 195),
            "total_bilirubin": ("HIGH", 1.5, 6.2),
            "esr": ("HIGH", 25, 60)
        }
    },
    "Nephrology": {
        "concerns": [
            "Bilateral swelling in both ankles, feet, and morning puffy eyes",
            "Elevated serum creatinine and low eGFR on annual kidney panel",
            "Frothy and foamy urine with decreased daily urine output",
            "Persistent flank and lower back dull ache with high blood pressure",
            "Severe metallic taste in mouth and loss of appetite in renal patient",
            "High BUN and microalbuminuria detected on urine analysis",
            "Fluid retention, leg heaviness, and nocturia (frequent night urination)",
            "Chronic kidney disease monitoring with elevated uric acid",
            "Puffiness around eyelids in morning and swollen legs in evening",
            "Decreased urination with generalized body swelling and fatigue"
        ],
        "symptoms": [
            ["leg swelling", "ankle edema", "puffy face", "fatigue"],
            ["elevated creatinine", "low egfr", "foamy urine"],
            ["flank pain", "decreased urine", "metallic taste"],
            ["high bun", "fluid retention", "hypertension"],
            ["protein in urine", "facial puffiness", "swollen feet"],
            ["high uric acid", "kidney pain", "nighttime urination"]
        ],
        "body_regions": ["Kidneys", "Flank / Lower Back", "Legs and Feet", "Systemic"],
        "abnormal_markers": {
            "serum_creatinine": ("HIGH", 1.5, 5.8),
            "bun": ("HIGH", 24, 75),
            "egfr": ("LOW", 20, 58),
            "uric_acid": ("HIGH", 7.5, 12.0)
        }
    },
    "Pulmonology": {
        "concerns": [
            "Chronic dry cough lasting for over six weeks without relief",
            "Shortness of breath and wheezing sounds when exhaling at night",
            "Coughing up thick yellowish-green phlegm with chest tightness",
            "Severe asthma flare-up triggered by cold weather and dust",
            "Difficulty taking a deep breath and tightness in lungs",
            "Post-viral persistent cough with nocturnal choking sensations",
            "Rapid shallow breathing and breathlessness on mild exertion",
            "History of smoking with progressive exertion dyspnea and wheeze",
            "Chest congestion, rattling breathing, and dry tickling cough",
            "Bronchial spasms and whistling sound in chest while sleeping"
        ],
        "symptoms": [
            ["chronic cough", "wheezing", "shortness of breath"],
            ["cough with phlegm", "chest tightness", "breathing difficulty"],
            ["asthma flare", "nocturnal wheeze", "shallow breathing"],
            ["chest congestion", "mucus cough", "lung tightness"],
            ["post-viral cough", "breathlessness", "bronchial irritation"]
        ],
        "body_regions": ["Lungs", "Chest / Respiratory", "Throat", "Upper Respiratory"],
        "abnormal_markers": {
            "wbc_count": ("HIGH", 11500, 16000),
            "crp": ("HIGH", 4.0, 18.0),
            "esr": ("HIGH", 25, 55)
        }
    },
    "Dermatology": {
        "concerns": [
            "Itchy red raised rash spreading across arms and chest",
            "Severe facial cystic acne with painful inflamed breakouts",
            "Dry scaly silvery plaques on both elbows and knees",
            "Sudden outbreak of hives with intense burning and itching",
            "Changing shape and darkening color of a skin mole",
            "Eczema flare-up causing cracked, weeping, and bleeding skin",
            "Excessive hair shedding and thinning with itchy scalp dandruff",
            "Fungal skin infection in groin and underarms with scaly border",
            "Brittle discolored yellowish toenails with fungal thickening",
            "Persistent skin redness, flushing, and sensitive pustules"
        ],
        "symptoms": [
            ["skin rash", "intense itching", "red bumps", "flaking skin"],
            ["cystic acne", "facial breakouts", "inflamed skin"],
            ["scaly plaques", "silver scales on elbows", "dry cracked skin"],
            ["hives", "urticaria", "burning skin", "allergic wheals"],
            ["changing mole", "dark pigmentation", "irregular skin spot"],
            ["hair loss", "scalp itching", "dandruff", "thinning hair"],
            ["fungal rash", "skin peeling", "nail discoloration"]
        ],
        "body_regions": ["Skin", "Face", "Scalp", "Arms and Legs", "Body Surface"],
        "abnormal_markers": {
            "esr": ("HIGH", 20, 45),
            "crp": ("HIGH", 2.5, 9.0)
        }
    },
    "Neurology": {
        "concerns": [
            "Severe one-sided throbbing migraine with nausea and light sensitivity",
            "Frequent tension headaches across forehead and neck stiffness",
            "Tingling numbness and pins-and-needles sensation in both hands",
            "Involuntary trembling in hands and fingers at rest",
            "Episodes of room spinning, vertigo, and loss of balance",
            "Sudden shooting nerve pain down the neck into fingers",
            "Temporary memory lapses and difficulty finding words",
            "Facial twitching, eyelid spasms, and electric shock sensations",
            "Chronic daily headaches waking patient up in early morning",
            "Unsteady gait, coordination issues, and dizziness upon walking"
        ],
        "symptoms": [
            ["severe migraine", "throbbing headache", "photophobia", "nausea"],
            ["numbness in fingers", "tingling sensation", "pins and needles"],
            ["hand tremors", "muscle twitching", "shaky hands"],
            ["vertigo", "spinning dizziness", "loss of balance", "unsteady gait"],
            ["tension headache", "neck stiffness", "head pressure"],
            ["nerve pain", "shooting sensations", "facial spasm"]
        ],
        "body_regions": ["Head", "Brain / Nervous System", "Spine / Neck", "Hands and Feet"],
        "abnormal_markers": {
            "esr": ("HIGH", 15, 35)
        }
    },
    "Orthopedics": {
        "concerns": [
            "Severe sharp pain in right knee when climbing stairs and walking",
            "Chronic lower back pain with stiffness radiating into buttocks",
            "Morning stiffness in multiple finger joints lasting over an hour",
            "Frozen shoulder with restricted range of motion and night pain",
            "Swollen painful ankle after twisting during sports activity",
            "Hip joint crepitus and grinding ache during weight bearing",
            "Radiating sciatica pain shooting down the back of left leg",
            "Tendonitis in wrist with difficulty holding objects or writing",
            "Osteoarthritis flare-up in knees with joint effusion and swelling",
            "Neck muscle spasm and limited ability to turn head sideways"
        ],
        "symptoms": [
            ["knee pain", "joint stiffness", "difficulty walking", "swelling"],
            ["lower back ache", "sciatica", "lumbar spasm", "buttock pain"],
            ["morning joint stiffness", "finger pain", "rheumatic ache"],
            ["shoulder pain", "frozen shoulder", "inability to raise arm"],
            ["ankle sprain", "swollen joint", "bone tenderness", "bruising"],
            ["hip ache", "joint grinding", "crepitus", "restricted mobility"]
        ],
        "body_regions": ["Knee", "Lower Back", "Shoulder", "Joints / Skeleton", "Ankle / Foot", "Hip"],
        "abnormal_markers": {
            "uric_acid": ("HIGH", 7.8, 13.5),
            "esr": ("HIGH", 30, 75),
            "crp": ("HIGH", 4.0, 16.0)
        }
    },
    "General Medicine": {
        "concerns": [
            "Mild fever, running nose, and dry throat for two days",
            "Seasonal flu symptoms with generalized body ache and mild chill",
            "General physical weakness and exhaustion after long working hours",
            "Annual comprehensive wellness health checkup and physical exam",
            "Mild headache, nasal congestion, and sneezing episodes",
            "General fatigue, slight loss of appetite, and low energy",
            "Mild viral syndrome with low-grade fever and muscle aches",
            "Routine health evaluation for employment medical certificate",
            "Mild stomach upset after travel with slight nausea",
            "General wellness check for routine blood pressure and vitals"
        ],
        "symptoms": [
            ["mild fever", "running nose", "body ache", "throat irritation"],
            ["seasonal flu", "sneezing", "nasal congestion", "mild headache"],
            ["general weakness", "fatigue", "low energy", "malaise"],
            ["annual checkup", "routine wellness", "preventive check"],
            ["mild stomach upset", "slight nausea", "travel fatigue"]
        ],
        "body_regions": ["General / Whole Body", "Head & Throat", "Systemic"],
        "abnormal_markers": {
            "wbc_count": ("NORMAL", 6000, 8500),
            "crp": ("NORMAL", 0.5, 1.8)
        }
    }
}

DEFAULT_NORMAL_RANGES = {
    "glucose_fasting": (70.0, 99.0),
    "hba1c": (4.0, 5.6),
    "total_cholesterol": (125.0, 199.0),
    "ldl_cholesterol": (50.0, 99.0),
    "hdl_cholesterol": (40.0, 60.0),
    "triglycerides": (50.0, 149.0),
    "hemoglobin": (12.5, 16.5),
    "wbc_count": (4500.0, 10500.0),
    "platelet_count": (150000.0, 400000.0),
    "alt_sgpt": (10.0, 40.0),
    "ast_sgot": (10.0, 35.0),
    "total_bilirubin": (0.2, 1.0),
    "serum_creatinine": (0.6, 1.1),
    "bun": (7.0, 18.0),
    "egfr": (90.0, 120.0),
    "tsh": (0.4, 4.0),
    "free_t4": (0.8, 1.8),
    "uric_acid": (3.5, 6.8),
    "crp": (0.1, 2.5),
    "esr": (2.0, 15.0)
}

OVERLAPPING_SPECIALTY_PAIRS = {
    "Cardiology": ["Nephrology", "Pulmonology", "Endocrinology"],
    "Endocrinology": ["Nephrology", "Cardiology", "Gastroenterology"],
    "Hematology": ["Gastroenterology", "Nephrology", "General Medicine"],
    "Gastroenterology": ["Endocrinology", "Hematology"],
    "Nephrology": ["Endocrinology", "Cardiology"],
    "Pulmonology": ["Cardiology", "General Medicine"],
    "Dermatology": ["Orthopedics", "General Medicine"],
    "Neurology": ["Orthopedics", "Cardiology"],
    "Orthopedics": ["Neurology", "Dermatology"],
    "General Medicine": ["Pulmonology", "Hematology"]
}

COMMON_VAGUE_CONCERNS = [
    "Feeling unusually exhausted and weak lately",
    "Follow-up on abnormal blood work and routine testing",
    "General body malaise, fatigue, and low energy levels",
    "Unexplained dizziness and persistent tiredness",
    "Mild chronic aches and feeling run-down",
    "Routine comprehensive medical health review",
    "Feeling unwell with lack of stamina and focus"
]

def generate_sample(specialty: str) -> dict:
    profile = CLINICAL_PROFILES[specialty]
    
    # 15% of patients report common non-specific complaints across clinics
    if random.random() < 0.15:
        concern = random.choice(COMMON_VAGUE_CONCERNS)
    else:
        concern = random.choice(profile["concerns"])
        
    all_syms = list(random.choice(profile["symptoms"]))
    k_sym = random.randint(1, len(all_syms))
    symptom_set = random.sample(all_syms, k=k_sym)
    body_region = random.choice(profile["body_regions"])
    
    if specialty == "General Medicine":
        severity = random.randint(1, 5)
        duration = random.randint(1, 10)
    else:
        severity = random.randint(4, 10)
        duration = random.randint(3, 90)

    sample_biomarkers = {}
    sample_flags = {}
    for b_name, (norm_min, norm_max) in DEFAULT_NORMAL_RANGES.items():
        sample_biomarkers[b_name] = round(random.uniform(norm_min, norm_max), 2)
        sample_flags[b_name] = "NORMAL"

    # 1. Primary specialty-specific biomarker injection
    # Reduced from 0.88 to 0.55 (50-60% range) so signals are noisier and less deterministic
    abnormal_dict = profile["abnormal_markers"]
    for b_name, (flag_type, val_min, val_max) in abnormal_dict.items():
        if random.random() < 0.55:
            val = round(random.uniform(val_min, val_max), 2)
            sample_biomarkers[b_name] = val
            sample_flags[b_name] = flag_type

    # 2. Deliberate class overlap (18% fraction: 15-20% range)
    # Injects biomarker and symptom patterns that plausibly belong to two specialties at once
    # (e.g. elevated glucose + elevated creatinine relevant to both Endocrinology and Nephrology),
    # labeled with only one 'true' specialty, to simulate real diagnostic ambiguity.
    if random.random() < 0.18:
        candidate_overlaps = OVERLAPPING_SPECIALTY_PAIRS.get(specialty, [s for s in SPECIALTIES if s != specialty])
        sec_spec = random.choice(candidate_overlaps)
        sec_profile = CLINICAL_PROFILES[sec_spec]
        
        # Inject secondary abnormal biomarkers (plausibly belonging to two specialties at once)
        sec_abnormal = sec_profile.get("abnormal_markers", {})
        if sec_abnormal:
            chosen = random.sample(list(sec_abnormal.items()), k=min(2, len(sec_abnormal)))
            for b_name, (flag_type, val_min, val_max) in chosen:
                val = round(random.uniform(val_min, val_max), 2)
                sample_biomarkers[b_name] = val
                sample_flags[b_name] = flag_type
                    
        # Inject secondary co-occurring symptom
        sec_symptoms = random.choice(sec_profile["symptoms"])
        sec_sym = random.choice(sec_symptoms)
        if sec_sym not in symptom_set:
            symptom_set.append(sec_sym)
        if random.random() < 0.50:
            sec_concern = random.choice(sec_profile["concerns"])
            concern = f"{concern} and {sec_concern.lower()}"
        else:
            concern = f"{concern} with {sec_sym}"
        if random.random() < 0.35:
            body_region = random.choice(sec_profile["body_regions"])

    # 3. Increased random unrelated biomarker noise probability from 0.15 to 0.28 (25-30% range)
    if random.random() < 0.28:
        random_b = random.choice(CANONICAL_BIOMARKERS)
        if random_b not in abnormal_dict:
            norm_min, norm_max = DEFAULT_NORMAL_RANGES[random_b]
            if random.random() < 0.5:
                sample_biomarkers[random_b] = round(norm_max * random.uniform(1.05, 1.25), 2)
                sample_flags[random_b] = "HIGH"
            else:
                sample_biomarkers[random_b] = round(norm_min * random.uniform(0.75, 0.95), 2)
                sample_flags[random_b] = "LOW"

    symptoms_text = ", ".join(symptom_set)
    full_text = f"Primary Concern: {concern}. Symptoms: {symptoms_text}. Affected Area: {body_region}."

    row = {
        "primary_concern": concern,
        "symptoms": symptoms_text,
        "body_region": body_region,
        "full_text": full_text,
        "severity_score": severity,
        "duration_days": duration,
        "specialty": specialty,
        "specialty_id": SPECIALTIES.index(specialty)
    }

    for b_name in CANONICAL_BIOMARKERS:
        row[f"val_{b_name}"] = sample_biomarkers[b_name]
        row[f"flag_{b_name}"] = sample_flags[b_name]

    return row

def generate_dataset(num_samples_per_class: int = 350, output_path: str = None):
    random.seed(42)
    rows = []
    for spec in SPECIALTIES:
        for _ in range(num_samples_per_class):
            rows.append(generate_sample(spec))
            
    random.shuffle(rows)
    
    if output_path and rows:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fieldnames = list(rows[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
        print(f"[OK] Generated {len(rows)} samples across {len(SPECIALTIES)} specialties. Saved to: {output_path}")
        
    return rows

if __name__ == "__main__":
    out_file = r"c:\Users\Uzair\Documents\AML_REACT_PROJECT\backend\app\ml\data\medical_specialty_dataset.csv"
    generate_dataset(num_samples_per_class=350, output_path=out_file)
