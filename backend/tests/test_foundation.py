import os
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app.config import get_settings
from app.database import database_is_ready, initialize
from app.main import health, live


class FoundationTests(unittest.TestCase):
    def make_db_path(self) -> Path:
        path = Path(__file__).resolve().parents[1] / "data" / f"test_{uuid4().hex}.db"
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_database_initializes_idempotently(self) -> None:
        db_path = self.make_db_path()
        initialize(db_path)
        initialize(db_path)
        self.assertTrue(database_is_ready(db_path))
        with closing(sqlite3.connect(db_path)) as connection:
            count = connection.execute("SELECT COUNT(*) FROM app_meta").fetchone()[0]
        self.assertEqual(count, 2)

    def test_health_uses_configured_database(self) -> None:
        db_path = self.make_db_path()
        with patch.dict(os.environ, {"CHAOS_DB_PATH": str(db_path)}):
            initialize(db_path)
            self.assertEqual(health().status, "ok")
            self.assertEqual(health().database, "ready")
            self.assertEqual(live(), {"status": "ok"})

    def test_relative_database_path_is_project_relative(self) -> None:
        with patch.dict(os.environ, {"CHAOS_DB_PATH": "backend/data/custom.db"}):
            self.assertTrue(get_settings().db_path.is_absolute())
            self.assertEqual(get_settings().db_path.name, "custom.db")


if __name__ == "__main__":
    unittest.main()
