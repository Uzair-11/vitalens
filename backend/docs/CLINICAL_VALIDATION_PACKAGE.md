# VitaLens Clinical Validation Package

> [!WARNING]
> **DOCUMENT STATUS: PENDING FORMAL HUMAN CLINICAL REVIEW (UNVALIDATED)**  
> **Current Clinical Sign-Off State**: **UNREVIEWED**  
> This document compiles the exhaustive clinical decision points, reference intervals, emergency triage heuristics, and algorithmic mappings of the VitaLens health platform. It is generated specifically as a human reviewable audit package for licensed medical practitioners. **No medical claims made within the codebase have been validated or approved by a licensed physician as of this release.**

---

## 1. Live Biomarker Reference Ranges & Critical Thresholds

The following table reflects the exact reference ranges, measurement units, and critical thresholds deployed in the live `vitalens_db` database (`biomarker_references` table), incorporating all Phase 3B and Phase 9 clinical updates:

| Category | Test Name | Canonical Name | Default Unit | Normal Min (`ref_min`) | Normal Max (`ref_max`) | Critical Low (`critical_low`) | Critical High (`critical_high`) |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| **Complete Blood Count** | Hematocrit | Hematocrit (PCV) | `%` | 36.0 | 50.0 | 20.0 | 60.0 |
| **Complete Blood Count** | Red Blood Cell Count | Red Blood Cell Count (RBC) | `million/mcL` | 4.2 | 5.9 | 2.5 | 7.0 |
| **Hematology** | Hemoglobin | Hemoglobin (Hb) | `g/dL` | 12.0 | 17.5 | 7.0 | 20.0 |
| **Hematology** | Platelets | Platelet Count | `cells/mcL` | 150,000 | 450,000 | 50,000 | 1,000,000 |
| **Hematology** | White Blood Cell Count | White Blood Cell Count (WBC) | `cells/mcL` | 4,500 | 11,000 | 2,000 | 25,000 |
| **Lipid Profile** | HDL Cholesterol | HDL Cholesterol | `mg/dL` | 40.0 | 60.0 | 20.0 | 120.0 |
| **Lipid Profile** | LDL Cholesterol | LDL Cholesterol | `mg/dL` | 0.0 | 100.0 | 0.0 | 250.0 |
| **Lipid Profile** | Total Cholesterol | Total Cholesterol | `mg/dL` | 125.0 | 200.0 | 80.0 | 400.0 |
| **Lipid Profile** | Triglycerides | Triglycerides | `mg/dL` | 0.0 | 150.0 | 0.0 | 500.0 |
| **Liver Function** | ALT | Alanine Aminotransferase (ALT) | `U/L` | 7.0 | 56.0 | 0.0 | 500.0 |
| **Liver Function** | AST | Aspartate Aminotransferase (AST) | `U/L` | 10.0 | 40.0 | 0.0 | 500.0 |
| **Metabolic** | Fasting Blood Glucose | Fasting Blood Glucose | `mg/dL` | 70.0 | 99.0 | 50.0 | 350.0 |
| **Metabolic** | HbA1c | Glycated Hemoglobin (HbA1c) | `%` | 4.0 | 5.6 | 3.5 | 14.0 |
| **Renal Panel** | BUN | Blood Urea Nitrogen (BUN) | `mg/dL` | 7.0 | 20.0 | 2.0 | 80.0 |
| **Renal Panel** | Serum Creatinine | Serum Creatinine | `mg/dL` | 0.6 | 1.2 | 0.2 | 5.0 |
| **Thyroid Panel** | TSH | Thyroid Stimulating Hormone (TSH) | `uIU/mL` | 0.4 | 4.0 | 0.05 | 20.0 |

### Extended Canonical Biomarkers (Recognized in Extraction & FHIR Pipelines)
* **Serum Calcium**: Normal `8.5 - 10.2 mg/dL`, Critical Low `< 6.5 mg/dL`, Critical High `> 13.0 mg/dL`.
* **Serum Potassium**: Normal `3.5 - 5.0 mEq/L`, Critical Low `< 2.8 mEq/L`, Critical High `> 6.2 mEq/L`.
* **Serum Sodium**: Normal `135 - 145 mEq/L`, Critical Low `< 120 mEq/L`, Critical High `> 160 mEq/L`.
* **Total Bilirubin**: Normal `0.2 - 1.2 mg/dL`, Critical High `> 12.0 mg/dL`.

---

## 2. LOINC Standard Semantic Code Mappings

The following table documents every internal test identifier to standard LOINC code mapping implemented in [`app/integrations/abdm/fhir_mapper.py`](file:///c:/Users/Uzair/Documents/AML_REACT_PROJECT/backend/app/integrations/abdm/fhir_mapper.py) (`CANONICAL_LOINC_MAP`):

| Clinical Domain | Internal Canonical Alias | LOINC Code | LOINC Long Common Name |
|---|---|:---:|---|
| **CBC** | `hemoglobin`, `hemoglobin (hb)`, `hgb` | `718-7` | Hemoglobin [Mass/volume] in Blood |
| **CBC** | `white blood cell count`, `wbc` | `6690-2` | Leukocytes [#/volume] in Blood by Automated count |
| **CBC** | `red blood cell count`, `rbc` | `789-8` | Erythrocytes [#/volume] in Blood by Automated count |
| **CBC** | `platelets`, `platelet count` | `777-3` | Platelets [#/volume] in Blood by Automated count |
| **CBC** | `hematocrit`, `hematocrit (pcv)`, `pcv` | `4544-3` | Hematocrit [Volume Fraction] of Blood by Automated count |
| **Diabetes / Metabolism** | `fasting blood glucose`, `fasting glucose`, `fbs` | `1558-6` | Fasting glucose [Mass/volume] in Serum or Plasma |
| **Diabetes / Metabolism** | `blood glucose`, `glucose` | `2345-7` | Glucose [Mass/volume] in Serum or Plasma |
| **Diabetes / Metabolism** | `hba1c`, `glycated hemoglobin (hba1c)` | `4548-4` | Hemoglobin A1c/Hemoglobin.total in Blood |
| **Lipid Panel** | `total cholesterol`, `cholesterol, total` | `2093-3` | Cholesterol [Mass/volume] in Serum or Plasma |
| **Lipid Panel** | `ldl cholesterol`, `ldl` | `13457-7` | Cholesterol in LDL [Mass/volume] in Serum or Plasma by calculation |
| **Lipid Panel** | `hdl cholesterol`, `hdl` | `2085-9` | Cholesterol in HDL [Mass/volume] in Serum or Plasma |
| **Lipid Panel** | `triglycerides`, `triglyceride` | `2571-8` | Triglyceride [Mass/volume] in Serum or Plasma |
| **Renal Panel** | `serum creatinine`, `creatinine` | `2160-0` | Creatinine [Mass/volume] in Serum or Plasma |
| **Renal Panel** | `bun`, `blood urea nitrogen`, `urea` | `3094-0` | Urea nitrogen [Mass/volume] in Serum or Plasma |
| **Renal Panel** | `egfr`, `estimated gfr` | `33914-3` | Glomerular filtration rate/1.73 sq M.predicted |
| **Liver Panel** | `alt`, `alanine aminotransferase (alt)`, `sgpt` | `1742-6` | Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma |
| **Liver Panel** | `ast`, `aspartate aminotransferase (ast)`, `sgot` | `1920-8` | Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma |
| **Liver Panel** | `total bilirubin`, `bilirubin total` | `1975-2` | Bilirubin.total [Mass/volume] in Serum or Plasma |
| **Liver Panel** | `direct bilirubin` | `1968-7` | Bilirubin.direct [Mass/volume] in Serum or Plasma |
| **Liver Panel** | `alkaline phosphatase`, `alp` | `6768-6` | Alkaline phosphatase [Enzymatic activity/volume] in Serum or Plasma |
| **Thyroid Panel** | `tsh`, `thyroid stimulating hormone (tsh)` | `3016-3` | Thyrotropin [Units/volume] in Serum or Plasma |
| **Thyroid Panel** | `free t3` | `3051-2` | Triiodothyronine.free [Mass/volume] in Serum or Plasma |
| **Thyroid Panel** | `free t4` | `3024-7` | Thyroxine.free [Mass/volume] in Serum or Plasma |
| **Electrolytes** | `serum calcium`, `calcium` | `17861-6` | Calcium [Mass/volume] in Serum or Plasma |
| **Electrolytes** | `serum potassium`, `potassium` | `2823-3` | Potassium [Moles/volume] in Serum or Plasma |
| **Electrolytes** | `serum sodium`, `sodium` | `2951-2` | Sodium [Moles/volume] in Serum or Plasma |

---

## 3. Emergency Red-Flag Detection & Triage Rules

Emergency screening executes across all patient-facing AI pathways before response delivery (`specialty_matcher.py` / `rag_engine.py`):

### 3.1 Keyword Patterns (`EMERGENCY_SYMPTOMS`)
The following verbatim strings trigger immediate emergency escalation when detected in patient intake text or Q&A queries:
1. `"chest pain"`
2. `"crushing pressure"`
3. `"shortness of breath"`
4. `"difficulty breathing"`
5. `"sudden numbness"`
6. `"facial droop"`
7. `"slurred speech"`
8. `"loss of consciousness"`
9. `"coughing blood"`
10. `"severe sudden headache"`
11. `"anaphylaxis"`
12. `"severe allergic reaction"`

### 3.2 Critical Biomarker Trigger
Any report containing a biomarker value that breaches `critical_low` or `critical_high` (e.g. Glucose $> 350\text{ mg/dL}$, Hemoglobin $< 7.0\text{ g/dL}$, Potassium $> 6.2\text{ mEq/L}$) immediately sets `is_emergency_flagged = True`.

### 3.3 Clinical Escalation Message
When triggered, the platform suppresses standard outpatient scheduling and displays the following emergency advisory banner:
> 🚨 **CRITICAL MEDICAL ALERT**: Your query mentions potential emergency symptoms. If you are experiencing chest pain, severe shortness of breath, sudden numbness, or acute distress, please contact emergency medical services (dial 112 / 911) or proceed to the nearest emergency room immediately.

---

## 4. Specialty-Matching Logic & Confidence Scoring

Specialty recommendation combines clinical rule overrides with TF-IDF natural language matching:

### 4.1 Biomarker-Driven Rule Overrides
When an uploaded report contains abnormal lab values, clinical rules take precedence:
* **Elevated Lipids** (Cholesterol, LDL, Triglycerides) $\longrightarrow$ **Cardiology**
* **Abnormal Glycemia or Thyroid** (Glucose, HbA1c, TSH) $\longrightarrow$ **Endocrinology**
* **Abnormal Cytopenias/Cytoses** (Hemoglobin, Platelets, WBC) $\longrightarrow$ **Hematology**
* **Elevated Transaminases / Bilirubin** (ALT, AST, Bilirubin) $\longrightarrow$ **Gastroenterology**
* **Renal Retention Markers** (Creatinine, BUN, eGFR) $\longrightarrow$ **Nephrology**

### 4.2 Natural Language Symptom Matching (`SPECIALTY_TAXONOMY`)
Symptom descriptions are vectorized via TF-IDF across 10 specialties:
* **Cardiology**: Palpitations, chest tightness, exertion dyspnea, hypertension, dizziness on standing.
* **Endocrinology**: Polydipsia, polyuria, unexplained weight loss, heat/cold intolerance, chronic fatigue.
* **Hematology**: Anemia, pallor, easy bruising, spontaneous bleeding, fatigue.
* **Gastroenterology**: Epigastric pain, acid reflux, jaundice, altered bowel habits, postprandial distress.
* **Nephrology**: Lower extremity edema, foamy urine, flank pain, oliguria.
* **Pulmonology**: Chronic cough, wheezing, hemoptysis, sputum production, asthma.
* **Dermatology**: Pruritus, rashes, erythema, eczema, suspicious skin lesions.
* **Neurology**: Migraine, neuropathic tingling, vertigo, focal tremors, limb weakness.
* **Orthopedics**: Arthralgia, joint swelling, restricted range of motion, mechanical back pain.
* **General Medicine**: Non-specific malaise, low-grade fever, seasonal allergies, routine wellness.

### 4.3 Confidence Calculation Formulas
* **Concordant Signal** (Lab rule agrees with NLP semantic match $\text{score} > 0.15$):  
  $$\text{Confidence} = \min(0.95, 0.70 + \text{CosineSimilarity})$$
* **Lab-Dominant Signal** (Lab abnormality present, symptom text unspecific $\le 0.10$):  
  $$\text{Confidence} = 0.88$$
* **Symptom-Dominant Signal** (Normal labs, strong symptom match $\text{score} > 0.20$):  
  $$\text{Confidence} = \min(0.92, 0.60 + \text{CosineSimilarity})$$
* **General Medicine Fallback**:  
  $$\text{Confidence} = 0.80$$

---

## 5. AI / RAG Safety Guardrails & Confidence Thresholds

### 5.1 The 0.70 Confidence Cutoff
> [!IMPORTANT]
> **Engineering Disclosure on 0.70 Threshold**:
> In Phase 9, a confidence score cutoff of **`0.70`** was implemented as the gating criterion between verified outputs and the physician review queue. **This 0.70 threshold was selected as an engineering heuristic** based on term overlap and token distribution. **It has not been calibrated against real clinical patient outcomes or diagnostic sensitivity curves.** Reviewing clinicians must evaluate whether this cutoff is sufficiently conservative or requires adjustment.

### 5.2 Review Queue Routing & Labeling
* Inferences scoring $< 0.70$ or containing ambiguous grounding are flagged with `review_status = "PENDING_REVIEW"`.
* The patient response is prepended with the mandatory disclaimer:
  > ⚠️ **CLINICAL NOTICE: UNREVIEWED AI RESPONSE**: This query has lower diagnostic confidence or ambiguous grounding in your current lab data. This item has been flagged for physician review in the clinical queue.

---

## 6. Catalog of Known Clinical Content Limitations & Gaps

The following clinical gaps have been surfaced across Phases 1–9 and require clinician evaluation:

1. **Empty Description Field in `biomarker_references`**:
   The live database contains blank `description` columns for all 16 canonical biomarkers. Plain-language summaries currently rely entirely on procedural templates in `explainer_ai.py`.
2. **Uniform Reference Ranges (Lack of Demographic Stratification)**:
   Reference intervals currently do not stratify by biological sex (e.g. separate male/female Hemoglobin reference intervals), age brackets (pediatric vs adult vs geriatric), or pregnancy trimesters.
3. **Absence of Unit Conversion Engine**:
   The platform assumes standard US units (`mg/dL`, `g/dL`). Uploaded reports utilizing SI units (e.g. `mmol/L` for Blood Glucose or Cholesterol) will fail threshold checks unless an automated unit-conversion layer is introduced.
4. **Fuzzy / Substring Fallback Matching**:
   Biomarkers not matching exact canonical strings fall back to token substring matching in OCR text, creating potential edge-case ambiguities.

---

## 7. Review Attribution & Schema Architecture

When a licensed clinician reviews and approves these clinical rules, the existing database schema natively records review attribution across the following tables:

* **`glossary_terms`**:
  * `reviewed_by` (`VARCHAR(255)`): Clinician license identifier / name.
  * `reviewed_at` (`TIMESTAMP WITH TIME ZONE`): Audit timestamp.
* **`specialty_recommendations`**:
  * `review_status` (`VARCHAR(50)`): `"REVIEWED_APPROVED"`, `"REVIEWED_MODIFIED"`, or `"PENDING_REVIEW"`.
  * `reviewed_by` (`VARCHAR(255)`): Reviewing physician ID.
  * `reviewed_at` (`TIMESTAMP WITH TIME ZONE`): Review timestamp.
* **`ai_interaction_logs`**:
  * `review_status` (`VARCHAR(50)`): Persists audit trail for all RAG and clinical inferences.

---

## 8. Clinician Sign-Off Instrument

*This section must be completed and signed by a licensed physician (MD / DO / MBBS or equivalent board-certified clinician).*

### Reviewer Information
* **Reviewer Full Name**: __________________________________________________
* **Professional Title**: __________________________________________________
* **Medical License Number & State/Country**: ______________________________
* **Institutional Affiliation**: ___________________________________________
* **Clinical Specialty**: _________________________________________________
* **Review Date**: ________________________________________________________

---

### Subsystem Review Checklist

#### 1. Biomarker Reference Ranges & Critical Thresholds (Section 1)
* [ ] **Approved** as clinically sound for adult outpatient triage.
* [ ] **Needs Modifications** (Specify below).
* [ ] **Rejected**.
* *Clinician Comments*:  
  _________________________________________________________________________
  _________________________________________________________________________

#### 2. LOINC Semantic Code Mappings (Section 2)
* [ ] **Approved** (All standard codes accurately reflect internal biomarkers).
* [ ] **Needs Modifications** (Specify below).
* [ ] **Rejected**.
* *Clinician Comments*:  
  _________________________________________________________________________
  _________________________________________________________________________

#### 3. Emergency Red-Flag Detection Rules (Section 3)
* [ ] **Approved** (Emergency symptom terms and critical biomarker thresholds are appropriate).
* [ ] **Needs Modifications** (List missing red-flag terms or adjust thresholds).
* [ ] **Rejected**.
* *Clinician Comments*:  
  _________________________________________________________________________
  _________________________________________________________________________

#### 4. Specialty-Matching Rules & Taxonomy (Section 4)
* [ ] **Approved** (Rule overrides and taxonomy keywords align with clinical referral standards).
* [ ] **Needs Modifications** (Specify below).
* [ ] **Rejected**.
* *Clinician Comments*:  
  _________________________________________________________________________
  _________________________________________________________________________

#### 5. AI / RAG Safety Guardrails & 0.70 Confidence Cutoff (Section 5)
* [ ] **Approved** (0.70 cutoff and unreviewed warning banner are clinically acceptable).
* [ ] **Needs Modifications** (Recommend alternative cutoff: ______).
* [ ] **Rejected**.
* *Clinician Comments*:  
  _________________________________________________________________________
  _________________________________________________________________________

---

### Formal Clinician Sign-Off Signature

I hereby confirm that I have reviewed the clinical decision logic, reference boundaries, emergency triage triggers, and semantic mappings set forth in this validation package.

* **Clinician Signature**: __________________________________________________
* **Date**: ________________________
