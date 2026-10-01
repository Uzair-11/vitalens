# VitaLens Privacy, Consent & Regulatory Compliance Technical Scaffolding

**Notice:** This document and the associated codebase represent the *technical mechanisms* developed to support digital personal data protection (DPDP) and clinical safety. This technical scaffolding is **NOT a substitute for formal legal, compliance, or clinical review**, and must be reviewed by qualified legal counsel and clinical compliance officers prior to production deployment with live patient data.

---

## 1. Implemented Technical Scaffolding

The following technical mechanisms and boundaries have been implemented, automated, and tested within Phase 5:

| Category | Technical Mechanism | Implementation Details |
| :--- | :--- | :--- |
| **Granular DPDP Consent Model** | `consents` table & ORM model | Tracks user consents for `REPORT_ANALYSIS`, `AI_PROCESSING`, `DOCTOR_DATA_ACCESS`, `NOTIFICATIONS`, and `MARKETING` with explicit `granted` booleans, `granted_at`, and `revoked_at` timestamps. |
| **Report Processing Gating** | `enforce_user_consent` check on `POST /reports/{id}/analyze` | Blocks automated OCR, biomarker extraction, range evaluation, and plain-English summaries unless active `REPORT_ANALYSIS` consent is granted. Returns specific HTTP 403 error. |
| **AI Feature Gating** | `enforce_user_consent` check on `POST /ai/symptoms`, `POST /ai/recommend-specialty`, `POST /ai/qa` | Blocks symptom logging, hybrid specialty matching, and grounded report Q&A unless active `AI_PROCESSING` consent is granted. |
| **Doctor-Patient Access Dual-Gate** | Two-gate authorization on `GET /doctor/patients/{id}` | Access strictly requires **both** an active/completed appointment relationship via `verify_doctor_patient_relationship()` **and** active `DOCTOR_DATA_ACCESS` patient consent via `verify_user_consent()`. |
| **Privacy Center Endpoints** | `GET /api/v1/me/consents` & `PATCH /api/v1/me/consents/{type}` | Enables patients to view and toggle granular consent preferences at any time. Every change is timestamped and audit-logged. |
| **Right to Data Portability** | `GET /api/v1/me/data-export` | Generates a complete, structured JSON export of patient profile, uploaded reports, extracted biomarkers, AI analyses, symptom logs, appointments, consultation notes, and consent history strictly scoped to the requesting user (zero cross-tenant leakage). |
| **Right to Erasure / Soft Delete** | `POST /api/v1/me/delete-account` | Soft-deletes user profile (`is_deleted = True`, `is_active = False`), blocks future logins, and immediately revokes all active refresh tokens in the database. |
| **Immutable Audit Logging** | `record_audit_log()` | Records actor user ID, action (`GRANT_CONSENT`, `REVOKE_CONSENT`, `EXPORT_USER_DATA`, `DELETE_ACCOUNT_REQUESTED`, `VIEW_PATIENT_CHART`), resource type, resource ID, and metadata for every compliance-relevant event. |

---

## 2. Needs Legal / Compliance Review

The following items are outside automated technical scope and **require formal legal, operational, and regulatory review**:

1. **Data Localization Mandate:**
   - Formal verification that production cloud storage (AWS S3 / GCP Cloud Storage) and database hosting instances are provisioned within Indian jurisdiction (e.g., AWS Asia Pacific Mumbai `ap-south-1` or GCP Delhi/Mumbai) to satisfy Indian health data residency laws.
2. **Designated DPDP Grievance Officer & Contact Publication:**
   - Formal corporate appointment of a Data Protection Officer (DPO) / Grievance Officer under the Digital Personal Data Protection Act (DPDPA), 2023.
   - Publication of official name, designation, physical address, and grievance redressal email in the public Terms of Service and Privacy Policy.
3. **Regulatory Breach Notification Protocol:**
   - Establishing standard operating procedures (SOPs) and operational runbooks for mandatory 72-hour notifications to the Data Protection Board of India (DPBI) and affected individuals in the event of any security or data incident.
4. **ABDM Alignment & HIP/HIU Certification:**
   - Alignment with Ayushman Bharat Digital Mission (ABDM) Milestone 1, 2, and 3 certifications (Ayushman Bharat Health Account / ABHA issuance, Health Information Provider, and Health Information User bridging).
5. **Patient-Facing Legal Copy & Consent Notices:**
   - Legal review and sign-off on user-facing consent descriptions, plain-language privacy notices, and terms of service displayed within the mobile and web client interfaces.
