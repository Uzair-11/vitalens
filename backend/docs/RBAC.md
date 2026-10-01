# VitaLens Role-Based Access Control (RBAC) Permission Matrix

This document defines the official permission boundaries enforced across all API endpoints and database models in the VitaLens platform.

---

## 1. Role Hierarchy

* **`PATIENT`**: Standard registered user who uploads lab reports, receives non-diagnostic AI summaries, logs symptoms, discovers doctors, and books consultations.
* **`DOCTOR`**: Licensed healthcare practitioner with verified credentials who manages consultation availability, views consented patient records, updates appointment statuses, and records clinical consultation notes.
* **`SUPPORT_STAFF`**: Operational support member who assists with user onboarding, appointment conflict troubleshooting, and basic audit log monitoring.
* **`ADMIN`**: Platform administrator who verifies doctors, manages clinical reference thresholds, and reviews AI recommendation queues.
* **`SUPER_ADMIN`**: Full platform authority with unrestricted management and system maintenance access.

---

## 2. Resource Permission Matrix

| Resource / Endpoint | `PATIENT` | `DOCTOR` | `SUPPORT_STAFF` | `ADMIN` | `SUPER_ADMIN` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Auth: Register (Patient)** | ✅ Create | ❌ | ❌ | ❌ | ❌ |
| **Auth: Login / Refresh** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Auth: View/Update Own Profile**| ✅ (Own) | ✅ (Own) | ✅ (Own) | ✅ (Own) | ✅ (Own) |
| **Auth: DPDP Privacy Center (Consents/Export)**| ✅ (Own) | ❌ | ❌ | ❌ | ❌ |
| **Reports: Upload & Analyze** | ✅ (Own) | ❌ | ❌ | ❌ | ❌ |
| **Reports: List & View Details**| ✅ (Own) | ❌ | ❌ | ❌ | ❌ |
| **Reports: Delete Report** | ✅ (Own) | ❌ | ❌ | ❌ | ❌ |
| **AI: Symptom Intake & Recs** | ✅ (Own) | ❌ | ❌ | ❌ | ❌ |
| **AI: Report Q&A** | ✅ (Own) | ❌ | ❌ | ❌ | ❌ |
| **Doctors: Public Search & Directory** | ✅ Read | ✅ Read | ✅ Read | ✅ Read | ✅ Read |
| **Appointments: Book / Cancel (Patient)** | ✅ (Own) | ❌ | ❌ | ❌ | ❌ |
| **Appointments: Reschedule** | ✅ (Own) | ✅ (Own) | ✅ | ✅ | ✅ |
| **Doctor: View Own Dashboard (`/doctor/me`)**| ❌ | ✅ | ❌ | ❌ | ✅ |
| **Doctor: Manage Schedule (`/doctor/schedule`)**| ❌ | ✅ | ❌ | ❌ | ✅ |
| **Doctor: View Assigned Appts**| ❌ | ✅ (Assigned) | ❌ | ❌ | ✅ |
| **Doctor: Clinical Notes (`/notes`)**| ❌ | ✅ (Assigned) | ❌ | ❌ | ✅ |
| **Doctor: View Patient Chart (`/doctor/patients`)**| ❌ | ✅ (Consented/Active Appt) | ❌ | ❌ | ✅ |
| **Admin: Create & Verify Doctors**| ❌ | ❌ | ❌ | ✅ | ✅ |
| **Admin: Manage Patient Accounts**| ❌ | ❌ | ✅ (Read) | ✅ | ✅ |
| **Admin: Resolve Appointments** | ❌ | ❌ | ✅ (Read) | ✅ | ✅ |
| **Admin: Clinical Thresholds CRUD**| ❌ | ❌ | ❌ | ✅ | ✅ |
| **Admin: AI Review Queue** | ❌ | ❌ | ✅ (Read) | ✅ | ✅ |
| **Admin: Analytics Dashboard** | ❌ | ❌ | ✅ (Read) | ✅ | ✅ |

---

## 3. Resource-Level Authorization Rules

1. **Doctor-Patient Relationship Guard:**
   A user with role `DOCTOR` cannot query any patient's reports or medical profile unless there is an active or completed appointment in the database linking that doctor to the patient. Attempting to access an unlinked patient returns `HTTP 403 Forbidden`.
2. **Patient Data Isolation:**
   All queries for reports, biomarkers, appointments, and symptoms are filtered strictly by `current_user.id`.
3. **Public Registration Role Enforcement:**
   Public self-service registration (`POST /api/v1/auth/register`) only ever creates accounts with `role="PATIENT"`. Staff, Doctor, and Admin accounts can only be provisioned by an authenticated Admin.
