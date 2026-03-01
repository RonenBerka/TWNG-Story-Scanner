"""Seed script: ensures DB schema is up-to-date and reports admin credentials.

Usage:
    python -m app.db.seed
"""

import os
import subprocess
import sys


def run_seed() -> None:
    print("=== TWNG Story Scanner — Seed ===\n")

    # 1. Run Alembic migrations
    print("[1/2] Running Alembic migrations …")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: Alembic failed:\n{result.stderr}")
        sys.exit(1)
    for line in result.stdout.strip().splitlines():
        print(f"  {line}")
    for line in result.stderr.strip().splitlines():
        if line.startswith("INFO"):
            print(f"  {line}")
    print()

    # 2. Report admin credentials (env-var based, no DB user table)
    admin_user = os.environ.get("ADMIN_USERNAME", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin")
    print("[2/2] Admin credentials (from environment):")
    print(f"  Username : {admin_user}")
    print(f"  Password : {admin_pass}")
    print()
    print("Seed complete. Ready to ingest and curate stories.")


if __name__ == "__main__":
    run_seed()
