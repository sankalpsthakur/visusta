"""
Simple migration runner for the MARS SQLite database.

Reads .sql files from db/migrations/ in sorted order, applies each one
that has not already been recorded in the _migrations table.
"""

from __future__ import annotations

from pathlib import Path

from db.connection import get_db

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

_BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS _migrations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    filename   TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""


def run_migrations() -> list[str]:
    """
    Apply all pending migrations. Returns list of filenames applied this run.

    The _migrations table is created by this runner (not by a migration file)
    to avoid a bootstrap chicken-and-egg problem.
    """
    applied: list[str] = []

    with get_db() as conn:
        conn.executescript(_BOOTSTRAP_SQL)

        already_applied = {
            row["filename"]
            for row in conn.execute("SELECT filename FROM _migrations").fetchall()
        }

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for migration_path in migration_files:
            filename = migration_path.name
            if filename in already_applied:
                continue

            sql = migration_path.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _migrations (filename) VALUES (?)", (filename,)
            )
            applied.append(filename)

    return applied
