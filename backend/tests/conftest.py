"""Pytest fixtures."""
import sys
from collections.abc import AsyncIterator
from pathlib import Path

# Add backend/ to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a fresh engine per test, disposed after."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=0,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    """Provide a session that connects via the test-local engine."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncIterator[AsyncClient]:
    """HTTP client bound to the ASGI app (no real network)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac