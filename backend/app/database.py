"""SQLite connection and initial schema."""

import sqlite3
from contextlib import closing
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
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
                ("schema_version", "1"),
            )


def database_is_ready(db_path: Path) -> bool:
    try:
        with closing(connect(db_path)) as connection:
            row = connection.execute(
                "SELECT value FROM app_meta WHERE key = ?", ("schema_version",)
            ).fetchone()
        return row is not None and row["value"] == "1"
    except sqlite3.Error:
        return False

