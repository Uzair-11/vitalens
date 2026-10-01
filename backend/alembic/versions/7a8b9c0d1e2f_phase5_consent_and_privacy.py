"""phase5_consent_and_privacy

Revision ID: 7a8b9c0d1e2f
Revises: 3b2605618b08
Create Date: 2026-08-30 15:47:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '3b2605618b08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates consents table with idempotent PL/pgSQL block."""
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'consents') THEN
                CREATE TABLE consents (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    consent_type VARCHAR(50) NOT NULL,
                    granted BOOLEAN NOT NULL DEFAULT true,
                    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    revoked_at TIMESTAMP WITH TIME ZONE
                );
                CREATE INDEX ix_consents_user_id ON consents(user_id);
                CREATE INDEX ix_consents_consent_type ON consents(consent_type);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Drops consents table."""
    op.drop_index(op.f('ix_consents_consent_type'), table_name='consents')
    op.drop_index(op.f('ix_consents_user_id'), table_name='consents')
    op.drop_table('consents')
