from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '000000000001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_superuser', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_suspended', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. medical_specialties
    op.create_table(
        'medical_specialties',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_name', sa.String(length=50), server_default='stethoscope', nullable=True),
    )
    op.create_index('ix_medical_specialties_name', 'medical_specialties', ['name'], unique=True)

    # 3. doctors
    op.create_table(
        'doctors',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('specialty_id', sa.String(length=36), sa.ForeignKey('medical_specialties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('years_of_experience', sa.Integer(), server_default='5', nullable=True),
        sa.Column('consultation_fee', sa.Float(), server_default='50.0', nullable=True),
        sa.Column('rating', sa.Float(), server_default='5.0', nullable=True),
        sa.Column('review_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_available', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('verification_status', sa.String(length=50), server_default='VERIFIED', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_doctors_full_name', 'doctors', ['full_name'])
    op.create_index('ix_doctors_specialty_id', 'doctors', ['specialty_id'])

    # 4. doctor_availabilities
    op.create_table(
        'doctor_availabilities',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('doctor_id', sa.String(length=36), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('available_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('slot_duration_minutes', sa.Integer(), server_default='30', nullable=True),
        sa.Column('is_booked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_doctor_availabilities_doctor_id', 'doctor_availabilities', ['doctor_id'])
    op.create_index('ix_doctor_availabilities_available_date', 'doctor_availabilities', ['available_date'])

    # 5. medical_reports
    op.create_table(
        'medical_reports',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('report_type', sa.String(length=100), server_default='Blood Test', nullable=True),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_medical_reports_user_id', 'medical_reports', ['user_id'])

    # 6. biomarkers
    op.create_table(
        'biomarkers',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('report_id', sa.String(length=36), sa.ForeignKey('medical_reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('test_name', sa.String(length=255), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=True),
        sa.Column('value_numeric', sa.Float(), nullable=True),
        sa.Column('value_text', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('reference_min', sa.Float(), nullable=True),
        sa.Column('reference_max', sa.Float(), nullable=True),
        sa.Column('reference_text', sa.String(length=100), nullable=True),
        sa.Column('flag', sa.String(length=50), server_default='NORMAL', nullable=True),
        sa.Column('category', sa.String(length=100), server_default='General Panel', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_biomarkers_report_id', 'biomarkers', ['report_id'])
    op.create_index('ix_biomarkers_test_name', 'biomarkers', ['test_name'])
    op.create_index('ix_biomarkers_canonical_name', 'biomarkers', ['canonical_name'])

    # 7. report_analyses
    op.create_table(
        'report_analyses',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('report_id', sa.String(length=36), sa.ForeignKey('medical_reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plain_summary', sa.Text(), nullable=True),
        sa.Column('terminology_glossary', sa.JSON(), nullable=True),
        sa.Column('clinical_disclaimer', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_report_analyses_report_id', 'report_analyses', ['report_id'])

    # 8. symptom_logs
    op.create_table(
        'symptom_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symptoms', sa.JSON(), nullable=False),
        sa.Column('severity', sa.String(length=50), server_default='MILD', nullable=True),
        sa.Column('duration', sa.String(length=100), nullable=True),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('logged_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_symptom_logs_user_id', 'symptom_logs', ['user_id'])

    # 9. appointments
    op.create_table(
        'appointments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', sa.String(length=36), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slot_id', sa.String(length=36), sa.ForeignKey('doctor_availabilities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('appointment_date', sa.Date(), nullable=False),
        sa.Column('appointment_time', sa.Time(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='CONFIRMED', nullable=True),
        sa.Column('reason_for_visit', sa.Text(), nullable=True),
        sa.Column('cancelled_by', sa.String(length=50), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_appointments_user_id', 'appointments', ['user_id'])
    op.create_index('ix_appointments_doctor_id', 'appointments', ['doctor_id'])

    # 10. consultation_notes
    op.create_table(
        'consultation_notes',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('appointment_id', sa.String(length=36), sa.ForeignKey('appointments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', sa.String(length=36), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clinical_notes', sa.Text(), nullable=False),
        sa.Column('prescriptions', sa.JSON(), nullable=True),
        sa.Column('follow_up_instructions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_consultation_notes_appointment_id', 'consultation_notes', ['appointment_id'])
    op.create_index('ix_consultation_notes_doctor_id', 'consultation_notes', ['doctor_id'])

    # 11. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('actor_user_id', sa.String(length=36), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('log_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_actor_user_id', 'audit_logs', ['actor_user_id'])

    # 12. biomarker_references
    op.create_table(
        'biomarker_references',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('test_name', sa.String(length=255), unique=True, nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('default_unit', sa.String(length=50), nullable=True),
        sa.Column('ref_min', sa.Float(), nullable=True),
        sa.Column('ref_max', sa.Float(), nullable=True),
        sa.Column('critical_low', sa.Float(), nullable=True),
        sa.Column('critical_high', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_biomarker_references_test_name', 'biomarker_references', ['test_name'])
    op.create_index('ix_biomarker_references_canonical_name', 'biomarker_references', ['canonical_name'])

    # 13. glossary_terms
    op.create_table(
        'glossary_terms',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('term', sa.String(length=255), unique=True, nullable=False),
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('reviewed_by', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_glossary_terms_term', 'glossary_terms', ['term'])

    # 14. refresh_tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(length=500), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'])

    # 15. specialty_recommendations
    op.create_table(
        'specialty_recommendations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('report_analysis_id', sa.String(length=36), sa.ForeignKey('report_analyses.id', ondelete='CASCADE'), nullable=True),
        sa.Column('symptom_log_id', sa.String(length=36), sa.ForeignKey('symptom_logs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommended_specialty_id', sa.String(length=36), sa.ForeignKey('medical_specialties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), server_default='0.85', nullable=True),
        sa.Column('is_emergency_flagged', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('review_status', sa.String(length=50), server_default='UNREVIEWED', nullable=True),
        sa.Column('reviewed_by', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index('ix_specialty_recommendations_review_status', 'specialty_recommendations', ['review_status'])

def downgrade() -> None:
    op.drop_table('specialty_recommendations')
    op.drop_table('refresh_tokens')
    op.drop_table('glossary_terms')
    op.drop_table('biomarker_references')
    op.drop_table('audit_logs')
    op.drop_table('consultation_notes')
    op.drop_table('appointments')
    op.drop_table('symptom_logs')
    op.drop_table('report_analyses')
    op.drop_table('biomarkers')
    op.drop_table('medical_reports')
    op.drop_table('doctor_availabilities')
    op.drop_table('doctors')
    op.drop_table('medical_specialties')
    op.drop_table('users')
