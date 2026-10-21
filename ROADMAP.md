# AIsist Roadmap

## Phase 1 — Core assistant (complete)

- [x] FastAPI backend with LangGraph agent
- [x] Voice input via Deepgram STT over WebSocket
- [x] Voice output via Deepgram TTS
- [x] Todo / task management (CRUD via agent tools)
- [x] Reminder scheduling (APScheduler)
- [x] Google Calendar integration (OAuth 2.0, read + create events)
- [x] Family member profiles and preferences
- [x] PostgreSQL persistence (SQLAlchemy async + Alembic)
- [x] React + Vite + Tailwind frontend
- [x] Docker Compose for local development

## Phase 2 — Household management (in progress)

- [ ] Pantry tracking — add/remove items, low-stock alerts
- [ ] Grocery list management — auto-suggest from pantry and meal plan
- [ ] Meal planning — suggest weekly meals based on preferences and pantry
- [ ] Recipe lookup and storage
- [ ] Shopping list export (share link or text)

## Phase 3 — Multi-user and polish

- [ ] Per-user authentication (JWT / sessions)
- [ ] Multiple family member accounts with data isolation
- [ ] Push notifications for reminders (browser + mobile)
- [ ] Conversation history search
- [ ] Onboarding flow (connect calendar, add family members)
- [ ] Offline / PWA support

## Phase 4 — Integrations and intelligence

- [ ] Supermarket price comparison via external APIs
- [ ] Smart grocery ordering (Instacart or similar)
- [ ] Calendar conflict detection and suggestions
- [ ] Proactive suggestions ("You're low on eggs and eggs are in Tuesday's meal plan")
- [ ] Multi-language voice support

## Known issues / open bugs

- Google Calendar token refresh needs error-recovery handling
- Voice WebSocket drops silently on network interruption — needs reconnect logic
- Frontend has no loading state during long agent responses

## Ideas / icebox

- Shared family dashboard (read-only link)
- Slack / WhatsApp bot interface
- Home automation hooks (lights, thermostat)
