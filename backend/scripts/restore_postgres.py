import os
import sys
import subprocess
import argparse
from urllib.parse import urlparse

def find_pg_restore():
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, "pg_restore.exe" if os.name == "nt" else "pg_restore")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    for ver in ["18", "17", "16", "15", "14"]:
        candidate = rf"C:\Program Files\PostgreSQL\{ver}\bin\pg_restore.exe"
        if os.path.isfile(candidate):
            return candidate
    return "pg_restore"

def restore_postgres(dump_file: str, target_db: str = "vitalens_restore_drill", db_url: str = None) -> bool:
    if not os.path.isfile(dump_file):
        raise FileNotFoundError(f"Dump file not found: {dump_file}")

    if not db_url:
        db_url = os.getenv("DATABASE_URL", f"postgresql://postgres:admin@localhost:5432/{target_db}")

    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    parsed = urlparse(db_url)
    db_name = target_db or parsed.path.lstrip("/")
    user = parsed.username or "postgres"
    password = parsed.password or "admin"
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 5432)

    pg_restore_bin = find_pg_restore()
    print(f"[*] Starting restore of '{dump_file}' into database '{db_name}'...")

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    cmd = [
        pg_restore_bin,
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", db_name,
        "--clean",           # Clean (drop) database objects before recreating
        "--if-exists",       # Use IF EXISTS when dropping objects
        "--no-owner",        # Skip restoration of object ownership
        "-v",
        dump_file
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    # pg_restore returns 0 on success, or 1 if non-fatal warnings occurred (e.g., dropping non-existent tables)
    if result.returncode not in [0, 1]:
        print(f"[!] Restore encountered fatal errors: {result.stderr}")
        raise RuntimeError(f"pg_restore failed with exit code {result.returncode}")

    print(f"[OK] Restore into database '{db_name}' completed successfully.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VitaLens PostgreSQL Automated Restore Utility")
    parser.add_argument("--dump-file", required=True, help="Path to .dump file to restore")
    parser.add_argument("--target-db", default="vitalens_restore_drill", help="Target database name")
    parser.add_argument("--db-url", help="Full target database URL")
    args = parser.parse_args()

    try:
        restore_postgres(args.dump_file, args.target_db, args.db_url)
    except Exception as e:
        print(f"[!] Error during restore: {e}")
        sys.exit(1)
