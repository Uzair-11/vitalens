"""phase10_schema_safety_and_explanations

Revision ID: 1a2b3c4d5e6f
Revises: 0a1b2c3d4e5f
Create Date: 2026-10-02 01:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '0a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add deleted_at to users table if not exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'deleted_at'
            ) THEN
                ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """)

    # 2. Add index to biomarkers.flag if not exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'biomarkers' AND indexname = 'ix_biomarkers_flag'
            ) THEN
                CREATE INDEX ix_biomarkers_flag ON biomarkers(flag);
            END IF;
        END $$;
    """)

    # 3. Create biomarker_explanations table if not exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'biomarker_explanations') THEN
                CREATE TABLE biomarker_explanations (
                    id VARCHAR(36) PRIMARY KEY,
                    test_name VARCHAR(255) NOT NULL,
                    canonical_name VARCHAR(255) NOT NULL,
                    flag VARCHAR(20) NOT NULL,
                    explanation_text TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX ix_biomarker_explanations_canonical_name ON biomarker_explanations(canonical_name);
                CREATE INDEX ix_biomarker_explanations_flag ON biomarker_explanations(flag);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS biomarker_explanations;
        DROP INDEX IF EXISTS ix_biomarkers_flag;
        ALTER TABLE users DROP COLUMN IF EXISTS deleted_at;
    """)
