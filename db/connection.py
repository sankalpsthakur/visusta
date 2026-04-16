"""
SQLite connection factory for the MARS database.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# Module-level path — monkeypatch this in tests:
#   monkeypatch.setattr("db.connection.DB_PATH", tmp_path / "test.db")
DB_PATH: Path = Path(__file__).parent.parent / "data" / "visusta.db"


def get_connection() -> sqlite3.Connection:
    """Open and configure a raw SQLite connection to DB_PATH."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # timeout=30 raises Python's wait-for-lock from the 5s default. Backed up
    # by busy_timeout so concurrent writers also wait at the SQLite layer.
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding a configured connection with auto commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
