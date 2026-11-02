# Architecture (Phase 2)

The React/TypeScript dashboard runs on Vite at `127.0.0.1:5173`. It calls `/api/health` through Vite's local proxy. FastAPI runs at `127.0.0.1:8000` and creates a local SQLite file at startup. SQLite is the source of truth for round state, challenges, votes, processed event IDs, and completed challenge history.

The current round ID is stored in `app_meta`. Round changes use SQLite `BEGIN IMMEDIATE` transactions so concurrent requests cannot create two active rounds or overwrite votes unexpectedly. `rounds` stores the state and server deadlines; `challenges` stores the three options; `votes` has a primary key on `(round_id, user_id)`; `processed_events` prevents duplicate chat events. Resetting clears only the current pointer and preserves completed history.

Lifecycle: `IDLE → GENERATING → READY → VOTING → PENDING_APPROVAL → ACTIVE → COMPLETED / FAILED / SKIPPED → IDLE`. `GENERATING` occurs within the round-creation transaction; the client receives `READY` once all three options exist. Approval is stored while the round remains `PENDING_APPROVAL`, and the streamer starts it explicitly. Voting expiry is checked on every state read or write and by a one-second background task. Challenge expiry does not automatically declare failure.

Memory reads the five latest completed records. Two successes among the latest three raise difficulty by one; two failures lower it by one; skips do not count as failures. The latest failure adds a comeback theme. Recent titles are avoided when choosing from the predefined bank.

Environment variables configure the database path and allowed frontend origin. Control requests are local-only and check the browser Origin header. Broadcaster authentication will be added with Twitch integration. Credentials stay on the backend in future phases. The frontend currently receives only health information.

Future phases will add Ollama generation, Twitch EventSub ingestion, and a non-sensitive overlay state feed. Those features are not present yet.

