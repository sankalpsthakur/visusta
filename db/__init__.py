"""
MARS database package.

Exports:
    get_db          — context manager yielding a configured sqlite3.Connection
    get_connection  — open a raw connection (caller responsible for close)
    run_migrations  — apply pending .sql migrations from db/migrations/
"""

from db.connection import get_connection, get_db
from db.migrate import run_migrations

__all__ = ["get_db", "get_connection", "run_migrations"]
