# VitaLens Clinical Logic Summary & Review Document

This document summarizes every clinical decision point, reference range threshold, emergency red-flag rule, and specialty routing logic for review by licensed medical practitioners.

---

## 1. Biomarker Reference Ranges & Critical Thresholds

| Biomarker | Canonical Name | Normal Reference Range | Critical Low | Critical High | Clinical Category |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hemoglobin** | Hemoglobin (Hb) | 12.0 – 17.5 g/dL | < 7.0 g/dL | > 20.0 g/dL | Hematology |
| **White Blood Cell Count** | WBC Count | 4,500 – 11,000 cells/mcL | < 2,000 cells/mcL | > 25,000 cells/mcL | Hematology |
| **Platelet Count** | Platelets | 150,000 – 450,000 cells/mcL | < 50,000 cells/mcL | > 1,000,000 cells/mcL| Hematology |
| **Fasting Blood Glucose** | Fasting Glucose | 70.0 – 99.0 mg/dL | < 50.0 mg/dL | > 350.0 mg/dL | Metabolic |
| **HbA1c** | Glycated Hemoglobin | 4.0 – 5.6 % | < 3.5 % | > 14.0 % | Metabolic |
| **Total Cholesterol** | Total Cholesterol | 125.0 – 200.0 mg/dL | < 80.0 mg/dL | > 400.0 mg/dL | Lipid Profile |
| **Serum Creatinine** | Serum Creatinine | 0.6 – 1.2 mg/dL | < 0.2 mg/dL | > 5.0 mg/dL | Renal Panel |
| **TSH** | Thyroid Stimulating Hormone| 0.4 – 4.0 uIU/mL | < 0.05 uIU/mL | > 20.0 uIU/mL | Thyroid Panel |

---

## 2. Emergency Red-Flag Intercept Protocol

The system scans symptom inputs and extracted laboratory markers against acute clinical criteria. If any condition is met, outpatient booking is intercepted with an immediate urgent care alert:

### Emergency Symptom Keywords:
- Chest pain, crushing pressure, shortness of breath on rest, difficulty breathing
- Sudden numbness, facial droop, slurred speech, loss of consciousness
- Coughing blood, sudden severe "thunderclap" headache, anaphylaxis symptoms

### Critical Biomarker Flags:
- Any biomarker flagged as `CRITICAL` triggers an immediate alert advising urgent medical evaluation rather than standard outpatient scheduling.

---

## 3. Hybrid Specialty Routing Algorithm

The system combines:
1. **Biomarker Signal Matching:** Evaluates out-of-range lab markers and maps them to primary specialties (e.g. elevated LDL $\rightarrow$ Cardiology; elevated HbA1c/TSH $\rightarrow$ Endocrinology).
2. **TF-IDF Symptom Similarity:** Evaluates patient-described primary concerns against specialty taxonomies using cosine similarity.
3. **Clinical Priority Synthesis:** When high alignment exists between report anomalies and reported symptoms, high confidence scores ($0.85 - 0.95$) are assigned.
4. **General Medicine Fallback:** Ambiguous, mild, or non-specific symptoms route to General Medicine / Internal Medicine as the optimal primary triage point.
