"""phase7_payments_and_notifications

Revision ID: 8b9c0d1e2f3a
Revises: 7a8b9c0d1e2f
Create Date: 2026-08-30 21:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b9c0d1e2f3a'
down_revision: Union[str, Sequence[str], None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add payment columns to appointments table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_status') THEN
                ALTER TABLE appointments ADD COLUMN payment_status VARCHAR(50) NOT NULL DEFAULT 'PAID';
                CREATE INDEX ix_appointments_payment_status ON appointments(payment_status);
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_id') THEN
                ALTER TABLE appointments ADD COLUMN payment_id VARCHAR(100);
                CREATE INDEX ix_appointments_payment_id ON appointments(payment_id);
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_order_id') THEN
                ALTER TABLE appointments ADD COLUMN payment_order_id VARCHAR(100);
                CREATE INDEX ix_appointments_payment_order_id ON appointments(payment_order_id);
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_amount') THEN
                ALTER TABLE appointments ADD COLUMN payment_amount VARCHAR(50);
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_currency') THEN
                ALTER TABLE appointments ADD COLUMN payment_currency VARCHAR(10) DEFAULT 'INR';
            END IF;
        END $$;
    """)

    # 2. Create notification_logs table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'notification_logs') THEN
                CREATE TABLE notification_logs (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    recipient VARCHAR(255) NOT NULL,
                    notification_type VARCHAR(50) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    subject VARCHAR(255),
                    body TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX ix_notification_logs_user_id ON notification_logs(user_id);
                CREATE INDEX ix_notification_logs_status ON notification_logs(status);
                CREATE INDEX ix_notification_logs_event_type ON notification_logs(event_type);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notification_logs CASCADE;")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_status') THEN
                ALTER TABLE appointments DROP COLUMN payment_status;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_id') THEN
                ALTER TABLE appointments DROP COLUMN payment_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_order_id') THEN
                ALTER TABLE appointments DROP COLUMN payment_order_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_amount') THEN
                ALTER TABLE appointments DROP COLUMN payment_amount;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'payment_currency') THEN
                ALTER TABLE appointments DROP COLUMN payment_currency;
            END IF;
        END $$;
    """)
