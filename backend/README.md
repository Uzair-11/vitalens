# VitaLens Backend API & Applied AI Service

VitaLens is an AI-assisted health report analysis and specialist recommendation system built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **scikit-learn**, and multi-role RBAC architecture.

---

## 1. Quick Start

### Start Server:
```bash
cd backend
python main.py
```
* Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
* Health Check: `http://localhost:8000/health`
* Readiness Probe: `http://localhost:8000/health/ready`

### Pre-Seeded Accounts:
* **Patient User:** `demo@healthapp.com` / `password123`
* **Doctor User:** `doctor.jenkins@vitalens.health` / `doctor123`
* **Admin User:** `admin@vitalens.health` / `admin123`

---

## 2. Production Database Backup Strategy

### Automated PostgreSQL Backup Plan:
1. **Daily Logical Snapshots (`pg_dump`):**
   ```bash
   pg_dump -Fc -v -h <host> -U postgres -d vitalens_db -f /backups/vitalens_$(date +%Y%m%d_%H%M%S).dump
   ```
2. **Automated Cron Schedule:**
   * Frequency: Daily at 02:00 UTC.
   * Retention: Keep daily backups for 30 days, weekly backups for 12 weeks, monthly backups for 1 year.
   * Encryption: Encrypt `.dump` archives with AES-256 before uploading to cold cloud storage (AWS S3 Glacier / GCP Coldline).
3. **Disaster Recovery Drill:**
   * Restore verification script:
   ```bash
   pg_restore -v -d vitalens_recovery_test /backups/vitalens_latest.dump
   ```

---

## 3. Architecture & Security Documentation

* **Role-Based Access Control:** See [RBAC.md](docs/RBAC.md)
* **DPDP & Regulatory Compliance Scaffolding:** See [COMPLIANCE_NOTES.md](docs/COMPLIANCE_NOTES.md)
* **Clinical Decision Logic:** See [CLINICAL_LOGIC_SUMMARY.md](docs/CLINICAL_LOGIC_SUMMARY.md)
