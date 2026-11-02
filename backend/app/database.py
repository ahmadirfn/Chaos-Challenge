"""SQLite connection and initial schema."""

import sqlite3
from contextlib import closing
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(db_path: Path) -> None:
    with closing(connect(db_path)) as connection:
        with connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )"""
            )
            connection.execute(
                "INSERT OR IGNORE INTO app_meta (key, value) VALUES (?, ?)",
                ("schema_version", "2"),
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS rounds (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    stream_mode TEXT NOT NULL,
                    intensity TEXT NOT NULL,
                    difficulty INTEGER NOT NULL,
                    voting_duration INTEGER NOT NULL,
                    voting_ends_at REAL,
                    started_at REAL,
                    ends_at REAL,
                    created_at REAL NOT NULL,
                    completed_at REAL,
                    approved_challenge_id TEXT
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS challenges (
                    id TEXT PRIMARY KEY,
                    round_id TEXT NOT NULL REFERENCES rounds(id),
                    position INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    difficulty INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    success_criteria TEXT NOT NULL,
                    rejected INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(round_id, position)
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS votes (
                    round_id TEXT NOT NULL REFERENCES rounds(id),
                    user_id TEXT NOT NULL,
                    challenge_id TEXT NOT NULL REFERENCES challenges(id),
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(round_id, user_id)
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS processed_events (
                    event_id TEXT PRIMARY KEY,
                    round_id TEXT NOT NULL REFERENCES rounds(id)
                )"""
            )
            connection.execute(
                "INSERT OR IGNORE INTO app_meta (key, value) VALUES (?, ?)",
                ("current_round_id", ""),
            )
            connection.execute(
                "UPDATE app_meta SET value = ? WHERE key = ?", ("2", "schema_version")
            )


def database_is_ready(db_path: Path) -> bool:
    try:
        with closing(connect(db_path)) as connection:
            row = connection.execute(
                "SELECT value FROM app_meta WHERE key = ?", ("schema_version",)
            ).fetchone()
        return row is not None and row["value"] == "2"
    except sqlite3.Error:
        return False

