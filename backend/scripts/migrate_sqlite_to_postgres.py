"""
VitaLens Database Migration Utility: SQLite to PostgreSQL
Initializes target PostgreSQL schema and copies existing records row-by-row without data loss.

Usage:
    python scripts/migrate_sqlite_to_postgres.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import sqlite3
import asyncio
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
from app.models import *  # Register all models for metadata creation

TABLE_ORDER = [
    "users",
    "medical_specialties",
    "doctors",
    "doctor_availabilities",
    "medical_reports",
    "biomarkers",
    "report_analyses",
    "symptom_logs",
    "specialty_recommendations",
    "appointments",
    "refresh_tokens",
    "audit_logs",
    "consultation_notes",
    "consents",
    "biomarker_references",
    "glossary_terms"
]

BOOLEAN_COLUMNS = {
    "users": ["is_active", "is_deleted"],
    "doctors": ["is_active"],
    "doctor_availabilities": ["is_booked"],
    "specialty_recommendations": ["is_emergency_flagged"],
    "refresh_tokens": ["revoked"],
    "consents": ["granted"],
}

async def init_pg_schema(async_pg_url: str):
    """Initializes tables on PostgreSQL using SQLAlchemy metadata."""
    print(f">> Initializing PostgreSQL schema on {async_pg_url.split('@')[-1]}...")
    engine = create_async_engine(async_pg_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print(">> PostgreSQL schema initialized successfully.")

def migrate(sqlite_path: str, sync_pg_url: str, async_pg_url: str):
    print(f">> Starting SQLite to PostgreSQL migration from '{sqlite_path}'...")
    if not os.path.exists(sqlite_path):
        print(f"[!] Source SQLite file '{sqlite_path}' does not exist.")
        sys.exit(1)

    # 1. Initialize schema in PostgreSQL
    asyncio.run(init_pg_schema(async_pg_url))

    # 2. Open source and destination connections
    src_conn = sqlite3.connect(sqlite_path)
    src_conn.row_factory = sqlite3.Row
    src_cur = src_conn.cursor()

    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("[!] Error: psycopg2 is required. Install via 'pip install psycopg2-binary'")
        sys.exit(1)

    dest_conn = psycopg2.connect(sync_pg_url)
    dest_cur = dest_conn.cursor()

    migration_report = {}

    for table in TABLE_ORDER:
        try:
            # Get PostgreSQL table columns
            dest_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            dest_cols = {r[0]: r[1] for r in dest_cur.fetchall()}
            if not dest_cols:
                continue

            # Get SQLite table columns
            src_cur.execute(f"PRAGMA table_info({table})")
            src_cols = [c["name"] for c in src_cur.fetchall()]

            # Common matching columns
            common_cols = [c for c in src_cols if c in dest_cols]
            if not common_cols:
                continue

            bool_cols = BOOLEAN_COLUMNS.get(table, [])

            src_cur.execute(f"SELECT * FROM {table}")
            rows = src_cur.fetchall()
            if not rows:
                migration_report[table] = 0
                print(f"[*] {table:26}: 0 rows")
                continue

            cleaned_rows = []
            for row in rows:
                row_dict = dict(row)
                for b_col in bool_cols:
                    if b_col in row_dict and row_dict[b_col] is not None:
                        row_dict[b_col] = bool(row_dict[b_col])
                cleaned_rows.append(tuple(row_dict[c] for c in common_cols))

            escaped_cols = ", ".join([f'"{c}"' for c in common_cols])
            placeholders = ", ".join(["%s"] * len(common_cols))
            insert_stmt = f"INSERT INTO {table} ({escaped_cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

            psycopg2.extras.execute_batch(dest_cur, insert_stmt, cleaned_rows)
            dest_conn.commit()
            migration_report[table] = len(cleaned_rows)
            print(f"[OK] Migrated {table:26}: {len(cleaned_rows)} rows")
        except Exception as e:
            dest_conn.rollback()
            print(f"[!] Error on table '{table}': {str(e)}")

    src_conn.close()
    dest_conn.close()
    print("\n" + "="*50)
    print(">> MIGRATION COMPLETE SUMMARY:")
    for t, count in migration_report.items():
        print(f"   • {t:26}: {count} rows")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate VitaLens SQLite database to PostgreSQL.")
    parser.add_argument("--sqlite-path", default="health_app.db", help="Path to source SQLite database file")
    parser.add_argument("--sync-pg-url", default="postgresql://postgres:admin@localhost:5432/vitalens_db", help="Synchronous psycopg2 connection string")
    parser.add_argument("--async-pg-url", default="postgresql+asyncpg://postgres:admin@localhost:5432/vitalens_db", help="Asyncpg connection string")
    args = parser.parse_args()

    migrate(args.sqlite_path, args.sync_pg_url, args.async_pg_url)
