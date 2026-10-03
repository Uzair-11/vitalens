"""
Seed all Medical Specialties recognized in India (National Medical Commission / NMC & NBE).
Includes Broad Specialties (MD/MS) and Super Specialties (DM/MCh/DrNB).
"""
import asyncio
import uuid
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.medical_specialty import MedicalSpecialty

INDIAN_MEDICAL_SPECIALTIES = [
    {
        "name": "General Medicine (Internal Medicine)",
        "description": "Comprehensive primary, preventive, and complex chronic medical care for adults including diabetes, hypertension, infections, and multisystem illnesses.",
        "icon_name": "stethoscope",
    },
    {
        "name": "General Surgery",
        "description": "Evaluation and surgical treatment of abdominal complaints, hernias, soft tissue lesions, gallbladder disorders, and acute surgical conditions.",
        "icon_name": "scissors",
    },
    {
        "name": "Obstetrics & Gynaecology (OB-GYN)",
        "description": "Women's reproductive health, prenatal/postnatal care, childbirth, pregnancy management, menstrual disorders, PCOS, and pelvic health.",
        "icon_name": "heart",
    },
    {
        "name": "Pediatrics & Child Health",
        "description": "Comprehensive medical care for infants, children, and adolescents, including immunization, developmental milestones, and pediatric illnesses.",
        "icon_name": "baby",
    },
    {
        "name": "Orthopaedics & Joint Replacement",
        "description": "Bones, joints, ligaments, tendons, spine disorders, sports injuries, fractures, and total joint replacement surgeries.",
        "icon_name": "bone",
    },
    {
        "name": "Cardiology",
        "description": "Heart disease diagnosis and management including chest pain, angina, arrhythmias, coronary artery disease, heart failure, and hypertension.",
        "icon_name": "heart",
    },
    {
        "name": "Dermatology, Venereology & Leprosy (Skin & Hair)",
        "description": "Diagnosis and management of skin, hair, and nail disorders, acne, eczema, psoriasis, fungal infections, and cosmetic dermatology.",
        "icon_name": "activity",
    },
    {
        "name": "Neurology",
        "description": "Brain, spinal cord, nerve, and muscle disorders including stroke, migraine, epilepsy, Parkinson's disease, and neuropathies.",
        "icon_name": "brain",
    },
    {
        "name": "Gastroenterology & Hepatology",
        "description": "Digestive health, acid reflux, stomach ulcers, liver cirrhosis, fatty liver, jaundice, IBS, and colon disorders.",
        "icon_name": "activity",
    },
    {
        "name": "Nephrology & Kidney Care",
        "description": "Kidney health, chronic kidney disease (CKD), acute renal failure, dialysis management, proteinuria, and kidney transplantation.",
        "icon_name": "activity",
    },
    {
        "name": "Pulmonology & Respiratory Medicine",
        "description": "Lungs and respiratory system care including asthma, COPD, tuberculosis, bronchitis, pneumonia, sleep apnea, and allergy.",
        "icon_name": "activity",
    },
    {
        "name": "Endocrinology & Diabetology",
        "description": "Hormonal and metabolic disorders including Type 1 & 2 Diabetes, thyroid imbalances, obesity, adrenal and pituitary diseases.",
        "icon_name": "activity",
    },
    {
        "name": "Psychiatry & Behavioral Health",
        "description": "Mental health, anxiety disorders, clinical depression, bipolar disorder, schizophrenia, stress disorders, and addiction recovery.",
        "icon_name": "brain",
    },
    {
        "name": "Ophthalmology (Eye Care)",
        "description": "Vision care, cataract surgery, refractive errors, glaucoma, diabetic retinopathy, cornea disorders, and eye surgeries.",
        "icon_name": "eye",
    },
    {
        "name": "ENT / Otorhinolaryngology",
        "description": "Ear, nose, throat, sinuses, head and neck conditions, hearing loss, vertigo, tonsillitis, and sinus surgeries.",
        "icon_name": "activity",
    },
    {
        "name": "Medical Oncology (Cancer Medicine)",
        "description": "Comprehensive medical oncology, systemic cancer chemotherapy, targeted therapies, immunotherapy, and cancer screening.",
        "icon_name": "shield",
    },
    {
        "name": "Surgical Oncology",
        "description": "Operative oncological management and surgical removal of solid tumors, breast cancer, oral cancers, and gastrointestinal cancers.",
        "icon_name": "scissors",
    },
    {
        "name": "Radiation Oncology",
        "description": "Radiotherapy, stereotactic radiosurgery, and brachytherapy treatments for solid malignancies and benign conditions.",
        "icon_name": "activity",
    },
    {
        "name": "Urology & Andrology",
        "description": "Urinary system and male reproductive health, kidney stones, prostate enlargement, urinary infections, and male infertility.",
        "icon_name": "activity",
    },
    {
        "name": "Neurosurgery",
        "description": "Brain tumors, spinal cord trauma, disc herniation, aneurysm clipping, and advanced minimally invasive neurosurgery.",
        "icon_name": "brain",
    },
    {
        "name": "Cardiothoracic & Vascular Surgery (CTVS)",
        "description": "Coronary artery bypass grafting (CABG), heart valve repair/replacement, aortic aneurysm repair, and lung surgeries.",
        "icon_name": "heart",
    },
    {
        "name": "Pediatric Surgery",
        "description": "Specialized surgical care for newborns, infants, and children with congenital anomalies and pediatric surgical conditions.",
        "icon_name": "baby",
    },
    {
        "name": "Plastic, Aesthetic & Reconstructive Surgery",
        "description": "Reconstructive surgery for trauma and burns, micro-vascular reconstruction, cleft lip repair, and aesthetic cosmetic surgery.",
        "icon_name": "scissors",
    },
    {
        "name": "Rheumatology & Clinical Immunology",
        "description": "Joint, autoimmune, and connective tissue disorders including rheumatoid arthritis, lupus (SLE), ankylosing spondylitis, and gout.",
        "icon_name": "activity",
    },
    {
        "name": "Clinical Hematology & Bone Marrow Transplant",
        "description": "Blood disorders, leukemia, lymphoma, multiple myeloma, thalassemia, sickle cell anemia, and stem cell transplantation.",
        "icon_name": "activity",
    },
    {
        "name": "Emergency Medicine & Trauma Care",
        "description": "Immediate evaluation, acute resuscitation, and stabilization of life-threatening medical and traumatic emergencies.",
        "icon_name": "activity",
    },
    {
        "name": "Critical Care & Intensive Care Medicine (ICU)",
        "description": "Management of critically ill patients with sepsis, multi-organ failure, mechanical ventilation, and hemodynamic monitoring.",
        "icon_name": "activity",
    },
    {
        "name": "Anesthesiology & Pain Management",
        "description": "Perioperative anesthesia, interventional chronic pain management, cancer pain relief, and intensive post-operative care.",
        "icon_name": "activity",
    },
    {
        "name": "Radio-diagnosis & Interventional Radiology",
        "description": "Diagnostic imaging (X-Ray, Ultrasound, CT, MRI, PET) and minimally invasive image-guided vascular interventions.",
        "icon_name": "eye",
    },
    {
        "name": "Pathology & Laboratory Medicine",
        "description": "Histopathology, cytopathology, hematology, clinical biochemistry, microbiological cultures, and blood banking.",
        "icon_name": "activity",
    },
    {
        "name": "Physical Medicine & Rehabilitation (PMR)",
        "description": "Rehabilitation medicine for spinal cord injury, stroke recovery, amputee care, musculoskeletal pain, and disability management.",
        "icon_name": "activity",
    },
    {
        "name": "Family Medicine & Preventive Healthcare",
        "description": "Continuing, comprehensive, patient-centered care for families and individuals across all ages and disease stages.",
        "icon_name": "stethoscope",
    },
    {
        "name": "Infectious Diseases",
        "description": "Diagnosis and management of tropical infections, HIV/AIDS, viral fevers, multidrug-resistant infections, and travel medicine.",
        "icon_name": "shield",
    },
    {
        "name": "Geriatric Medicine",
        "description": "Specialized healthcare addressing unique medical, cognitive, and functional needs of older adults and elderly individuals.",
        "icon_name": "activity",
    },
    {
        "name": "Clinical Genetics & Genomics",
        "description": "Diagnostic evaluation and genetic counseling for hereditary disorders, chromosomal abnormalities, and birth defects.",
        "icon_name": "activity",
    },
    {
        "name": "Nuclear Medicine",
        "description": "Diagnostic and therapeutic applications of radionuclides including PET-CT scans, thyroid ablation, and bone scintigraphy.",
        "icon_name": "activity",
    },
    {
        "name": "Palliative & Supportive Medicine",
        "description": "Relief of pain and symptoms to optimize quality of life for patients and families facing serious, life-limiting illnesses.",
        "icon_name": "heart",
    },
    {
        "name": "Sports Medicine & Arthroscopy",
        "description": "Prevention, diagnosis, and rehabilitation of athletic injuries, ligament tears (ACL/PCL), and joint preservation.",
        "icon_name": "bone",
    },
    {
        "name": "Vascular & Endovascular Surgery",
        "description": "Diagnosis and minimally invasive endovascular/surgical treatment of arteries, varicose veins, and diabetic foot ulcers.",
        "icon_name": "scissors",
    },
    {
        "name": "Neonatology (NICU)",
        "description": "Subspecialty of pediatrics focused on premature births, low birth weight, birth asphyxia, and newborn critical care.",
        "icon_name": "baby",
    },
    {
        "name": "Dentistry & Oral Maxillofacial Surgery",
        "description": "Oral health, teeth restoration, orthodontics, periodontics, dental implants, and facial bone trauma surgery.",
        "icon_name": "activity",
    },
    {
        "name": "Diabetology & Metabolic Care",
        "description": "Focused clinical management of diabetes mellitus, insulin regimes, continuous glucose monitoring, and metabolic syndrome.",
        "icon_name": "activity",
    },
    {
        "name": "Allergy & Clinical Immunology",
        "description": "Management of allergic rhinitis, food allergies, drug reactions, urticaria, angioedema, and immunodeficiency disorders.",
        "icon_name": "shield",
    },
    {
        "name": "AYUSH / Integrative Medicine",
        "description": "Evidence-informed traditional and complementary medical systems recognized in India including Ayurveda, Yoga, and Naturopathy.",
        "icon_name": "activity",
    },
]

async def seed_specialties():
    print(f"Connecting to database to seed {len(INDIAN_MEDICAL_SPECIALTIES)} Indian medical specialties...")
    async with AsyncSessionLocal() as session:
        created_count = 0
        existing_count = 0

        for item in INDIAN_MEDICAL_SPECIALTIES:
            # Check if exists by name
            q = select(MedicalSpecialty).where(MedicalSpecialty.name == item["name"])
            res = await session.execute(q)
            existing = res.scalars().first()

            if existing:
                existing.description = item["description"]
                existing.icon_name = item["icon_name"]
                existing.is_active = True
                existing_count += 1
            else:
                spec = MedicalSpecialty(
                    id=str(uuid.uuid4()),
                    name=item["name"],
                    description=item["description"],
                    icon_name=item["icon_name"],
                    is_active=True,
                )
                session.add(spec)
                created_count += 1

        await session.commit()
        print(f"SUCCESS: Seeded {created_count} new specialties, updated {existing_count} existing. Total: {created_count + existing_count}")

if __name__ == "__main__":
    asyncio.run(seed_specialties())
