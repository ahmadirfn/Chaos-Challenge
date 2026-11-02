"""Environment configuration for the local development server."""

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    db_path: Path
    frontend_origin: str


def get_settings() -> Settings:
    raw_path = Path(os.getenv("CHAOS_DB_PATH", "backend/data/chaos.db"))
    db_path = raw_path if raw_path.is_absolute() else PROJECT_ROOT / raw_path
    return Settings(
        host=os.getenv("CHAOS_HOST", "127.0.0.1"),
        port=int(os.getenv("CHAOS_PORT", "8000")),
        db_path=db_path,
        frontend_origin=os.getenv("CHAOS_FRONTEND_ORIGIN", "http://127.0.0.1:5173"),
    )

