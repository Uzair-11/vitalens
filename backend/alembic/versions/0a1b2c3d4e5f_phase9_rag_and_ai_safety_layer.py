"""phase9_rag_and_ai_safety_layer

Revision ID: 0a1b2c3d4e5f
Revises: 9c0d1e2f3a4b
Create Date: 2026-08-30 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '9c0d1e2f3a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. report_embeddings table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'report_embeddings') THEN
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
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_interaction_logs') THEN
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
                CREATE INDEX ix_ai_interaction_logs_user_id ON ai_interaction_logs(user_id);
                CREATE INDEX ix_ai_interaction_logs_report_id ON ai_interaction_logs(report_id);
                CREATE INDEX ix_ai_interaction_logs_is_emergency_flagged ON ai_interaction_logs(is_emergency_flagged);
                CREATE INDEX ix_ai_interaction_logs_review_status ON ai_interaction_logs(review_status);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS ai_interaction_logs;
        DROP TABLE IF EXISTS report_embeddings;
    """)
