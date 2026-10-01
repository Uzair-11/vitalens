import os
import sys
import time
import asyncio
import httpx
from datetime import date, timedelta
from httpx import ASGITransport

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

BASE_URL = os.getenv("TEST_BASE_URL", "http://test")

async def benchmark_endpoint(client: httpx.AsyncClient, name: str, method: str, url: str, **kwargs):
    start = time.perf_counter()
    status = 0
    err = None
    try:
        if method == "GET":
            res = await client.get(url, **kwargs)
        elif method == "POST":
            res = await client.post(url, **kwargs)
        status = res.status_code
        res_data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
    except Exception as e:
        err = str(e)
        res_data = {}
    duration_ms = (time.perf_counter() - start) * 1000.0
    return {
        "name": name,
        "status": status,
        "duration_ms": duration_ms,
        "error": err,
        "data": res_data
    }

async def run_worker_flow(worker_id: int, results: list):
    transport = ASGITransport(app=app) if BASE_URL == "http://test" else None
    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL, timeout=30.0, follow_redirects=True) as client:
        # 1. Probe readiness
        r_ready = await benchmark_endpoint(client, "GET /health/ready", "GET", "/health/ready")
        results.append(r_ready)

        # 2. Login Flow (using verified demo credentials)
        login_payload = {
            "email": "demo@healthapp.com",
            "password": "password123"
        }
        r_login = await benchmark_endpoint(
            client, "POST /auth/login-json", "POST", "/api/v1/auth/login-json", json=login_payload
        )
        results.append(r_login)

        token = r_login.get("data", {}).get("access_token")
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # 3. Report Upload Flow (Valid PDF magic bytes)
        pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
        files = {"file": (f"load_test_report_{worker_id}.pdf", pdf_bytes, "application/pdf")}
        r_upload = await benchmark_endpoint(
            client, "POST /reports/upload", "POST", "/api/v1/reports/upload", headers=headers, files=files
        )
        results.append(r_upload)

        # 4. Doctor Listing & Availability
        r_docs = await benchmark_endpoint(
            client, "GET /doctors/", "GET", "/api/v1/doctors/", headers=headers
        )
        results.append(r_docs)

async def main():
    print("================================================================================")
    print("               VITALENS PHASE 6 CONCURRENCY & SMOKE BENCHMARK                   ")
    print("================================================================================")
    print(f"[*] Target Backend: {BASE_URL}")
    num_workers = 15
    print(f"[*] Launching {num_workers} concurrent client workers...")

    results = []
    start_total = time.perf_counter()

    tasks = [run_worker_flow(i, results) for i in range(num_workers)]
    await asyncio.gather(*tasks, return_exceptions=True)

    total_time = time.perf_counter() - start_total
    print(f"[OK] Completed in {total_time:.2f} seconds.\n")

    # Aggregate metrics
    endpoints = {}
    for r in results:
        name = r["name"]
        if name not in endpoints:
            endpoints[name] = {"durations": [], "success": 0, "fail": 0}
        
        endpoints[name]["durations"].append(r["duration_ms"])
        if 200 <= r["status"] < 300:
            endpoints[name]["success"] += 1
        else:
            endpoints[name]["fail"] += 1

    print("| Endpoint | Total Requests | Success | Failed | Avg Latency (ms) | Min (ms) | Max (ms) |")
    print("|---|---|---|---|---|---|---|")
    for name, m in sorted(endpoints.items()):
        durs = m["durations"]
        avg_lat = sum(durs) / len(durs) if durs else 0
        min_lat = min(durs) if durs else 0
        max_lat = max(durs) if durs else 0
        total = len(durs)
        print(f"| {name} | {total} | {m['success']} | {m['fail']} | {avg_lat:.1f}ms | {min_lat:.1f}ms | {max_lat:.1f}ms |")

    total_reqs = len(results)
    total_success = sum(1 for r in results if 200 <= r["status"] < 300)
    total_failures = total_reqs - total_success
    print(f"\nOverall Throughput: {total_reqs / total_time:.1f} req/sec")
    print(f"Success Rate: {(total_success / total_reqs) * 100:.1f}% ({total_success}/{total_reqs})")
    print(f"Errors/Connection Pool Timeouts: {total_failures}")
    print("================================================================================")

if __name__ == "__main__":
    asyncio.run(main())
