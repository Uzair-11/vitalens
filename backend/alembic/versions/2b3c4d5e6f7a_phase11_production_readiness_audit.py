"""phase11_production_readiness_audit

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-10-01 20:34:34.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b3c4d5e6f7a'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$ BEGIN
        -- 1. users table
        BEGIN
            ALTER TABLE users ADD COLUMN phone_verified BOOLEAN NOT NULL DEFAULT false;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT false;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT false;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN verified_at TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN first_name VARCHAR(100);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN last_name VARCHAR(100);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN address_line1 VARCHAR(255);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN address_line2 VARCHAR(255);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN city VARCHAR(100);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN state VARCHAR(100);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN postal_code VARCHAR(20);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN country VARCHAR(50) DEFAULT 'India';
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN registration_ip VARCHAR(45);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(45);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN data_retention_expires_at TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE users ADD COLUMN account_locked_until TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 2. doctors table
        BEGIN
            ALTER TABLE doctors ADD COLUMN registration_number VARCHAR(100);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE doctors ADD CONSTRAINT uq_doctors_registration_number UNIQUE(registration_number);
        EXCEPTION
            WHEN duplicate_table THEN null;
            WHEN duplicate_object THEN null;
        END;
        BEGIN
            ALTER TABLE doctors ADD COLUMN registration_council VARCHAR(100);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE doctors ADD COLUMN state_code VARCHAR(10);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE doctors ADD COLUMN email VARCHAR(255);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE doctors ADD COLUMN phone VARCHAR(50);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE doctors ADD COLUMN gender VARCHAR(20);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE doctors ADD COLUMN consultation_mode VARCHAR(50) DEFAULT 'HYBRID';
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 3. appointments table
        BEGIN
            ALTER TABLE appointments ADD COLUMN booking_reference VARCHAR(20);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE appointments ADD COLUMN cancelled_at TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE appointments ADD COLUMN cancelled_by_user_id VARCHAR(36);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 4. consents table
        BEGIN
            ALTER TABLE consents ADD COLUMN consent_version VARCHAR(20) NOT NULL DEFAULT '1.0';
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE consents ADD COLUMN purpose VARCHAR(255);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE consents ADD COLUMN ip_address VARCHAR(45);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE consents ADD COLUMN user_agent VARCHAR(500);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 5. audit_logs table
        BEGIN
            ALTER TABLE audit_logs ADD COLUMN user_agent VARCHAR(500);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE audit_logs ADD COLUMN session_id VARCHAR(100);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 6. medical_reports table
        BEGIN
            ALTER TABLE medical_reports ADD COLUMN file_hash_sha256 VARCHAR(64);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE medical_reports ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE medical_reports ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 7. consultation_notes table
        BEGIN
            ALTER TABLE consultation_notes ADD COLUMN is_finalized BOOLEAN NOT NULL DEFAULT false;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE consultation_notes ADD COLUMN finalized_at TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 8. doctor_availabilities table
        BEGIN
            ALTER TABLE doctor_availabilities ADD COLUMN booked_appointment_id VARCHAR(36);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 9. notification_logs table
        BEGIN
            ALTER TABLE notification_logs ADD COLUMN sent_at TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 10. doctor_working_hours table
        BEGIN
            ALTER TABLE doctor_working_hours ADD CONSTRAINT uq_doctor_working_hours_doctor_day_time UNIQUE (doctor_id, day_of_week, start_time);
        EXCEPTION
            WHEN duplicate_table THEN null;
            WHEN duplicate_object THEN null;
        END;

        -- 11. biomarker_references table
        BEGIN
            ALTER TABLE biomarker_references ADD COLUMN synonyms JSON DEFAULT '[]'::json;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE biomarker_references ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 12. ai_interaction_logs table
        BEGIN
            ALTER TABLE ai_interaction_logs ADD COLUMN response_time_ms INTEGER;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 13. medical_specialties table
        BEGIN
            ALTER TABLE medical_specialties ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 14. symptom_logs table
        BEGIN
            ALTER TABLE symptom_logs ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE symptom_logs ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 15. report_analyses table
        BEGIN
            ALTER TABLE report_analyses ADD COLUMN model_version VARCHAR(100);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;

        -- 16. refresh_tokens table
        BEGIN
            ALTER TABLE refresh_tokens ADD COLUMN device_info VARCHAR(255);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE refresh_tokens ADD COLUMN user_agent VARCHAR(500);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
        BEGIN
            ALTER TABLE refresh_tokens ADD COLUMN ip_address VARCHAR(50);
        EXCEPTION
            WHEN duplicate_column THEN null;
        END;
    END $$;
    """)

    # Indices
    op.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_appointments_booking_reference') THEN
            CREATE UNIQUE INDEX ix_appointments_booking_reference ON appointments(booking_reference);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_users_city') THEN
            CREATE INDEX ix_users_city ON users(city);
        END IF;
    END $$;
    """)


def downgrade():
    op.execute("""
    DO $$ BEGIN
        -- 16. refresh_tokens table
        ALTER TABLE refresh_tokens DROP COLUMN IF EXISTS ip_address;
        ALTER TABLE refresh_tokens DROP COLUMN IF EXISTS user_agent;
        ALTER TABLE refresh_tokens DROP COLUMN IF EXISTS device_info;

        -- 15. report_analyses table
        ALTER TABLE report_analyses DROP COLUMN IF EXISTS model_version;

        -- 14. symptom_logs table
        ALTER TABLE symptom_logs DROP COLUMN IF EXISTS deleted_at;
        ALTER TABLE symptom_logs DROP COLUMN IF EXISTS is_deleted;

        -- 13. medical_specialties table
        ALTER TABLE medical_specialties DROP COLUMN IF EXISTS is_active;

        -- 12. ai_interaction_logs table
        ALTER TABLE ai_interaction_logs DROP COLUMN IF EXISTS response_time_ms;

        -- 11. biomarker_references table
        ALTER TABLE biomarker_references DROP COLUMN IF EXISTS is_active;
        ALTER TABLE biomarker_references DROP COLUMN IF EXISTS synonyms;

        -- 10. doctor_working_hours table
        ALTER TABLE doctor_working_hours DROP CONSTRAINT IF EXISTS uq_doctor_working_hours_doctor_day_time;

        -- 9. notification_logs table
        ALTER TABLE notification_logs DROP COLUMN IF EXISTS sent_at;

        -- 8. doctor_availabilities table
        ALTER TABLE doctor_availabilities DROP COLUMN IF EXISTS booked_appointment_id;

        -- 7. consultation_notes table
        ALTER TABLE consultation_notes DROP COLUMN IF EXISTS finalized_at;
        ALTER TABLE consultation_notes DROP COLUMN IF EXISTS is_finalized;

        -- 6. medical_reports table
        ALTER TABLE medical_reports DROP COLUMN IF EXISTS deleted_at;
        ALTER TABLE medical_reports DROP COLUMN IF EXISTS is_deleted;
        ALTER TABLE medical_reports DROP COLUMN IF EXISTS file_hash_sha256;

        -- 5. audit_logs table
        ALTER TABLE audit_logs DROP COLUMN IF EXISTS session_id;
        ALTER TABLE audit_logs DROP COLUMN IF EXISTS user_agent;

        -- 4. consents table
        ALTER TABLE consents DROP COLUMN IF EXISTS user_agent;
        ALTER TABLE consents DROP COLUMN IF EXISTS ip_address;
        ALTER TABLE consents DROP COLUMN IF EXISTS purpose;
        ALTER TABLE consents DROP COLUMN IF EXISTS consent_version;

        -- 3. appointments table
        DROP INDEX IF EXISTS ix_appointments_booking_reference;
        ALTER TABLE appointments DROP COLUMN IF EXISTS cancelled_by_user_id;
        ALTER TABLE appointments DROP COLUMN IF EXISTS cancelled_at;
        ALTER TABLE appointments DROP COLUMN IF EXISTS booking_reference;

        -- 2. doctors table
        ALTER TABLE doctors DROP COLUMN IF EXISTS consultation_mode;
        ALTER TABLE doctors DROP COLUMN IF EXISTS gender;
        ALTER TABLE doctors DROP COLUMN IF EXISTS phone;
        ALTER TABLE doctors DROP COLUMN IF EXISTS email;
        ALTER TABLE doctors DROP COLUMN IF EXISTS state_code;
        ALTER TABLE doctors DROP COLUMN IF EXISTS registration_council;
        ALTER TABLE doctors DROP CONSTRAINT IF EXISTS uq_doctors_registration_number;
        ALTER TABLE doctors DROP COLUMN IF EXISTS registration_number;

        -- 1. users table
        DROP INDEX IF EXISTS ix_users_city;
        ALTER TABLE users DROP COLUMN IF EXISTS account_locked_until;
        ALTER TABLE users DROP COLUMN IF EXISTS data_retention_expires_at;
        ALTER TABLE users DROP COLUMN IF EXISTS last_login_at;
        ALTER TABLE users DROP COLUMN IF EXISTS last_login_ip;
        ALTER TABLE users DROP COLUMN IF EXISTS registration_ip;
        ALTER TABLE users DROP COLUMN IF EXISTS country;
        ALTER TABLE users DROP COLUMN IF EXISTS postal_code;
        ALTER TABLE users DROP COLUMN IF EXISTS state;
        ALTER TABLE users DROP COLUMN IF EXISTS city;
        ALTER TABLE users DROP COLUMN IF EXISTS address_line2;
        ALTER TABLE users DROP COLUMN IF EXISTS address_line1;
        ALTER TABLE users DROP COLUMN IF EXISTS last_name;
        ALTER TABLE users DROP COLUMN IF EXISTS first_name;
        ALTER TABLE users DROP COLUMN IF EXISTS verified_at;
        ALTER TABLE users DROP COLUMN IF EXISTS is_verified;
        ALTER TABLE users DROP COLUMN IF EXISTS email_verified;
        ALTER TABLE users DROP COLUMN IF EXISTS phone_verified;
    END $$;
    """)
