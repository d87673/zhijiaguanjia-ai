"""
Pytest configuration and fixtures for 智家管家AI backend tests.
Uses in-memory SQLite (no Docker needed).

Key adaptation: SQLite doesn't support PostgreSQL ARRAY.
We replace ARRAY(String) with JSON on Customer.tags and Staff.skills,
plus a TypeDecorator that serializes list→JSON string on bind
and deserializes JSON string→list on result.
"""
import os
import json

os.environ["TESTING"] = "1"

from sqlalchemy import JSON, ARRAY
from sqlalchemy.types import TypeDecorator


class JsonListType(TypeDecorator):
    """Stores Python list[str] as TEXT(JSON) for SQLite.
    Behaves transparently: bind=list, result=list."""
    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return value  # already serialized
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []


# ── Patch: swap ARRAY columns BEFORE table creation ──
import app.models.models as _mod

for _model_cls in [_mod.Customer, _mod.Staff]:
    for _col in _model_cls.__table__.columns:
        if isinstance(_col.type, ARRAY):
            _col.type = JsonListType(none_as_null=True)

# Safety: make SQLite dialect able to compile any remaining ARRAY
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
if not hasattr(SQLiteTypeCompiler, 'visit_ARRAY'):
    SQLiteTypeCompiler.visit_ARRAY = lambda self, t, **kw: self.visit_JSON(JSON(), **kw)

# ── Now safe to import ──
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from app.core.database import Base
from app.models.models import (
    User, Company, Service, Customer, Staff,
    Order, OrderItem, Payment, Conversation, Message,
)

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


async def override_get_current_user():
    from datetime import datetime, timezone
    return User(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        name="测试账号",
        email="test@zhijiaguanjia.ai",
        role="admin",
        phone="13800000000",
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        is_active=True,
        created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )


async def override_get_current_company():
    return "c0d1e2f3-a4b5-6789-abcd-ef1234567890"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Fresh isolated database session for each test."""
    from app.core.deps import get_current_user, get_current_company
    from app.core.database import get_db

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_company] = override_get_current_company

    async with TestSessionLocal() as session:
        company = Company(
            id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
            name="测试家政公司",
            slug="test-company",
            plan="pro",
        )
        session.add(company)
        await session.flush()
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Async HTTP client for testing endpoints."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-mock-token-for-testing"}
