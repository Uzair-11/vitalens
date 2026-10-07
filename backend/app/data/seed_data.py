import os
import asyncio
import uuid
from typing import Optional
from datetime import date, time, timedelta, timezone, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.specialty import MedicalSpecialty
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.user import User
from app.models.consent import Consent
from app.models.content import BiomarkerReference, GlossaryTerm
from app.models.biomarker_explanation import BiomarkerExplanation
from app.ml.explainer_ai import EXPLANATION_BANK
from app.core.security import get_password_hash
from app.core.config import settings

SPECIALTIES_DATA = [
    {
        "name": "Cardiology",
        "description": "Specializes in diagnosing and treating diseases of the heart and blood vessels.",
        "icon_name": "heart-pulse"
    },
    {
        "name": "Endocrinology",
        "description": "Focuses on hormone imbalances, diabetes, metabolic disorders, and thyroid diseases.",
        "icon_name": "dna"
    },
    {
        "name": "Hematology",
        "description": "Deals with blood disorders, anemia, clotting issues, and blood cell abnormalities.",
        "icon_name": "droplet"
    },
    {
        "name": "Gastroenterology",
        "description": "Treats disorders of the digestive system, stomach, liver, and intestines.",
        "icon_name": "activity"
    },
    {
        "name": "Nephrology",
        "description": "Specializes in kidney care, renal function management, and electrolyte disorders.",
        "icon_name": "shield"
    },
    {
        "name": "Pulmonology",
        "description": "Treats respiratory conditions, lungs, asthma, and chronic cough disorders.",
        "icon_name": "wind"
    },
    {
        "name": "Dermatology",
        "description": "Specializes in conditions affecting the skin, hair, and nails.",
        "icon_name": "smile"
    },
    {
        "name": "Neurology",
        "description": "Treats conditions affecting the brain, spinal cord, and nervous system.",
        "icon_name": "zap"
    },
    {
        "name": "Orthopedics",
        "description": "Focuses on the musculoskeletal system, bones, joints, ligaments, and tendons.",
        "icon_name": "award"
    },
    {
        "name": "General Medicine",
        "description": "Comprehensive primary care, routine wellness, and holistic health evaluations.",
        "icon_name": "stethoscope"
    }
]

from app.data.synthetic_doctors_dataset import SYNTHETIC_DOCTORS_55

SPECIALTY_ALIAS_MAP = {
    "Cardiology": ["Cardiology"],
    "Endocrinology": ["Endocrinology & Diabetology", "Endocrinology", "Diabetology & Metabolic Care"],
    "Gastroenterology": ["Gastroenterology & Hepatology", "Gastroenterology"],
    "Hematology": ["Clinical Hematology & Bone Marrow Transplant", "Hematology"],
    "Nephrology": ["Nephrology & Kidney Care", "Nephrology"],
    "Pulmonology": ["Pulmonology & Respiratory Medicine", "Pulmonology"],
    "Dermatology": ["Dermatology, Venereology & Leprosy (Skin & Hair)", "Dermatology"],
    "Neurology": ["Neurology"],
    "Orthopedics": ["Orthopaedics & Joint Replacement", "Orthopedics", "Orthopaedics"],
    "General Medicine": ["General Medicine (Internal Medicine)", "General Medicine", "Family Medicine & Preventive Healthcare"],
}
FIXTURE_TEST_DOCTORS = [
    {
        "specialty": "Cardiology",
        "email": "doctor.jenkins@vitalens.health",
        "full_name": "Dr. Sarah Jenkins, MD, FACC",
        "qualification": "MD (Cardiology), Harvard Medical School",
        "registration_number": "FIX-REG-JENKINS-001",
        "registration_council": "Maharashtra Medical Council",
        "state_code": "MH",
        "experience_years": 14,
        "clinic_name": "Apex Heart & Vascular Institute",
        "address": "742 Evergreen Terrace, Suite 400",
        "city": "Ahmedabad",
        "consultation_fee": 95.00,
        "rating": 4.9,
        "review_count": 128,
        "profile_photo_url": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&q=80&w=300",
        "languages": ["English", "Spanish"],
        "bio": "Dr. Jenkins is a board-certified cardiologist specializing in preventive cardiology, lipid management, and non-invasive cardiovascular imaging.",
        "verification_status": "VERIFIED",
        "credential_documents": ["SYNTHETIC_VERIFIED_CREDENTIAL_DATASET"],
        "is_active": True
    },
    {
        "specialty": "Cardiology",
        "email": "doctor.vance@vitalens.health",
        "full_name": "Dr. Robert Vance, MD",
        "qualification": "MBBS, MD (Cardiovascular Diseases)",
        "registration_number": "FIX-REG-VANCE-002",
        "registration_council": "Maharashtra Medical Council",
        "state_code": "MH",
        "experience_years": 18,
        "clinic_name": "Vance Cardiovascular Care Center",
        "address": "120 Medical Arts Pavilion, 3rd Floor",
        "city": "Ahmedabad",
        "consultation_fee": 110.00,
        "rating": 4.8,
        "review_count": 94,
        "profile_photo_url": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&q=80&w=300",
        "languages": ["English"],
        "bio": "Senior interventional cardiologist with nearly two decades of clinical experience in managing coronary health and rhythm disorders.",
        "verification_status": "VERIFIED",
        "credential_documents": ["SYNTHETIC_VERIFIED_CREDENTIAL_DATASET"],
        "is_active": True
    },
    {
        "specialty": "Endocrinology",
        "email": "doctor.rostova@vitalens.health",
        "full_name": "Dr. Elena Rostova, MD",
        "qualification": "MD (Endocrinology & Diabetes)",
        "registration_number": "FIX-REG-ROSTOVA-003",
        "registration_council": "Gujarat Medical Council",
        "state_code": "GJ",
        "experience_years": 11,
        "clinic_name": "Metabolic & Thyroid Wellness Clinic",
        "address": "88 Science Blvd, Suite 210",
        "city": "Ahmedabad",
        "consultation_fee": 85.00,
        "rating": 4.9,
        "review_count": 156,
        "profile_photo_url": "https://images.unsplash.com/photo-1594824813570-588267b93ef2?auto=format&fit=crop&q=80&w=300",
        "languages": ["English", "Russian"],
        "bio": "Specialist in metabolic syndromes, personalized diabetes care, thyroid optimization, and hormonal regulation.",
        "verification_status": "VERIFIED",
        "credential_documents": ["SYNTHETIC_VERIFIED_CREDENTIAL_DATASET"],
        "is_active": True
    }
]

DOCTORS_DATA = FIXTURE_TEST_DOCTORS + SYNTHETIC_DOCTORS_55

SLOT_TIMES = [
    time(9, 0), time(9, 30), time(10, 0), time(10, 30),
    time(11, 0), time(11, 30), time(14, 0), time(14, 30),
    time(15, 0), time(15, 30), time(16, 0), time(16, 30)
]

BIOMARKER_SEED = [
    {"test_name": "Hemoglobin", "canonical_name": "Hemoglobin (Hb)", "category": "Complete Blood Count", "default_unit": "g/dL", "ref_min": 12.0, "ref_max": 17.5, "critical_low": 7.0, "critical_high": 20.0},
    {"test_name": "White Blood Cell Count", "canonical_name": "White Blood Cell Count (WBC)", "category": "Complete Blood Count", "default_unit": "cells/mcL", "ref_min": 4000, "ref_max": 11000, "critical_low": 2000, "critical_high": 30000},
    {"test_name": "Red Blood Cell Count", "canonical_name": "Red Blood Cell Count (RBC)", "category": "Complete Blood Count", "default_unit": "million/mcL", "ref_min": 4.2, "ref_max": 5.9, "critical_low": 2.5, "critical_high": 7.0},
    {"test_name": "Platelets", "canonical_name": "Platelet Count", "category": "Complete Blood Count", "default_unit": "cells/mcL", "ref_min": 150000, "ref_max": 450000, "critical_low": 50000, "critical_high": 1000000},
    {"test_name": "Hematocrit", "canonical_name": "Hematocrit (PCV)", "category": "Complete Blood Count", "default_unit": "%", "ref_min": 36.0, "ref_max": 50.0, "critical_low": 20.0, "critical_high": 60.0},
    {"test_name": "Fasting Blood Glucose", "canonical_name": "Fasting Blood Glucose", "category": "Diabetes & Metabolism", "default_unit": "mg/dL", "ref_min": 70.0, "ref_max": 99.0, "critical_low": 50.0, "critical_high": 350.0},
    {"test_name": "HbA1c", "canonical_name": "Glycated Hemoglobin (HbA1c)", "category": "Diabetes & Metabolism", "default_unit": "%", "ref_min": 4.0, "ref_max": 5.6, "critical_low": 3.5, "critical_high": 14.0},
    {"test_name": "Total Cholesterol", "canonical_name": "Total Cholesterol", "category": "Lipid Profile", "default_unit": "mg/dL", "ref_min": 125.0, "ref_max": 200.0, "critical_low": 80.0, "critical_high": 400.0},
    {"test_name": "LDL Cholesterol", "canonical_name": "LDL Cholesterol", "category": "Lipid Profile", "default_unit": "mg/dL", "ref_min": 0.0, "ref_max": 100.0, "critical_low": 0.0, "critical_high": 250.0},
    {"test_name": "HDL Cholesterol", "canonical_name": "HDL Cholesterol", "category": "Lipid Profile", "default_unit": "mg/dL", "ref_min": 40.0, "ref_max": 60.0, "critical_low": 20.0, "critical_high": 120.0},
    {"test_name": "Triglycerides", "canonical_name": "Triglycerides", "category": "Lipid Profile", "default_unit": "mg/dL", "ref_min": 0.0, "ref_max": 150.0, "critical_low": 0.0, "critical_high": 500.0},
    {"test_name": "Serum Creatinine", "canonical_name": "Serum Creatinine", "category": "Renal Panel", "default_unit": "mg/dL", "ref_min": 0.6, "ref_max": 1.2, "critical_low": 0.2, "critical_high": 5.0},
    {"test_name": "BUN", "canonical_name": "Blood Urea Nitrogen (BUN)", "category": "Renal Panel", "default_unit": "mg/dL", "ref_min": 7.0, "ref_max": 20.0, "critical_low": 2.0, "critical_high": 80.0},
    {"test_name": "ALT", "canonical_name": "Alanine Aminotransferase (ALT)", "category": "Liver Function", "default_unit": "U/L", "ref_min": 7.0, "ref_max": 56.0, "critical_low": 0.0, "critical_high": 500.0},
    {"test_name": "AST", "canonical_name": "Aspartate Aminotransferase (AST)", "category": "Liver Function", "default_unit": "U/L", "ref_min": 10.0, "ref_max": 40.0, "critical_low": 0.0, "critical_high": 500.0},
    {"test_name": "TSH", "canonical_name": "Thyroid Stimulating Hormone (TSH)", "category": "Thyroid Panel", "default_unit": "uIU/mL", "ref_min": 0.4, "ref_max": 4.0, "critical_low": 0.05, "critical_high": 20.0},
    {"test_name": "Free T4", "canonical_name": "Free T4", "category": "Thyroid Panel", "default_unit": "ng/dL", "ref_min": 0.8, "ref_max": 1.8, "critical_low": 0.3, "critical_high": 3.5},
    {"test_name": "Ferritin", "canonical_name": "Ferritin", "category": "Iron Studies", "default_unit": "ng/mL", "ref_min": 15.0, "ref_max": 150.0, "critical_low": 5.0, "critical_high": 1000.0},
    {"test_name": "Iron", "canonical_name": "Iron", "category": "Iron Studies", "default_unit": "ug/dL", "ref_min": 50.0, "ref_max": 170.0, "critical_low": 20.0, "critical_high": 300.0},
    {"test_name": "Total Bilirubin", "canonical_name": "Bilirubin, Total", "category": "Liver Function", "default_unit": "mg/dL", "ref_min": 0.1, "ref_max": 1.2, "critical_low": 0.0, "critical_high": 15.0, "synonyms": ["bilirubin, total", "total bilirubin", "serum bilirubin", "bilirubin"]},
    {"test_name": "Sodium", "canonical_name": "Sodium", "category": "Comprehensive Metabolic Panel", "default_unit": "mEq/L", "ref_min": 135.0, "ref_max": 145.0, "critical_low": 120.0, "critical_high": 160.0, "synonyms": ["sodium", "serum sodium", "na", "na+", "s. sodium"]},
    {"test_name": "Potassium", "canonical_name": "Potassium", "category": "Comprehensive Metabolic Panel", "default_unit": "mEq/L", "ref_min": 3.5, "ref_max": 5.1, "critical_low": 2.8, "critical_high": 6.2, "synonyms": ["potassium", "serum potassium", "k", "k+", "s. potassium"]},
    {"test_name": "Chloride", "canonical_name": "Chloride", "category": "Comprehensive Metabolic Panel", "default_unit": "mEq/L", "ref_min": 96.0, "ref_max": 106.0, "critical_low": 80.0, "critical_high": 120.0, "synonyms": ["chloride", "serum chloride", "cl", "cl-", "s. chloride"]},
    {"test_name": "Calcium", "canonical_name": "Calcium", "category": "Comprehensive Metabolic Panel", "default_unit": "mg/dL", "ref_min": 8.5, "ref_max": 10.2, "critical_low": 6.5, "critical_high": 13.0, "synonyms": ["calcium", "serum calcium", "ca", "total calcium", "ca++", "s. calcium"]},
    {"test_name": "Urine Protein", "canonical_name": "Urine Protein", "category": "Urinalysis", "default_unit": "mg/dL", "ref_min": 0.0, "ref_max": 14.0, "critical_low": None, "critical_high": 300.0, "synonyms": ["urine protein", "protein urine", "protein, urine", "urinary protein", "urine albumin"]},
    {"test_name": "Urine Glucose", "canonical_name": "Urine Glucose", "category": "Urinalysis", "default_unit": "mg/dL", "ref_min": 0.0, "ref_max": 15.0, "critical_low": None, "critical_high": 500.0, "synonyms": ["urine glucose", "glucose urine", "glucose, urine", "urinary glucose", "urine sugar"]},
    {"test_name": "eGFR", "canonical_name": "Estimated Glomerular Filtration Rate (eGFR)", "category": "Renal Panel", "default_unit": "mL/min/1.73m2", "ref_min": 90.0, "ref_max": None, "critical_low": 15.0, "critical_high": None, "synonyms": ["egfr", "estimated glomerular filtration rate", "estimated glomerular filtration rate (egfr)", "gfr", "estimated gfr", "egfr (ckd-epi)", "gfr estimated"]},
    {"test_name": "Uric Acid", "canonical_name": "Uric Acid, Serum", "category": "Renal Panel", "default_unit": "mg/dL", "ref_min": 3.5, "ref_max": 7.2, "critical_low": 1.5, "critical_high": 12.0, "synonyms": ["uric acid", "serum uric acid", "uric acid, serum", "s. uric acid"]},
    {"test_name": "C-Reactive Protein", "canonical_name": "C-Reactive Protein (CRP)", "category": "Inflammatory Markers", "default_unit": "mg/L", "ref_min": 0.0, "ref_max": 3.0, "critical_low": None, "critical_high": 50.0, "synonyms": ["crp", "c-reactive protein", "c-reactive protein (crp)", "hs-crp", "high sensitivity crp"]},
    {"test_name": "Erythrocyte Sedimentation Rate", "canonical_name": "Erythrocyte Sedimentation Rate (ESR)", "category": "Inflammatory Markers", "default_unit": "mm/hr", "ref_min": 0.0, "ref_max": 20.0, "critical_low": None, "critical_high": 100.0, "synonyms": ["esr", "erythrocyte sedimentation rate", "erythrocyte sedimentation rate (esr)", "sed rate", "westergren esr"]},
]

GLOSSARY_SEED = [
    {"term": "Hemoglobin", "definition": "A specialized iron-rich protein in red blood cells that transports oxygen from the lungs to body tissues."},
    {"term": "WBC", "definition": "White blood cells that defend the body against infections, allergic reactions, and cellular stress."},
    {"term": "Platelets", "definition": "Cell fragments circulating in blood that initiate clotting to stop bleeding when vessels are damaged."},
    {"term": "Fasting Blood Glucose", "definition": "The concentration of sugar circulating in the bloodstream following an overnight period of fasting."},
    {"term": "HbA1c", "definition": "An established marker reflecting average blood sugar control over the past 60 to 90 days."},
    {"term": "Total Cholesterol", "definition": "The total amount of cholesterol circulating in the blood, comprising HDL, LDL, and triglycerides."},
    {"term": "LDL", "definition": "Low-Density Lipoprotein, often called 'bad cholesterol' because excessive levels can build up in arterial walls."},
    {"term": "HDL", "definition": "High-Density Lipoprotein, termed 'good cholesterol' as it helps transport excess cholesterol back to the liver."},
    {"term": "Triglycerides", "definition": "A prevalent type of fat in your blood stored in fat cells and used for cellular energy between meals."},
    {"term": "Serum Creatinine", "definition": "A standard waste product of muscle metabolism filtered out continuously by healthy kidneys."},
    {"term": "BUN", "definition": "Blood Urea Nitrogen, a waste byproduct formed in the liver when proteins break down and cleared by the kidneys."},
    {"term": "eGFR", "definition": "Estimated Glomerular Filtration Rate, calculating how efficiently your kidneys are filtering waste products."},
    {"term": "ALT", "definition": "An enzyme primarily located inside liver cells that enters the bloodstream when liver cells experience stress or irritation."},
    {"term": "AST", "definition": "An enzyme found in liver, heart, and muscle tissue that can increase when these tissues undergo stress."},
    {"term": "TSH", "definition": "Thyroid Stimulating Hormone produced by the pituitary gland to control metabolic rate and thyroid activity."},
    {"term": "Free T4", "definition": "Free Thyroxine, the active circulating form of thyroid hormone regulating metabolism, energy, and body temperature."},
    {"term": "Ferritin", "definition": "A cellular protein that stores iron and releases it in a controlled fashion; the most reliable indicator of total body iron reserves."},
    {"term": "Iron", "definition": "An essential mineral required for producing hemoglobin, transporting oxygen throughout the body, and maintaining cellular energy."},
    {"term": "Bilirubin", "definition": "A yellowish compound formed during the normal breakdown of red blood cells, processed and excreted by the liver through bile."},
    {"term": "RBC", "definition": "Red blood cells (erythrocytes) that carry oxygen from your lungs to every tissue and organ in your body while returning carbon dioxide to be exhaled."},
    {"term": "Hematocrit", "definition": "The percentage of your total blood volume made up of red blood cells, reflecting overall hydration status and oxygen-carrying capacity."},
    {"term": "Sodium", "definition": "A vital mineral and electrolyte that helps balance fluid levels in and around your cells, stabilizes blood pressure, and enables proper nerve and muscle signaling."},
    {"term": "Potassium", "definition": "An essential electrolyte that controls heart rhythm, regulates blood pressure, and facilitates normal muscle contractions and nerve impulses throughout the body."},
    {"term": "Chloride", "definition": "An electrolyte that works closely with sodium and potassium to maintain electrical neutrality, proper fluid balance, and blood pH acid-base equilibrium."},
    {"term": "Calcium", "definition": "A fundamental mineral required for building and maintaining strong bones and teeth, blood clotting, muscle contractions, and heart nerve transmission."},
    {"term": "Urine Protein", "definition": "Measures protein in the urine (proteinuria). Healthy kidneys keep proteins in the blood; presence in urine can be an early indicator of kidney stress or damage."},
    {"term": "Urine Glucose", "definition": "Measures sugar in the urine (glucosuria). Normally absent; spillover occurs when blood sugar exceeds renal absorption thresholds, often indicating poorly controlled diabetes."},
    {"term": "Uric Acid", "definition": "A natural waste byproduct formed during the breakdown of purines; elevated levels can form painful crystals in joints (gout) or lead to kidney stones."},
    {"term": "CRP", "definition": "C-Reactive Protein, a protein produced rapidly by the liver in response to acute inflammation, tissue injury, bacterial infection, or vascular stress."},
    {"term": "ESR", "definition": "Erythrocyte Sedimentation Rate, an indicator measuring how quickly red blood cells settle to the bottom of a test tube; higher rates suggest systemic inflammation."}
]

from app.core.db_sync import sync_sqlite_schema

async def seed_database(custom_engine=None, custom_session_factory=None, include_doctors: Optional[bool] = None):
    """Initializes tables and seeds initial specialties, admin/demo users, and clinical content."""
    target_engine = custom_engine or engine
    target_session_factory = custom_session_factory or AsyncSessionLocal

    if include_doctors is None:
        include_doctors = os.getenv("SEED_DOCTORS", "false").lower() == "true"


    if "sqlite" in settings.DATABASE_URL:
        sync_sqlite_schema()
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with target_session_factory() as session:
        # 1. Seed Demo Patient User
        user_q = select(User).where(User.email == "demo@healthapp.com")
        user_res = await session.execute(user_q)
        demo_user = user_res.scalars().first()
        if not demo_user:
            demo_user = User(
                email="demo@healthapp.com",
                hashed_password=get_password_hash("password123"),
                role="PATIENT",
                full_name="Alex Mercer",
                phone="+1 (555) 234-5678",
                date_of_birth=date(1996, 5, 14),
                biological_sex="Male",
                blood_group="O+",
                emergency_contact="Jane Mercer: +1 (555) 987-6543"
            )
            session.add(demo_user)
            await session.commit()
            await session.refresh(demo_user)
            
            # Seed consents
            for c_type in ["REPORT_ANALYSIS", "AI_PROCESSING", "DOCTOR_DATA_ACCESS", "NOTIFICATIONS", "MARKETING"]:
                session.add(Consent(user_id=demo_user.id, consent_type=c_type, granted=True))
            await session.commit()
            print("[OK] Seeded demo patient user: demo@healthapp.com / password123")


        # 2. Seed Admin User
        admin_q = select(User).where(User.email == "admin@vitalens.health")
        admin_res = await session.execute(admin_q)
        if not admin_res.scalars().first():
            admin_user = User(
                email="admin@vitalens.health",
                hashed_password=get_password_hash("admin123"),
                role="ADMIN",
                full_name="VitaLens System Administrator",
                phone="+1 (555) 000-0001",
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print("[OK] Seeded admin user: admin@vitalens.health / admin123")

        # 2b. Seed Secondary Admin User (admin@healthapp.com)
        admin2_q = select(User).where(User.email == "admin@healthapp.com")
        admin2_res = await session.execute(admin2_q)
        if not admin2_res.scalars().first():
            admin2_user = User(
                email="admin@healthapp.com",
                hashed_password=get_password_hash("admin123"),
                role="ADMIN",
                full_name="Admin User",
                phone="+1 (555) 000-0003",
                is_active=True
            )
            session.add(admin2_user)
            await session.commit()
            print("[OK] Seeded admin user: admin@healthapp.com / admin123")

        # 2c. Seed Support Staff User
        staff_q = select(User).where(User.email == "staff@vitalens.health")
        staff_res = await session.execute(staff_q)
        staff_user = staff_res.scalars().first()
        if not staff_user:
            staff_user = User(
                email="staff@vitalens.health",
                hashed_password=get_password_hash("staff123"),
                role="SUPPORT_STAFF",
                full_name="VitaLens Support Staff",
                phone="+1 (555) 000-0002",
                is_active=True
            )
            session.add(staff_user)
            await session.commit()
            print("[OK] Seeded support staff user: staff@vitalens.health / staff123")

        # 3. Seed Specialties
        specialty_map = {}
        for s_data in SPECIALTIES_DATA:
            canonical_name = s_data["name"]
            candidates = SPECIALTY_ALIAS_MAP.get(canonical_name, [canonical_name])
            spec = None
            for cand in candidates:
                q = select(MedicalSpecialty).where(MedicalSpecialty.name == cand)
                res = await session.execute(q)
                spec = res.scalars().first()
                if spec:
                    break
            if not spec:
                q = select(MedicalSpecialty).where(MedicalSpecialty.name.ilike(f"%{canonical_name[:6]}%"))
                res = await session.execute(q)
                spec = res.scalars().first()
            if not spec:
                spec = MedicalSpecialty(
                    name=s_data["name"],
                    description=s_data["description"],
                    icon_name=s_data["icon_name"]
                )
                session.add(spec)
                await session.commit()
                await session.refresh(spec)
            specialty_map[canonical_name] = spec.id

        # 4. Seed Doctors and Linked Doctor User Accounts (opt-in only)
        if include_doctors:
            for doc_data in DOCTORS_DATA:
                spec_id = specialty_map.get(doc_data["specialty"])
                if not spec_id:
                    candidates = SPECIALTY_ALIAS_MAP.get(doc_data["specialty"], [doc_data["specialty"]])
                    for cand in candidates:
                        q = select(MedicalSpecialty).where(MedicalSpecialty.name == cand)
                        res = await session.execute(q)
                        spec = res.scalars().first()
                        if spec:
                            spec_id = spec.id
                            specialty_map[doc_data["specialty"]] = spec_id
                            break
                if not spec_id:
                    continue

                # Check or create doctor user login account
                doc_user_q = select(User).where(User.email == doc_data["email"])
                doc_user_res = await session.execute(doc_user_q)
                doc_user = doc_user_res.scalars().first()
                if not doc_user:
                    doc_user = User(
                        email=doc_data["email"],
                        hashed_password=get_password_hash("doctor123"),
                        role="DOCTOR",
                        full_name=doc_data["full_name"],
                        phone=doc_data.get("phone"),
                        is_active=True
                    )
                    session.add(doc_user)
                    await session.commit()
                    await session.refresh(doc_user)
                else:
                    if not doc_user.phone and doc_data.get("phone"):
                        doc_user.phone = doc_data.get("phone")
                    doc_user.is_active = True
                    await session.commit()

                # Check if doctor exists by registration_number, email, or full_name
                doc = None
                if doc_data.get("registration_number"):
                    doc_q = select(Doctor).where(Doctor.registration_number == doc_data["registration_number"])
                    doc_res = await session.execute(doc_q)
                    doc = doc_res.scalars().first()
                if not doc and doc_data.get("email"):
                    doc_q = select(Doctor).where(Doctor.email == doc_data["email"])
                    doc_res = await session.execute(doc_q)
                    doc = doc_res.scalars().first()
                if not doc:
                    doc_q = select(Doctor).where(Doctor.full_name == doc_data["full_name"])
                    doc_res = await session.execute(doc_q)
                    doc = doc_res.scalars().first()
                
                if not doc:
                    doc = Doctor(
                        user_id=doc_user.id,
                        specialty_id=spec_id,
                        full_name=doc_data["full_name"],
                        qualification=doc_data["qualification"],
                        registration_number=doc_data.get("registration_number"),
                        registration_council=doc_data.get("registration_council"),
                        state_code=doc_data.get("state_code"),
                        email=doc_data.get("email"),
                        phone=doc_data.get("phone"),
                        gender=doc_data.get("gender"),
                        consultation_mode=doc_data.get("consultation_mode", "HYBRID"),
                        experience_years=doc_data.get("experience_years", 0),
                        clinic_name=doc_data["clinic_name"],
                        address=doc_data["address"],
                        city=doc_data["city"],
                        consultation_fee=doc_data.get("consultation_fee", 800.0),
                        rating=doc_data.get("rating", 5.0),
                        review_count=doc_data.get("review_count", 0),
                        profile_photo_url=doc_data.get("profile_photo_url"),
                        languages=doc_data.get("languages", ["English"]),
                        bio=doc_data.get("bio"),
                        verification_status=doc_data.get("verification_status", "VERIFIED"),
                        credential_documents=doc_data.get("credential_documents", ["SYNTHETIC_VERIFIED_CREDENTIAL_DATASET"]),
                        is_active=True
                    )
                    session.add(doc)
                    await session.commit()
                    await session.refresh(doc)
                else:
                    doc.user_id = doc_user.id
                    doc.specialty_id = spec_id
                    doc.qualification = doc_data["qualification"]
                    doc.registration_number = doc_data.get("registration_number")
                    doc.registration_council = doc_data.get("registration_council")
                    doc.state_code = doc_data.get("state_code")
                    doc.email = doc_data.get("email")
                    doc.phone = doc_data.get("phone")
                    doc.gender = doc_data.get("gender")
                    doc.consultation_mode = doc_data.get("consultation_mode", "HYBRID")
                    doc.experience_years = doc_data.get("experience_years", 0)
                    doc.clinic_name = doc_data["clinic_name"]
                    doc.address = doc_data["address"]
                    doc.city = doc_data["city"]
                    doc.consultation_fee = doc_data.get("consultation_fee", 800.0)
                    doc.rating = doc_data.get("rating", 5.0)
                    doc.review_count = doc_data.get("review_count", 0)
                    doc.profile_photo_url = doc_data.get("profile_photo_url")
                    doc.languages = doc_data.get("languages", ["English"])
                    doc.bio = doc_data.get("bio")
                    doc.verification_status = doc_data.get("verification_status", "VERIFIED")
                    doc.credential_documents = doc_data.get("credential_documents", ["SYNTHETIC_VERIFIED_CREDENTIAL_DATASET"])
                    doc.is_active = True
                    await session.commit()

                # Check working hours count
                from app.models.doctor_schedule import DoctorWorkingHours
                wh_cnt_q = select(DoctorWorkingHours).where(DoctorWorkingHours.doctor_id == doc.id)
                wh_res = await session.execute(wh_cnt_q)
                if len(wh_res.scalars().all()) == 0:
                    for day_idx in range(6):  # Mon-Sat
                        wh_item = DoctorWorkingHours(
                            doctor_id=doc.id,
                            day_of_week=day_idx,
                            start_time=time(9, 0),
                            end_time=time(17, 0),
                            slot_duration_minutes=30,
                            is_active=True
                        )
                        session.add(wh_item)
                    await session.commit()

                # Check slots count
                slots_cnt_q = select(DoctorAvailability).where(
                    DoctorAvailability.doctor_id == doc.id,
                    DoctorAvailability.available_date >= date.today()
                )
                slots_res = await session.execute(slots_cnt_q)
                if len(slots_res.scalars().all()) == 0:
                    today = date.today()
                    for day_offset in range(1, 15):
                        slot_date = today + timedelta(days=day_offset)
                        if slot_date.weekday() == 6:
                            continue
                        for t in SLOT_TIMES:
                            end_t = time(t.hour, (t.minute + 30) % 60) if t.minute == 0 else time(t.hour + 1, 0)
                            slot = DoctorAvailability(
                                doctor_id=doc.id,
                                available_date=slot_date,
                                start_time=t,
                                end_time=end_t,
                                slot_duration_minutes=30,
                                is_booked=False
                            )
                            session.add(slot)
                    await session.commit()


        # 5. Seed Clinical Content Reference Thresholds
        for b_seed in BIOMARKER_SEED:
            b_q = select(BiomarkerReference).where(BiomarkerReference.test_name == b_seed["test_name"])
            b_res = await session.execute(b_q)
            if not b_res.scalars().first():
                session.add(BiomarkerReference(**b_seed))
        await session.commit()

        # 6. Seed Glossary
        for g_seed in GLOSSARY_SEED:
            g_q = select(GlossaryTerm).where(GlossaryTerm.term == g_seed["term"])
            g_res = await session.execute(g_q)
            if not g_res.scalars().first():
                session.add(GlossaryTerm(**g_seed, reviewed_by="Clinical Reference Board", reviewed_at=datetime.now(timezone.utc)))
        await session.commit()

        # 7. Seed Clinical Biomarker Explanations
        for ex in EXPLANATION_BANK:
            e_q = select(BiomarkerExplanation).where(
                BiomarkerExplanation.canonical_name == ex["test"],
                BiomarkerExplanation.flag == ex["flag"]
            )
            e_res = await session.execute(e_q)
            if not e_res.scalars().first():
                session.add(BiomarkerExplanation(
                    test_name=ex["test"],
                    canonical_name=ex["test"],
                    flag=ex["flag"],
                    explanation_text=ex["explanation"]
                ))
        await session.commit()

        doc_msg = f"{len(DOCTORS_DATA)} verified doctors, " if include_doctors else ""
        print(f"[OK] Database initialized with {doc_msg}clinical thresholds, explanation bank, admin accounts, and glossary.")

if __name__ == "__main__":
    asyncio.run(seed_database(include_doctors=True))
