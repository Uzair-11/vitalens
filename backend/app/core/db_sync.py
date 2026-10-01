import sqlite3
import os

def sync_sqlite_schema(db_path: str = "health_app.db"):
    """
    Ensures all newly added columns and constraints exist in the local SQLite database
    without needing manual table drop.
    """
    try:
        if not os.path.exists(db_path):
            return

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        def add_column_if_missing(table: str, col_name: str, col_type: str):
            try:
                cur.execute(f"PRAGMA table_info({table})")
                cols = [c[1] for c in cur.fetchall()]
                if cols and col_name not in cols:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    conn.commit()
            except Exception:
                pass

        # users
        add_column_if_missing("users", "role", "VARCHAR(50) DEFAULT 'PATIENT'")
        add_column_if_missing("users", "is_active", "BOOLEAN DEFAULT 1")
        add_column_if_missing("users", "is_deleted", "BOOLEAN DEFAULT 0")
        add_column_if_missing("users", "created_at", "DATETIME")
        add_column_if_missing("users", "updated_at", "DATETIME")

        # doctors
        add_column_if_missing("doctors", "user_id", "VARCHAR(36)")
        add_column_if_missing("doctors", "verification_status", "VARCHAR(50) DEFAULT 'VERIFIED'")
        add_column_if_missing("doctors", "credential_documents", "JSON")
        add_column_if_missing("doctors", "is_active", "BOOLEAN DEFAULT 1")
        add_column_if_missing("doctors", "created_at", "DATETIME")
        add_column_if_missing("doctors", "updated_at", "DATETIME")

        # specialty_recommendations
        add_column_if_missing("specialty_recommendations", "review_status", "VARCHAR(50) DEFAULT 'UNREVIEWED'")
        add_column_if_missing("specialty_recommendations", "reviewed_by", "VARCHAR(255)")
        add_column_if_missing("specialty_recommendations", "reviewed_at", "DATETIME")
        add_column_if_missing("specialty_recommendations", "created_at", "DATETIME")

        # appointments
        add_column_if_missing("appointments", "created_at", "DATETIME")
        add_column_if_missing("appointments", "updated_at", "DATETIME")

        conn.close()
    except Exception as e:
        print(f"[!] SQLite schema sync notice: {e}")
