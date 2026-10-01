import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.core.database import Base, get_db
from app.data.seed_data import seed_database
from app.ml.lab_extractor import invalidate_biomarker_cache
from app.ml.explainer_ai import invalidate_glossary_cache
from main import app

# Determine isolated test database URL
TEST_DB_URL = (
    os.getenv("TEST_DATABASE_URL")
    or getattr(settings, "TEST_DATABASE_URL", None)
    or "sqlite+aiosqlite:///./test_vitalens_dev.db"
)

# Explicitly override application database URL and storage provider for test runner
settings.DATABASE_URL = TEST_DB_URL
settings.STORAGE_PROVIDER = "local"
from app.core import storage as app_storage
local_storage = app_storage.LocalStorageAdapter()
app_storage.storage_adapter = local_storage
import main
main.storage_adapter = local_storage
import app.services.report_service as rs
rs.storage_adapter = local_storage

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    poolclass=NullPool if "postgresql" in TEST_DB_URL else None,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DB_URL else {}
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Apply dependency override
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """
    Isolates each test: drops all tables, recreates schema on test DB, and seeds fresh reference records.
    """
    invalidate_biomarker_cache()
    invalidate_glossary_cache()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await seed_database(custom_engine=test_engine, custom_session_factory=TestingSessionLocal, include_doctors=True)

    yield

    invalidate_biomarker_cache()
    invalidate_glossary_cache()
    await test_engine.dispose()
