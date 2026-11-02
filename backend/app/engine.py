"""Persistent, backend-owned round lifecycle and deterministic challenge memory."""

import sqlite3
import time
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from .database import connect
from .schemas import CreateRound, HistoryItem, MemoryGuidance, Outcome, RoundState, VoteInput


class EngineError(Exception):
    def __init__(self, message: str, status_code: int = 409) -> None:
        super().__init__(message)
        self.status_code = status_code


# Each mode has more templates than one round needs, so recent titles can be avoided.
# Tuple: title, description, category, success criteria, duration in seconds.
CHALLENGE_BANK: dict[str, list[tuple[str, str, str, str, int]]] = {
    "gaming": [
        ("One Hand Hero", "Play using only one hand for the challenge window.", "control", "Finish the window without using your other hand.", 90),
        ("No Map Navigator", "Hide the minimap and navigate by landmarks.", "gameplay", "Reach an in-game objective without opening the map.", 120),
        ("The Backwards Plan", "Explain your next play backwards before attempting it.", "performance", "Explain and complete one planned play.", 90),
        ("Quiet Clutch", "Play one segment without speaking; use on-screen emotes to react.", "performance", "Complete one segment without speaking.", 90),
        ("Viewer Strategy", "Let chat choose between two safe in-game approaches.", "audience", "Try the selected approach for one segment.", 120),
        ("Inventory Roulette", "Choose one available item at random and make it useful.", "gameplay", "Use the selected item in a meaningful play.", 120),
        ("Side Quest Sprint", "Choose a small optional in-game goal and attempt it before time runs out.", "gameplay", "Attempt the chosen optional goal.", 120),
        ("Narrator Mode", "Narrate your next in-game decision like a documentary.", "performance", "Narrate a complete gameplay segment.", 90),
    ],
    "just_chatting": [
        ("Three Word Story", "Tell a short story using three words suggested by viewers.", "storytelling", "Include all three words in a complete story.", 120),
        ("Hot Take Timer", "Defend a harmless opinion for one minute.", "conversation", "Finish a one-minute explanation.", 60),
        ("Emoji Translator", "Translate a viewer emoji sequence into a dramatic scene.", "performance", "Act out a scene based on the emojis.", 90),
        ("Mystery Question", "Pick a lighthearted viewer question and answer with a story.", "audience", "Answer one question with a full story.", 120),
        ("Speed List", "List ten things in a viewer-chosen safe category.", "conversation", "Name ten distinct items before the timer ends.", 90),
        ("Compliment Chain", "Give playful compliments to three fictional characters.", "performance", "Complete three distinct compliments.", 90),
        ("Tiny Debate", "Argue both sides of a lighthearted question.", "conversation", "Give one reason for each side.", 90),
        ("Character Interview", "Interview an imaginary character suggested by viewers.", "performance", "Ask and answer three questions in character.", 120),
    ],
    "creative": [
        ("Five Shape Sketch", "Make a quick sketch using only five basic shapes.", "art", "Finish a recognizable sketch with five shapes.", 180),
        ("Color Constraint", "Create a small piece with only two chosen colors.", "art", "Complete a small piece using two colors.", 180),
        ("Remix a Doodle", "Turn a simple doodle into a new character.", "design", "Finish one transformed character.", 180),
        ("One Minute Logo", "Sketch a logo for a fictional product in one minute.", "design", "Present a completed logo concept.", 90),
        ("Soundtrack Scene", "Draw a scene inspired by the mood of a royalty-free track.", "art", "Finish a scene and explain the connection.", 180),
        ("Viewer Palette", "Use three colors suggested by chat in a tiny illustration.", "audience", "Complete an illustration with all three colors.", 180),
        ("Texture Challenge", "Create a small piece using three different textures.", "art", "Show three distinct textures in one piece.", 180),
        ("Alternate Ending", "Redesign the ending of a fictional scene in a quick sketch.", "design", "Present one complete alternate ending sketch.", 180),
    ],
}


@contextmanager
def transaction(db_path: Path) -> Iterator[sqlite3.Connection]:
    with closing(connect(db_path)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def _current_id(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT value FROM app_meta WHERE key = ?", ("current_round_id",)).fetchone()
    return row["value"] if row else ""


def _current_round(connection: sqlite3.Connection) -> sqlite3.Row:
    round_id = _current_id(connection)
    if not round_id:
        raise EngineError("No current round. Create a round first.", 404)
    row = connection.execute("SELECT * FROM rounds WHERE id = ?", (round_id,)).fetchone()
    if row is None:
        raise EngineError("Current round record is missing.", 500)
    return row


def _require_status(round_row: sqlite3.Row, *statuses: str) -> None:
    if round_row["status"] not in statuses:
        raise EngineError(f"Action requires {', '.join(statuses)}; current status is {round_row['status']}.")


def _sync_time(connection: sqlite3.Connection, now: float) -> None:
    round_id = _current_id(connection)
    if round_id:
        connection.execute(
            """UPDATE rounds SET status = 'PENDING_APPROVAL'
            WHERE id = ? AND status = 'VOTING' AND voting_ends_at <= ?""",
            (round_id, now),
        )


def _history(connection: sqlite3.Connection, limit: int) -> list[HistoryItem]:
    rows = connection.execute(
        """SELECT c.id AS challenge_id, r.id AS round_id, c.title,
                  c.description, c.difficulty, r.stream_mode, c.duration,
                  LOWER(r.status) AS outcome, r.created_at, r.completed_at
           FROM rounds r JOIN challenges c ON c.id = r.approved_challenge_id
           WHERE r.status IN ('COMPLETED', 'FAILED', 'SKIPPED')
           ORDER BY r.completed_at DESC, r.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    return [HistoryItem.model_validate(dict(row) | {"outcome": "success" if row["outcome"] == "completed" else row["outcome"]}) for row in rows]


def _memory(connection: sqlite3.Connection, intensity: str) -> MemoryGuidance:
    history = _history(connection, 5)
    base = {"chill": 1, "balanced": 2, "wild": 3}[intensity]
    recent = history[:3]
    successes = sum(item.outcome == "success" for item in recent)
    failures = sum(item.outcome == "failed" for item in recent)
    adjustment = 1 if successes >= 2 else -1 if failures >= 2 else 0
    difficulty = max(1, min(5, base + adjustment))
    comeback = bool(history and history[0].outcome == "failed")
    summary = "; ".join(f"{item.title}: {item.outcome}" for item in history) or "No completed challenges yet"
    return MemoryGuidance(
        difficulty=difficulty,
        comeback=comeback,
        recent_titles=[item.title for item in history],
        summary=summary,
    )


def memory(db_path: Path, intensity: str = "balanced") -> MemoryGuidance:
    if intensity not in {"chill", "balanced", "wild"}:
        raise EngineError("Invalid intensity.", 422)
    with transaction(db_path) as connection:
        return _memory(connection, intensity)


def _snapshot(connection: sqlite3.Connection, now: float) -> RoundState:
    round_id = _current_id(connection)
    if not round_id:
        return RoundState(status="IDLE", round_id=None, server_time=now)
    row = _current_round(connection)
    challenge_rows = connection.execute(
        """SELECT c.*, COUNT(v.user_id) AS votes FROM challenges c
           LEFT JOIN votes v ON v.challenge_id = c.id
           WHERE c.round_id = ? GROUP BY c.id ORDER BY c.position""",
        (round_id,),
    ).fetchall()
    challenges = [dict(item) | {"rejected": bool(item["rejected"])} for item in challenge_rows]
    eligible = [item for item in challenges if not item["rejected"]]
    winning_id = sorted(eligible, key=lambda item: (-item["votes"], item["position"]))[0]["id"] if eligible else None
    return RoundState(
        status=row["status"], round_id=round_id, stream_mode=row["stream_mode"],
        intensity=row["intensity"], difficulty=row["difficulty"],
        voting_duration=row["voting_duration"], voting_ends_at=row["voting_ends_at"],
        started_at=row["started_at"], ends_at=row["ends_at"],
        created_at=row["created_at"], completed_at=row["completed_at"],
        approved_challenge_id=row["approved_challenge_id"], winning_challenge_id=winning_id,
        total_votes=sum(item["votes"] for item in challenges), challenges=challenges, server_time=now,
    )


def state(db_path: Path, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        _sync_time(connection, now)
        return _snapshot(connection, now)


def create_round(db_path: Path, data: CreateRound, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        _sync_time(connection, now)
        if _current_id(connection):
            raise EngineError("A round already exists. Reset it before creating another.")
        guidance = _memory(connection, data.intensity)
        recent_titles = {title.removeprefix("Comeback: ") for title in guidance.recent_titles}
        templates = CHALLENGE_BANK[data.stream_mode]
        selected = [item for item in templates if item[0] not in recent_titles][:3]
        if len(selected) < 3:
            selected += [item for item in templates if item not in selected][:3 - len(selected)]
        round_id = uuid4().hex
        connection.execute(
            """INSERT INTO rounds (id, status, stream_mode, intensity, difficulty,
               voting_duration, created_at) VALUES (?, 'GENERATING', ?, ?, ?, ?, ?)""",
            (round_id, data.stream_mode, data.intensity, guidance.difficulty, data.voting_duration, now),
        )
        for position, template in enumerate(selected, start=1):
            title, description, category, criteria, duration = template
            if position == 1 and guidance.comeback:
                title = f"Comeback: {title}"
            connection.execute(
                """INSERT INTO challenges (id, round_id, position, title, description,
                   duration, difficulty, category, success_criteria)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uuid4().hex, round_id, position, title, description, duration,
                 guidance.difficulty, category, criteria),
            )
        connection.execute("UPDATE rounds SET status = 'READY' WHERE id = ?", (round_id,))
        connection.execute("UPDATE app_meta SET value = ? WHERE key = ?", (round_id, "current_round_id"))
        return _snapshot(connection, now)


def start_voting(db_path: Path, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        row = _current_round(connection)
        _require_status(row, "READY")
        connection.execute(
            "UPDATE rounds SET status = 'VOTING', voting_ends_at = ? WHERE id = ?",
            (now + row["voting_duration"], row["id"]),
        )
        return _snapshot(connection, now)


def vote(db_path: Path, data: VoteInput, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        _sync_time(connection, now)
        row = _current_round(connection)
        _require_status(row, "VOTING")
        if data.event_id and connection.execute("SELECT 1 FROM processed_events WHERE event_id = ?", (data.event_id,)).fetchone():
            return _snapshot(connection, now)
        challenge = connection.execute(
            "SELECT id FROM challenges WHERE round_id = ? AND position = ?",
            (row["id"], data.choice),
        ).fetchone()
        if challenge is None:
            raise EngineError("Invalid challenge choice.", 422)
        connection.execute(
            """INSERT INTO votes (round_id, user_id, challenge_id, updated_at)
               VALUES (?, ?, ?, ?) ON CONFLICT(round_id, user_id)
               DO UPDATE SET challenge_id = excluded.challenge_id, updated_at = excluded.updated_at""",
            (row["id"], data.user_id, challenge["id"], now),
        )
        if data.event_id:
            connection.execute("INSERT INTO processed_events (event_id, round_id) VALUES (?, ?)", (data.event_id, row["id"]))
        return _snapshot(connection, now)


def close_voting(db_path: Path, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        row = _current_round(connection)
        _require_status(row, "VOTING")
        connection.execute("UPDATE rounds SET status = 'PENDING_APPROVAL' WHERE id = ?", (row["id"],))
        return _snapshot(connection, now)


def _choice(connection: sqlite3.Connection, round_id: str, position: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM challenges WHERE round_id = ? AND position = ?", (round_id, position)
    ).fetchone()
    if row is None:
        raise EngineError("Invalid challenge choice.", 422)
    return row


def approve(db_path: Path, position: int, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        row = _current_round(connection)
        _require_status(row, "PENDING_APPROVAL")
        challenge = _choice(connection, row["id"], position)
        if challenge["rejected"]:
            raise EngineError("This challenge was rejected.")
        connection.execute("UPDATE rounds SET approved_challenge_id = ? WHERE id = ?", (challenge["id"], row["id"]))
        return _snapshot(connection, now)


def reject(db_path: Path, position: int, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        row = _current_round(connection)
        _require_status(row, "PENDING_APPROVAL")
        challenge = _choice(connection, row["id"], position)
        connection.execute("UPDATE challenges SET rejected = 1 WHERE id = ?", (challenge["id"],))
        if row["approved_challenge_id"] == challenge["id"]:
            connection.execute("UPDATE rounds SET approved_challenge_id = NULL WHERE id = ?", (row["id"],))
        return _snapshot(connection, now)


def start_challenge(db_path: Path, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        row = _current_round(connection)
        _require_status(row, "PENDING_APPROVAL")
        if not row["approved_challenge_id"]:
            raise EngineError("Approve a challenge before starting it.")
        challenge = connection.execute("SELECT duration FROM challenges WHERE id = ?", (row["approved_challenge_id"],)).fetchone()
        connection.execute(
            "UPDATE rounds SET status = 'ACTIVE', started_at = ?, ends_at = ? WHERE id = ?",
            (now, now + challenge["duration"], row["id"]),
        )
        return _snapshot(connection, now)


def finish(db_path: Path, outcome: Outcome, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    status = {"success": "COMPLETED", "failed": "FAILED", "skipped": "SKIPPED"}[outcome]
    with transaction(db_path) as connection:
        row = _current_round(connection)
        _require_status(row, "ACTIVE")
        connection.execute(
            "UPDATE rounds SET status = ?, completed_at = ? WHERE id = ?", (status, now, row["id"])
        )
        return _snapshot(connection, now)


def reset(db_path: Path, now: float | None = None) -> RoundState:
    now = time.time() if now is None else now
    with transaction(db_path) as connection:
        row = _current_round(connection)
        if row["status"] == "ACTIVE":
            raise EngineError("Finish or skip the active challenge before resetting.")
        connection.execute("UPDATE app_meta SET value = '' WHERE key = ?", ("current_round_id",))
        return _snapshot(connection, now)


def history(db_path: Path, limit: int = 20) -> list[HistoryItem]:
    with transaction(db_path) as connection:
        return _history(connection, limit)
