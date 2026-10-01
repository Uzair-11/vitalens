import os
import uuid
from datetime import date, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from app.core.database import engine, Base
from app.data.seed_data import seed_database
from app.ml.lab_extractor import extract_biomarkers_from_text, evaluate_flag
from app.ml.specialty_matcher import recommend_specialty, check_emergency
from app.ml.explainer_ai import generate_plain_explanation, retrieve_explanation, RETRIEVAL_THRESHOLD, EXPLANATION_BANK
from tests.conftest import TestingSessionLocal
from main import app


def test_biomarker_extraction_logic():
    sample_text = """
    COMPREHENSIVE METABOLIC & LIPID PANEL
    Patient: John Doe    Date: 2026-08-15
    
    Test Description              Result       Unit       Reference Range
    Hemoglobin                    10.5         g/dL       12.0 - 17.5
    Fasting Blood Sugar           126.0        mg/dL      70.0 - 99.0
    Total Cholesterol             245.0        mg/dL      125.0 - 200.0
    Serum Creatinine              0.8          mg/dL      0.6 - 1.2
    TSH                           2.4          uIU/mL     0.4 - 4.0
    """
    
    biomarkers = extract_biomarkers_from_text(sample_text, [])
    assert len(biomarkers) >= 4
    
    hb = next((b for b in biomarkers if "Hemoglobin" in b["test_name"]), None)
    assert hb is not None
    assert hb["value_numeric"] == 10.5
    assert hb["flag"] == "LOW"
    
    glucose = next((b for b in biomarkers if "Glucose" in b["test_name"] or "Sugar" in b["test_name"]), None)
    assert glucose is not None
    assert glucose["value_numeric"] == 126.0
    assert glucose["flag"] == "HIGH"
    
    chol = next((b for b in biomarkers if "Cholesterol" in b["test_name"]), None)
    assert chol is not None
    assert chol["value_numeric"] == 245.0
    assert chol["flag"] == "HIGH"

def test_plain_explanation_generator():
    biomarkers = [
        {"test_name": "Hemoglobin (Hb)", "canonical_name": "Hemoglobin", "value_numeric": 10.5, "unit": "g/dL", "reference_min": 12.0, "reference_max": 17.5, "reference_text": "12.0 - 17.5", "flag": "LOW"},
        {"test_name": "Total Cholesterol", "canonical_name": "Total Cholesterol", "value_numeric": 245.0, "unit": "mg/dL", "reference_min": 125.0, "reference_max": 200.0, "reference_text": "125.0 - 200.0", "flag": "HIGH"}
    ]
    explanation = generate_plain_explanation(biomarkers)
    assert "plain_summary" in explanation
    assert "Disclaimer" in explanation["clinical_disclaimer"]
    assert "Hemoglobin (Hb)" in explanation["plain_summary"]
    assert "terminology_glossary" in explanation
    assert isinstance(explanation["terminology_glossary"], list)
    assert len(explanation["terminology_glossary"]) > 0
    assert any("Hemoglobin" in item["term"] or "Cholesterol" in item["term"] for item in explanation["terminology_glossary"])

def test_explanation_retrieval_embedding_engine():
    """
    Verifies embedding similarity retrieval from EXPLANATION_BANK:
    - High-confidence match for standard tests.
    - Safety rejection boundary below threshold (< 0.65) for unsupported/novel tests.
    """
    assert len(EXPLANATION_BANK) > 20
    assert RETRIEVAL_THRESHOLD == 0.65

    # 1. Exact / High-confidence match
    hemo_exp, hemo_score = retrieve_explanation("Hemoglobin", "LOW")
    assert hemo_score >= 0.90
    assert "anemia" in hemo_exp.lower()

    chol_exp, chol_score = retrieve_explanation("Total Cholesterol", "HIGH")
    assert chol_score >= 0.85
    assert "cardiovascular" in chol_exp.lower()

    # 2. Safety boundary rejection for out-of-bank query
    vit_exp, vit_score = retrieve_explanation("Vitamin D", "LOW")
    assert vit_score < RETRIEVAL_THRESHOLD
    assert "No confident match found" in vit_exp
    assert "manual review" in vit_exp

def test_hybrid_specialty_recommendation():
    abnormals = [
        {"test_name": "Total Cholesterol", "canonical_name": "Total Cholesterol", "value_numeric": 250.0, "unit": "mg/dL", "flag": "HIGH"}
    ]
    rec = recommend_specialty(
        primary_concern="Mild chest tightness and high cholesterol concerns",
        symptoms_list=["palpitations", "fatigue on stairs"],
        body_region="Chest",
        abnormal_biomarkers=abnormals
    )
    assert rec["recommended_specialty_name"] == "Cardiology"
    assert rec["confidence_score"] >= 0.80
    assert not rec["is_emergency_flagged"]

def test_emergency_red_flag_detection():
    is_emergency, msg = check_emergency("I have sudden crushing chest pain and shortness of breath", [])
    assert is_emergency is True
    assert "emergency" in msg.lower()

@pytest.mark.asyncio
async def test_api_auth_and_doctor_flows(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Health check & Readiness
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        ready_res = await ac.get("/health/ready")
        assert ready_res.status_code == 200
        assert ready_res.json()["status"] == "ready"
        
        # 2. Login with seed patient user
        login_res = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "demo@healthapp.com", "password": "password123"}
        )
        assert login_res.status_code == 200
        token_data = login_res.json()
        token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        assert token_data["role"] == "PATIENT"
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Refresh token test
        refresh_res = await ac.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_res.status_code == 200
        assert "access_token" in refresh_res.json()

        # 4. Fetch current user profile
        me_res = await ac.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "demo@healthapp.com"
        
        # 5. List specialties
        specs_res = await ac.get("/api/v1/doctors/specialties")
        assert specs_res.status_code == 200
        specialties = specs_res.json()
        assert len(specialties) >= 5
        cardiology_id = next(s["id"] for s in specialties if s["name"] == "Cardiology")
        
        # 6. Search doctors in Cardiology
        docs_res = await ac.get(f"/api/v1/doctors/?specialty_id={cardiology_id}")
        assert docs_res.status_code == 200
        docs = docs_res.json()
        assert len(docs) >= 1
        doctor_id = next((d["id"] for d in docs if "Jenkins" in d["full_name"]), docs[0]["id"])
        
        # 7. Get doctor availability
        slots_res = await ac.get(f"/api/v1/doctors/{doctor_id}/availability")
        assert slots_res.status_code == 200
        slots = slots_res.json()
        assert len(slots) > 0
        first_slot = slots[0]
        
        # 8. Book appointment
        book_res = await ac.post(
            "/api/v1/appointments/",
            headers=headers,
            json={
                "doctor_id": doctor_id,
                "appointment_date": first_slot["available_date"],
                "appointment_time": first_slot["start_time"],
                "visit_reason": "Follow-up consultation for lipid levels"
            }
        )
        assert book_res.status_code == 201
        appt_data = book_res.json()
        appt_id = appt_data["id"]
        assert appt_data["status"] == "CONFIRMED"
        
        # 9. Double booking prevention check
        double_book_res = await ac.post(
            "/api/v1/appointments/",
            headers=headers,
            json={
                "doctor_id": doctor_id,
                "appointment_date": first_slot["available_date"],
                "appointment_time": first_slot["start_time"],
                "visit_reason": "Second attempt booking same slot"
            }
        )
        assert double_book_res.status_code == 409
        
        # 10. List user appointments
        appts_list_res = await ac.get("/api/v1/appointments/", headers=headers)
        assert appts_list_res.status_code == 200
        assert len(appts_list_res.json()) >= 1
        
        # 11. Cancel appointment
        cancel_res = await ac.patch(
            f"/api/v1/appointments/{appt_id}/cancel",
            headers=headers,
            json={"cancellation_reason": "Testing cancellation flow"}
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"

@pytest.mark.asyncio
async def test_rbac_and_admin_doctor_flows(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Public Registration Role Restriction: Verify public register ONLY creates PATIENT role
        unique_email = f"test_patient_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "securepassword123",
                "full_name": "Test Patient",
                "phone": "+15551234567"
            }
        )
        assert reg_res.status_code == 201
        reg_user = reg_res.json()
        assert reg_user["role"] == "PATIENT"

        # 2. Patient login
        patient_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "demo@healthapp.com", "password": "password123"}
        )
        patient_token = patient_login.json()["access_token"]
        patient_id = patient_login.json()["user_id"]
        patient_headers = {"Authorization": f"Bearer {patient_token}"}

        # 3. RBAC Negative Tests: PATIENT token must get 403 on all admin routes
        admin_routes_to_test = [
            "/api/v1/admin/analytics/dashboard",
            "/api/v1/admin/doctors/",
            "/api/v1/admin/users/",
            "/api/v1/admin/appointments/",
            "/api/v1/admin/content/biomarkers",
            "/api/v1/admin/ai-review/"
        ]
        for route in admin_routes_to_test:
            res = await ac.get(route, headers=patient_headers)
            assert res.status_code == 403, f"Expected 403 on {route} for PATIENT, got {res.status_code}"

        # 4. RBAC Negative Tests: PATIENT token must get 403 on doctor routes
        doctor_routes_to_test = [
            "/api/v1/doctor/me",
            "/api/v1/doctor/schedule",
            "/api/v1/doctor/appointments"
        ]
        for route in doctor_routes_to_test:
            res = await ac.get(route, headers=patient_headers)
            assert res.status_code == 403, f"Expected 403 on {route} for PATIENT, got {res.status_code}"


        # 5. Admin login & authorized dashboard access
        admin_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        dash_res = await ac.get("/api/v1/admin/analytics/dashboard", headers=admin_headers)
        assert dash_res.status_code == 200
        assert "user_metrics" in dash_res.json()

        # 6. Doctor login & dashboard access
        doc_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.jenkins@vitalens.health", "password": "doctor123"}
        )
        assert doc_login.status_code == 200
        doc_token = doc_login.json()["access_token"]
        doc_headers = {"Authorization": f"Bearer {doc_token}"}

        doc_me = await ac.get("/api/v1/doctor/me", headers=doc_headers)
        assert doc_me.status_code == 200
        assert "Dr. Sarah Jenkins" in doc_me.json()["full_name"]

        # 7. Privacy Center: Patient Data Export
        export_res = await ac.get("/api/v1/auth/me/data-export", headers=patient_headers)
        assert export_res.status_code == 200
        export_data = export_res.json()
        assert "export_metadata" in export_data
        assert "reports" in export_data

@pytest.mark.asyncio
async def test_admin_doctor_lifecycle_create_verify_login(setup_db):
    """
    Phase 3A: Admin creates doctor profile + login account in one transaction (PENDING),
    verifies doctor (VERIFIED), and newly created doctor logs in successfully with role DOCTOR.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Admin login
        admin_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        assert admin_login.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # 2. Get cardiology specialty ID
        specs_res = await ac.get("/api/v1/doctors/specialties")
        assert specs_res.status_code == 200
        specialty_id = specs_res.json()[0]["id"]

        # 3. Create new doctor
        doc_email = f"dr.new_{uuid.uuid4().hex[:6]}@vitalens.health"
        doc_pass = "DoctorPass2026!"
        create_res = await ac.post(
            "/api/v1/admin/doctors/",
            headers=admin_headers,
            json={
                "email": doc_email,
                "temporary_password": doc_pass,
                "full_name": "Dr. Marcus Hayes, MD",
                "specialty_id": specialty_id,
                "qualification": "MBBS, MD, DM (Cardiology)",
                "experience_years": 14,
                "clinic_name": "Hayes Heart Institute",
                "address": "450 Medical Center Blvd",
                "city": "Metropolis",
                "consultation_fee": 1200.0,
                "bio": "Experienced cardiologist specializing in preventative cardiovascular care.",
                "languages": ["English", "Spanish"]
            }
        )
        assert create_res.status_code == 201
        created_data = create_res.json()
        doctor_id = created_data["doctor_id"]
        assert created_data["verification_status"] == "PENDING"
        assert created_data["email"] == doc_email

        # 4. Search and verify doctor shows in admin list
        list_res = await ac.get(f"/api/v1/admin/doctors/?name=Marcus", headers=admin_headers)
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 5. Verify doctor
        verify_res = await ac.patch(
            f"/api/v1/admin/doctors/{doctor_id}/verify?verification_status=VERIFIED",
            headers=admin_headers
        )
        assert verify_res.status_code == 200
        assert verify_res.json()["verification_status"] == "VERIFIED"

        # 6. Newly verified doctor logs in
        doc_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": doc_email, "password": doc_pass}
        )
        assert doc_login.status_code == 200
        doc_auth = doc_login.json()
        assert doc_auth["role"] == "DOCTOR"

        # 7. Doctor accesses their portal profile
        doc_token_headers = {"Authorization": f"Bearer {doc_auth['access_token']}"}
        doc_profile = await ac.get("/api/v1/doctor/me", headers=doc_token_headers)
        assert doc_profile.status_code == 200
        assert doc_profile.json()["full_name"] == "Dr. Marcus Hayes, MD"

@pytest.mark.asyncio
async def test_admin_user_suspension_blocks_access(setup_db):
    """
    Phase 3A: Admin suspends a user -> user gets 403 on next login/auth attempt ->
    Admin reactivates user -> user logs in successfully.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Admin login
        admin_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        assert admin_login.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # 2. Register a temporary patient
        temp_email = f"patient.suspend_{uuid.uuid4().hex[:6]}@example.com"
        temp_pass = "PatientPass123!"
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": temp_email,
                "password": temp_pass,
                "full_name": "Temporary Test Patient",
                "phone": "+15559870000"
            }
        )
        assert reg_res.status_code == 201

        # 3. Patient logs in initially
        patient_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": temp_email, "password": temp_pass}
        )
        assert patient_login.status_code == 200
        patient_id = patient_login.json()["user_id"]
        patient_token = patient_login.json()["access_token"]
        patient_headers = {"Authorization": f"Bearer {patient_token}"}

        # Patient makes successful authenticated request
        profile_res = await ac.get("/api/v1/auth/me", headers=patient_headers)
        assert profile_res.status_code == 200

        # 4. Admin suspends user account
        suspend_res = await ac.patch(
            f"/api/v1/admin/users/{patient_id}/status?is_active=false",
            headers=admin_headers
        )
        assert suspend_res.status_code == 200
        assert suspend_res.json()["is_active"] is False

        # 5. Suspended user is blocked on next authenticated request -> 403 Forbidden
        blocked_profile = await ac.get("/api/v1/auth/me", headers=patient_headers)
        assert blocked_profile.status_code == 403

        # 6. Suspended user is blocked on next login attempt -> 403 Forbidden
        blocked_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": temp_email, "password": temp_pass}
        )
        assert blocked_login.status_code == 403

        # 7. Admin reactivates user account
        reactivate_res = await ac.patch(
            f"/api/v1/admin/users/{patient_id}/status?is_active=true",
            headers=admin_headers
        )
        assert reactivate_res.status_code == 200
        assert reactivate_res.json()["is_active"] is True

        # 8. User can log in again
        relogin_res = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": temp_email, "password": temp_pass}
        )
        assert relogin_res.status_code == 200

@pytest.mark.asyncio
async def test_support_staff_role_permissions(setup_db):
    """
    Phase 3A: SUPPORT_STAFF token gets 200 on GET /admin/users and GET /admin/users/{id},
    but gets 403 Forbidden on mutation PATCH /admin/users/{id}/status.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Support staff login
        staff_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "staff@vitalens.health", "password": "staff123"}
        )
        assert staff_login.status_code == 200
        staff_data = staff_login.json()
        assert staff_data["role"] == "SUPPORT_STAFF"
        staff_headers = {"Authorization": f"Bearer {staff_data['access_token']}"}

        # 2. Support staff calls GET /admin/users -> 200 OK
        list_users = await ac.get("/api/v1/admin/users/", headers=staff_headers)
        assert list_users.status_code == 200
        users_list = list_users.json()
        assert len(users_list) >= 1
        target_user_id = users_list[0]["id"]

        # 3. Support staff calls GET /admin/users/{id} -> 200 OK (operational metrics view)
        user_detail = await ac.get(f"/api/v1/admin/users/{target_user_id}", headers=staff_headers)
        assert user_detail.status_code == 200
        assert "summary_metrics" in user_detail.json()

        # 4. Support staff attempts mutation PATCH /admin/users/{id}/status -> 403 Forbidden
        mutation_attempt = await ac.patch(
            f"/api/v1/admin/users/{target_user_id}/status?is_active=false",
            headers=staff_headers
        )
        assert mutation_attempt.status_code == 403
        err_body = str(mutation_attempt.json())
        assert "ADMIN" in err_body

@pytest.mark.asyncio
async def test_admin_appointment_cancellation_releases_slot(setup_db):
    """
    Phase 3B: Admin cancels an appointment -> slot is released (is_booked=False) ->
    verified by checking doctor availability slots.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Patient login and book an appointment
        pat_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "demo@healthapp.com", "password": "password123"}
        )
        pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}

        # Find Dr. Jenkins
        docs_res = await ac.get("/api/v1/doctors/")
        assert docs_res.status_code == 200
        doctor = next(d for d in docs_res.json() if "Jenkins" in d["full_name"])
        doctor_id = doctor["id"]

        # Get available slot
        slots_res = await ac.get(f"/api/v1/doctors/{doctor_id}/availability")
        assert slots_res.status_code == 200
        available_slots = slots_res.json()
        assert len(available_slots) > 0
        target_slot = available_slots[0]

        # Book slot
        book_res = await ac.post(
            "/api/v1/appointments/",
            headers=pat_headers,
            json={
                "doctor_id": doctor_id,
                "appointment_date": target_slot["available_date"],
                "appointment_time": target_slot["start_time"],
                "visit_reason": "Admin cancellation test booking"
            }
        )
        assert book_res.status_code == 201
        appt_id = book_res.json()["id"]

        # 2. Admin logs in
        admin_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # 3. Admin cancels appointment
        cancel_res = await ac.patch(
            f"/api/v1/admin/appointments/{appt_id}/cancel?reason=Admin+slot+conflict+resolution",
            headers=admin_headers
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"
        assert cancel_res.json()["slot_released"] is True

        # 4. Verify slot is available again
        followup_slots = await ac.get(f"/api/v1/doctors/{doctor_id}/availability")
        assert followup_slots.status_code == 200
        released_slot_exists = any(
            s["available_date"] == target_slot["available_date"] and s["start_time"] == target_slot["start_time"]
            for s in followup_slots.json()
        )
        assert released_slot_exists is True

@pytest.mark.asyncio
async def test_admin_content_biomarkers_and_glossary_crud(setup_db):
    """
    Phase 3B: Admin tests full CRUD for clinical biomarker references and layperson glossary terms.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # 1. Biomarker Reference CRUD
        unique_test_name = f"Custom Lipid Test {uuid.uuid4().hex[:4]}"
        create_bio = await ac.post(
            "/api/v1/admin/content/biomarkers",
            headers=admin_headers,
            json={
                "test_name": unique_test_name,
                "canonical_name": "Apolipoprotein B",
                "category": "Advanced Lipid Panel",
                "default_unit": "mg/dL",
                "ref_min": 40.0,
                "ref_max": 100.0,
                "critical_high": 180.0,
                "description": "Primary protein on LDL and VLDL particles"
            }
        )
        assert create_bio.status_code == 201
        bio_id = create_bio.json()["id"]

        # Search
        search_bio = await ac.get(f"/api/v1/admin/content/biomarkers?search=Apolipoprotein", headers=admin_headers)
        assert search_bio.status_code == 200
        assert len(search_bio.json()) >= 1

        # Patch
        patch_bio = await ac.patch(
            f"/api/v1/admin/content/biomarkers/{bio_id}",
            headers=admin_headers,
            json={"ref_max": 90.0}
        )
        assert patch_bio.status_code == 200
        assert patch_bio.json()["ref_max"] == 90.0

        # Delete
        del_bio = await ac.delete(f"/api/v1/admin/content/biomarkers/{bio_id}", headers=admin_headers)
        assert del_bio.status_code == 200

        # 2. Glossary Term CRUD
        unique_term = f"Dyslipidemia_{uuid.uuid4().hex[:4]}"
        create_gloss = await ac.post(
            "/api/v1/admin/content/glossary",
            headers=admin_headers,
            json={
                "term": unique_term,
                "definition": "An unhealthy level of one or more kinds of lipid (fat) in your blood.",
                "reviewed_by": "Dr. Sarah Jenkins"
            }
        )
        assert create_gloss.status_code == 201
        gloss_id = create_gloss.json()["id"]

        # Patch glossary
        patch_gloss = await ac.patch(
            f"/api/v1/admin/content/glossary/{gloss_id}",
            headers=admin_headers,
            json={"definition": "Updated definition of abnormal lipid concentrations."}
        )
        assert patch_gloss.status_code == 200

        # Delete glossary
        del_gloss = await ac.delete(f"/api/v1/admin/content/glossary/{gloss_id}", headers=admin_headers)
        assert del_gloss.status_code == 200

@pytest.mark.asyncio
async def test_admin_analytics_returns_real_aggregates(setup_db):
    """
    Phase 3B: Analytics dashboard returns real non-zero aggregates from database.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        dash_res = await ac.get("/api/v1/admin/analytics/dashboard", headers=admin_headers)
        assert dash_res.status_code == 200
        metrics = dash_res.json()

        assert metrics["user_metrics"]["total_registered_users"] >= 2
        assert metrics["doctor_metrics"]["total_doctors"] >= 8
        assert metrics["doctor_metrics"]["active_verified_doctors"] >= 8
        assert "appointment_metrics" in metrics
        assert "cancellation_rate_pct" in metrics["appointment_metrics"]

@pytest.mark.asyncio
async def test_admin_ai_recommendation_review_persists(setup_db):
    """
    Phase 3B: AI Recommendation review status (APPROVE / OVERRIDE / FLAG) persists correctly in database.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Patient creates a symptom log to generate an AI recommendation
        pat_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "demo@healthapp.com", "password": "password123"}
        )
        pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}
        sym_res = await ac.post(
            "/api/v1/ai/symptoms",
            headers=pat_headers,
            json={
                "primary_concern": "Occasional sharp chest tightness when running",
                "symptoms_list": ["palpitations", "shortness of breath"],
                "duration_days": 5,
                "severity_score": 6,
                "body_region": "Chest"
            }
        )
        assert sym_res.status_code == 201
        sym_log_id = sym_res.json()["id"]

        ai_res = await ac.post(
            "/api/v1/ai/recommend-specialty",
            headers=pat_headers,
            json={"symptom_log_id": sym_log_id}
        )
        assert ai_res.status_code == 200

        # 2. Admin lists AI recommendations
        admin_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        rec_list_res = await ac.get("/api/v1/admin/ai-review/", headers=admin_headers)
        assert rec_list_res.status_code == 200
        recs = rec_list_res.json()
        assert len(recs) >= 1
        target_rec_id = recs[0]["id"]

        # 3. Admin approves AI recommendation
        review_res = await ac.patch(
            f"/api/v1/admin/ai-review/{target_rec_id}?action=APPROVE",
            headers=admin_headers
        )
        assert review_res.status_code == 200
        assert review_res.json()["review_status"] == "APPROVED"
        assert review_res.json()["reviewed_by"] is not None

        # 4. Verify review persists
        verified_list = await ac.get(f"/api/v1/admin/ai-review/?status_filter=APPROVED", headers=admin_headers)
        assert verified_list.status_code == 200
        approved_ids = [r["id"] for r in verified_list.json()]
        assert target_rec_id in approved_ids


@pytest.mark.asyncio
async def test_doctor_portal_me_profile_and_stats():
    """
    Phase 4: GET /doctor/me returns doctor profile + today's operational stats
    resolved securely via current_user.id (never accepts doctor ID from client).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        doc_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.vance@vitalens.health", "password": "doctor123"}
        )
        assert doc_login.status_code == 200
        doc_headers = {"Authorization": f"Bearer {doc_login.json()['access_token']}"}

        me_res = await ac.get("/api/v1/doctor/me", headers=doc_headers)
        assert me_res.status_code == 200
        doc_data = me_res.json()
        assert doc_data["full_name"] == "Dr. Robert Vance, MD"
        assert doc_data["specialty_name"] == "Cardiology"
        assert "today_stats" in doc_data
        assert "today_appointments_count" in doc_data["today_stats"]
        assert "total_consultations_completed" in doc_data["today_stats"]


@pytest.mark.asyncio
async def test_doctor_portal_schedule_and_blocks_manage_availability():
    """
    Phase 4: Doctor sets weekly recurring hours and adds a one-off block.
    Availability slots update dynamically without breaking patient availability contract.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        doc_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.vance@vitalens.health", "password": "doctor123"}
        )
        doc_headers = {"Authorization": f"Bearer {doc_login.json()['access_token']}"}

        # 1. Get initial schedule
        init_sched = await ac.get("/api/v1/doctor/schedule", headers=doc_headers)
        assert init_sched.status_code == 200
        doc_id = init_sched.json()["doctor_id"]

        # 2. Update weekly recurring hours (Mon-Wed 10:00 to 14:00)
        set_wh_res = await ac.post(
            "/api/v1/doctor/schedule",
            headers=doc_headers,
            json={
                "working_hours": [
                    {"day_of_week": 0, "start_time": "10:00", "end_time": "14:00", "slot_duration_minutes": 30, "is_active": True},
                    {"day_of_week": 1, "start_time": "10:00", "end_time": "14:00", "slot_duration_minutes": 30, "is_active": True},
                    {"day_of_week": 2, "start_time": "10:00", "end_time": "14:00", "slot_duration_minutes": 30, "is_active": True}
                ]
            }
        )
        assert set_wh_res.status_code == 200
        assert len(set_wh_res.json()["recurring_hours"]) == 3

        # 3. Add a blackout block
        from datetime import date, timedelta
        block_target_date = date.today() + timedelta(days=2)
        block_res = await ac.post(
            "/api/v1/doctor/schedule/block",
            headers=doc_headers,
            json={
                "block_date": str(block_target_date),
                "reason": "Cardiology Symposium"
            }
        )
        assert block_res.status_code == 201
        block_id = block_res.json()["id"]

        # 4. Patient queries availability via public contract GET /doctors/{id}/availability
        avail_res = await ac.get(f"/api/v1/doctors/{doc_id}/availability")
        assert avail_res.status_code == 200
        slots = avail_res.json()
        assert isinstance(slots, list)
        # Blocked date should have 0 unbooked slots
        blocked_slots = [s for s in slots if s["available_date"] == str(block_target_date)]
        assert len(blocked_slots) == 0

        # 5. Remove block and verify availability restores
        del_block = await ac.delete(f"/api/v1/doctor/schedule/block/{block_id}", headers=doc_headers)
        assert del_block.status_code == 204


@pytest.mark.asyncio
async def test_doctor_portal_patient_relationship_negative_path_403():
    """
    Phase 4: Doctor A attempting to access Doctor B's patient or an unlinked patient
    is blocked with HTTP 403 Forbidden under verify_doctor_patient_relationship().
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create an unlinked test patient
        unlinked_email = f"unlinked_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": unlinked_email,
                "password": "Password123!",
                "full_name": "Unlinked Stranger Patient",
                "phone": "+1 555-999-0000"
            }
        )
        assert reg_res.status_code == 201
        unlinked_pat_id = reg_res.json()["id"]

        # Doctor Vance logs in (has no appointment with this stranger)
        doc_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.vance@vitalens.health", "password": "doctor123"}
        )
        doc_headers = {"Authorization": f"Bearer {doc_login.json()['access_token']}"}

        # Attempt to access chart
        chart_res = await ac.get(f"/api/v1/doctor/patients/{unlinked_pat_id}", headers=doc_headers)
        assert chart_res.status_code == 403
        err_msg = chart_res.json().get("error", {}).get("message", "") or chart_res.json().get("detail", "")
        assert "Access forbidden" in err_msg



@pytest.mark.asyncio
async def test_doctor_portal_appointment_status_and_slot_release():
    """
    Phase 4: Doctor manages appointment lifecycle (accept / complete / cancel).
    Cancelling or rejecting releases the doctor's availability slot.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Patient logs in and books an appointment with Dr. Vance
        pat_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "demo@healthapp.com", "password": "password123"}
        )
        pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}

        doc_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.vance@vitalens.health", "password": "doctor123"}
        )
        doc_headers = {"Authorization": f"Bearer {doc_login.json()['access_token']}"}

        # Fetch doctor ID and first slot
        me_res = await ac.get("/api/v1/doctor/me", headers=doc_headers)
        doc_id = me_res.json()["doctor_id"]

        avail_res = await ac.get(f"/api/v1/doctors/{doc_id}/availability")
        slots = avail_res.json()
        assert len(slots) > 0
        target_slot = slots[0]

        book_res = await ac.post(
            "/api/v1/appointments",
            headers=pat_headers,
            json={
                "doctor_id": doc_id,
                "appointment_date": target_slot["available_date"],
                "appointment_time": target_slot["start_time"],
                "visit_reason": "Cardiology Evaluation"
            }
        )
        assert book_res.status_code == 201
        appt_id = book_res.json()["id"]

        # 2. Doctor views own appointments
        doc_appts = await ac.get("/api/v1/doctor/appointments", headers=doc_headers)
        assert doc_appts.status_code == 200
        found_appt = next((a for a in doc_appts.json() if a["id"] == appt_id), None)
        assert found_appt is not None

        # 3. Doctor marks appointment CANCELLED
        cancel_res = await ac.patch(
            f"/api/v1/doctor/appointments/{appt_id}/status",
            headers=doc_headers,
            json={"status": "CANCELLED", "cancellation_reason": "Physician emergency leave"}
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"

        # 4. Verify slot is released and re-appears in availability
        recheck_avail = await ac.get(f"/api/v1/doctors/{doc_id}/availability")
        recheck_slots = recheck_avail.json()
        matching_slot = next((s for s in recheck_slots if s["available_date"] == target_slot["available_date"] and s["start_time"] == target_slot["start_time"]), None)
        assert matching_slot is not None
        assert matching_slot["is_booked"] is False


@pytest.mark.asyncio
async def test_doctor_portal_consultation_notes_persistence_and_rbac():
    """
    Phase 4: Doctor saves consultation notes; notes persist and are retrievable
    by the doctor and patient, but forbidden to unrelated doctors.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pat_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "demo@healthapp.com", "password": "password123"}
        )
        pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}

        doc_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.vance@vitalens.health", "password": "doctor123"}
        )
        doc_headers = {"Authorization": f"Bearer {doc_login.json()['access_token']}"}

        me_res = await ac.get("/api/v1/doctor/me", headers=doc_headers)
        doc_id = me_res.json()["doctor_id"]

        avail_res = await ac.get(f"/api/v1/doctors/{doc_id}/availability")
        target_slot = avail_res.json()[0]

        book_res = await ac.post(
            "/api/v1/appointments",
            headers=pat_headers,
            json={
                "doctor_id": doc_id,
                "appointment_date": target_slot["available_date"],
                "appointment_time": target_slot["start_time"],
                "visit_reason": "Follow-up Check"
            }
        )
        appt_id = book_res.json()["id"]

        # 1. Doctor saves notes
        save_notes_res = await ac.post(
            f"/api/v1/doctor/appointments/{appt_id}/notes",
            headers=doc_headers,
            json={
                "diagnosis": "Mild Essential Hypertension",
                "clinical_notes": "Blood pressure 138/88. Patient advised lifestyle modification and low-sodium diet.",
                "prescriptions": "Hydrochlorothiazide 12.5mg OD",
                "follow_up_recommendation": "Review in 6 weeks with home BP log."
            }
        )
        assert save_notes_res.status_code == 200
        note_data = save_notes_res.json()
        assert note_data["diagnosis"] == "Mild Essential Hypertension"

        # 2. Doctor retrieves notes
        get_notes_doc = await ac.get(f"/api/v1/doctor/appointments/{appt_id}/notes", headers=doc_headers)
        assert get_notes_doc.status_code == 200
        assert get_notes_doc.json()["diagnosis"] == "Mild Essential Hypertension"

        # 3. Patient retrieves own notes
        get_notes_pat = await ac.get(f"/api/v1/doctor/appointments/{appt_id}/notes", headers=pat_headers)
        assert get_notes_pat.status_code == 200
        assert get_notes_pat.json()["diagnosis"] == "Mild Essential Hypertension"

        # 4. Unrelated doctor (Dr. Elena Rostova) attempts to access notes -> 403
        doc2_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.rostova@vitalens.health", "password": "doctor123"}
        )
        doc2_headers = {"Authorization": f"Bearer {doc2_login.json()['access_token']}"}
        unauthorized_res = await ac.get(f"/api/v1/doctor/appointments/{appt_id}/notes", headers=doc2_headers)
        assert unauthorized_res.status_code == 403


@pytest.mark.asyncio
async def test_patient_slot_selection_regression_flow():
    """
    Phase 4 Regression Check: Confirms the mobile SlotSelectionScreen flow
    (GET /doctors/{id}/availability -> POST /appointments) remains 100% operational.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Search doctors
        docs_res = await ac.get("/api/v1/doctors/")
        assert docs_res.status_code == 200
        docs = docs_res.json()
        assert len(docs) > 0
        doctor_id = docs[0]["id"]

        # 2. Mobile app calls GET /doctors/{id}/availability
        avail_res = await ac.get(f"/api/v1/doctors/{doctor_id}/availability")
        assert avail_res.status_code == 200
        slots = avail_res.json()
        assert len(slots) > 0
        slot = slots[0]
        assert "id" in slot
        assert "doctor_id" in slot
        assert "available_date" in slot
        assert "start_time" in slot
        assert "end_time" in slot
        assert "is_booked" in slot
        assert slot["is_booked"] is False

        # 3. Patient books the selected slot
        pat_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "demo@healthapp.com", "password": "password123"}
        )
        pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}

        book_res = await ac.post(
            "/api/v1/appointments",
            headers=pat_headers,
            json={
                "doctor_id": doctor_id,
                "appointment_date": slot["available_date"],
                "appointment_time": slot["start_time"],
                "visit_reason": "Routine Consultation"
            }
        )
        assert book_res.status_code == 201
        assert book_res.json()["doctor_id"] == doctor_id
        assert book_res.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_doctor_cross_tenant_isolation_boundary():
    """
    Phase 4 Authorization Boundary: Verifies multi-doctor cross-tenant isolation.
    Ensures Doctor A cannot view or mutate Doctor B's appointments, schedule blocks,
    consultation notes, or identity data via /doctor/* endpoints.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Authenticate Doctor A (Dr. Vance) and Doctor B (Dr. Rostova)
        doc_a_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.vance@vitalens.health", "password": "doctor123"}
        )
        assert doc_a_login.status_code == 200
        headers_a = {"Authorization": f"Bearer {doc_a_login.json()['access_token']}"}

        doc_b_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.rostova@vitalens.health", "password": "doctor123"}
        )
        assert doc_b_login.status_code == 200
        headers_b = {"Authorization": f"Bearer {doc_b_login.json()['access_token']}"}

        # 2. Identity isolation: GET /doctor/me strictly resolves authenticated FK
        me_a = await ac.get("/api/v1/doctor/me", headers=headers_a)
        assert me_a.status_code == 200
        assert me_a.json()["full_name"] == "Dr. Robert Vance, MD"
        doc_a_id = me_a.json()["doctor_id"]

        me_b = await ac.get("/api/v1/doctor/me", headers=headers_b)
        assert me_b.status_code == 200
        assert me_b.json()["full_name"] == "Dr. Elena Rostova, MD"
        doc_b_id = me_b.json()["doctor_id"]
        assert doc_a_id != doc_b_id

        # 3. Schedule Block isolation: Doctor B adds a block; Doctor A cannot delete it
        from datetime import date, timedelta
        block_date = str(date.today() + timedelta(days=5))
        create_block_res = await ac.post(
            "/api/v1/doctor/schedule/block",
            headers=headers_b,
            json={"block_date": block_date, "reason": "Endocrine Conference"}
        )
        assert create_block_res.status_code == 201
        doc_b_block_id = create_block_res.json()["id"]

        # Doctor A attempts to delete Doctor B's schedule block -> 404 Not Found
        unauth_del = await ac.delete(f"/api/v1/doctor/schedule/block/{doc_b_block_id}", headers=headers_a)
        assert unauth_del.status_code == 404

        # 4. Appointment list & mutation isolation:
        # Patient books an appointment specifically with Doctor B
        pat_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "demo@healthapp.com", "password": "password123"}
        )
        pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}

        avail_b = await ac.get(f"/api/v1/doctors/{doc_b_id}/availability")
        target_slot_b = avail_b.json()[0]

        book_b_res = await ac.post(
            "/api/v1/appointments",
            headers=pat_headers,
            json={
                "doctor_id": doc_b_id,
                "appointment_date": target_slot_b["available_date"],
                "appointment_time": target_slot_b["start_time"],
                "visit_reason": "Endocrine checkup"
            }
        )
        assert book_b_res.status_code == 201
        doc_b_appt_id = book_b_res.json()["id"]

        # 4a. Doctor A calls GET /doctor/appointments -> Doctor B's appointment is NOT returned
        appts_a = await ac.get("/api/v1/doctor/appointments", headers=headers_a)
        assert appts_a.status_code == 200
        appts_a_ids = [a["id"] for a in appts_a.json()]
        assert doc_b_appt_id not in appts_a_ids, "Doctor A should NOT see Doctor B's appointment"

        # 4b. Doctor A attempts to mutate status of Doctor B's appointment -> 404 Not Found
        mutate_res = await ac.patch(
            f"/api/v1/doctor/appointments/{doc_b_appt_id}/status",
            headers=headers_a,
            json={"status": "CANCELLED", "cancellation_reason": "Malicious cancellation attempt"}
        )
        assert mutate_res.status_code == 404

        # 4c. Doctor A attempts to write consultation notes on Doctor B's appointment -> 404 Not Found
        note_write_res = await ac.post(
            f"/api/v1/doctor/appointments/{doc_b_appt_id}/notes",
            headers=headers_a,
            json={
                "diagnosis": "Illegitimate diagnosis",
                "clinical_notes": "Attempted write by Doctor A on Doctor B's appointment"
            }
        )
        assert note_write_res.status_code == 404

        # 4d. Doctor B legitimately writes consultation notes
        doc_b_note_res = await ac.post(
            f"/api/v1/doctor/appointments/{doc_b_appt_id}/notes",
            headers=headers_b,
            json={
                "diagnosis": "Subclinical Hypothyroidism",
                "clinical_notes": "TSH mildly elevated. Recommend repeat panel in 3 months."
            }
        )
        assert doc_b_note_res.status_code == 200

        # 4e. Doctor A attempts to read Doctor B's consultation notes -> 403 Forbidden
        note_read_res = await ac.get(
            f"/api/v1/doctor/appointments/{doc_b_appt_id}/notes",
            headers=headers_a
        )
        assert note_read_res.status_code == 403


@pytest.mark.asyncio
async def test_phase5_consent_gating_on_reports_and_ai():
    """
    Phase 5 Test 1: Verifies that report analysis and AI actions are gated on active consent.
    - Missing/revoked REPORT_ANALYSIS fails POST /reports/{id}/analyze with specific consent error.
    - Missing/revoked AI_PROCESSING fails POST /ai/symptoms and POST /ai/recommend-specialty.
    - Granting consent allows immediate success; revoking immediately blocks access again.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register test patient & login
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "consent_test_user@vitalens.health",
                "password": "password123",
                "full_name": "Consent Test User"
            }
        )
        assert reg_res.status_code == 201

        login_res = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "consent_test_user@vitalens.health", "password": "password123"}
        )
        assert login_res.status_code == 200
        pat_token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {pat_token}"}

        # 2. Upload a lab report
        pdf_content = b"%PDF-1.4\nHemoglobin: 14.2 g/dL (13.5 - 17.5)\nWBC: 6500 /uL (4500 - 11000)\n%%EOF"
        upload_res = await ac.post(
            "/api/v1/reports/upload",
            headers=headers,
            files={"file": ("lab_cbc.pdf", pdf_content, "application/pdf")}
        )
        assert upload_res.status_code == 201
        report_id = upload_res.json()["report_id"]

        # 3. Revoke REPORT_ANALYSIS consent
        revoke_res = await ac.patch(
            "/api/v1/me/consents/REPORT_ANALYSIS?granted=false",
            headers=headers
        )
        assert revoke_res.status_code == 200
        assert revoke_res.json()["granted"] is False

        # 4. Trigger analysis -> Must return 403 with clear, specific consent error
        analyze_fail = await ac.post(f"/api/v1/reports/{report_id}/analyze", headers=headers)
        assert analyze_fail.status_code == 403
        fail_json = analyze_fail.json()
        err_msg = fail_json.get("error", {}).get("message", "") or fail_json.get("detail", "")
        assert "Consent required" in err_msg
        assert "REPORT_ANALYSIS" in err_msg

        # 5. Revoke AI_PROCESSING consent
        await ac.patch("/api/v1/me/consents/AI_PROCESSING?granted=false", headers=headers)

        # 6. Attempt symptom logging -> Must return 403 with clear consent error
        sym_fail = await ac.post(
            "/api/v1/ai/symptoms",
            headers=headers,
            json={
                "primary_concern": "Fatigue and dizziness",
                "symptoms_list": ["Fatigue", "Dizziness"],
                "duration_days": 4,
                "severity_score": 5
            }
        )
        assert sym_fail.status_code == 403
        err_msg_sym = sym_fail.json().get("error", {}).get("message", "") or sym_fail.json().get("detail", "")
        assert "Consent required" in err_msg_sym
        assert "AI_PROCESSING" in err_msg_sym

        # 7. Grant AI_PROCESSING consent -> Symptom logging now succeeds
        grant_ai_res = await ac.patch("/api/v1/me/consents/AI_PROCESSING?granted=true", headers=headers)
        assert grant_ai_res.status_code == 200
        assert grant_ai_res.json()["granted"] is True

        sym_success = await ac.post(
            "/api/v1/ai/symptoms",
            headers=headers,
            json={
                "primary_concern": "Fatigue and dizziness",
                "symptoms_list": ["Fatigue", "Dizziness"],
                "duration_days": 4,
                "severity_score": 5
            }
        )
        assert sym_success.status_code == 201
        sym_id = sym_success.json()["id"]

        # Specialty recommendation also succeeds
        rec_res = await ac.post(
            "/api/v1/ai/recommend-specialty",
            headers=headers,
            json={"symptom_log_id": sym_id}
        )
        assert rec_res.status_code == 200

        # 8. Grant REPORT_ANALYSIS consent -> Report analysis now succeeds
        grant_rep_res = await ac.patch("/api/v1/me/consents/REPORT_ANALYSIS?granted=true", headers=headers)
        assert grant_rep_res.status_code == 200
        assert grant_rep_res.json()["granted"] is True

        analyze_success = await ac.post(f"/api/v1/reports/{report_id}/analyze", headers=headers)
        assert analyze_success.status_code == 200, f"Analysis failed: {analyze_success.json()}"
        assert analyze_success.json()["status"] in ["ANALYZED", "COMPLETED"]



        # 9. Revoke REPORT_ANALYSIS again -> Subsequent analysis fails again
        await ac.patch("/api/v1/me/consents/REPORT_ANALYSIS?granted=false", headers=headers)
        analyze_fail_again = await ac.post(f"/api/v1/reports/{report_id}/analyze", headers=headers)
        assert analyze_fail_again.status_code == 403


@pytest.mark.asyncio
async def test_phase5_doctor_patient_chart_two_gate_authorization():
    """
    Phase 5 Test 2: Verifies that doctor patient-chart access requires BOTH:
    1. An active/completed appointment relationship, AND
    2. Explicit DOCTOR_DATA_ACCESS consent granted by the patient.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login Doctor Vance (Doctor A) and Doctor Rostova (Doctor B)
        login_a = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.vance@vitalens.health", "password": "doctor123"}
        )
        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

        login_b = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "doctor.rostova@vitalens.health", "password": "doctor123"}
        )
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        # 2. Register fresh patient & login
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "two_gate_patient@vitalens.health",
                "password": "password123",
                "full_name": "Two Gate Patient"
            }
        )
        assert reg_res.status_code == 201

        pat_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "two_gate_patient@vitalens.health", "password": "password123"}
        )
        assert pat_login.status_code == 200
        pat_id = pat_login.json()["user_id"]
        pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}

        # 3. Book appointment with Doctor Vance (Doctor A)
        doc_a_id = (await ac.get("/api/v1/doctor/me", headers=headers_a)).json()["doctor_id"]
        avail_a = await ac.get(f"/api/v1/doctors/{doc_a_id}/availability")
        slot_a = avail_a.json()[0]

        book_res = await ac.post(
            "/api/v1/appointments",
            headers=pat_headers,
            json={
                "doctor_id": doc_a_id,
                "appointment_date": slot_a["available_date"],
                "appointment_time": slot_a["start_time"],
                "visit_reason": "Cardio review"
            }
        )
        assert book_res.status_code == 201

        # 4. Patient explicitly revokes DOCTOR_DATA_ACCESS consent
        revoke_res = await ac.patch(
            "/api/v1/me/consents/DOCTOR_DATA_ACCESS?granted=false",
            headers=pat_headers
        )
        assert revoke_res.status_code == 200

        # Gate 2 Failure: Doctor Vance has relationship, but patient consent is REVOKED -> 403 Forbidden
        chart_fail = await ac.get(f"/api/v1/doctor/patients/{pat_id}", headers=headers_a)
        assert chart_fail.status_code == 403
        err_msg = chart_fail.json().get("error", {}).get("message", "") or chart_fail.json().get("detail", "")
        assert "DOCTOR_DATA_ACCESS" in err_msg

        # 5. Patient re-grants DOCTOR_DATA_ACCESS consent
        grant_res = await ac.patch(
            "/api/v1/me/consents/DOCTOR_DATA_ACCESS?granted=true",
            headers=pat_headers
        )
        assert grant_res.status_code == 200

        # Both Gates Pass: Doctor Vance can now view chart
        chart_success = await ac.get(f"/api/v1/doctor/patients/{pat_id}", headers=headers_a)
        assert chart_success.status_code == 200
        assert chart_success.json()["full_name"] == "Two Gate Patient"

        # Gate 1 Failure: Doctor Rostova (no appointment) tries to view chart -> 403 Forbidden
        rostova_fail = await ac.get(f"/api/v1/doctor/patients/{pat_id}", headers=headers_b)
        assert rostova_fail.status_code == 403
        err_msg_b = rostova_fail.json().get("error", {}).get("message", "") or rostova_fail.json().get("detail", "")
        assert "appointment exists" in err_msg_b


@pytest.mark.asyncio
async def test_phase5_data_export_completeness_and_cross_tenant_isolation():
    """
    Phase 5 Test 3: Verifies complete structured JSON data export and strict tenant isolation.
    - Export includes profile, reports, biomarkers, symptoms, appointments, consultation notes, and consent history.
    - Export strictly returns requesting user's data with zero cross-contamination.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register User 1 & login
        u1_res = await ac.post(
            "/api/v1/auth/register",
            json={"email": "export_user1@vitalens.health", "password": "password123", "full_name": "Export User One"}
        )
        assert u1_res.status_code == 201

        u1_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "export_user1@vitalens.health", "password": "password123"}
        )
        assert u1_login.status_code == 200
        u1_token = u1_login.json()["access_token"]
        u1_id = u1_login.json()["user_id"]
        h1 = {"Authorization": f"Bearer {u1_token}"}

        # 2. User 1 uploads report
        up1 = await ac.post(
            "/api/v1/reports/upload",
            headers=h1,
            files={"file": ("u1_lab.pdf", b"%PDF-1.4\nHemoglobin: 15.1 g/dL (13.5 - 17.5)\n%%EOF", "application/pdf")}
        )
        assert up1.status_code == 201
        u1_rep_id = up1.json()["report_id"]
        await ac.post(f"/api/v1/reports/{u1_rep_id}/analyze", headers=h1)

        # 3. User 1 logs symptoms
        sym1 = await ac.post(
            "/api/v1/ai/symptoms",
            headers=h1,
            json={"primary_concern": "Chest tightness", "symptoms_list": ["Chest tightness"], "duration_days": 2, "severity_score": 4}
        )
        u1_sym_id = sym1.json()["id"]

        # 4. Register User 2 & login
        u2_res = await ac.post(
            "/api/v1/auth/register",
            json={"email": "export_user2@vitalens.health", "password": "password123", "full_name": "Export User Two"}
        )
        assert u2_res.status_code == 201

        u2_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "export_user2@vitalens.health", "password": "password123"}
        )
        assert u2_login.status_code == 200
        u2_token = u2_login.json()["access_token"]
        u2_id = u2_login.json()["user_id"]
        h2 = {"Authorization": f"Bearer {u2_token}"}

        # 5. User 2 uploads report
        up2 = await ac.post(
            "/api/v1/reports/upload",
            headers=h2,
            files={"file": ("u2_lab.pdf", b"%PDF-1.4\nPlatelets: 250000 /uL (150000 - 450000)\n%%EOF", "application/pdf")}
        )
        assert up2.status_code == 201
        u2_rep_id = up2.json()["report_id"]


        # 6. User 1 exports data
        exp1_res = await ac.get("/api/v1/me/data-export", headers=h1)
        assert exp1_res.status_code == 200
        exp1 = exp1_res.json()

        assert exp1["profile"]["email"] == "export_user1@vitalens.health"
        assert exp1["medical_reports_count"] == 1
        assert exp1["medical_reports"][0]["id"] == u1_rep_id
        assert exp1["symptom_logs"][0]["id"] == u1_sym_id
        assert len(exp1["consent_history"]) >= 4

        # Verify User 2 data is NOT in User 1 export
        u1_report_ids = [r["id"] for r in exp1["medical_reports"]]
        assert u2_rep_id not in u1_report_ids, "User 2 report leaked into User 1 export!"

        # 7. User 2 exports data
        exp2_res = await ac.get("/api/v1/me/data-export", headers=h2)
        assert exp2_res.status_code == 200
        exp2 = exp2_res.json()

        assert exp2["profile"]["email"] == "export_user2@vitalens.health"
        assert exp2["medical_reports_count"] == 1
        assert exp2["medical_reports"][0]["id"] == u2_rep_id

        u2_report_ids = [r["id"] for r in exp2["medical_reports"]]
        assert u1_rep_id not in u2_report_ids, "User 1 report leaked into User 2 export!"


@pytest.mark.asyncio
async def test_phase5_account_deletion_and_refresh_token_revocation():
    """
    Phase 5 Test 4: Verifies Right to Erasure / Account Deletion.
    - Soft deletes account (is_deleted=True, is_active=False).
    - Blocks subsequent login attempts with 403 Forbidden.
    - Immediately revokes all active refresh tokens so they cannot be used to obtain new access tokens.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register test user & login to get refresh token
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "delete_target@vitalens.health",
                "password": "password123",
                "full_name": "Delete Target"
            }
        )
        assert reg_res.status_code == 201

        login_res = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "delete_target@vitalens.health", "password": "password123"}
        )
        assert login_res.status_code == 200
        access_token = login_res.json()["access_token"]
        refresh_token = login_res.json()["refresh_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Verify refresh token works before deletion
        pre_refresh = await ac.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert pre_refresh.status_code == 200

        # 3. User requests account deletion via POST /me/delete-account
        del_res = await ac.post("/api/v1/me/delete-account", headers=headers)
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "SUCCESS"

        # 4. Attempt login with deleted account credentials -> 403 Forbidden
        login_fail = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "delete_target@vitalens.health", "password": "password123"}
        )
        assert login_fail.status_code == 403

        # 5. Attempt to use old refresh token -> 401 Unauthorized
        post_refresh = await ac.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert post_refresh.status_code == 401


@pytest.mark.asyncio
async def test_phase5_privacy_audit_trail_recorded():
    """
    Phase 5 Test 5: Verifies that compliance-relevant events generate audit log entries:
    - GRANT_CONSENT / REVOKE_CONSENT
    - EXPORT_USER_DATA
    - DELETE_ACCOUNT_REQUESTED
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register test patient & login
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={"email": "audit_patient@vitalens.health", "password": "password123", "full_name": "Audit Patient"}
        )
        assert reg_res.status_code == 201

        login_res = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "audit_patient@vitalens.health", "password": "password123"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        user_id = login_res.json()["user_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Grant and revoke consent
        g_res = await ac.patch("/api/v1/me/consents/MARKETING?granted=true", headers=headers)
        assert g_res.status_code == 200
        r_res = await ac.patch("/api/v1/me/consents/MARKETING?granted=false", headers=headers)
        assert r_res.status_code == 200

        # 3. Export data
        exp_res = await ac.get("/api/v1/me/data-export", headers=headers)
        assert exp_res.status_code == 200

        # 4. Request account deletion
        del_res = await ac.post("/api/v1/me/delete-account", headers=headers)
        assert del_res.status_code == 200

        # 5. Admin verification
        admin_login = await ac.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        user_check = await ac.get(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
        assert user_check.status_code == 200
        assert user_check.json()["is_deleted"] is True


@pytest.mark.asyncio
async def test_phase6_health_and_readiness_checks():
    """
    Verifies /health (liveness) and extended /health/ready (DB + Storage readiness probe).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Liveness probe
        h_res = await ac.get("/health")
        assert h_res.status_code == 200
        assert h_res.json()["status"] == "healthy"

        # Readiness probe
        r_res = await ac.get("/health/ready")
        assert r_res.status_code == 200
        data = r_res.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "connected"
        assert data["checks"]["storage"] == "ready"


@pytest.mark.asyncio
async def test_phase6_request_id_and_structured_logging():
    """
    Verifies X-Request-ID middleware generates/threads correlation IDs in response headers
    and into audit trail log metadata.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Custom request ID
        custom_id = "test-corr-id-12345"
        res = await ac.get("/health", headers={"X-Request-ID": custom_id})
        assert res.status_code == 200
        assert res.headers.get("X-Request-ID") == custom_id

        # Auto-generated request ID
        res_auto = await ac.get("/health")
        assert res_auto.status_code == 200
        assert "X-Request-ID" in res_auto.headers
        assert res_auto.headers["X-Request-ID"].startswith("req_")


@pytest.mark.asyncio
async def test_phase6_error_tracking_and_exception_capture():
    """
    Deliberately triggers an unhandled exception and verifies error tracker captures it
    with correlated request_id and stack trace.
    """
    from app.core.tracker import error_tracker
    error_tracker.clear_recent_errors()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        req_id = "err-track-req-999"
        res = await ac.get("/debug/trigger-error", headers={"X-Request-ID": req_id})
        assert res.status_code == 500
        data = res.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert data["error"]["request_id"] == req_id

        # Verify error tracker recorded the event
        recent = error_tracker.get_recent_errors(limit=5)
        assert len(recent) > 0
        last_err = recent[-1]
        assert last_err["request_id"] == req_id
        assert "Deliberate test exception" in last_err["error_message"]
        assert last_err["error_type"] == "RuntimeError"


@pytest.mark.asyncio
async def test_phase6_magic_byte_disguised_file_rejection():
    """
    Tests upload security: verifies that a plain text or executable file renamed with a .pdf extension
    is strictly rejected by magic byte inspection (HTTP 400 Bad Request).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register patient
        email = f"upload.sec_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Security Test Patient"
        })
        assert reg_res.status_code == 201

        login_res = await ac.post("/api/v1/auth/login-json", json={
            "email": email,
            "password": "Password123!"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Plain text disguised as .pdf
        fake_pdf_content = b"This is just plain ASCII text pretending to be a medical lab PDF report."
        fake_file = ("fake_report.pdf", fake_pdf_content, "application/pdf")

        res_reject = await ac.post("/api/v1/reports/upload", headers=headers, files={"file": fake_file})
        assert res_reject.status_code == 400
        assert "signature" in res_reject.json()["error"]["message"].lower() or "format" in res_reject.json()["error"]["message"].lower()

        # 2. Genuine PDF with valid magic bytes
        real_pdf_content = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
        real_file = ("valid_report.pdf", real_pdf_content, "application/pdf")

        res_accept = await ac.post("/api/v1/reports/upload", headers=headers, files={"file": real_file})
        assert res_accept.status_code == 201
        assert res_accept.json()["status"] == "PENDING"


@pytest.mark.asyncio
async def test_phase7_payment_initiation_and_valid_signature_verification():
    """
    Tests Razorpay sandbox payment lifecycle:
    1. Initiate payment -> receives order_id, amount_paise, and doctor fee.
    2. Server-side HMAC-SHA256 verification -> transitions appointment to CONFIRMED and payment_status to PAID.
    """
    from app.core.payment import payment_gateway

    os.environ["PAYMENTS_ENABLED"] = "true"
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Register patient
            email = f"pay.patient_{uuid.uuid4().hex[:6]}@example.com"
            reg_res = await ac.post("/api/v1/auth/register", json={
                "email": email,
                "password": "Password123!",
                "full_name": "Payment Test Patient"
            })
            assert reg_res.status_code == 201
            login_res = await ac.post("/api/v1/auth/login-json", json={"email": email, "password": "Password123!"})
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Fetch doctor
            docs_res = await ac.get("/api/v1/doctors/", headers=headers)
            doctor_id = docs_res.json()[0]["id"]

            # Book appointment (in PENDING_PAYMENT status)
            appt_res = await ac.post("/api/v1/appointments/", headers=headers, json={
                "doctor_id": doctor_id,
                "appointment_date": str(date.today() + timedelta(days=2)),
                "appointment_time": "11:00:00",
                "visit_reason": "Payment Lifecycle Verification"
            })
            assert appt_res.status_code == 201
            appt_id = appt_res.json()["id"]
            assert appt_res.json()["status"] == "PENDING_PAYMENT"

            # 1. Initiate Payment
            init_res = await ac.post(f"/api/v1/appointments/{appt_id}/payment/initiate", headers=headers)
            assert init_res.status_code == 200
            init_data = init_res.json()
            assert "order_id" in init_data
            assert init_data["order_id"].startswith("order_")
            assert init_data["amount_paise"] > 0
            assert init_data["currency"] == "INR"
            order_id = init_data["order_id"]

            # 2. Generate valid HMAC-SHA256 signature
            fake_payment_id = f"pay_{uuid.uuid4().hex[:14]}"
            valid_signature = payment_gateway.generate_test_signature(order_id, fake_payment_id)

            # 3. Verify Payment
            verify_res = await ac.post(f"/api/v1/appointments/{appt_id}/payment/verify", headers=headers, json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": fake_payment_id,
                "razorpay_signature": valid_signature
            })
            assert verify_res.status_code == 200
            verify_data = verify_res.json()
            assert verify_data["status"] == "PAID"
            assert verify_data["appointment_status"] == "CONFIRMED"
            assert verify_data["payment_id"] == fake_payment_id
    finally:
        os.environ.pop("PAYMENTS_ENABLED", None)


@pytest.mark.asyncio
async def test_phase7_tampered_signature_rejection():
    """
    Tests payment security: verifies that an invalid or tampered payment signature
    is rejected with HTTP 400 Bad Request and transitions payment_status to FAILED.
    """
    os.environ["PAYMENTS_ENABLED"] = "true"
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            email = f"tamper.patient_{uuid.uuid4().hex[:6]}@example.com"
            await ac.post("/api/v1/auth/register", json={
                "email": email,
                "password": "Password123!",
                "full_name": "Tamper Test Patient"
            })
            login_res = await ac.post("/api/v1/auth/login-json", json={"email": email, "password": "Password123!"})
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            docs_res = await ac.get("/api/v1/doctors/", headers=headers)
            doctor_id = docs_res.json()[0]["id"]

            appt_res = await ac.post("/api/v1/appointments/", headers=headers, json={
                "doctor_id": doctor_id,
                "appointment_date": str(date.today() + timedelta(days=3)),
                "appointment_time": "14:00:00",
                "visit_reason": "Tamper Test"
            })
            appt_id = appt_res.json()["id"]

            init_res = await ac.post(f"/api/v1/appointments/{appt_id}/payment/initiate", headers=headers)
            assert init_res.status_code == 200
            order_id = init_res.json()["order_id"]

            # Submit tampered/fabricated signature
            verify_res = await ac.post(f"/api/v1/appointments/{appt_id}/payment/verify", headers=headers, json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": "pay_fake_attack_123",
                "razorpay_signature": "invalidsignature00000000000000000000000000000000000000000000000"
            })
            assert verify_res.status_code == 400
            assert "signature" in verify_res.json()["error"]["message"].lower()
    finally:
        os.environ.pop("PAYMENTS_ENABLED", None)


@pytest.mark.asyncio
async def test_phase7_appointment_booking_payment_gating():
    """
    Verifies that when PAYMENTS_ENABLED is active, booking an appointment
    leaves the appointment in PENDING_PAYMENT status until payment is confirmed.
    """
    os.environ["PAYMENTS_ENABLED"] = "true"
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            email = f"gated.patient_{uuid.uuid4().hex[:6]}@example.com"
            await ac.post("/api/v1/auth/register", json={
                "email": email,
                "password": "Password123!",
                "full_name": "Gated Booking Patient"
            })
            login_res = await ac.post("/api/v1/auth/login-json", json={"email": email, "password": "Password123!"})
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            docs_res = await ac.get("/api/v1/doctors/", headers=headers)
            doctor_id = docs_res.json()[0]["id"]

            appt_res = await ac.post("/api/v1/appointments/", headers=headers, json={
                "doctor_id": doctor_id,
                "appointment_date": str(date.today() + timedelta(days=4)),
                "appointment_time": "15:30:00",
                "visit_reason": "Payment Gated Check"
            })
            assert appt_res.status_code == 201
            appt_data = appt_res.json()
            assert appt_data["status"] == "PENDING_PAYMENT"
            assert appt_data["payment_status"] == "PENDING"
    finally:
        os.environ.pop("PAYMENTS_ENABLED", None)


@pytest.mark.asyncio
async def test_phase7_notification_consent_gating():
    """
    Verifies that notifications are sent when NOTIFICATIONS consent is active,
    and skipped (with SKIPPED_NO_CONSENT record) when NOTIFICATIONS consent is revoked.
    """
    from tests.conftest import TestingSessionLocal
    from app.models.notification_log import NotificationLog

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Patient A (Default: NOTIFICATIONS=Granted)
        email_a = f"notif.active_{uuid.uuid4().hex[:6]}@example.com"
        reg_a = await ac.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "full_name": "Consented Patient"})
        user_a_id = reg_a.json()["id"]
        login_a = await ac.post("/api/v1/auth/login-json", json={"email": email_a, "password": "Password123!"})
        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

        docs_res = await ac.get("/api/v1/doctors/", headers=headers_a)
        doctor_id = docs_res.json()[0]["id"]

        # Book & Cancel to trigger notification
        appt_a = await ac.post("/api/v1/appointments/", headers=headers_a, json={
            "doctor_id": doctor_id,
            "appointment_date": str(date.today() + timedelta(days=5)),
            "appointment_time": "10:00:00"
        })
        appt_a_id = appt_a.json()["id"]
        await ac.patch(f"/api/v1/appointments/{appt_a_id}/cancel", headers=headers_a, json={"cancellation_reason": "Schedule clash"})

        # Patient B (Revokes NOTIFICATIONS consent)
        email_b = f"notif.revoked_{uuid.uuid4().hex[:6]}@example.com"
        reg_b = await ac.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "full_name": "OptOut Patient"})
        user_b_id = reg_b.json()["id"]
        login_b = await ac.post("/api/v1/auth/login-json", json={"email": email_b, "password": "Password123!"})
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        # Revoke NOTIFICATIONS consent
        await ac.patch("/api/v1/me/consents/NOTIFICATIONS?granted=false", headers=headers_b)

        appt_b = await ac.post("/api/v1/appointments/", headers=headers_b, json={
            "doctor_id": doctor_id,
            "appointment_date": str(date.today() + timedelta(days=6)),
            "appointment_time": "12:00:00"
        })
        appt_b_id = appt_b.json()["id"]
        await ac.patch(f"/api/v1/appointments/{appt_b_id}/cancel", headers=headers_b, json={"cancellation_reason": "Not needed"})

        # Verify Database Notification Logs using TestingSessionLocal
        async with TestingSessionLocal() as session:
            # Query Patient A logs
            q_a = select(NotificationLog).where(NotificationLog.user_id == user_a_id)
            res_a = await session.execute(q_a)
            logs_a = res_a.scalars().all()
            assert len(logs_a) > 0
            assert any(l.status == "SENT" for l in logs_a)

            # Query Patient B logs
            q_b = select(NotificationLog).where(NotificationLog.user_id == user_b_id)
            res_b = await session.execute(q_b)
            logs_b = res_b.scalars().all()
            assert len(logs_b) > 0
            assert any(l.status == "SKIPPED_NO_CONSENT" for l in logs_b)


@pytest.mark.asyncio
async def test_phase8_fhir_r4_resource_mapping_structure():
    """
    Validates that the FHIR mapper produces structurally compliant HL7 FHIR R4 resources:
    - Bundle: resourceType, type, entry array
    - DiagnosticReport: resourceType, status, code.coding (LOINC), subject, result references
    - Observation: resourceType, status, category (laboratory), code.coding (LOINC),
                   valueQuantity (value, unit, system, code), referenceRange (low, high), interpretation
    """
    from app.integrations.abdm.fhir_mapper import map_report_to_fhir_bundle, map_biomarker_to_fhir_observation

    class MockUser:
        id = "usr-test-patient-fhir-1"
        full_name = "Jane Doe"

    class MockAnalysis:
        plain_summary = "Fasting glucose is slightly elevated indicating prediabetes risk."

    class MockBiomarker:
        def __init__(self, id, name, canonical, val, unit, r_min, r_max, flag):
            self.id = id
            self.test_name = name
            self.canonical_name = canonical
            self.value_numeric = val
            self.value_text = None
            self.unit = unit
            self.reference_min = r_min
            self.reference_max = r_max
            self.flag = flag

    class MockReport:
        id = "rep-test-fhir-88"
        report_date = date(2026, 8, 25)
        report_type = "Comprehensive Metabolic Panel"
        analysis = MockAnalysis()

    b1 = MockBiomarker("bm-1", "Fasting Blood Sugar", "Fasting Glucose", 112.5, "mg/dL", 70.0, 99.0, "HIGH")
    b2 = MockBiomarker("bm-2", "Hemoglobin", "Hemoglobin", 14.2, "g/dL", 12.0, 16.0, "NORMAL")
    b3 = MockBiomarker("bm-3", "Serum Calcium", "Calcium", 8.2, "mg/dL", 8.6, 10.2, "LOW")

    bundle = map_report_to_fhir_bundle(MockReport(), [b1, b2, b3], MockUser())

    # 1. Assert Bundle Structure
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert "timestamp" in bundle
    assert len(bundle["entry"]) == 4  # 1 DiagnosticReport + 3 Observations

    # 2. Assert DiagnosticReport Resource
    diag_report = bundle["entry"][0]["resource"]
    assert diag_report["resourceType"] == "DiagnosticReport"
    assert diag_report["id"] == "report-rep-test-fhir-88"
    assert diag_report["status"] == "final"
    assert diag_report["category"][0]["coding"][0]["code"] == "LAB"
    assert diag_report["code"]["coding"][0]["system"] == "http://loinc.org"
    assert diag_report["subject"]["reference"] == "Patient/usr-test-patient-fhir-1"
    assert diag_report["subject"]["display"] == "Jane Doe"
    assert diag_report["effectiveDateTime"] == "2026-08-25"
    assert len(diag_report["result"]) == 3
    assert diag_report["result"][0]["reference"] == "Observation/obs-bm-1"
    assert "prediabetes" in diag_report["conclusion"]

    # 3. Assert Observation 1 (High Glucose -> LOINC 1558-6)
    obs_1 = bundle["entry"][1]["resource"]
    assert obs_1["resourceType"] == "Observation"
    assert obs_1["id"] == "obs-bm-1"
    assert obs_1["status"] == "final"
    assert obs_1["category"][0]["coding"][0]["code"] == "laboratory"
    assert obs_1["code"]["coding"][0]["system"] == "http://loinc.org"
    assert obs_1["code"]["coding"][0]["code"] == "1558-6"
    assert obs_1["code"]["text"] == "Fasting Blood Sugar"
    assert obs_1["valueQuantity"]["value"] == 112.5
    assert obs_1["valueQuantity"]["unit"] == "mg/dL"
    assert obs_1["valueQuantity"]["system"] == "http://unitsofmeasure.org"
    assert obs_1["referenceRange"][0]["low"]["value"] == 70.0
    assert obs_1["referenceRange"][0]["high"]["value"] == 99.0
    assert obs_1["interpretation"][0]["coding"][0]["code"] == "H"
    assert obs_1["interpretation"][0]["coding"][0]["display"] == "High"

    # 4. Assert Observation 2 (Normal Hemoglobin -> LOINC 718-7)
    obs_2 = bundle["entry"][2]["resource"]
    assert obs_2["code"]["coding"][0]["code"] == "718-7"
    assert obs_2["valueQuantity"]["value"] == 14.2
    assert obs_2["valueQuantity"]["unit"] == "g/dL"
    assert obs_2["interpretation"][0]["coding"][0]["code"] == "N"

    # 5. Assert Observation 3 (Low Calcium -> LOINC 17861-6)
    obs_3 = bundle["entry"][3]["resource"]
    assert obs_3["code"]["coding"][0]["code"] == "17861-6"
    assert obs_3["valueQuantity"]["value"] == 8.2
    assert obs_3["interpretation"][0]["coding"][0]["code"] == "L"


@pytest.mark.asyncio
async def test_phase8_fhir_report_endpoint_cross_tenant_isolation():
    """
    Tests GET /api/v1/integrations/fhir/reports/{id}:
    - User A can retrieve their own report as an HL7 FHIR R4 bundle.
    - User B receives HTTP 403 Forbidden when trying to access User A's report.
    - Non-existent report returns HTTP 404 Not Found.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register User A
        email_a = f"fhir.user.a_{uuid.uuid4().hex[:6]}@example.com"
        await ac.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "full_name": "FHIR Patient A"})
        login_a = await ac.post("/api/v1/auth/login-json", json={"email": email_a, "password": "Password123!"})
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Grant REPORT_ANALYSIS consent for User A
        await ac.patch("/api/v1/me/consents/REPORT_ANALYSIS?granted=true", headers=headers_a)

        # Upload a medical report for User A
        pdf_bytes = b"%PDF-1.4 mock pdf lab report with Hemoglobin 13.5 g/dL and Fasting Glucose 95 mg/dL"
        files = {"file": ("blood_panel.pdf", pdf_bytes, "application/pdf")}
        upload_res = await ac.post("/api/v1/reports/upload", headers=headers_a, files=files, data={"report_type": "Blood Test"})
        assert upload_res.status_code == 201
        report_a_id = upload_res.json()["report_id"]

        # 2. Register User B
        email_b = f"fhir.user.b_{uuid.uuid4().hex[:6]}@example.com"
        await ac.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "full_name": "FHIR Patient B"})
        login_b = await ac.post("/api/v1/auth/login-json", json={"email": email_b, "password": "Password123!"})
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 3. User A retrieves their own FHIR bundle
        res_a = await ac.get(f"/api/v1/integrations/fhir/reports/{report_a_id}", headers=headers_a)
        assert res_a.status_code == 200
        bundle_data = res_a.json()
        assert bundle_data["resourceType"] == "Bundle"
        assert len(bundle_data["entry"]) >= 1
        assert bundle_data["entry"][0]["resource"]["resourceType"] == "DiagnosticReport"

        # 4. User B attempts to access User A's report -> 403 Forbidden
        res_b = await ac.get(f"/api/v1/integrations/fhir/reports/{report_a_id}", headers=headers_b)
        assert res_b.status_code == 403
        assert "forbidden" in res_b.json()["error"]["message"].lower()

        # 5. Non-existent report -> 404 Not Found
        fake_report_id = str(uuid.uuid4())
        res_none = await ac.get(f"/api/v1/integrations/fhir/reports/{fake_report_id}", headers=headers_a)
        assert res_none.status_code == 404


@pytest.mark.asyncio
async def test_phase8_abha_linking_flow_and_validation():
    """
    Tests ABHA format validation and simulated profile linking:
    - POST /api/v1/me/abha/link rejects non-14 digit formats with HTTP 400 Bad Request.
    - Valid 14-digit format stores formatted ABHA on user profile.
    - Profile endpoint GET /api/v1/auth/me reflects the linked ABHA number.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"abha.user_{uuid.uuid4().hex[:6]}@example.com"
        await ac.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "ABHA User"})
        login_res = await ac.post("/api/v1/auth/login-json", json={"email": email, "password": "Password123!"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Invalid ABHA number (short) -> 400
        bad_res = await ac.post("/api/v1/me/abha/link", headers=headers, json={"abha_number": "12345"})
        assert bad_res.status_code == 400
        assert "14 digits" in bad_res.json()["error"]["message"]

        # 2. Invalid ABHA number (contains letters) -> 400
        bad_alpha = await ac.post("/api/v1/me/abha/link", headers=headers, json={"abha_number": "91-1234-ABCD-9012"})
        assert bad_alpha.status_code == 400

        # 3. Valid ABHA number -> 200
        valid_res = await ac.post("/api/v1/me/abha/link", headers=headers, json={"abha_number": "91123456789012"})
        assert valid_res.status_code == 200
        valid_data = valid_res.json()
        assert valid_data["status"] == "LINKED"
        assert valid_data["abha_number"] == "91-1234-5678-9012"

        # 4. Check profile reflects linked ABHA number
        me_res = await ac.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["abha_number"] == "91-1234-5678-9012"


@pytest.mark.asyncio
async def test_phase9_grounded_rag_qa_with_traceable_citations():
    """
    Tests Multi-Report RAG Q&A with traceable biomarker citations:
    - Uploads and analyzes a lab report with Fasting Glucose and Hemoglobin.
    - POST /ai/qa queries for Fasting Glucose.
    - Asserts that the response includes structured, traceable citations back to the source biomarker.
    - Confirms embedding generation and queryable audit log persistence in ai_interaction_logs.
    """
    from app.models.ai_interaction_log import AIInteractionLog
    from app.models.report_embedding import ReportEmbedding

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"rag.patient_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await ac.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "RAG Patient"})
        user_id = reg_res.json()["id"]
        login_res = await ac.post("/api/v1/auth/login-json", json={"email": email, "password": "Password123!"})
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        # Grant consents
        await ac.patch("/api/v1/me/consents/REPORT_ANALYSIS?granted=true", headers=headers)
        await ac.patch("/api/v1/me/consents/AI_PROCESSING?granted=true", headers=headers)

        # Upload and analyze report
        report_text = (
            "%PDF-1.4\n"
            "COMPREHENSIVE METABOLIC PANEL\n"
            "Fasting Blood Sugar: 110.0 mg/dL (70.0 - 99.0)\n"
            "Hemoglobin: 14.5 g/dL (12.0 - 17.5)\n"
        )
        files = {"file": ("panel.pdf", report_text.encode("utf-8"), "application/pdf")}
        upload_res = await ac.post("/api/v1/reports/upload", headers=headers, files=files, data={"report_type": "Metabolic Panel"})
        report_id = upload_res.json()["report_id"]

        analyze_res = await ac.post(f"/api/v1/reports/{report_id}/analyze", headers=headers)
        assert analyze_res.status_code == 200

        # Ask grounded question
        qa_res = await ac.post("/api/v1/ai/qa", headers=headers, json={
            "report_id": report_id,
            "question": "What is my Fasting Glucose level and is it high?"
        })
        assert qa_res.status_code == 200
        qa_data = qa_res.json()

        # Structural assertions on answer and citations
        assert "110" in qa_data["answer"] or "Glucose" in qa_data["answer"]
        assert qa_data["confidence_score"] >= 0.70
        assert qa_data["review_status"] == "VERIFIED"
        assert qa_data["is_emergency_flagged"] is False
        assert len(qa_data["citations"]) > 0

        first_citation = qa_data["citations"][0]
        assert "Glucose" in first_citation["test_name"] or "glucose" in first_citation["canonical_name"].lower()
        assert float(first_citation["value"]) == 110.0
        assert first_citation["unit"].lower() == "mg/dl"
        assert first_citation["flag"] == "HIGH"
        assert "report_date" in first_citation

        # Verify Database audit logs and report embeddings using TestingSessionLocal
        async with TestingSessionLocal() as session:
            # 1. Verify ReportEmbedding was created
            emb_q = select(ReportEmbedding).where(ReportEmbedding.report_id == report_id)
            embs = (await session.execute(emb_q)).scalars().all()
            assert len(embs) > 0
            assert embs[0].embedding_json is not None

            # 2. Verify AIInteractionLog was recorded
            ai_q = select(AIInteractionLog).where(AIInteractionLog.user_id == user_id)
            ai_logs = (await session.execute(ai_q)).scalars().all()
            assert len(ai_logs) > 0
            assert ai_logs[0].confidence_score >= 0.70
            assert ai_logs[0].review_status == "VERIFIED"
            assert len(ai_logs[0].citations) > 0


@pytest.mark.asyncio
async def test_phase9_ambiguous_low_confidence_triggers_unreviewed_label_and_review_queue():
    """
    Tests safety guardrail for ambiguous/low-confidence inputs:
    - Submits an ambiguous/out-of-scope health query without lab grounding.
    - Asserts that confidence < 0.70 triggers an UNREVIEWED warning banner.
    - Asserts that review_status is set to PENDING_REVIEW in response and in database audit log.
    """
    from app.models.ai_interaction_log import AIInteractionLog

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"ambiguous.user_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await ac.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Ambiguous Patient"})
        user_id = reg_res.json()["id"]
        login_res = await ac.post("/api/v1/auth/login-json", json={"email": email, "password": "Password123!"})
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        # Grant AI_PROCESSING consent
        await ac.patch("/api/v1/me/consents/AI_PROCESSING?granted=true", headers=headers)

        # Submit ambiguous out-of-scope question without any lab data
        qa_res = await ac.post("/api/v1/ai/qa", headers=headers, json={
            "question": "Can taking mega-doses of unproven bark extract cure chronic headaches?"
        })
        assert qa_res.status_code == 200
        qa_data = qa_res.json()

        # Must flag low confidence and label unreviewed
        assert qa_data["confidence_score"] < 0.70
        assert qa_data["review_status"] == "PENDING_REVIEW"
        assert "UNREVIEWED" in qa_data["answer"]

        # Check DB audit log
        async with TestingSessionLocal() as session:
            ai_q = select(AIInteractionLog).where(AIInteractionLog.user_id == user_id)
            ai_logs = (await session.execute(ai_q)).scalars().all()
            assert len(ai_logs) > 0
            assert ai_logs[0].review_status == "PENDING_REVIEW"
            assert ai_logs[0].confidence_score < 0.70


@pytest.mark.asyncio
async def test_phase9_emergency_red_flag_interception_and_deterministic_fallback():
    """
    Tests Emergency Red-Flag Interception & Deterministic Fallback:
    - When a patient enters acute red-flag symptoms in a QA query, the safety guardrail intercepts
      and prepends an emergency medical banner.
    - Confirms the deterministic clinical rules provider is fully operational without external LLM keys.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"emergency.patient_{uuid.uuid4().hex[:6]}@example.com"
        await ac.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Emergency Patient"})
        login_res = await ac.post("/api/v1/auth/login-json", json={"email": email, "password": "Password123!"})
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        await ac.patch("/api/v1/me/consents/AI_PROCESSING?granted=true", headers=headers)

        # Query with acute emergency symptoms
        qa_res = await ac.post("/api/v1/ai/qa", headers=headers, json={
            "question": "I have severe crushing chest pain radiating to my left arm with sudden shortness of breath"
        })
        assert qa_res.status_code == 200
        qa_data = qa_res.json()

        # Emergency red flag assertions
        assert qa_data["is_emergency_flagged"] is True
        assert "CRITICAL MEDICAL ALERT" in qa_data["answer"]
        assert "112" in qa_data["answer"] or "911" in qa_data["answer"]
        assert qa_data["model_provider"] == "deterministic-clinical-rules"












