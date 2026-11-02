import unittest
from pathlib import Path
from uuid import uuid4

from app.database import initialize
from app.engine import (
    EngineError, approve, close_voting, create_round, finish, history, memory,
    reject, reset, start_challenge, start_voting, state, vote,
)
from app.schemas import CreateRound, VoteInput


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = Path(__file__).resolve().parents[1] / "data" / f"test_{uuid4().hex}.db"
        initialize(self.db_path)
        self.addCleanup(self.db_path.unlink, missing_ok=True)

    def create(self, now: float = 1000, **kwargs) -> None:
        result = create_round(self.db_path, CreateRound(**kwargs), now=now)
        self.assertEqual(result.status, "READY")
        self.assertEqual(len(result.challenges), 3)

    def test_complete_lifecycle_persists_history(self) -> None:
        self.create()
        round_id = state(self.db_path, 1000).round_id
        self.assertEqual(start_voting(self.db_path, 1010).voting_ends_at, 1070)
        voted = vote(self.db_path, VoteInput(user_id="123", choice=2, event_id="msg1"), 1011)
        self.assertEqual(voted.total_votes, 1)
        self.assertEqual(close_voting(self.db_path, 1012).status, "PENDING_APPROVAL")
        approved = approve(self.db_path, 2, 1013)
        self.assertEqual(approved.approved_challenge_id, approved.challenges[1].id)
        active = start_challenge(self.db_path, 1014)
        self.assertEqual(active.status, "ACTIVE")
        self.assertEqual(active.ends_at, 1014 + active.challenges[1].duration)
        self.assertEqual(finish(self.db_path, "success", 1100).status, "COMPLETED")
        records = history(self.db_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].round_id, round_id)
        self.assertEqual(records[0].outcome, "success")
        self.assertEqual(records[0].completed_at, 1100)
        self.assertEqual(reset(self.db_path, 1101).status, "IDLE")
        self.assertEqual(len(history(self.db_path)), 1)

    def test_invalid_transitions_are_rejected(self) -> None:
        with self.assertRaises(EngineError):
            start_voting(self.db_path)
        self.create()
        with self.assertRaises(EngineError):
            create_round(self.db_path, CreateRound())
        with self.assertRaises(EngineError):
            approve(self.db_path, 1)
        with self.assertRaises(EngineError):
            vote(self.db_path, VoteInput(user_id="123", choice=1))
        start_voting(self.db_path, 1001)
        with self.assertRaises(EngineError):
            start_challenge(self.db_path)
        close_voting(self.db_path, 1002)
        with self.assertRaises(EngineError):
            start_challenge(self.db_path)
        approve(self.db_path, 1, 1003)
        start_challenge(self.db_path, 1004)
        with self.assertRaises(EngineError):
            reset(self.db_path)
        with self.assertRaises(EngineError):
            vote(self.db_path, VoteInput(user_id="123", choice=1), 1005)

    def test_vote_change_dedup_tie_and_round_scope(self) -> None:
        self.create()
        start_voting(self.db_path, 1000)
        first = vote(self.db_path, VoteInput(user_id="u1", choice=2, event_id="e1"), 1001)
        self.assertEqual(first.total_votes, 1)
        duplicate = vote(self.db_path, VoteInput(user_id="u1", choice=3, event_id="e1"), 1002)
        self.assertEqual(duplicate.challenges[1].votes, 1)
        changed = vote(self.db_path, VoteInput(user_id="u1", choice=1, event_id="e2"), 1003)
        self.assertEqual(changed.total_votes, 1)
        self.assertEqual(changed.challenges[0].votes, 1)
        tied = vote(self.db_path, VoteInput(user_id="u2", choice=2, event_id="e3"), 1004)
        self.assertEqual(tied.winning_challenge_id, tied.challenges[0].id)
        close_voting(self.db_path, 1005)
        with self.assertRaises(EngineError):
            vote(self.db_path, VoteInput(user_id="u3", choice=3), 1006)
        reset(self.db_path, 1007)
        self.create(now=1008)
        self.assertEqual(state(self.db_path, 1008).total_votes, 0)

    def test_voting_expires_on_server_time_and_no_vote_selection(self) -> None:
        self.create(voting_duration=10)
        start_voting(self.db_path, 1000)
        self.assertEqual(state(self.db_path, 1010).status, "PENDING_APPROVAL")
        with self.assertRaises(EngineError):
            vote(self.db_path, VoteInput(user_id="late", choice=1), 1011)
        self.assertEqual(state(self.db_path, 1011).total_votes, 0)
        self.assertEqual(approve(self.db_path, 3, 1012).approved_challenge_id,
                         state(self.db_path, 1012).challenges[2].id)

    def test_reject_and_memory_adaptation(self) -> None:
        self.create(stream_mode="creative")
        original_titles = [item.title for item in state(self.db_path, 1000).challenges]
        start_voting(self.db_path, 1001)
        close_voting(self.db_path, 1002)
        rejected = reject(self.db_path, 1, 1003)
        self.assertTrue(rejected.challenges[0].rejected)
        with self.assertRaises(EngineError):
            approve(self.db_path, 1, 1004)
        approve(self.db_path, 2, 1005)
        start_challenge(self.db_path, 1006)
        finish(self.db_path, "failed", 1007)
        reset(self.db_path, 1008)
        self.assertTrue(memory(self.db_path).comeback)
        self.create(now=1010, stream_mode="creative")
        titles = [item.title for item in state(self.db_path, 1010).challenges]
        self.assertTrue(titles[0].startswith("Comeback:"))
        self.assertNotIn(original_titles[1], titles)
        start_voting(self.db_path, 1011)
        close_voting(self.db_path, 1012)
        approve(self.db_path, 1, 1013)
        start_challenge(self.db_path, 1014)
        finish(self.db_path, "failed", 1015)
        self.assertEqual(memory(self.db_path).difficulty, 1)

    def test_skipped_is_not_failure_and_successes_raise_difficulty(self) -> None:
        for index, outcome in enumerate(("success", "skipped", "success")):
            now = 1000 + index * 20
            self.create(now=now)
            start_voting(self.db_path, now + 1)
            close_voting(self.db_path, now + 2)
            approve(self.db_path, 1, now + 3)
            start_challenge(self.db_path, now + 4)
            finish(self.db_path, outcome, now + 5)
            reset(self.db_path, now + 6)
        guidance = memory(self.db_path)
        self.assertEqual(guidance.difficulty, 3)
        self.assertFalse(guidance.comeback)
        self.assertEqual(len(history(self.db_path)), 3)


if __name__ == "__main__":
    unittest.main()
