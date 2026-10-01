"""
Migration 001: Add User Role and Doctor User FK with Backfill.
Applies schema alterations and backfills demo patient, doctor, and admin role assignments.
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def run_sqlite_migration(db_path: str = "health_app.db"):
    if not os.path.exists(db_path):
        print(f"[*] SQLite file '{db_path}' not found, skipping SQLite migration.")
        return

    print(f">> Running Migration 001 on SQLite '{db_path}'...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Add role column to users if not present
    cur.execute("PRAGMA table_info(users)")
    cols = [c[1] for c in cur.fetchall()]
    if "role" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'PATIENT'")
        print("   + Added 'role' column to users")

    # 2. Add user_id column to doctors if not present
    cur.execute("PRAGMA table_info(doctors)")
    doc_cols = [c[1] for c in cur.fetchall()]
    if "user_id" not in doc_cols:
        cur.execute("ALTER TABLE doctors ADD COLUMN user_id VARCHAR(36)")
        print("   + Added 'user_id' column to doctors")

    # 3. Backfill roles
    cur.execute("UPDATE users SET role = 'PATIENT' WHERE role IS NULL")
    cur.execute("UPDATE users SET role = 'PATIENT' WHERE email = 'demo@healthapp.com'")
    cur.execute("UPDATE users SET role = 'DOCTOR' WHERE email = 'doctor.jenkins@vitalens.health'")
    cur.execute("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@vitalens.health'")
    conn.commit()

    # 4. Link doctor.jenkins user to Dr. Sarah Jenkins doctor profile
    cur.execute("SELECT id FROM users WHERE email = 'doctor.jenkins@vitalens.health'")
    doc_user = cur.fetchone()
    if doc_user:
        doc_user_id = doc_user[0]
        cur.execute("UPDATE doctors SET user_id = ? WHERE full_name LIKE '%Jenkins%'", (doc_user_id,))
        conn.commit()
        print("   + Linked doctor.jenkins user identity to Doctor record.")

    conn.close()
    print(">> SQLite Migration 001 completed successfully.")

def run_postgres_migration(pg_url: str):
    print(f">> Running Migration 001 on PostgreSQL...")
    try:
        import psycopg2
    except ImportError:
        print("[!] psycopg2-binary not installed, skipping Postgres migration.")
        return

    try:
        conn = psycopg2.connect(pg_url)
        conn.autocommit = True
        cur = conn.cursor()

        # 1. Add role column to users if not present
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role') THEN
                    ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'PATIENT' NOT NULL;
                END IF;
            END $$;
        """)

        # 2. Add user_id column to doctors if not present
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='doctors' AND column_name='user_id') THEN
                    ALTER TABLE doctors ADD COLUMN user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;
                END IF;
            END $$;
        """)

        # 3. Backfill roles
        cur.execute("UPDATE users SET role = 'PATIENT' WHERE role IS NULL;")
        cur.execute("UPDATE users SET role = 'PATIENT' WHERE email = 'demo@healthapp.com';")
        cur.execute("UPDATE users SET role = 'DOCTOR' WHERE email = 'doctor.jenkins@vitalens.health';")
        cur.execute("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@vitalens.health';")

        # 4. Link doctor user identity
        cur.execute("SELECT id FROM users WHERE email = 'doctor.jenkins@vitalens.health';")
        doc_user = cur.fetchone()
        if doc_user:
            doc_user_id = doc_user[0]
            cur.execute("UPDATE doctors SET user_id = %s WHERE full_name LIKE '%%Jenkins%%';", (doc_user_id,))
            print("   + Linked doctor.jenkins user identity to Doctor record in Postgres.")

        conn.close()
        print(">> PostgreSQL Migration 001 completed successfully.")
    except Exception as e:
        print(f"[!] PostgreSQL Migration 001 notice: {e}")

if __name__ == "__main__":
    run_sqlite_migration()
    pg_sync_url = os.environ.get("SYNC_DATABASE_URL", "postgresql://postgres:admin@localhost:5432/vitalens_db")
    run_postgres_migration(pg_sync_url)
