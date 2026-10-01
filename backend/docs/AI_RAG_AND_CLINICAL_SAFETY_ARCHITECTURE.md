# VitaLens AI/RAG Upgrade & Clinical Safety Architecture (Phase 9)

## 1. Executive Summary & Deterministic Clinical RAG Engine

VitaLens exclusively utilizes an internal, deterministic Grounded RAG synthesis engine (`DeterministicClinicalRAGProvider`) with zero external network dependencies or external LLM API calls.

> [!IMPORTANT]
> **Deterministic Grounded Architecture Standard**:
> - External cloud LLM keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`) and outbound HTTP client layers have been completely eliminated from the codebase and configuration.
> - No outbound HTTP requests are made to third-party AI services.
> - The entire grounded RAG and semantic matching pipeline executes 100% deterministically on-device / on-premise, guaranteeing auditability, predictability, HIPAA/DISHA data confidentiality, and reproducible safety-critical evaluations.

---

## 2. Multi-Report Vector Store & pgvector Gap Disclosure

### 2.1 pgvector Local Extension Status
Inspection of the local PostgreSQL 18 instance via `SELECT * FROM pg_available_extensions WHERE name = 'vector';` returned `0 rows`, indicating that the compiled `pgvector` binary is not installed on the host OS.

### 2.2 Storage & Migration Architecture
To avoid silently introducing external vector databases (e.g. Pinecone/Chroma), embedding storage is natively integrated into PostgreSQL via the `report_embeddings` table:

```sql
CREATE TABLE report_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    report_id VARCHAR(36) NOT NULL REFERENCES medical_reports(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chunk_type VARCHAR(50) NOT NULL DEFAULT 'BIOMARKERS_SUMMARY',
    content_chunk TEXT NOT NULL,
    embedding_json JSON,
    metadata_json JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX ix_report_embeddings_report_id ON report_embeddings(report_id);
CREATE INDEX ix_report_embeddings_user_id ON report_embeddings(user_id);
```

- **Cloud Deployment Path**: When deploying to production managed PostgreSQL (AWS RDS, Supabase, GCP Cloud SQL), enabling the extension (`CREATE EXTENSION vector;`) and altering `embedding_json` to `embedding vector(768)` is a single Alembic migration step with zero application logic rewrite.

---

## 3. Clinical Safety & Guardrail Pipeline

Every patient query and AI response passes through an invariant 4-stage clinical safety pipeline:

```
Patient Query (POST /api/v1/ai/qa)
               │
               ▼
   [ Consent Enforcement: AI_PROCESSING ]
               │
               ▼
   [ Gate 1: Acute Emergency Red-Flag Interception ]
               │ ├── Flagged? ──► Prepend Emergency Advisory (Dial 112/911)
               ▼
   [ Multi-Report Grounded Context & Biomarker Retrieval ]
               │
               ▼
   [ Deterministic Clinical Synthesis ]
               │
               ▼
   [ Gate 2: Traceable Grounded Biomarker Citations Attached ]
               │
               ▼
   [ Gate 3: Confidence Threshold Evaluation ]
               │ ├── Score < 0.70 ──► Labeled [UNREVIEWED_AI_RESPONSE]
               │                      Review Status = PENDING_REVIEW
               ▼
   [ Gate 4: Queryable Audit Logging (ai_interaction_logs) ]
               │
               ▼
        Patient Delivery
```

### 3.1 Traceable Biomarker Citations
Every clinical statement returned by `/ai/qa` includes a structured `citations` array linking observations to verified laboratory findings:
- `test_name` / `canonical_name`: Standardized test identifier.
- `value`: Numeric or qualitative lab measurement.
- `unit`: Measurement unit (e.g. `mg/dL`, `g/dL`).
- `flag`: Reference flag (`NORMAL`, `HIGH`, `LOW`, `CRITICAL`).
- `report_date`: Timestamped origin report date.

### 3.2 Low-Confidence Routing & Clinical Review Queue
- Queries with insufficient or ambiguous laboratory evidence yield a confidence score $< 0.70$.
- The response is prepended with a clear clinical warning (`⚠️ CLINICAL NOTICE: UNREVIEWED AI RESPONSE`) and persisted with `review_status = "PENDING_REVIEW"`, routing it directly to the physician/admin review queue.

---

## 4. Queryable AI Interaction Audit Log

All AI inferences are persisted in `ai_interaction_logs`:

```sql
CREATE TABLE ai_interaction_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_id VARCHAR(36) REFERENCES medical_reports(id) ON DELETE SET NULL,
    prompt TEXT NOT NULL,
    response_text TEXT NOT NULL,
    confidence_score FLOAT NOT NULL DEFAULT 1.0,
    citations JSON,
    is_emergency_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    review_status VARCHAR(50) NOT NULL DEFAULT 'VERIFIED',
    model_provider VARCHAR(100) NOT NULL DEFAULT 'deterministic-clinical-rules',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```
