"""
PEVN Backend — Test Configuration & Fixtures

Provides fixtures for async HTTP client and isolated in-memory test database sessions.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Set default test environment variables
# ---------------------------------------------------------------------------
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-pevn-phase1-not-for-production-" + "0" * 80,
)
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

from app.core.config import get_settings
from app.core.security.interfaces import SystemRole
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_application
from app.models.grade import EducationalLevel, Grade
from app.models.role import Permission, Role


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio as the anyio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an isolated in-memory SQLite database session for tests.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables in SQLite
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        # Seed standard roles & permissions
        roles_data = [
            (SystemRole.SUPERADMIN.value, "Super Administrador", 100),
            (SystemRole.NATIONAL_ADMIN.value, "Administrador Nacional", 90),
            (SystemRole.DEPARTMENT_ADMIN.value, "Administrador Departamental", 80),
            (SystemRole.MUNICIPALITY_ADMIN.value, "Administrador Municipal", 70),
            (SystemRole.INSTITUTION_ADMIN.value, "Administrador Institucional", 60),
            (SystemRole.RECTOR.value, "Rector", 50),
            (SystemRole.ACADEMIC_COORDINATOR.value, "Coordinador Académico", 40),
            (SystemRole.TEACHER.value, "Docente", 30),
            (SystemRole.STUDENT.value, "Estudiante", 10),
        ]
        for name, display, rlevel in roles_data:
            role = Role(name=name, display_name=display, level=rlevel)
            session.add(role)

        # Seed standard permissions
        perms_data = [
            ("users", "create"),
            ("users", "read"),
            ("users", "update"),
            ("users", "delete"),
            ("institutions", "read"),
            ("institutions", "update"),
            ("grades", "read"),
            ("grades", "write"),
        ]
        for res, act in perms_data:
            perm = Permission(
                resource=res,
                action=act,
                description=f"Permite {act} en {res}",
            )
            session.add(perm)

        # Seed standard national grades
        grades_data = [
            ("TRANSICION", "Transición", EducationalLevel.PREESCOLAR, 0),
            ("G01", "Primero", EducationalLevel.PRIMARIA, 1),
            ("G02", "Segundo", EducationalLevel.PRIMARIA, 2),
            ("G03", "Tercero", EducationalLevel.PRIMARIA, 3),
            ("G04", "Cuarto", EducationalLevel.PRIMARIA, 4),
            ("G05", "Quinto", EducationalLevel.PRIMARIA, 5),
            ("G06", "Sexto", EducationalLevel.SECUNDARIA, 6),
            ("G07", "Séptimo", EducationalLevel.SECUNDARIA, 7),
            ("G08", "Octavo", EducationalLevel.SECUNDARIA, 8),
            ("G09", "Noveno", EducationalLevel.SECUNDARIA, 9),
            ("G10", "Décimo", EducationalLevel.MEDIA, 10),
            ("G11", "Undécimo", EducationalLevel.MEDIA, 11),
        ]
        for code, gname, ed_level, order in grades_data:
            grade = Grade(
                code=code,
                name=gname,
                level=ed_level,
                ordinal_order=order,
            )
            session.add(grade)

        await session.commit()
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP test client with database session override.
    """
    get_settings.cache_clear()

    test_app = create_application()

    # Override get_async_session dependency to use the isolated test db_session
    async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    test_app.dependency_overrides[get_async_session] = _override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=test_app),  # type: ignore[arg-type]
        base_url="http://testserver",
        headers={"Host": "localhost"},
    ) as test_client:
        yield test_client

    get_settings.cache_clear()
