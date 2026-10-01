import os
import sys
import subprocess
import argparse
from datetime import datetime
from urllib.parse import urlparse

def find_pg_dump():
    # Check PATH first
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, "pg_dump.exe" if os.name == "nt" else "pg_dump")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    # Default common Windows install locations
    for ver in ["18", "17", "16", "15", "14"]:
        candidate = rf"C:\Program Files\PostgreSQL\{ver}\bin\pg_dump.exe"
        if os.path.isfile(candidate):
            return candidate
    return "pg_dump"

def backup_postgres(db_url: str = None, output_dir: str = "backups") -> str:
    if not db_url:
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/vitalens_db")

    # Normalize asyncpg URL to standard postgresql
    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip("/")
    user = parsed.username or "postgres"
    password = parsed.password or "admin"
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 5432)

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(output_dir, f"{db_name}_backup_{timestamp}.dump")

    pg_dump_bin = find_pg_dump()
    print(f"[*] Starting PostgreSQL backup for database '{db_name}'...")
    print(f"[*] Target backup file: {backup_file}")

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    cmd = [
        pg_dump_bin,
        "-h", host,
        "-p", port,
        "-U", user,
        "-F", "c", # Custom binary compressed format
        "-b",      # Include large objects
        "-v",      # Verbose
        "-f", backup_file,
        db_name
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Backup failed: {result.stderr}")
        raise RuntimeError(f"pg_dump failed with exit code {result.returncode}")

    file_size_kb = os.path.getsize(backup_file) / 1024.0
    print(f"[OK] Backup successfully created: {backup_file} ({file_size_kb:.2f} KB)")
    return os.path.abspath(backup_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VitaLens PostgreSQL Automated Backup Utility")
    parser.add_argument("--db-url", help="Database URL to backup (defaults to DATABASE_URL or dev DB)")
    parser.add_argument("--output-dir", default="backups", help="Destination folder for dump files")
    args = parser.parse_args()

    try:
        backup_postgres(args.db_url, args.output_dir)
    except Exception as e:
        print(f"[!] Error during backup: {e}")
        sys.exit(1)
