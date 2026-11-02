# CHAOS DIRECTOR

**Your Stream. Their Choices. AI-Powered Chaos.**

CHAOS DIRECTOR is a local-first Twitch stream challenge app. **Phase 2 is complete:** the backend supports persistent predefined challenge rounds, voting, approval, outcomes, and Chaos Memory. The React dashboard is still a preview; interactive controls arrive in Phase 5. Ollama, Twitch, OBS, and demo mode are planned for later phases.

## Requirements

- Windows 10/11 with PowerShell
- Python 3.11 or newer
- Node.js 20.19 or newer and npm
- Git (optional for local use)

No Twitch account, API key, Ollama instance, Docker, or paid service is needed for Phase 2.

## Start the backend

Open **PowerShell terminal 1** in the repository root:

```powershell
cd C:\Users\User\Desktop\chaos_challenge
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
cd .\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The server creates `backend/data/chaos.db` when it starts. Check [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) for `{"status":"ok","database":"ready","phase":2}`. API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Start the frontend

Open **PowerShell terminal 2** in the repository root:

```powershell
cd C:\Users\User\Desktop\chaos_challenge\frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The dashboard should show **System online** and **SQLite database READY**. Vite forwards `/api` requests to the local backend. The dashboard polls the health endpoint every ten seconds; stop the backend to see the offline state, then restart it to see recovery.

## Try a complete round

With the backend running, open **PowerShell terminal 3** in the repository root. These commands use predefined challenges and do not need Twitch or Ollama:

```powershell
$api = "http://127.0.0.1:8000/api"
Invoke-RestMethod "$api/rounds" -Method Post -ContentType "application/json" -Body '{"stream_mode":"gaming","intensity":"balanced","voting_duration":60}'
Invoke-RestMethod "$api/voting/start" -Method Post
Invoke-RestMethod "$api/votes" -Method Post -ContentType "application/json" -Body '{"user_id":"viewer123","choice":1,"event_id":"example-message-1"}'
Invoke-RestMethod "$api/voting/close" -Method Post
Invoke-RestMethod "$api/challenges/approve" -Method Post -ContentType "application/json" -Body '{"choice":1}'
Invoke-RestMethod "$api/challenge/start" -Method Post
Invoke-RestMethod "$api/challenge/success" -Method Post
Invoke-RestMethod "$api/history"
Invoke-RestMethod "$api/memory"
Invoke-RestMethod "$api/round/reset" -Method Post
```

Use `failed` or `skipped` instead of `success` for other outcomes. A viewer may change their vote during voting. One effective vote per user is stored, and duplicate `event_id` values are ignored. Voting closes automatically at the configured server timestamp. The streamer may approve any non-rejected option, including when no votes arrive. Ties favor the lowest challenge position. Challenge timers use `started_at` and `ends_at` timestamps; completion remains a streamer decision. Invalid actions return HTTP 409 with a useful message. `GET /api/state` and `GET /api/history` restore persisted state after a restart.

Phase 2 control routes are restricted to loopback requests and the configured UI origin. Keep Uvicorn bound to `127.0.0.1`; broadcaster authentication is planned for Twitch integration in Phase 4.

## Configuration

`.env.example` lists the intended environment variables. Defaults work without setting any variables. Set variables in the **backend terminal before starting Uvicorn** when needed:

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

The Python tests cover SQLite initialization, round transitions, vote deduplication and changes, timer expiry, history, memory adaptation, and health logic. The frontend build checks TypeScript and produces a production bundle.

## Project layout

```text
backend/app/           FastAPI configuration, SQLite and chaos engine
backend/tests/         Python foundation and engine tests
frontend/src/          React dashboard and API client
docs/                  Architecture and phase notes
.env.example           Future integration variable template
```

## Current limitations

- Dashboard configuration fields and challenge controls remain previews and disabled. Use the API docs or PowerShell to drive a round.
- Twitch, Ollama, stream overlay, and demo mode are not implemented yet.
- Phase 2 uses a finite predefined challenge bank. Local AI generation arrives in Phase 3.

