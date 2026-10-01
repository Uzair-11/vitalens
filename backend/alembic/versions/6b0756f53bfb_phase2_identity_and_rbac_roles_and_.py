"""phase2_identity_and_rbac_roles_and_doctor_fk

Revision ID: 6b0756f53bfb
Revises: 
Create Date: 2026-08-29 21:46:38.948378

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6b0756f53bfb'
down_revision: Union[str, Sequence[str], None] = '000000000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Apply Phase 2 Identity & RBAC schema additions and backfill."""
    # 1. Add role column to users if not present
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role') THEN
                ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'PATIENT' NOT NULL;
            END IF;
        END $$;
    """)

    # 2. Add user_id column to doctors if not present
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='doctors' AND column_name='user_id') THEN
                ALTER TABLE doctors ADD COLUMN user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;
            END IF;
        END $$;
    """)

    # 3. Role backfills
    op.execute("UPDATE users SET role = 'PATIENT' WHERE role IS NULL;")
    op.execute("UPDATE users SET role = 'PATIENT' WHERE email = 'demo@healthapp.com';")
    op.execute("UPDATE users SET role = 'DOCTOR' WHERE email = 'doctor.jenkins@vitalens.health';")
    op.execute("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@vitalens.health';")

def downgrade() -> None:
    """Revert Phase 2 schema additions."""
    op.execute("ALTER TABLE doctors DROP COLUMN IF EXISTS user_id;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role;")
