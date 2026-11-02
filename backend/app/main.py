"""Phase 1 API foundation."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_settings
from .database import database_is_ready, initialize


class HealthResponse(BaseModel):
    status: str
    database: str
    phase: int


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize(get_settings().db_path)
    yield


app = FastAPI(title="CHAOS DIRECTOR API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    if not database_is_ready(get_settings().db_path):
        raise HTTPException(status_code=503, detail="Database unavailable")
    return HealthResponse(status="ok", database="ready", phase=1)


@app.get("/api/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}

