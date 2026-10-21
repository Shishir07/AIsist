from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import init_db
from app.agent.graph import init_graph, close_graph
from app.routes.api import router as api_router
from app.routes.voice_ws import router as voice_router
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await init_graph()
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    await close_graph()


app = FastAPI(
    title="AIsist API",
    description="Voice Personal Assistant - Phase 1",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix="/api")
app.include_router(voice_router)


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}
