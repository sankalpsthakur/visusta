"""
Tests for MARS SQLite schema, migration runner, and CRUD operations.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from freezegun import freeze_time

import db.connection as db_connection_module
from db.connection import get_connection, get_db
from db.migrate import run_migrations


# ── Helpers ────────────────────────────────────────────────────────────────────

@pytest.fixture()
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect DB_PATH to a temp file and run migrations. Yields the db path."""
    test_db = tmp_path / "test_mars.db"
    monkeypatch.setattr(db_connection_module, "DB_PATH", test_db)
    run_migrations()
    return test_db


# ── Migration runner ───────────────────────────────────────────────────────────

def test_migrations_create_migrations_table(isolated_db: Path) -> None:
    conn = sqlite3.connect(str(isolated_db))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='_migrations'"
    ).fetchall()
    conn.close()
    assert len(rows) == 1


def test_migrations_applied_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    test_db = tmp_path / "idempotent.db"
    monkeypatch.setattr(db_connection_module, "DB_PATH", test_db)

    first_run = run_migrations()
    second_run = run_migrations()

    assert len(first_run) == 3          # 001 + 002 + 003
    assert second_run == []             # nothing left to apply


def test_all_tables_created(isolated_db: Path) -> None:
    conn = sqlite3.connect(str(isolated_db))
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '\\_%' ESCAPE '\\'"
        ).fetchall()
    }
    conn.close()

    expected = {
        "locales",
        "client_locale_settings",
        "industry_profiles",
        "keyword_rules",
        "source_proposals",
        "report_templates",
        "template_versions",
        "client_template_overrides",
        "report_drafts",
        "draft_revisions",
        "draft_chat_messages",
        "approval_states",
        "export_jobs",
    }
    assert expected.issubset(tables)


# ── Locales seed ───────────────────────────────────────────────────────────────

def test_26_locales_seeded(isolated_db: Path) -> None:
    conn = sqlite3.connect(str(isolated_db))
    count = conn.execute("SELECT COUNT(*) FROM locales").fetchone()[0]
    conn.close()
    assert count == 26


def test_english_locale_exists(isolated_db: Path) -> None:
    conn = sqlite3.connect(str(isolated_db))
    row = conn.execute("SELECT * FROM locales WHERE code='en'").fetchone()
    conn.close()
    assert row is not None
    assert row[1] == "English"


def test_all_expected_locale_codes_present(isolated_db: Path) -> None:
    expected_codes = {
        "bg", "hr", "cs", "da", "nl", "en", "et", "fi", "fr", "de",
        "el", "hu", "ga", "it", "lv", "lt", "mt", "pl", "pt", "ro",
        "sk", "sl", "es", "sv", "nb", "nn",
    }
    conn = sqlite3.connect(str(isolated_db))
    codes = {row[0] for row in conn.execute("SELECT code FROM locales").fetchall()}
    conn.close()
    assert codes == expected_codes


# ── get_db context manager ─────────────────────────────────────────────────────

def test_get_db_commits_on_success(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO industry_profiles (name, config_json) VALUES (?, ?)",
            ("test-profile", "{}"),
        )
    # Read back in a fresh connection
    with get_db() as conn:
        row = conn.execute(
            "SELECT name FROM industry_profiles WHERE name='test-profile'"
        ).fetchone()
    assert row is not None


def test_get_db_rolls_back_on_error(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO industry_profiles (name, config_json) VALUES (?, ?)",
                ("rollback-profile", "{}"),
            )
            raise RuntimeError("intentional failure")
    except RuntimeError:
        pass

    with get_db() as conn:
        row = conn.execute(
            "SELECT name FROM industry_profiles WHERE name='rollback-profile'"
        ).fetchone()
    assert row is None


# ── keyword_rules CRUD ─────────────────────────────────────────────────────────

def test_keyword_rule_insert_and_fetch(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO keyword_rules (client_id, phrase, locale, weight) VALUES (?, ?, ?, ?)",
            ("client-1", "packaging waste", "en", 2.5),
        )
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM keyword_rules WHERE client_id='client-1'"
        ).fetchone()
    assert row is not None
    assert row["phrase"] == "packaging waste"
    assert row["weight"] == 2.5


def test_keyword_rule_unique_constraint(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO keyword_rules (client_id, phrase, locale) VALUES (?, ?, ?)",
            ("client-1", "duplicate", "en"),
        )
    with pytest.raises(Exception):
        with get_db() as conn:
            conn.execute(
                "INSERT INTO keyword_rules (client_id, phrase, locale) VALUES (?, ?, ?)",
                ("client-1", "duplicate", "en"),
            )


# ── source_proposals CRUD ──────────────────────────────────────────────────────

def test_source_proposal_default_status(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO source_proposals (client_id, url) VALUES (?, ?)",
            ("client-1", "https://eur-lex.europa.eu/"),
        )
    with get_db() as conn:
        row = conn.execute("SELECT status FROM source_proposals").fetchone()
    assert row["status"] == "pending"


def test_source_proposal_status_transition(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO source_proposals (client_id, url, status) VALUES (?, ?, ?)",
            ("client-1", "https://example.com", "approved"),
        )
    with get_db() as conn:
        row = conn.execute("SELECT status FROM source_proposals").fetchone()
    assert row["status"] == "approved"


# ── report_templates + template_versions CRUD ──────────────────────────────────

@freeze_time("2026-02-15")
def test_template_and_version_insert(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO report_templates (name, base_locale) VALUES (?, ?)",
            ("CSRD Q-Report", "en"),
        )
        tmpl_id = cur.lastrowid
        conn.execute(
            "INSERT INTO template_versions (template_id, version_number, sections_json) VALUES (?, ?, ?)",
            (tmpl_id, 1, json.dumps([{"section_id": "s1", "heading": "Executive Summary"}])),
        )

    with get_db() as conn:
        tmpl = conn.execute(
            "SELECT * FROM report_templates WHERE id=?", (tmpl_id,)
        ).fetchone()
        ver = conn.execute(
            "SELECT * FROM template_versions WHERE template_id=?", (tmpl_id,)
        ).fetchone()

    assert tmpl["name"] == "CSRD Q-Report"
    sections = json.loads(ver["sections_json"])
    assert sections[0]["section_id"] == "s1"


def test_template_version_unique_constraint(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO report_templates (name, base_locale) VALUES (?, ?)", ("T2", "en")
        )
        tmpl_id = cur.lastrowid
        conn.execute(
            "INSERT INTO template_versions (template_id, version_number, sections_json) VALUES (?, ?, ?)",
            (tmpl_id, 1, "[]"),
        )
    with pytest.raises(Exception):
        with get_db() as conn:
            conn.execute(
                "INSERT INTO template_versions (template_id, version_number, sections_json) VALUES (?, ?, ?)",
                (tmpl_id, 1, "[]"),
            )


# ── report_drafts CRUD ─────────────────────────────────────────────────────────

def test_draft_default_status(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO report_drafts (client_id, title, primary_locale) VALUES (?, ?, ?)",
            ("client-1", "Feb 2026 Report", "en"),
        )
    with get_db() as conn:
        row = conn.execute("SELECT status FROM report_drafts").fetchone()
    assert row["status"] == "composing"


def test_draft_invalid_status_rejected(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with pytest.raises(Exception):
        with get_db() as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute(
                "INSERT INTO report_drafts (client_id, title, status) VALUES (?, ?, ?)",
                ("client-1", "Bad Draft", "invalid_status"),
            )


# ── draft_revisions CRUD ───────────────────────────────────────────────────────

def test_draft_revision_history(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO report_drafts (client_id, title, primary_locale) VALUES (?, ?, ?)",
            ("client-1", "Draft A", "en"),
        )
        draft_id = cur.lastrowid

        sections_v1 = json.dumps([{"section_id": "intro", "heading": "Introduction", "locale": "en", "blocks": []}])
        sections_v2 = json.dumps([{"section_id": "intro", "heading": "Introduction Updated", "locale": "en", "blocks": []}])

        conn.execute(
            "INSERT INTO draft_revisions (draft_id, revision_number, sections_json, authored_by) VALUES (?, ?, ?, ?)",
            (draft_id, 1, sections_v1, "agent"),
        )
        conn.execute(
            "INSERT INTO draft_revisions (draft_id, revision_number, sections_json, authored_by) VALUES (?, ?, ?, ?)",
            (draft_id, 2, sections_v2, "human"),
        )

    with get_db() as conn:
        revisions = conn.execute(
            "SELECT * FROM draft_revisions WHERE draft_id=? ORDER BY revision_number",
            (draft_id,),
        ).fetchall()

    assert len(revisions) == 2
    assert revisions[0]["authored_by"] == "agent"
    assert revisions[1]["revision_number"] == 2
    v1_sections = json.loads(revisions[0]["sections_json"])
    assert v1_sections[0]["heading"] == "Introduction"


# ── approval_states CRUD ───────────────────────────────────────────────────────

def test_approval_state_per_section(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO report_drafts (client_id, title, primary_locale) VALUES (?, ?, ?)",
            ("client-1", "Draft B", "en"),
        )
        draft_id = cur.lastrowid

        conn.execute(
            "INSERT INTO approval_states (draft_id, section_id, status, reviewer) VALUES (?, ?, ?, ?)",
            (draft_id, "s1", "approved", "alice"),
        )
        conn.execute(
            "INSERT INTO approval_states (draft_id, section_id, status, reviewer) VALUES (?, ?, ?, ?)",
            (draft_id, "s2", "needs_revision", "bob"),
        )

    with get_db() as conn:
        rows = conn.execute(
            "SELECT section_id, status FROM approval_states WHERE draft_id=? ORDER BY section_id",
            (draft_id,),
        ).fetchall()

    assert len(rows) == 2
    assert rows[0]["status"] == "approved"
    assert rows[1]["section_id"] == "s2"


def test_approval_state_unique_per_draft_section(
    isolated_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO report_drafts (client_id, title) VALUES (?, ?)",
            ("client-1", "D"),
        )
        draft_id = cur.lastrowid
        conn.execute(
            "INSERT INTO approval_states (draft_id, section_id) VALUES (?, ?)",
            (draft_id, "s1"),
        )
    with pytest.raises(Exception):
        with get_db() as conn:
            conn.execute(
                "INSERT INTO approval_states (draft_id, section_id) VALUES (?, ?)",
                (draft_id, "s1"),
            )


# ── export_jobs CRUD ───────────────────────────────────────────────────────────

def test_export_job_insert(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO report_drafts (client_id, title) VALUES (?, ?)",
            ("client-1", "Draft C"),
        )
        draft_id = cur.lastrowid
        conn.execute(
            "INSERT INTO export_jobs (draft_id, format, locale, requested_by) VALUES (?, ?, ?, ?)",
            (draft_id, "pdf", "en", "user-1"),
        )

    with get_db() as conn:
        job = conn.execute("SELECT * FROM export_jobs WHERE draft_id=?", (draft_id,)).fetchone()

    assert job["format"] == "pdf"
    assert job["status"] == "pending"
    assert job["locale"] == "en"


# ── client_locale_settings CRUD ────────────────────────────────────────────────

def test_client_locale_settings_upsert(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO client_locale_settings (client_id, primary_locale, enabled_locales) VALUES (?, ?, ?)",
            ("client-1", "en", json.dumps(["en", "de", "fr"])),
        )
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM client_locale_settings WHERE client_id='client-1'"
        ).fetchone()
    locales = json.loads(row["enabled_locales"])
    assert "de" in locales
    assert row["primary_locale"] == "en"


# ── draft_chat_messages CRUD ───────────────────────────────────────────────────

def test_chat_message_insert(isolated_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_connection_module, "DB_PATH", isolated_db)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO report_drafts (client_id, title) VALUES (?, ?)",
            ("client-1", "Chat Draft"),
        )
        draft_id = cur.lastrowid
        conn.execute(
            "INSERT INTO draft_chat_messages (draft_id, role, content, section_id) VALUES (?, ?, ?, ?)",
            (draft_id, "user", "Please expand this section.", "intro"),
        )
        conn.execute(
            "INSERT INTO draft_chat_messages (draft_id, role, content) VALUES (?, ?, ?)",
            (draft_id, "assistant", "I have expanded the introduction section."),
        )

    with get_db() as conn:
        messages = conn.execute(
            "SELECT * FROM draft_chat_messages WHERE draft_id=? ORDER BY id",
            (draft_id,),
        ).fetchall()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["section_id"] == "intro"
    assert messages[1]["section_id"] is None  # draft-level
