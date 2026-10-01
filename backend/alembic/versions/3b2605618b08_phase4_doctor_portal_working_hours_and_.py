"""phase4_doctor_portal_working_hours_and_schedule_blocks

Revision ID: 3b2605618b08
Revises: 6b0756f53bfb
Create Date: 2026-08-29 22:30:00.808343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b2605618b08'
down_revision: Union[str, Sequence[str], None] = '6b0756f53bfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'doctor_working_hours',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('doctor_id', sa.String(length=36), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('slot_duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_doctor_working_hours_doctor_id'), 'doctor_working_hours', ['doctor_id'], unique=False)

    op.create_table(
        'doctor_schedule_blocks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('doctor_id', sa.String(length=36), nullable=False),
        sa.Column('block_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_doctor_schedule_blocks_doctor_id'), 'doctor_schedule_blocks', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_doctor_schedule_blocks_block_date'), 'doctor_schedule_blocks', ['block_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_doctor_schedule_blocks_block_date'), table_name='doctor_schedule_blocks')
    op.drop_index(op.f('ix_doctor_schedule_blocks_doctor_id'), table_name='doctor_schedule_blocks')
    op.drop_table('doctor_schedule_blocks')
    op.drop_index(op.f('ix_doctor_working_hours_doctor_id'), table_name='doctor_working_hours')
    op.drop_table('doctor_working_hours')

