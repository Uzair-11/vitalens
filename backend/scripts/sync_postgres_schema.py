import asyncio
from app.core.database import engine
from sqlalchemy import text

async def sync_pg():
    async with engine.begin() as conn:
        cols = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'users';"
        ))
        existing_cols = {r[0] for r in cols.fetchall()}
        print(f"Postgres existing cols in users: {len(existing_cols)}")

        cols_to_add = [
            ("first_name", "VARCHAR(100)"),
            ("last_name", "VARCHAR(100)"),
            ("address_line1", "VARCHAR(255)"),
            ("address_line2", "VARCHAR(255)"),
            ("city", "VARCHAR(100)"),
            ("state", "VARCHAR(100)"),
            ("postal_code", "VARCHAR(20)"),
            ("country", "VARCHAR(50) DEFAULT 'India'"),
            ("registration_ip", "VARCHAR(45)"),
            ("last_login_ip", "VARCHAR(45)"),
            ("is_verified", "BOOLEAN DEFAULT false"),
            ("verified_at", "TIMESTAMPTZ"),
            ("phone_verified", "BOOLEAN DEFAULT false"),
            ("email_verified", "BOOLEAN DEFAULT false"),
            ("last_login_at", "TIMESTAMPTZ"),
            ("data_retention_expires_at", "TIMESTAMPTZ"),
            ("account_locked_until", "TIMESTAMPTZ"),
            ("deleted_at", "TIMESTAMPTZ"),
        ]

        for col_name, col_type in cols_to_add:
            if col_name not in existing_cols:
                print(f"Adding column '{col_name}' to users...")
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))

        # Create email_otps table
        print("Creating email_otps table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS email_otps (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                otp_code VARCHAR(10) NOT NULL,
                purpose VARCHAR(50) NOT NULL,
                attempts INTEGER DEFAULT 0 NOT NULL,
                is_used BOOLEAN DEFAULT false NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            );
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_otps_email ON email_otps (email);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_otps_purpose ON email_otps (purpose);"))
        print("Postgres sync completed successfully!")

if __name__ == "__main__":
    asyncio.run(sync_pg())
