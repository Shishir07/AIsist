from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings
from app.db.models import Base

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Create all tables on startup (dev only — use Alembic in prod)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed reference data (idempotent — skips if already seeded)
    from app.db.seed import run_seeds
    async with AsyncSessionLocal() as db:
        await run_seeds(db)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
