"""Local API for the persistent chaos engine."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_settings
from .database import database_is_ready, initialize
from . import engine
from .schemas import ChoiceInput, CreateRound, HistoryItem, MemoryGuidance, Outcome, RoundState, VoteInput


logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    database: str
    phase: int


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize(get_settings().db_path)
    async def close_expired_voting() -> None:
        while True:
            await asyncio.sleep(1)
            try:
                await asyncio.to_thread(engine.state, get_settings().db_path)
            except Exception:
                logger.exception("Unable to synchronize round timer")

    task = asyncio.create_task(close_expired_voting())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="CHAOS DIRECTOR API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(engine.EngineError)
async def engine_error_handler(_request: Request, exc: engine.EngineError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


def local_control(request: Request) -> None:
    """Until Twitch auth arrives, control is limited to loopback and the configured UI origin."""
    if request.client and request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=403, detail="Control is available on localhost only")
    origin = request.headers.get("origin")
    if origin and origin != get_settings().frontend_origin:
        raise HTTPException(status_code=403, detail="Untrusted control origin")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    if not database_is_ready(get_settings().db_path):
        raise HTTPException(status_code=503, detail="Database unavailable")
    return HealthResponse(status="ok", database="ready", phase=2)


@app.get("/api/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/state", response_model=RoundState)
def get_state() -> RoundState:
    return engine.state(get_settings().db_path)


@app.get("/api/history", response_model=list[HistoryItem])
def get_history() -> list[HistoryItem]:
    return engine.history(get_settings().db_path)


@app.get("/api/memory", response_model=MemoryGuidance)
def get_memory(intensity: str = "balanced") -> MemoryGuidance:
    return engine.memory(get_settings().db_path, intensity)


@app.post("/api/rounds", response_model=RoundState, dependencies=[Depends(local_control)])
def create_round(data: CreateRound) -> RoundState:
    return engine.create_round(get_settings().db_path, data)


@app.post("/api/voting/start", response_model=RoundState, dependencies=[Depends(local_control)])
def start_voting() -> RoundState:
    return engine.start_voting(get_settings().db_path)


@app.post("/api/votes", response_model=RoundState, dependencies=[Depends(local_control)])
def vote(data: VoteInput) -> RoundState:
    return engine.vote(get_settings().db_path, data)


@app.post("/api/voting/close", response_model=RoundState, dependencies=[Depends(local_control)])
def close_voting() -> RoundState:
    return engine.close_voting(get_settings().db_path)


@app.post("/api/challenges/approve", response_model=RoundState, dependencies=[Depends(local_control)])
def approve(data: ChoiceInput) -> RoundState:
    return engine.approve(get_settings().db_path, data.choice)


@app.post("/api/challenges/reject", response_model=RoundState, dependencies=[Depends(local_control)])
def reject(data: ChoiceInput) -> RoundState:
    return engine.reject(get_settings().db_path, data.choice)


@app.post("/api/challenge/start", response_model=RoundState, dependencies=[Depends(local_control)])
def start_challenge() -> RoundState:
    return engine.start_challenge(get_settings().db_path)


@app.post("/api/challenge/{outcome}", response_model=RoundState, dependencies=[Depends(local_control)])
def finish(outcome: Outcome) -> RoundState:
    return engine.finish(get_settings().db_path, outcome)


@app.post("/api/round/reset", response_model=RoundState, dependencies=[Depends(local_control)])
def reset() -> RoundState:
    return engine.reset(get_settings().db_path)

