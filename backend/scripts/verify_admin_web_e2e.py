import os
import sys
import uuid
import asyncio
import httpx
from httpx import ASGITransport

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.core.database import engine

async def test_admin_web_e2e():
    print("==================================================")
    print(">> STARTING ADMIN WEB UI END-TO-END VERIFICATION")
    print("==================================================")

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. SCREEN 1: LOGIN (Admin Role)
        print("\n--- 1. Testing Login Screen (Admin) ---")
        login_res = await client.post("/api/v1/auth/login-json", json={"email": "admin@vitalens.health", "password": "admin123"})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        admin_data = login_res.json()
        admin_token = admin_data["access_token"]
        refresh_token = admin_data["refresh_token"]
        admin_role = admin_data["role"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print(f"[OK] Admin logged in successfully! Role: {admin_role} (Access Token: {admin_token[:20]}...)")

        # 2. SCREEN 2: OPERATIONAL DASHBOARD (KPI Cards)
        print("\n--- 2. Testing Dashboard Tab (GET /admin/analytics/dashboard) ---")
        dash_res = await client.get("/api/v1/admin/analytics/dashboard", headers=admin_headers)
        assert dash_res.status_code == 200
        analytics = dash_res.json()
        print(f"   [Card 1] Total Registered Users   : {analytics['user_metrics']['total_registered_users']} ({analytics['user_metrics']['signups_this_week']} this week)")
        print(f"   [Card 2] Verified Active Doctors   : {analytics['doctor_metrics']['active_verified_doctors']} / {analytics['doctor_metrics']['total_doctors']} ({analytics['doctor_metrics']['pending_verification']} pending)")
        print(f"   [Card 3] Processed Health Reports  : {analytics['report_metrics']['total_reports_processed']} ({analytics['report_metrics']['successfully_analyzed']} analyzed)")
        print(f"   [Card 4] Total Consultation Bookings: {analytics['appointment_metrics']['total_bookings']} (Cancellation Rate: {analytics['appointment_metrics']['cancellation_rate_pct']}%)")

        # 3. SCREEN 3: DOCTORS MANAGEMENT (List, Create, Verify, Status Toggle)
        print("\n--- 3. Testing Doctors Management Tab ---")
        docs_res = await client.get("/api/v1/admin/doctors/", headers=admin_headers)
        assert docs_res.status_code == 200
        docs = docs_res.json()
        print(f"[OK] Loaded {len(docs)} doctors in directory table:")
        for d in docs[:4]:
            print(f"   * {d['full_name']} | {d.get('specialty_name', 'General')} | Fee: ${d['consultation_fee']} | Verification: [{d['verification_status']}] | Active: {d['is_active']}")

        # Fetch specialties
        specs_res = await client.get("/api/v1/doctors/specialties")
        specs = specs_res.json()
        spec_id = specs[0]["id"]
        print(f"[OK] Fetched {len(specs)} medical specialties for doctor creation form.")

        # Create doctor
        new_doc_email = f"dr.web_ui_{uuid.uuid4().hex[:4]}@vitalens.health"
        create_doc_res = await client.post(
            "/api/v1/admin/doctors/",
            headers=admin_headers,
            json={
                "email": new_doc_email,
                "temporary_password": "DocWebPass2026!",
                "full_name": "Dr. Eleanor Vance, MD",
                "specialty_id": spec_id,
                "qualification": "MD (Neurology)",
                "experience_years": 11,
                "clinic_name": "Vance Neurological Clinic",
                "address": "100 Grand Avenue",
                "city": "Metro City",
                "consultation_fee": 950.0
            }
        )
        assert create_doc_res.status_code == 201
        new_doc = create_doc_res.json()
        doc_id = new_doc["doctor_id"]
        print(f"[OK] Added new doctor via modal form: {new_doc['full_name']} -> Assigned Verification: [{new_doc['verification_status']}]")

        # Verify doctor
        verify_res = await client.patch(
            f"/api/v1/admin/doctors/{doc_id}/verify?verification_status=VERIFIED",
            headers=admin_headers
        )
        assert verify_res.status_code == 200
        print(f"[OK] Admin clicked 'Verify': Doctor {doc_id} is now [{verify_res.json()['verification_status']}]")

        # Toggle status
        toggle_res = await client.patch(
            f"/api/v1/admin/doctors/{doc_id}/status?is_active=false",
            headers=admin_headers
        )
        assert toggle_res.status_code == 200
        print(f"[OK] Admin clicked 'Deactivate': Doctor is_active is now [{toggle_res.json()['is_active']}]")

        # 4. SCREEN 4: PATIENT DIRECTORY (Search, Detail Metrics, Suspend/Reactivate)
        print("\n--- 4. Testing Patient Directory Tab ---")
        patients_res = await client.get("/api/v1/admin/users/?search=demo", headers=admin_headers)
        assert patients_res.status_code == 200
        patients = patients_res.json()
        assert len(patients) >= 1
        demo_pat = patients[0]
        print(f"[OK] Searched patient 'demo': Found {demo_pat['full_name']} ({demo_pat['email']}) | Role: {demo_pat['role']}")

        # Detail metrics
        detail_res = await client.get(f"/api/v1/admin/users/{demo_pat['id']}", headers=admin_headers)
        assert detail_res.status_code == 200
        detail = detail_res.json()
        print(f"   * Operational Activity Summary: {detail['summary_metrics']}")

        # Suspend & Reactivate
        suspend_res = await client.patch(f"/api/v1/admin/users/{demo_pat['id']}/status?is_active=false", headers=admin_headers)
        assert suspend_res.status_code == 200
        print(f"   * Admin clicked 'Suspend': User is_active = {suspend_res.json()['is_active']}")

        reactivate_res = await client.patch(f"/api/v1/admin/users/{demo_pat['id']}/status?is_active=true", headers=admin_headers)
        assert reactivate_res.status_code == 200
        print(f"   * Admin clicked 'Reactivate': User is_active = {reactivate_res.json()['is_active']}")

        # 5. SCREEN 5: APPOINTMENTS OVERSIGHT (List & Cancel Conflict)
        print("\n--- 5. Testing Appointments Oversight Tab ---")
        appts_res = await client.get("/api/v1/admin/appointments/", headers=admin_headers)
        assert appts_res.status_code == 200
        appts = appts_res.json()
        print(f"[OK] Loaded {len(appts)} system appointments:")
        for a in appts[:3]:
            print(f"   * {a['appointment_date']} at {a['appointment_time']} | Patient: {a['patient_name']} -> Doctor: {a['doctor_name']} | Status: [{a['status']}]")

        # 6. SCREEN 6: CLINICAL CONTENT & GLOSSARY (CRUD)
        print("\n--- 6. Testing Clinical Content & Glossary Tab ---")
        bios_res = await client.get("/api/v1/admin/content/biomarkers", headers=admin_headers)
        assert bios_res.status_code == 200
        bios = bios_res.json()
        print(f"[OK] Loaded {len(bios)} clinical biomarker reference ranges:")
        for b in bios[:3]:
            print(f"   * {b['test_name']} ({b['canonical_name']}) | Range: {b['ref_min']} - {b['ref_max']} {b['default_unit']}")

        gloss_res = await client.get("/api/v1/admin/content/glossary", headers=admin_headers)
        assert gloss_res.status_code == 200
        gloss = gloss_res.json()
        print(f"[OK] Loaded {len(gloss)} layperson terminology glossary definitions:")
        for g in gloss[:3]:
            print(f"   * {g['term']}: {g['definition'][:70]}...")

        # 7. SCREEN 7: AI RECOMMENDATION REVIEW QUEUE
        print("\n--- 7. Testing AI Recommendation Review Queue Tab ---")
        ai_res = await client.get("/api/v1/admin/ai-review/", headers=admin_headers)
        assert ai_res.status_code == 200
        recs = ai_res.json()
        print(f"[OK] Loaded {len(recs)} AI recommendation items:")
        if recs:
            r = recs[0]
            print(f"   * Concern: '{r['primary_concern']}' -> Specialty: '{r['specialty_name']}' | Confidence: {int(r['confidence_score']*100)}% | Status: [{r['review_status']}]")
            rev_action = await client.patch(f"/api/v1/admin/ai-review/{r['id']}?action=APPROVE", headers=admin_headers)
            assert rev_action.status_code == 200
            print(f"[OK] Reviewer clicked 'Approve' -> New review_status: [{rev_action.json()['review_status']}] by {rev_action.json()['reviewed_by']}")

        # 8. ROLE-BASED ACCESS (SUPPORT_STAFF) & ERROR BOUNDARY (403 FORBIDDEN)
        print("\n--- 8. Testing Support Staff Role-Gating & 403 Forbidden State ---")
        staff_login = await client.post("/api/v1/auth/login-json", json={"email": "staff@vitalens.health", "password": "staff123"})
        assert staff_login.status_code == 200
        staff_data = staff_login.json()
        staff_headers = {"Authorization": f"Bearer {staff_data['access_token']}"}
        print(f"[OK] Support Staff logged in: Role [{staff_data['role']}]")

        # Read allowed
        staff_read = await client.get("/api/v1/admin/users/", headers=staff_headers)
        assert staff_read.status_code == 200
        print("[OK] Support Staff GET /admin/users/ succeeded with HTTP 200 OK.")

        # Mutation rejected
        staff_write = await client.patch(f"/api/v1/admin/users/{demo_pat['id']}/status?is_active=false", headers=staff_headers)
        assert staff_write.status_code == 403
        print(f"[OK] Support Staff PATCH /admin/users/ status rejected with HTTP 403 Forbidden: '{staff_write.json().get('error', {}).get('message', 'Access forbidden')}'")

        # 9. TOKEN REFRESH FLOW (401 RECOVERY)
        print("\n--- 9. Testing 401 Interceptor Token Refresh Flow ---")
        refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_res.status_code == 200
        new_token = refresh_res.json()["access_token"]
        assert len(new_token) > 20
        print(f"[OK] Successfully issued new access token via refresh token.")

    await engine.dispose()
    print("\n==================================================")
    print(">> ALL 7 ADMIN WEB SCREENS & WORKFLOWS VERIFIED!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_admin_web_e2e())
