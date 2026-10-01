import os
import sys
import asyncio
import httpx
from httpx import ASGITransport

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.core.database import engine
from app.ml.lab_extractor import extract_biomarkers_from_text

async def verify_cache_invalidation():
    print("==================================================")
    print(">> STARTING LIVE CACHE-INVALIDATION CHECK")
    print("==================================================")

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Admin login
        login_res = await client.post(
            "/api/v1/auth/login-json",
            json={"email": "admin@vitalens.health", "password": "admin123"}
        )
        assert login_res.status_code == 200
        admin_token = login_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Get Hemoglobin reference ID
        bios_res = await client.get("/api/v1/admin/content/biomarkers", headers=admin_headers)
        assert bios_res.status_code == 200
        biomarkers_list = bios_res.json()
        hb_ref = next((b for b in biomarkers_list if b["test_name"] == "Hemoglobin"), None)
        assert hb_ref is not None, "Hemoglobin biomarker reference not found in DB"
        hb_id = hb_ref["id"]
        original_min = hb_ref["ref_min"]
        original_max = hb_ref["ref_max"]
        print(f"Step 1: Initial Hemoglobin Reference Range: {original_min} - {original_max} g/dL (ID: {hb_id})")

        # 3. Test text with Hemoglobin = 15.5 g/dL
        sample_report = "LAB REPORT\nHemoglobin: 15.5 g/dL\nFasting Blood Sugar: 85 mg/dL"

        # Initial extraction under original threshold (12.0 - 17.5)
        res1 = extract_biomarkers_from_text(sample_report)
        hb_item1 = next((b for b in res1 if "Hemoglobin" in b["test_name"]), None)
        print(f"\nStep 2: Analysis BEFORE PATCH (Value: 15.5 g/dL):")
        print(f"   * Expected Range : {hb_item1['reference_min']} - {hb_item1['reference_max']} {hb_item1['unit']}")
        print(f"   * Evaluated Flag : [{hb_item1['flag']}] (Expected: NORMAL)")
        assert hb_item1["flag"] == "NORMAL"

        # 4. PATCH ref_max to 14.0 g/dL via Admin API (triggers invalidate_biomarker_cache)
        print(f"\nStep 3: Executing PATCH /api/v1/admin/content/biomarkers/{hb_id} with ref_max = 14.0...")
        patch_res = await client.patch(
            f"/api/v1/admin/content/biomarkers/{hb_id}",
            headers=admin_headers,
            json={"ref_max": 14.0}
        )
        assert patch_res.status_code == 200
        print(f"   * API Response Status: {patch_res.status_code} OK")
        print(f"   * Updated Record in DB: ref_min={patch_res.json()['ref_min']}, ref_max={patch_res.json()['ref_max']}")

        # 5. Immediate re-extraction in the SAME running server process without restarting
        res2 = extract_biomarkers_from_text(sample_report)
        hb_item2 = next((b for b in res2 if "Hemoglobin" in b["test_name"]), None)
        print(f"\nStep 4: Analysis IMMEDIATELY AFTER PATCH (Value: 15.5 g/dL, Same Process):")
        print(f"   * Evaluated Range : {hb_item2['reference_min']} - {hb_item2['reference_max']} {hb_item2['unit']}")
        print(f"   * Evaluated Flag  : [{hb_item2['flag']}] (Expected: HIGH)")
        assert hb_item2["flag"] == "HIGH", f"Expected HIGH but got {hb_item2['flag']}"

        # 6. Revert back to original clinical range (12.0 - 17.5)
        print(f"\nStep 5: Reverting Hemoglobin ref_max back to {original_max} g/dL...")
        revert_res = await client.patch(
            f"/api/v1/admin/content/biomarkers/{hb_id}",
            headers=admin_headers,
            json={"ref_max": original_max}
        )
        assert revert_res.status_code == 200

        # 7. Final extraction check
        res3 = extract_biomarkers_from_text(sample_report)
        hb_item3 = next((b for b in res3 if "Hemoglobin" in b["test_name"]), None)
        print(f"\nStep 6: Analysis AFTER REVERT (Value: 15.5 g/dL):")
        print(f"   * Evaluated Range : {hb_item3['reference_min']} - {hb_item3['reference_max']} {hb_item3['unit']}")
        print(f"   * Evaluated Flag  : [{hb_item3['flag']}] (Expected: NORMAL)")
        assert hb_item3["flag"] == "NORMAL"

    await engine.dispose()
    print("\n==================================================")
    print(">> LIVE CACHE-INVALIDATION CHECK PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(verify_cache_invalidation())
