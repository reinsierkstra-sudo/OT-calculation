"""
Database bootstrap and connection helper.

Usage:
    python -m app.db --init   # create fresh DB + seed settings
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

DB_PATH = Path(__file__).parent.parent / "data" / "hours.db"
TOML_PATH = Path(__file__).parent.parent / "config" / "settings.toml"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS raw_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc        TEXT    NOT NULL,
    channel       TEXT    NOT NULL,
    event_id      INTEGER NOT NULL,
    kind          TEXT    NOT NULL,
    record_number INTEGER NOT NULL,
    raw_xml       TEXT,
    UNIQUE (channel, record_number)
);
CREATE INDEX IF NOT EXISTS idx_raw_events_ts ON raw_events(ts_utc);

CREATE TABLE IF NOT EXISTS harvester_watermark (
    channel        TEXT PRIMARY KEY,
    last_record_no INTEGER NOT NULL,
    last_run_utc   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    start_ts     TEXT    NOT NULL,
    end_ts       TEXT,
    duration_min INTEGER,
    kind         TEXT    NOT NULL DEFAULT 'unknown',
    ot_flagged   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_ts);

CREATE TABLE IF NOT EXISTS session_overrides (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    start_ts     TEXT NOT NULL,
    end_ts       TEXT,
    action       TEXT NOT NULL CHECK (action IN ('delete','confirm')),
    created_at   TEXT NOT NULL,
    UNIQUE (start_ts, end_ts)
);

CREATE TABLE IF NOT EXISTS vacation_categories (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT    NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS vacation_grants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER NOT NULL REFERENCES vacation_categories(id),
    year          INTEGER NOT NULL,
    hours_granted REAL    NOT NULL,
    note          TEXT,
    UNIQUE (category_id, year)
);

CREATE TABLE IF NOT EXISTS manual_entries (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    kind                 TEXT    NOT NULL,
    date                 TEXT    NOT NULL,
    start_time           TEXT,
    hours                REAL    NOT NULL,
    vacation_category_id INTEGER REFERENCES vacation_categories(id),
    note                 TEXT,
    created_at           TEXT    NOT NULL,
    CHECK (kind IN ('vacation','sick','ot_taken')),
    CHECK (kind != 'vacation' OR vacation_category_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_manual_entries_date ON manual_entries(date);

CREATE TABLE IF NOT EXISTS holidays (
    date   TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('auto','manual'))
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _seed_settings(conn: sqlite3.Connection) -> None:
    with TOML_PATH.open("rb") as f:
        cfg = tomllib.load(f)

    rows = [
        ("work_start",              cfg["work"]["work_start"]),
        ("work_end",                cfg["work"]["work_end"]),
        ("break_minutes",           str(cfg["work"]["break_minutes"])),
        ("contract_hours_per_week", str(cfg["work"]["contract_hours_per_week"])),
        ("work_days",               ",".join(cfg["work"]["work_days"])),
        ("timezone",                cfg["work"]["timezone"]),
        ("network_profile_name",    cfg["harvester"]["network_profile_name"]),
        ("office_ssid",             cfg["harvester"]["office_ssid"]),
        ("stitch_gap_seconds",      str(cfg["harvester"]["stitch_gap_seconds"])),
        ("ot_flag_threshold_hours", str(cfg["ot_flag"]["ot_flag_threshold_hours"])),
        ("holidays_country",        cfg["holidays"]["country"]),
        ("seed_years_around_current", str(cfg["holidays"]["seed_years_around_current"])),
        ("server_host",             cfg["server"]["host"]),
        ("server_port",             str(cfg["server"]["port"])),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", rows
    )


def get_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    _seed_settings(conn)
    conn.commit()
    conn.close()
    print(f"Database initialised at {DB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="Create/bootstrap database")
    args = parser.parse_args()
    if args.init:
        init_db()
    else:
        parser.print_help()
