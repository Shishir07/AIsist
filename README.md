# AIsist — AI-Powered Personal Task Tracker

A voice-first personal assistant that manages your daily life in plain English. Ask "add milk to the grocery list", "what's on my calendar tomorrow?", or "remind me to call mum at 6 pm" — an LLM agent understands the intent, calls the right tools, and keeps your family's data in sync.

**Status:** Phase 1 complete (voice chat + todos + reminders + Google Calendar). Phase 2 (meal planning, pantry, groceries) in progress. See [ROADMAP.md](ROADMAP.md).

---

## Who it's for

- **Individuals and families** who want a single assistant for tasks, reminders, calendars, grocery lists, and meal planning — operated by voice or text.
- **Developers** who want a worked example of a stateful, multi-tool LangGraph agent backed by FastAPI, PostgreSQL, and a React frontend.

---

## What it does

| Feature | Status |
|---|---|
| Voice input (Deepgram STT) and voice output (Deepgram TTS) | ✅ Phase 1 |
| Natural-language task / todo management | ✅ Phase 1 |
| Reminder scheduling with APScheduler | ✅ Phase 1 |
| Google Calendar read + write via OAuth 2.0 | ✅ Phase 1 |
| Family member profiles and preferences | ✅ Phase 1 |
| Pantry tracking | 🔧 Phase 2 |
| Grocery list management | 🔧 Phase 2 |
| Meal planning and recipe suggestions | 🔧 Phase 2 |
| Multi-user auth and per-user data isolation | 📋 Phase 3 |

---

## Built with

| Layer | Technology |
|---|---|
| **Backend language** | Python 3.11 |
| **API framework** | FastAPI 0.115+ |
| **AI / agent** | LangGraph 0.2+, LangChain Anthropic (Claude) |
| **Database** | PostgreSQL 16 (SQLAlchemy async + Alembic) |
| **Voice** | Deepgram SDK (STT + TTS) |
| **Calendar** | Google Calendar API (OAuth 2.0) |
| **Scheduler** | APScheduler 3.10 |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Infrastructure** | Docker Compose |

---

## Architecture

```
Browser / Voice Client
        │
        ▼
  React Frontend  ──►  WebSocket /voice-ws
        │                    │
        │              FastAPI Backend
        │                    │
        │         LangGraph Agent Orchestrator
        │          │       │        │
        │       Tools   PostgreSQL  Google
        │     (todo,      (state,   Calendar
        │    reminder,   history)   (events)
        │    calendar,
        │    family…)
        │
        └──►  POST /api/chat  (text)
```

---

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- An [Anthropic API key](https://console.anthropic.com/)
- A [Deepgram API key](https://console.deepgram.com/) (for voice)
- Google OAuth 2.0 credentials (for calendar; optional)

### 1. Configure

```bash
cp .env.example .env
# Edit .env — fill in ANTHROPIC_API_KEY, DEEPGRAM_API_KEY,
# GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and set a strong APP_SECRET_KEY.
# POSTGRES_PASSWORD and DATABASE_URL must match.
```

`.env` is git-ignored. No secrets are committed anywhere in this repository.

For Google Calendar, download your OAuth client JSON from Google Cloud Console and save it to `credentials/google_client_secret.json` (this path is also git-ignored).

### 2. Start the databases

```bash
docker compose up -d db
```

PostgreSQL will be available on `localhost:5433`.

### 3. Run the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head          # run migrations
uvicorn app.main:app --reload --port 8000
```

API is at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

UI is at `http://localhost:5173`.

### 5. Run everything with Docker Compose

```bash
cp .env.example .env   # fill in secrets
docker compose up --build
```

---

## API overview

| Route | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /api/status` | Connection status (Google Calendar linked?) |
| `POST /api/chat` | Text chat — returns agent response |
| `WS /voice-ws` | Bidirectional voice WebSocket (STT → agent → TTS) |
| `GET /api/auth/google/login` | Start Google OAuth flow |
| `GET /api/auth/google/callback` | OAuth callback |
| `DELETE /api/auth/google/disconnect` | Unlink Google account |
| `GET /api/todos` | List todos |
| `GET /api/family` | List family members |

Full interactive docs: `http://localhost:8000/docs`

---

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `DEEPGRAM_API_KEY` | Deepgram key for STT and TTS |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `DATABASE_URL` | PostgreSQL async URL |
| `APP_SECRET_KEY` | Secret for signing session tokens |
| `ENVIRONMENT` | `development` or `production` |

---

## Development notes

- The agent uses a LangGraph `StateGraph`; each tool is a discrete node. See `backend/app/agent/`.
- Database migrations live in `backend/alembic/versions/`. Run `alembic revision --autogenerate -m "description"` to create a new one.
- Voice is handled over a WebSocket in `backend/app/routes/voice_ws.py`; the client streams audio chunks and receives synthesised audio back.
- Scheduled reminders use APScheduler; the scheduler is started in the FastAPI lifespan (`backend/app/scheduler.py`).

---

## License

[MIT](LICENSE)
