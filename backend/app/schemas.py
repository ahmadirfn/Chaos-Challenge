"""Validated API input and output contracts for the core engine."""

from typing import Literal

from pydantic import BaseModel, Field


StreamMode = Literal["gaming", "just_chatting", "creative"]
Intensity = Literal["chill", "balanced", "wild"]
Outcome = Literal["success", "failed", "skipped"]


class CreateRound(BaseModel):
    stream_mode: StreamMode = "gaming"
    intensity: Intensity = "balanced"
    voting_duration: int = Field(default=60, ge=10, le=600)


class VoteInput(BaseModel):
    user_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    choice: int = Field(ge=1, le=3)
    event_id: str | None = Field(default=None, min_length=1, max_length=100)


class ChoiceInput(BaseModel):
    choice: int = Field(ge=1, le=3)


class Challenge(BaseModel):
    id: str
    title: str
    description: str
    duration: int
    difficulty: int = Field(ge=1, le=5)
    category: str
    success_criteria: str
    position: int
    votes: int
    rejected: bool


class RoundState(BaseModel):
    status: str
    round_id: str | None
    stream_mode: StreamMode | None = None
    intensity: Intensity | None = None
    difficulty: int | None = None
    voting_duration: int | None = None
    voting_ends_at: float | None = None
    started_at: float | None = None
    ends_at: float | None = None
    created_at: float | None = None
    completed_at: float | None = None
    approved_challenge_id: str | None = None
    winning_challenge_id: str | None = None
    total_votes: int = 0
    challenges: list[Challenge] = Field(default_factory=list)
    server_time: float


class HistoryItem(BaseModel):
    challenge_id: str
    round_id: str
    title: str
    description: str
    difficulty: int
    stream_mode: StreamMode
    duration: int
    outcome: Outcome
    created_at: float
    completed_at: float


class MemoryGuidance(BaseModel):
    difficulty: int
    comeback: bool
    recent_titles: list[str]
    summary: str
