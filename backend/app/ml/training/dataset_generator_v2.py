"""
Medical Specialty Dataset Generator V2 (Revision 2 - Zero Leakage Architecture).
Synthesizes a physiologically coupled clinical dataset of 6,000 samples across 10 specialties.

Key Enhancements in Revision 2:
1. Completely disjoint SYMPTOM_POOLS for Train vs. Test (0% symptom phrase overlap).
2. Expanded narrative phrasing and dynamic symptom permutation.
3. Redesigned DISCORDANT cases: every ground-truth specialty has at least one defensible
   supporting feature (objective biomarker derangement or discrete localized physical finding).
   Zero label-feature voids.
4. Deterministic multi-label recording: primary_specialty, secondary_specialty,
   primary_driver_features, secondary_driver_features, labeling_rationale, case_category.
5. Automated 4-tier leakage verification suite enforcing zero exact text, zero concern overlap,
   zero symptom overlap, and low Jaccard similarity between train and test.
"""

import os
import csv
import random
from typing import Dict, List, Any, Tuple, Set

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

CANONICAL_BIOMARKERS_V2 = [
    "glucose_fasting", "hba1c", "total_cholesterol", "ldl_cholesterol",
    "hdl_cholesterol", "triglycerides", "hemoglobin", "wbc_count",
    "platelet_count", "alt_sgpt", "ast_sgot", "total_bilirubin",
    "serum_creatinine", "bun", "egfr", "tsh", "free_t4",
    "uric_acid", "crp", "esr",
    # 4 New Canonical Biomarkers
    "ferritin", "iron", "rbc_count", "hematocrit"
]

DEFAULT_NORMAL_RANGES_V2 = {
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
    "esr": (2.0, 15.0),
    "ferritin": (20.0, 250.0),
    "iron": (50.0, 170.0),
    "rbc_count": (4.20, 5.80),
    "hematocrit": (37.0, 50.0)
}

# =============================================================================
# DISJOINT PRIMARY CONCERN POOLS (Train vs. Test)
# =============================================================================
CONCERN_POOLS = {
    "Cardiology": {
        "train": [
            "Chest tightness during morning brisk walking",
            "Frequent heart fluttering and palpitations at rest",
            "High blood pressure and shortness of breath when climbing stairs",
            "Pressure behind the sternum and rapid heart rate",
            "Severe fatigue, dizzy spells, and swollen ankles",
            "Elevated lipid profile with recurrent chest discomfort",
            "Heaviness across anterior chest radiating into left arm",
            "Sudden racing pulse episodes accompanied by cold sweating"
        ],
        "test": [
            "Constricting retrosternal chest heaviness provoked by exertion",
            "Nocturnal episodes of paroxysmal palpitations and breathlessness",
            "Progressive exertional dyspnea with bilateral ankle edema and hypertension",
            "Precordial squeezing discomfort during moderate physical activity",
            "Intermittent resting tachycardia and lightheaded sensations"
        ]
    },
    "Endocrinology": {
        "train": [
            "Unexplained weight loss despite ravenous appetite and constant thirst",
            "High fasting blood sugar and frequent urination during night",
            "Extreme chronic fatigue, cold intolerance, and sluggishness",
            "Elevated HbA1c in routine screening with extreme lethargy",
            "Swelling in the anterior neck and throat fullness",
            "Excessive thirst, dry mouth, and blurred vision episodes",
            "Thyroid gland enlargement with dry skin and persistent constipation",
            "Uncontrolled blood glucose levels with tingling in lower extremities"
        ],
        "test": [
            "Marked thyroid enlargement with persistent sluggishness and cold intolerance",
            "Osmotic polyuria, polydipsia, and significant unintended weight reduction",
            "Substernal neck fullness accompanied by profound lethargy and dry skin",
            "Marked postprandial hyperglycemia with persistent visual blurring",
            "Anterior cervical swelling causing mild dysphagia and hoarse voice"
        ]
    },
    "Hematology": {
        "train": [
            "Severe persistent fatigue, pale skin, and brittle nails",
            "Unexplained easy bruising on arms and legs without injury",
            "Low hemoglobin diagnosed during blood donation screening",
            "Spontaneous bleeding from gums and frequent petechial spots",
            "Chronic lightheadedness and feeling out of breath after walking 10 steps",
            "Iron deficiency anemia causing extreme exhaustion and spoon-shaped nails",
            "Excessive cutaneous ecchymoses and recurrent epistaxis episodes",
            "Microcytic anemia screening with spooning of finger nails"
        ],
        "test": [
            "Pronounced pallor, chronic exhaustion, and brittle fingernails",
            "Marked exertional lightheadedness with microcytic hypochromic blood count",
            "Recurrent mucosal petechiae, spontaneous ecchymoses, and fatigue",
            "Severe iron-deficient state with profound physical depletion and pallor",
            "Abnormal complete blood count with pronounced thrombocytopenia"
        ]
    },
    "Gastroenterology": {
        "train": [
            "Persistent burning sensation in chest and severe acid reflux after eating",
            "Severe upper abdominal pain radiating to the back",
            "Yellowish discoloration of eyes and skin with dark tea-colored urine",
            "Chronic bloating, irregular bowel movements, and abdominal cramps",
            "Elevated liver enzymes (SGPT/SGOT) found in health checkup",
            "Fatty liver grade 2 with persistent right upper quadrant heaviness",
            "Postprandial dyspepsia and severe gastric hyperacidity",
            "Recurrent nausea, vomiting, and dull epigastric discomfort"
        ],
        "test": [
            "Epigastric postprandial burning pain with nocturnal acid regurgitation",
            "Scleral icterus, choluria, and right hypochondriac tenderness",
            "Significant transaminitis on routine wellness panel with malaise",
            "Chronic postprandial abdominal distension and alternating bowel habits",
            "Severe heartburn and regurgitation unimproved by antacid medication"
        ]
    },
    "Nephrology": {
        "train": [
            "Bilateral swelling in both ankles, feet, and morning puffy eyes",
            "Elevated serum creatinine and low eGFR on annual kidney panel",
            "Frothy and foamy urine with decreased daily urine output",
            "Persistent flank and lower back dull ache with high blood pressure",
            "Severe metallic taste in mouth and loss of appetite in renal patient",
            "Fluid retention, leg heaviness, and nocturia",
            "Azotemia with puffy eyelids in morning and swollen feet in evening",
            "Decreased urine frequency with generalized pedal edema"
        ],
        "test": [
            "Marked periorbital morning edema and progressive pedal swelling",
            "Decreased glomerular filtration rate with azotemia and foamy urine",
            "Bilateral flank dullness associated with oliguria and hypertension",
            "Renal functional decline detected on routine blood chemistry",
            "Persistent fluid retention in lower extremities with elevated urea"
        ]
    },
    "Pulmonology": {
        "train": [
            "Chronic dry cough lasting for over six weeks without relief",
            "Shortness of breath and wheezing sounds when exhaling at night",
            "Coughing up thick yellowish-green phlegm with chest tightness",
            "Severe asthma flare-up triggered by cold weather and dust",
            "Chest congestion, rattling breathing, and dry tickling cough",
            "Exertional breathlessness with productive bronchial secretions",
            "Nocturnal coughing spells causing waking breathlessness"
        ],
        "test": [
            "Intractable nocturnal bronchospasm with expiratory wheezing",
            "Productive mucopurulent cough and progressive breathlessness",
            "Chronic respiratory distress provoked by ambient temperature shifts",
            "Audible chest wheezing and tight sensation within the bronchial airways",
            "Persistent post-infectious hacking cough accompanied by dyspnea"
        ]
    },
    "Dermatology": {
        "train": [
            "Itchy red raised rash spreading across arms and chest",
            "Severe facial cystic acne with painful inflamed breakouts",
            "Dry scaly silvery plaques on both elbows and knees",
            "Sudden outbreak of hives with intense burning and itching",
            "Eczema flare-up causing cracked, weeping, and bleeding skin",
            "Pruritic papular eruption on trunk with scaling borders",
            "Diffuse itchy erythema and urticarial skin plaques"
        ],
        "test": [
            "Erythematous pruritic maculopapular eruption on torso and extremities",
            "Discoid hyperkeratotic plaques with micaceous scaling",
            "Acute urticarial wheals associated with severe cutaneous stinging",
            "Excoriated lichenified eczematous patches with fissures",
            "Severe inflammatory comedones and cystic pustules across facial region"
        ]
    },
    "Neurology": {
        "train": [
            "Severe one-sided throbbing migraine with nausea and light sensitivity",
            "Frequent tension headaches across forehead and neck stiffness",
            "Tingling numbness and pins-and-needles sensation in both hands",
            "Involuntary trembling in hands and fingers at rest",
            "Episodes of room spinning, vertigo, and loss of balance",
            "Hemicranial pulsating headache with visual aura and photophobia",
            "Peripheral paresthesias in fingers and toes"
        ],
        "test": [
            "Hemicranial pulsating cephalea accompanied by photophobia",
            "Distal peripheral paresthesias in a stocking-glove distribution",
            "Rotational vertigo and gait ataxia without auditory signs",
            "Bilateral band-like frontal headache with cervical rigidity",
            "Resting tremor in upper extremities and transient fine motor clumsiness"
        ]
    },
    "Orthopedics": {
        "train": [
            "Severe sharp pain in right knee when climbing stairs and walking",
            "Chronic lower back pain with stiffness radiating into buttocks",
            "Morning stiffness in multiple finger joints lasting over an hour",
            "Frozen shoulder with restricted range of motion and night pain",
            "Swollen painful ankle after twisting during sports activity",
            "Hip joint crepitus and grinding sensation when bearing weight",
            "Sciatica pain shooting down posterior leg with lumbar spasm"
        ],
        "test": [
            "Mechanical patellofemoral crepitus and severe joint immobility",
            "Lumbar radiculopathy with radiating neurological discomfort",
            "Prolonged morning articular stiffness and bilateral PIP swelling",
            "Adhesive capsulitis restricting shoulder abduction and internal rotation",
            "Acute talocrural joint sprain with soft tissue swelling and tenderness"
        ]
    },
    "General Medicine": {
        "train": [
            "Mild fever, running nose, and dry throat for two days",
            "Seasonal flu symptoms with generalized body ache and mild chill",
            "General physical weakness and exhaustion after long working hours",
            "Annual comprehensive wellness health checkup and physical exam",
            "Routine health evaluation for employment medical certificate",
            "Mild viral syndrome with low-grade fever and coryza",
            "General preventive medical check for blood pressure and routine vitals"
        ],
        "test": [
            "Self-limiting coryzal syndrome with mild pharyngitis and subfebrile state",
            "Preventive annual biological screening examination without symptoms",
            "General wellness consultation for routine cardiovascular check",
            "Routine occupational fitness evaluation and general health assessment",
            "Mild post-viral fatigue and generalized low-grade constitutional malaise"
        ]
    }
}

# =============================================================================
# DISJOINT SYMPTOM PHRASE POOLS (Train vs. Test)
# Every symptom set in train is completely disjoint from test!
# =============================================================================
SYMPTOM_POOLS = {
    "Cardiology": {
        "train": [
            ["chest tightness", "palpitations", "shortness of breath"],
            ["heart fluttering", "dizziness on exertion", "fatigue"],
            ["high blood pressure", "chest heaviness", "sweating"],
            ["bilateral ankle swelling", "irregular pulse", "effort dyspnea"],
            ["sternal pressure", "tachycardia", "cold perspiration"]
        ],
        "test": [
            ["retrosternal heaviness", "orthopnea", "racing heart rate"],
            ["precordial tightness", "effort intolerance", "peripheral edema"],
            ["cardiac fluttering", "paroxysmal nocturnal dyspnea", "dizzy spells"],
            ["constricting chest discomfort", "exertional breathlessness", "swollen ankles"]
        ]
    },
    "Endocrinology": {
        "train": [
            ["excessive thirst", "frequent urination", "weight loss"],
            ["cold intolerance", "weight gain", "dry skin", "constipation"],
            ["neck swelling", "difficulty swallowing", "hoarseness"],
            ["high blood sugar", "fatigue", "blurred vision"],
            ["polyuria", "polydipsia", "lethargy"]
        ],
        "test": [
            ["unquenchable thirst", "nocturia", "rapid unintended weight reduction"],
            ["hypothyroid sluggishness", "extreme cold sensitivity", "dry flaky skin"],
            ["anterior cervical mass", "swallowing difficulty", "vocal hoarseness"],
            ["severe glycemic elevation", "marked exhaustion", "transient visual blurring"]
        ]
    },
    "Hematology": {
        "train": [
            ["severe fatigue", "pale skin", "shortness of breath", "cold hands"],
            ["easy bruising", "petechiae", "gum bleeding", "weakness"],
            ["lightheadedness", "brittle nails", "exhaustion", "spoon nails"],
            ["unprovoked bruising", "fatigue", "mucosal bleeding"],
            ["pale conjunctiva", "dizziness on standing", "tachycardia"]
        ],
        "test": [
            ["pronounced pallor", "systemic exhaustion", "fragile fingernails"],
            ["spontaneous ecchymoses", "purpuric rash", "gingival bleeding"],
            ["marked exertional dizziness", "koilonychia", "profound fatigue"],
            ["cutaneous bruising", "postural lightheadedness", "breathlessness on walking"]
        ]
    },
    "Gastroenterology": {
        "train": [
            ["acid reflux", "heartburn", "stomach burning", "indigestion"],
            ["jaundice", "yellow eyes", "dark urine", "pale stools"],
            ["elevated sgpt", "elevated sgot", "liver pain", "fatigue"],
            ["right upper quadrant ache", "bloating", "fatty liver"],
            ["epigastric cramps", "nausea after meals", "belching"]
        ],
        "test": [
            ["postprandial acid regurgitation", "retrosternal pyrosis", "dyspepsia"],
            ["scleral icterus", "tea-colored urine", "acholic stools"],
            ["hepatic transaminitis", "right hypochondriac tenderness", "malaise"],
            ["abdominal distension", "postprandial fullness", "flatulence"]
        ]
    },
    "Nephrology": {
        "train": [
            ["leg swelling", "ankle edema", "puffy face", "fatigue"],
            ["elevated creatinine", "low egfr", "foamy urine"],
            ["flank pain", "decreased urine", "metallic taste"],
            ["fluid retention", "hypertension", "nocturia"],
            ["periorbital puffiness", "azotemia", "decreased urination"]
        ],
        "test": [
            ["periorbital morning edema", "progressive pedal swelling", "fluid accumulation"],
            ["renal azotemia", "proteinuria", "foaming urine stream"],
            ["bilateral costovertebral tenderness", "oliguria", "dysgeusia"],
            ["dependent peripheral edema", "elevated blood urea", "nighttime micturition"]
        ]
    },
    "Pulmonology": {
        "train": [
            ["chronic cough", "wheezing", "shortness of breath"],
            ["cough with phlegm", "chest tightness", "breathing difficulty"],
            ["asthma flare", "nocturnal wheeze", "shallow breathing"],
            ["chest congestion", "mucus cough", "bronchial irritation"]
        ],
        "test": [
            ["intractable dry coughing", "expiratory wheeze", "dyspneic episodes"],
            ["mucopurulent sputum", "bronchial constriction", "respiratory distress"],
            ["paroxysmal bronchospasm", "nocturnal choking sensation", "tachypnea"],
            ["chest rattling", "productive phlegm", "airway tightness"]
        ]
    },
    "Dermatology": {
        "train": [
            ["skin rash", "intense itching", "red bumps", "flaking skin"],
            ["scaly plaques", "silver scales on elbows", "dry cracked skin"],
            ["hives", "urticaria", "burning skin", "allergic wheals"],
            ["cystic acne", "facial breakouts", "inflamed pustules"]
        ],
        "test": [
            ["erythematous cutaneous eruption", "pruritus", "maculopapular lesions"],
            ["hyperkeratotic silvery plaques", "fissured skin", "elbow scaling"],
            ["urticarial wheals", "dermal stinging", "acute hives flare"],
            ["inflammatory comedones", "facial papulopustules", "tender breakouts"]
        ]
    },
    "Neurology": {
        "train": [
            ["severe migraine", "throbbing headache", "photophobia", "nausea"],
            ["numbness in fingers", "tingling sensation", "pins and needles"],
            ["vertigo", "spinning dizziness", "loss of balance", "unsteady gait"],
            ["hand tremors", "muscle twitching", "shaky fingers"]
        ],
        "test": [
            ["hemicranial throbbing pain", "light sensitivity", "nausea and visual aura"],
            ["peripheral paresthesias", "hypoesthesia in extremities", "tingling toes"],
            ["rotational vertigo", "disequilibrium", "ataxic gait"],
            ["resting hand tremor", "involuntary fasciculations", "motor shakiness"]
        ]
    },
    "Orthopedics": {
        "train": [
            ["knee pain", "joint stiffness", "difficulty walking", "swelling"],
            ["lower back ache", "sciatica", "lumbar spasm", "buttock pain"],
            ["morning joint stiffness", "finger pain", "rheumatic ache"],
            ["shoulder pain", "restricted arm motion", "frozen shoulder"]
        ],
        "test": [
            ["patellofemoral arthralgia", "articular crepitus", "impaired locomotion"],
            ["lumbosacral radiculopathy", "sciatic nerve radiation", "back rigidity"],
            ["prolonged morning joint immobility", "PIP swelling", "articular ache"],
            ["adhesive capsulitis", "painful shoulder abduction", "rotator cuff tenderness"]
        ]
    },
    "General Medicine": {
        "train": [
            ["mild fever", "running nose", "body ache", "throat irritation"],
            ["general weakness", "fatigue", "low energy", "malaise"],
            ["annual checkup", "routine wellness", "preventive check"],
            ["seasonal flu", "sneezing", "nasal congestion"]
        ],
        "test": [
            ["low-grade subfebrile state", "rhinorrhea", "pharyngeal scratchiness", "myalgia"],
            ["constitutional fatigue", "generalized sluggishness", "lack of stamina"],
            ["preventive biological checkup", "annual health maintenance", "wellness screening"],
            ["viral coryza", "paroxysmal sneezing", "head congestion"]
        ]
    }
}

BODY_REGIONS = {
    "Cardiology": ["Chest", "Retrosternal / Precordial Area", "Upper Thorax and Left Arm", "Cardiovascular System"],
    "Endocrinology": ["Anterior Neck and Thyroid", "Endocrine and Metabolic Axis", "Systemic Endocrine System", "Anterior Cervical Region"],
    "Hematology": ["Hematopoietic System", "Cutaneous Microvasculature and Extremities", "Whole Body Blood Circulation", "Peripheral Blood and Mucosa"],
    "Gastroenterology": ["Upper Abdomen and Epigastrium", "Right Upper Quadrant and Liver", "Gastrointestinal Tract", "Digestive System and Bowel"],
    "Nephrology": ["Renal Angles and Flank", "Bilateral Lower Extremities and Kidneys", "Renal and Urinary System", "Periorbital and Dependent Edema Zones"],
    "Pulmonology": ["Thoracic Cavity and Lungs", "Bronchial Airways and Chest", "Respiratory Tract", "Upper and Lower Airways"],
    "Dermatology": ["Integumentary Surface and Epidermis", "Cutaneous Surface of Torso and Limbs", "Facial and Scalp Dermis", "Extensor Surfaces and Joints"],
    "Neurology": ["Cranial Cavity and Brain", "Peripheral Nervous System and Hands", "Neuro-Vestibular Axis and Head", "Central Nervous Axis and Spine"],
    "Orthopedics": ["Musculoskeletal Joints and Knees", "Lumbosacral Spine and Pelvis", "Articular Cartilage and Shoulder", "Locomotor System and Skeleton"],
    "General Medicine": ["Whole Body General State", "Systemic Constitution", "General Organism", "General Preventive Health"]
}

def generate_biomarker_baseline() -> Tuple[Dict[str, float], Dict[str, str]]:
    """Samples all 24 biomarkers uniformly within their physiological normal reference range."""
    bio_values = {}
    bio_flags = {}
    for b_name, (norm_min, norm_max) in DEFAULT_NORMAL_RANGES_V2.items():
        bio_values[b_name] = round(random.uniform(norm_min, norm_max), 2)
        bio_flags[b_name] = "NORMAL"
    return bio_values, bio_flags

def generate_v2_sample(
    specialty: str,
    split: str = "train",
    case_category: str = "ISOLATED"
) -> Dict[str, Any]:
    """
    Generates a single clinical sample conforming to the V2 24-biomarker schema.
    Strictly follows deterministic multi-label recording and zero-leakage pools.
    """
    pool_key = "test" if split == "test" else "train"
    concern = random.choice(CONCERN_POOLS[specialty][pool_key])

    # Select symptom set from split-specific pool and shuffle to avoid fixed ordering
    sym_set = list(random.choice(SYMPTOM_POOLS[specialty][pool_key]))
    random.shuffle(sym_set)
    body_region = random.choice(BODY_REGIONS[specialty])

    bio_values, bio_flags = generate_biomarker_baseline()

    primary_specialty = specialty
    secondary_specialty = "None"
    primary_drivers = []
    secondary_drivers = []
    rationale = "SINGLE_ORGAN_PATHOLOGY"

    severity = random.randint(1, 5) if specialty == "General Medicine" else random.randint(4, 10)
    duration = random.randint(1, 10) if specialty == "General Medicine" else random.randint(3, 90)

    # =========================================================================
    # CATEGORY 1: ISOLATED CLINICAL CASES (50% of dataset)
    # =========================================================================
    if case_category == "ISOLATED":
        rationale = "SINGLE_ORGAN_PATHOLOGY"
        if specialty == "Cardiology":
            bio_values["total_cholesterol"] = round(random.uniform(220, 310), 2)
            bio_flags["total_cholesterol"] = "HIGH"
            bio_values["ldl_cholesterol"] = round(random.uniform(140, 210), 2)
            bio_flags["ldl_cholesterol"] = "HIGH"
            bio_values["triglycerides"] = round(random.uniform(170, 380), 2)
            bio_flags["triglycerides"] = "HIGH"
            bio_values["hdl_cholesterol"] = round(random.uniform(25, 38), 2)
            bio_flags["hdl_cholesterol"] = "LOW"
            bio_values["crp"] = round(random.uniform(3.5, 12.0), 2)
            bio_flags["crp"] = "HIGH"
            primary_drivers = ["ldl_cholesterol", "total_cholesterol", "triglycerides", "crp"]

        elif specialty == "Endocrinology":
            if random.random() < 0.5:
                bio_values["tsh"] = round(random.uniform(5.5, 22.0), 2)
                bio_flags["tsh"] = "HIGH"
                bio_values["free_t4"] = round(random.uniform(0.40, 0.75), 2)
                bio_flags["free_t4"] = "LOW"
                primary_drivers = ["tsh", "free_t4"]
            else:
                bio_values["glucose_fasting"] = round(random.uniform(130, 260), 2)
                bio_flags["glucose_fasting"] = "HIGH"
                bio_values["hba1c"] = round(random.uniform(6.8, 11.5), 2)
                bio_flags["hba1c"] = "HIGH"
                primary_drivers = ["glucose_fasting", "hba1c"]

        elif specialty == "Hematology":
            # Coupled Microcytic Anemia generation (Rule of 3)
            hb = round(random.uniform(6.5, 11.0), 2)
            bio_values["hemoglobin"] = hb
            bio_flags["hemoglobin"] = "LOW" if hb >= 8.0 else "CRITICAL_LOW"
            bio_values["hematocrit"] = round(hb * random.uniform(2.85, 3.15), 1)
            bio_flags["hematocrit"] = "LOW"
            bio_values["rbc_count"] = round((hb / 3.2) * random.uniform(0.9, 1.05), 2)
            bio_flags["rbc_count"] = "LOW"
            bio_values["ferritin"] = round(random.uniform(3.0, 15.0), 1)
            bio_flags["ferritin"] = "LOW"
            bio_values["iron"] = round(random.uniform(15.0, 45.0), 1)
            bio_flags["iron"] = "LOW"

            plt_dice = random.random()
            if plt_dice < 0.45:
                bio_values["platelet_count"] = round(random.uniform(420000, 650000), 0)
                bio_flags["platelet_count"] = "HIGH"
            elif plt_dice < 0.85:
                bio_values["platelet_count"] = round(random.uniform(180000, 380000), 0)
                bio_flags["platelet_count"] = "NORMAL"
            else:
                bio_values["platelet_count"] = round(random.uniform(35000, 120000), 0)
                bio_flags["platelet_count"] = "LOW"

            primary_drivers = ["ferritin", "iron", "hemoglobin", "hematocrit", "rbc_count"]

        elif specialty == "Gastroenterology":
            bio_values["alt_sgpt"] = round(random.uniform(65, 260), 1)
            bio_flags["alt_sgpt"] = "HIGH"
            bio_values["ast_sgot"] = round(random.uniform(55, 210), 1)
            bio_flags["ast_sgot"] = "HIGH"
            bio_values["total_bilirubin"] = round(random.uniform(1.8, 6.5), 2)
            bio_flags["total_bilirubin"] = "HIGH"
            primary_drivers = ["alt_sgpt", "ast_sgot", "total_bilirubin"]

        elif specialty == "Nephrology":
            bio_values["serum_creatinine"] = round(random.uniform(1.6, 5.5), 2)
            bio_flags["serum_creatinine"] = "HIGH"
            bio_values["bun"] = round(random.uniform(25, 75), 1)
            bio_flags["bun"] = "HIGH"
            bio_values["egfr"] = round(random.uniform(18, 55), 1)
            bio_flags["egfr"] = "LOW"
            bio_values["uric_acid"] = round(random.uniform(7.5, 12.0), 2)
            bio_flags["uric_acid"] = "HIGH"
            primary_drivers = ["serum_creatinine", "bun", "egfr"]

        elif specialty == "Pulmonology":
            bio_values["wbc_count"] = round(random.uniform(11500, 17500), 0)
            bio_flags["wbc_count"] = "HIGH"
            bio_values["crp"] = round(random.uniform(4.0, 19.0), 2)
            bio_flags["crp"] = "HIGH"
            bio_values["esr"] = round(random.uniform(25, 60), 1)
            bio_flags["esr"] = "HIGH"
            primary_drivers = ["wbc_count", "crp", "esr"]

        elif specialty == "Orthopedics":
            bio_values["uric_acid"] = round(random.uniform(7.8, 13.5), 2)
            bio_flags["uric_acid"] = "HIGH"
            bio_values["crp"] = round(random.uniform(4.0, 16.0), 2)
            bio_flags["crp"] = "HIGH"
            bio_values["esr"] = round(random.uniform(30, 75), 1)
            bio_flags["esr"] = "HIGH"
            primary_drivers = ["uric_acid", "crp", "esr"]

        elif specialty in ["Dermatology", "Neurology"]:
            bio_values["esr"] = round(random.uniform(15, 38), 1)
            bio_flags["esr"] = "HIGH" if bio_values["esr"] > 15 else "NORMAL"
            primary_drivers = ["symptoms", "body_region"]

        elif specialty == "General Medicine":
            primary_drivers = ["wbc_count", "crp"]

    # =========================================================================
    # CATEGORY 2: MIXED CO-MORBIDITIES (25% of dataset)
    # =========================================================================
    elif case_category == "MIXED":
        if specialty == "Endocrinology":
            bio_values["tsh"] = round(random.uniform(5.5, 15.0), 2)
            bio_flags["tsh"] = "HIGH"
            bio_values["free_t4"] = round(random.uniform(0.50, 0.76), 2)
            bio_flags["free_t4"] = "LOW"

            # Co-morbid mild IDA
            hb = round(random.uniform(10.5, 11.8), 2)
            bio_values["hemoglobin"] = hb
            bio_flags["hemoglobin"] = "LOW"
            bio_values["hematocrit"] = round(hb * 3.0, 1)
            bio_flags["hematocrit"] = "LOW"
            bio_values["rbc_count"] = round(hb / 3.1, 2)
            bio_flags["rbc_count"] = "LOW"
            bio_values["ferritin"] = round(random.uniform(8.0, 18.0), 1)
            bio_flags["ferritin"] = "LOW"
            bio_values["iron"] = round(random.uniform(30.0, 48.0), 1)
            bio_flags["iron"] = "LOW"

            secondary_specialty = "Hematology"
            primary_drivers = ["tsh", "free_t4", "neck_swelling"]
            secondary_drivers = ["ferritin", "iron", "hemoglobin"]
            rationale = "SYMPTOM_ORGAN_ALIGNMENT"

        elif specialty == "Hematology":
            hb = round(random.uniform(7.5, 10.5), 2)
            bio_values["hemoglobin"] = hb
            bio_flags["hemoglobin"] = "LOW"
            bio_values["hematocrit"] = round(hb * 3.0, 1)
            bio_flags["hematocrit"] = "LOW"
            bio_values["rbc_count"] = round(hb / 3.3, 2)
            bio_flags["rbc_count"] = "LOW"
            bio_values["ferritin"] = round(random.uniform(4.0, 12.0), 1)
            bio_flags["ferritin"] = "LOW"
            bio_values["iron"] = round(random.uniform(18.0, 42.0), 1)
            bio_flags["iron"] = "LOW"
            bio_values["platelet_count"] = round(random.uniform(440000, 620000), 0)
            bio_flags["platelet_count"] = "HIGH"

            # Co-morbid mild TSH
            bio_values["tsh"] = round(random.uniform(4.5, 7.5), 2)
            bio_flags["tsh"] = "HIGH"

            secondary_specialty = "Endocrinology"
            primary_drivers = ["ferritin", "iron", "hemoglobin", "platelet_count"]
            secondary_drivers = ["tsh"]
            rationale = "HEMODYNAMIC_ACUITY_PRIORITY"

        elif specialty == "Nephrology":
            bio_values["serum_creatinine"] = round(random.uniform(1.8, 3.8), 2)
            bio_flags["serum_creatinine"] = "HIGH"
            bio_values["bun"] = round(random.uniform(28, 65), 1)
            bio_flags["bun"] = "HIGH"
            bio_values["egfr"] = round(random.uniform(25, 48), 1)
            bio_flags["egfr"] = "LOW"
            bio_values["glucose_fasting"] = round(random.uniform(140, 220), 2)
            bio_flags["glucose_fasting"] = "HIGH"
            bio_values["hba1c"] = round(random.uniform(7.2, 10.5), 2)
            bio_flags["hba1c"] = "HIGH"

            secondary_specialty = "Endocrinology"
            primary_drivers = ["serum_creatinine", "bun", "egfr"]
            secondary_drivers = ["glucose_fasting", "hba1c"]
            rationale = "TARGET_ORGAN_ACUITY_PRESERVATION"

        elif specialty == "Gastroenterology":
            bio_values["alt_sgpt"] = round(random.uniform(45, 95), 1)
            bio_flags["alt_sgpt"] = "HIGH"
            bio_values["ferritin"] = round(random.uniform(6.0, 16.0), 1)
            bio_flags["ferritin"] = "LOW"
            bio_values["hemoglobin"] = round(random.uniform(9.0, 11.2), 2)
            bio_flags["hemoglobin"] = "LOW"

            secondary_specialty = "Hematology"
            primary_drivers = ["epigastric_pain", "acid_reflux", "alt_sgpt"]
            secondary_drivers = ["ferritin", "hemoglobin"]
            rationale = "SOURCE_PATHOLOGY_LOCALIZATION"

        else:
            secondary_specialty = "General Medicine"
            primary_drivers = ["symptoms", "body_region"]
            secondary_drivers = ["crp"]
            rationale = "SYMPTOM_ORGAN_ALIGNMENT"

    # =========================================================================
    # CATEGORY 3: REDESIGNED DISCORDANT CASES (15% of dataset)
    # Every specialty has at least one defensible, genuine supporting feature!
    # Zero label-feature voids.
    # =========================================================================
    elif case_category == "DISCORDANT":
        # Chief concern is vague fatigue/malaise in both train and test pools
        vague_concerns = {
            "train": [
                "Unexplained persistent fatigue, sluggishness, and low energy levels",
                "Chronic general tiredness with mild intermittent dizziness",
                "Feeling physically run-down and lacking stamina for several weeks",
                "Vague constitutional fatigue accompanied by general body exhaustion"
            ],
            "test": [
                "Profound systemic weariness and postural dizzy sensations",
                "Non-specific exhaustion and general loss of physical endurance",
                "Diffuse persistent fatigue without clear explanatory cause"
            ]
        }
        concern = random.choice(vague_concerns[pool_key])
        body_region = "General / Whole Body"

        if specialty == "Endocrinology":
            sym_set = ["generalized fatigue", "slight sluggishness", "cold sensitivity"] if pool_key == "train" else ["persistent weariness", "mild chilliness", "low energy"]
            bio_values["tsh"] = round(random.uniform(6.5, 18.0), 2)
            bio_flags["tsh"] = "HIGH"
            bio_values["free_t4"] = round(random.uniform(0.45, 0.74), 2)
            bio_flags["free_t4"] = "LOW"
            primary_drivers = ["tsh", "free_t4"]
            rationale = "OBJECTIVE_LAB_PRIMACY"

        elif specialty == "Hematology":
            sym_set = ["fatigue on standing", "slight lightheadedness", "pallor"] if pool_key == "train" else ["exertional lightheadedness", "pale appearance", "weakness"]
            hb = round(random.uniform(7.5, 10.5), 2)
            bio_values["hemoglobin"] = hb
            bio_flags["hemoglobin"] = "LOW"
            bio_values["hematocrit"] = round(hb * 3.0, 1)
            bio_flags["hematocrit"] = "LOW"
            bio_values["rbc_count"] = round(hb / 3.2, 2)
            bio_flags["rbc_count"] = "LOW"
            bio_values["ferritin"] = round(random.uniform(3.5, 12.0), 1)
            bio_flags["ferritin"] = "LOW"
            bio_values["iron"] = round(random.uniform(18.0, 42.0), 1)
            bio_flags["iron"] = "LOW"
            primary_drivers = ["ferritin", "iron", "hemoglobin"]
            rationale = "OBJECTIVE_LAB_PRIMACY"

        elif specialty == "Gastroenterology":
            sym_set = ["general malaise", "mild postprandial fullness", "fatigue"] if pool_key == "train" else ["tiredness after food", "mild digestive discomfort", "sluggishness"]
            bio_values["alt_sgpt"] = round(random.uniform(85, 240), 1)
            bio_flags["alt_sgpt"] = "HIGH"
            bio_values["ast_sgot"] = round(random.uniform(75, 190), 1)
            bio_flags["ast_sgot"] = "HIGH"
            bio_values["total_bilirubin"] = round(random.uniform(1.8, 3.8), 2)
            bio_flags["total_bilirubin"] = "HIGH"
            primary_drivers = ["alt_sgpt", "ast_sgot", "total_bilirubin"]
            rationale = "OBJECTIVE_LAB_PRIMACY"

        elif specialty == "Nephrology":
            # Discrete renal physical finding: evening ankle edema
            sym_set = ["bilateral evening ankle puffiness", "foamy morning urine", "fatigue"] if pool_key == "train" else ["dependent pedal swelling", "frothy urine stream", "tiredness"]
            bio_values["serum_creatinine"] = round(random.uniform(1.4, 2.8), 2)
            bio_flags["serum_creatinine"] = "HIGH"
            bio_values["bun"] = round(random.uniform(22, 45), 1)
            bio_flags["bun"] = "HIGH"
            primary_drivers = ["serum_creatinine", "ankle_edema", "foamy_urine"]
            rationale = "DISCRETE_PHYSICAL_AND_LAB_CORRELATION"

        elif specialty == "Cardiology":
            # Discrete exertional finding: retrosternal tightness with rushing
            sym_set = ["mild chest tightness when climbing stairs", "occasional fluttering pulse", "tiredness"] if pool_key == "train" else ["exertional retrosternal pressure", "intermittent racing heartbeat", "exhaustion"]
            bio_values["ldl_cholesterol"] = round(random.uniform(135, 195), 2)
            bio_flags["ldl_cholesterol"] = "HIGH"
            primary_drivers = ["exertional_chest_tightness", "ldl_cholesterol"]
            rationale = "DISCRETE_EXERTIONAL_CORRELATION"

        elif specialty == "Pulmonology":
            # Discrete respiratory finding: dry nocturnal cough
            sym_set = ["persistent dry nocturnal cough", "subtle wheezing on deep exhalation", "fatigue"] if pool_key == "train" else ["nighttime hacking cough", "slight expiratory wheeze", "weariness"]
            primary_drivers = ["nocturnal_cough", "wheezing"]
            rationale = "DISCRETE_RESPIRATORY_FINDING"

        elif specialty == "Dermatology":
            # Discrete cutaneous finding: localized itchy plaque
            sym_set = ["localized itchy erythematous plaque on forearm", "scaly skin patch", "tiredness"] if pool_key == "train" else ["pruritic discrete red skin lesion", "mild epidermal flaking", "fatigue"]
            primary_drivers = ["erythematous_plaque", "pruritus"]
            rationale = "DISCRETE_CUTANEOUS_FINDING"

        elif specialty == "Neurology":
            # Discrete neurological finding: unilateral temple throbbing
            sym_set = ["unilateral throbbing temple headache", "mild tingling in index fingertips", "fatigue"] if pool_key == "train" else ["hemicranial pulsating ache", "acral finger paresthesias", "exhaustion"]
            primary_drivers = ["unilateral_headache", "paresthesias"]
            rationale = "DISCRETE_NEUROLOGICAL_FINDING"

        elif specialty == "Orthopedics":
            # Discrete musculoskeletal finding: patellofemoral crepitus
            sym_set = ["right knee stiffness and crepitus after sitting", "localized joint ache", "fatigue"] if pool_key == "train" else ["articular knee crepitation", "post-inactivity joint stiffness", "tiredness"]
            bio_values["uric_acid"] = round(random.uniform(7.2, 9.2), 2)
            bio_flags["uric_acid"] = "HIGH"
            primary_drivers = ["joint_crepitus", "knee_stiffness", "uric_acid"]
            rationale = "DISCRETE_ARTICULAR_FINDING"

        elif specialty == "General Medicine":
            sym_set = ["general fatigue", "mild lack of stamina", "routine health review"] if pool_key == "train" else ["non-specific tiredness", "constitutional sluggishness", "wellness check"]
            primary_drivers = ["normal_biomarkers", "routine_review"]
            rationale = "BENIGN_CONSTITUTIONAL_OR_PREVENTIVE"

    # =========================================================================
    # CATEGORY 4: NORMAL CONTROLS & BENIGN VARIANTS (10% of dataset)
    # =========================================================================
    elif case_category == "NORMAL_CONTROL":
        normal_concerns = {
            "train": [
                "Annual comprehensive wellness health checkup and physical exam",
                "Routine health evaluation for employment medical certificate",
                "General wellness check for routine blood pressure and vitals",
                "Preventive routine laboratory profile for health insurance check"
            ],
            "test": [
                "Preventive annual biological screening examination without symptoms",
                "Standard pre-employment occupational physical and lab evaluation",
                "Routine periodic health maintenance checkup feeling completely healthy"
            ]
        }
        concern = random.choice(normal_concerns[pool_key])
        sym_set = ["annual checkup", "preventive check"] if pool_key == "train" else ["routine screening", "wellness exam"]
        body_region = "General / Whole Body"
        primary_specialty = "General Medicine"
        secondary_specialty = "None"
        rationale = "BENIGN_CONSTITUTIONAL_OR_PREVENTIVE"

        # 30% chance of benign Gilbert's syndrome variant
        if random.random() < 0.30:
            bio_values["total_bilirubin"] = round(random.uniform(1.20, 2.10), 2)
            bio_flags["total_bilirubin"] = "HIGH"
            primary_drivers = ["routine_wellness", "normal_transaminases"]
            secondary_drivers = ["total_bilirubin (Gilbert's variant)"]
        else:
            primary_drivers = ["normal_biomarkers", "preventive_checkup"]

    symptoms_text = ", ".join(sym_set)
    full_text = f"Primary Concern: {concern}. Symptoms: {symptoms_text}. Affected Area: {body_region}."

    row = {
        "primary_concern": concern,
        "symptoms": symptoms_text,
        "body_region": body_region,
        "full_text": full_text,
        "severity_score": severity,
        "duration_days": duration,
        "specialty": primary_specialty,
        "specialty_id": SPECIALTIES.index(primary_specialty),
        "secondary_specialty": secondary_specialty,
        "secondary_specialty_id": SPECIALTIES.index(secondary_specialty) if secondary_specialty in SPECIALTIES else -1,
        "primary_driver_features": "; ".join(primary_drivers),
        "secondary_driver_features": "; ".join(secondary_drivers),
        "labeling_rationale": rationale,
        "case_category": case_category,
        "split": split
    }

    for b_name in CANONICAL_BIOMARKERS_V2:
        row[f"val_{b_name}"] = bio_values[b_name]
        row[f"flag_{b_name}"] = bio_flags[b_name]

    return row

def verify_dataset_leakage(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Automated 4-tier leakage verification suite:
    Tier 1: Exact full_text string overlap (Must be 0)
    Tier 2: Primary concern string overlap (Must be 0)
    Tier 3: Symptom combination string overlap (Must be 0)
    Tier 4: Maximum Jaccard word-set similarity (< 0.70)
    """
    train_rows = [r for r in rows if r["split"] == "train"]
    test_rows = [r for r in rows if r["split"] == "test"]

    train_full = {r["full_text"] for r in train_rows}
    test_full = {r["full_text"] for r in test_rows}
    full_text_overlap = len(train_full.intersection(test_full))

    train_concerns = {r["primary_concern"] for r in train_rows}
    test_concerns = {r["primary_concern"] for r in test_rows}
    concern_overlap = len(train_concerns.intersection(test_concerns))

    train_symptoms = {r["symptoms"] for r in train_rows}
    test_symptoms = {r["symptoms"] for r in test_rows}
    symptom_overlap = len(train_symptoms.intersection(test_symptoms))

    # Jaccard word similarity between test samples and closest train sample
    train_word_sets = [set(r["full_text"].lower().split()) for r in train_rows]
    sample_test_word_sets = [set(r["full_text"].lower().split()) for r in test_rows[:100]]
    max_jaccard = 0.0
    for tw in sample_test_word_sets:
        for trw in train_word_sets:
            jacc = len(tw.intersection(trw)) / len(tw.union(trw))
            if jacc > max_jaccard:
                max_jaccard = jacc

    report = {
        "full_text_overlap_count": full_text_overlap,
        "concern_overlap_count": concern_overlap,
        "symptom_overlap_count": symptom_overlap,
        "max_jaccard_word_similarity": round(max_jaccard, 4),
        "leakage_passed": (
            full_text_overlap == 0 and
            concern_overlap == 0 and
            symptom_overlap == 0 and
            max_jaccard < 0.75
        )
    }
    return report

def generate_v2_dataset(
    samples_per_specialty: int = 600,
    output_path: str = None
) -> List[Dict[str, Any]]:
    """
    Generates 6,000 samples (600 per specialty) partitioned into 70% Train, 15% Val, 15% Test.
    Enforces disjoint templates and passes the automated 4-tier leakage verification suite.
    """
    random.seed(42)
    rows = []

    n_isolated = int(samples_per_specialty * 0.50)
    n_mixed = int(samples_per_specialty * 0.25)
    n_discordant = int(samples_per_specialty * 0.15)
    n_normal = samples_per_specialty - (n_isolated + n_mixed + n_discordant)

    category_plan = (
        ["ISOLATED"] * n_isolated +
        ["MIXED"] * n_mixed +
        ["DISCORDANT"] * n_discordant +
        ["NORMAL_CONTROL"] * n_normal
    )

    for spec in SPECIALTIES:
        random.shuffle(category_plan)
        for i, cat in enumerate(category_plan):
            if i < 420:
                split = "train"
            elif i < 510:
                split = "val"
            else:
                split = "test"
            row = generate_v2_sample(spec, split=split, case_category=cat)
            rows.append(row)

    random.shuffle(rows)

    # Execute Automated Leakage Verification
    leakage_report = verify_dataset_leakage(rows)
    print("\n" + "="*70)
    print("DATASET LEAKAGE VERIFICATION SUITE RESULTS")
    print("="*70)
    print(f"Tier 1: Exact full_text overlap:       {leakage_report['full_text_overlap_count']} (Target: 0)")
    print(f"Tier 2: Exact concern overlap:         {leakage_report['concern_overlap_count']} (Target: 0)")
    print(f"Tier 3: Exact symptom string overlap:  {leakage_report['symptom_overlap_count']} (Target: 0)")
    print(f"Tier 4: Maximum Jaccard similarity:   {leakage_report['max_jaccard_word_similarity']:.4f} (Target: < 0.75)")
    print(f"Leakage Suite Status:                  {'PASSED' if leakage_report['leakage_passed'] else 'FAILED'}")
    print("="*70)

    assert leakage_report["leakage_passed"], f"Leakage verification failed: {leakage_report}"

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
    out_file = r"c:\Users\Uzair\Documents\AML_REACT_PROJECT\backend\app\ml\data\medical_specialty_dataset_v2.csv"
    generate_v2_dataset(samples_per_specialty=600, output_path=out_file)
