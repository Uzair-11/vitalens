import sqlite3
import os

def sync_db():
    db_path = os.path.join(os.path.dirname(__file__), "..", "health_app.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    existing_cols = {col[1] for col in cur.execute("PRAGMA table_info(users)").fetchall()}
    print(f"Existing columns in users: {len(existing_cols)}")

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
        ("is_verified", "BOOLEAN DEFAULT 0"),
        ("verified_at", "DATETIME"),
        ("phone_verified", "BOOLEAN DEFAULT 0"),
        ("email_verified", "BOOLEAN DEFAULT 0"),
        ("last_login_at", "DATETIME"),
        ("data_retention_expires_at", "DATETIME"),
        ("account_locked_until", "DATETIME"),
        ("deleted_at", "DATETIME"),
    ]

    for col_name, col_type in cols_to_add:
        if col_name not in existing_cols:
            print(f"Adding column '{col_name}' ({col_type}) to users...")
            cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

    # Create email_otps table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS email_otps (
        id VARCHAR(36) PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        otp_code VARCHAR(10) NOT NULL,
        purpose VARCHAR(50) NOT NULL,
        attempts INTEGER DEFAULT 0 NOT NULL,
        is_used BOOLEAN DEFAULT 0 NOT NULL,
        expires_at DATETIME NOT NULL,
        created_at DATETIME NOT NULL
    )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS ix_email_otps_email ON email_otps (email)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_email_otps_purpose ON email_otps (purpose)")

    con.commit()
    con.close()
    print("Schema sync completed successfully!")

if __name__ == "__main__":
    sync_db()
