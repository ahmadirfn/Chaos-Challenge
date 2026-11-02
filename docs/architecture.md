# Architecture (Phase 1)

The React/TypeScript dashboard runs on Vite at `127.0.0.1:5173`. It calls `/api/health` through Vite's local proxy. FastAPI runs at `127.0.0.1:8000` and creates a local SQLite file at startup. The database is the planned source of truth for future round state; Phase 1 only records a schema version marker.

Environment variables configure the database path and allowed frontend origin. The backend permits GET requests from the configured origin only. Credentials stay on the backend in future phases. The frontend currently receives only health information.

Future phases will add one backend-controlled round state machine, challenge generation and memory services, Twitch EventSub ingestion, and a non-sensitive overlay state feed. Those features are not present yet.

