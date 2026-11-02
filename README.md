# CHAOS DIRECTOR

**Your Stream. Their Choices. AI-Powered Chaos.**

CHAOS DIRECTOR is a local-first Twitch stream challenge app. This repository currently contains **Phase 1 only**: a React dashboard foundation, FastAPI health endpoints, and SQLite setup. Challenge rounds, AI, Twitch, OBS, and demo mode are planned for later phases and are not yet functional.

## Requirements

- Windows 10/11 with PowerShell
- Python 3.11 or newer
- Node.js 20.19 or newer and npm
- Git (optional for local use)

No Twitch account, API key, Ollama instance, Docker, or paid service is needed for Phase 1.

## Start the backend

Open **PowerShell terminal 1** in the repository root:

```powershell
cd C:\Users\User\Desktop\chaos_challenge
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
cd .\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The server creates `backend/data/chaos.db` when it starts. Check [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) for `{"status":"ok","database":"ready","phase":1}`. API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Start the frontend

Open **PowerShell terminal 2** in the repository root:

```powershell
cd C:\Users\User\Desktop\chaos_challenge\frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The dashboard should show **System online** and **SQLite database READY**. Vite forwards `/api` requests to the local backend. The dashboard polls the health endpoint every ten seconds; stop the backend to see the offline state, then restart it to see recovery.

## Configuration

`.env.example` lists the intended environment variables. For Phase 1, defaults work without setting any variables. Set variables in the **backend terminal before starting Uvicorn** when needed:

```powershell
$env:CHAOS_DB_PATH = "backend/data/chaos.db"
$env:CHAOS_FRONTEND_ORIGIN = "http://127.0.0.1:5173"
```

The database path is relative to the repository root unless absolute. The backend binds to localhost by default. `CHAOS_HOST` and `CHAOS_PORT` document preferred server settings; pass matching `--host` and `--port` options to Uvicorn when changing them. The Vite proxy currently targets port 8000, so change `frontend/vite.config.ts` as well if you move the backend port. Do not put Twitch secrets in frontend variables. `.env` is ignored by Git.

## Tests

From **PowerShell terminal 3** in the repository root after installing dependencies:

```powershell
cd C:\Users\User\Desktop\chaos_challenge\backend
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
cd ..\frontend
npm run build
```

The Python tests check SQLite initialization, environment path handling, and health logic. The frontend build checks TypeScript and produces a production bundle.

## Project layout

```text
backend/app/           FastAPI configuration, database, health routes
backend/tests/         Python foundation tests
frontend/src/          React dashboard and API client
docs/                  Architecture and phase notes
.env.example           Future integration variable template
```

## Current limitations

- Dashboard configuration fields and challenge controls are previews and disabled.
- Twitch, Ollama, stream overlay, and demo mode are not implemented in Phase 1.
- SQLite currently stores only a schema marker. Challenge data tables arrive in Phase 2.

