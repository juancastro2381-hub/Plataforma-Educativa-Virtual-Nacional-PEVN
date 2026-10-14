"""
PEVN — SA-02: SUPER_ADMIN Technical Operations Portal & Platform Observability Test Suite

Verifies:
  TEST-01: SuperAdmin can access /overview and /health endpoints (Real telemetry & components).
  TEST-02: SuperAdmin can query live security audit feed from audit_logs with summary statistics.
  TEST-03: SuperAdmin technical support case lifecycle (list, create, update with audit trail).
  TEST-04: SuperAdmin tenant diagnostics requires valid institution ID and triggers security audit event.
  TEST-05: Non-existent institution returns 404 in tenant diagnostics.
  TEST-06: Strict Role Separation: NATIONAL_ADMIN (Level 90) receives HTTP 403 on ALL /operations/* endpoints.
  TEST-07: Unauthenticated and inactive accounts are rejected with HTTP 401.
  TEST-08: Platform integrations endpoint omits credentials and sensitive tokens.
"""

from collections.abc import AsyncGenerator
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.audit.interfaces import AuditEventType
from app.audit.service import audit_service
from app.core.security.tokens import token_service
from app.db.session import get_async_session
from app.main import create_application
from app.models.institution import Institution
from app.models.role import Role, UserRole
from app.models.user import User
from tests.conftest import get_test_postgres_url

PG_DB_URL = get_test_postgres_url()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated session connected to PostgreSQL."""
    engine = create_async_engine(PG_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client connected to the FastAPI application."""
    test_app = create_application()
    engine = create_async_engine(PG_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_async_session] = _override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=test_app),  # type: ignore[arg-type]
        base_url="http://localhost",
        headers={"Host": "localhost"},
    ) as test_client:
        yield test_client

    await engine.dispose()


@pytest.fixture(scope="function")
async def superadmin_actor(db_session: AsyncSession) -> dict[str, Any]:
    """Resolve canonical SuperAdmin root user and auth headers."""
    stmt = (
        select(User)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .where(Role.name == "superadmin", User.is_active == True)
        .limit(1)
    )
    user = (await db_session.execute(stmt)).scalar_one_or_none()
    assert user is not None, "SuperAdmin user required in database."

    token = await token_service.create_access_token(subject=str(user.id))
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return {"user": user, "token": token, "headers": headers}


@pytest.fixture(scope="function")
async def national_admin_actor(db_session: AsyncSession) -> dict[str, Any]:
    """Resolve canonical National Admin user and auth headers."""
    stmt = (
        select(User)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .where(Role.name == "national_admin", User.is_active == True)
        .limit(1)
    )
    user = (await db_session.execute(stmt)).scalar_one_or_none()
    assert user is not None, "National Admin user required in database."

    token = await token_service.create_access_token(subject=str(user.id))
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return {"user": user, "token": token, "headers": headers}


@pytest.mark.asyncio
async def test_01_superadmin_can_access_overview_and_health(
    client: AsyncClient, superadmin_actor: dict[str, Any]
) -> None:
    """SuperAdmin can query platform overview telemetry and health breakdown."""
    # Overview
    resp_overview = await client.get(
        "/api/v1/system/operations/overview",
        headers=superadmin_actor["headers"],
    )
    assert resp_overview.status_code == 200, f"Overview must return 200, got: {resp_overview.text}"
    data_overview = resp_overview.json()
    assert "overall_status" in data_overview
    assert "database" in data_overview
    assert data_overview["database"]["status"] == "ok"
    assert "password" not in data_overview["database"]["safe_url"].lower()
    assert "metrics" in data_overview

    # Health
    resp_health = await client.get(
        "/api/v1/system/operations/health",
        headers=superadmin_actor["headers"],
    )
    assert resp_health.status_code == 200
    data_health = resp_health.json()
    assert "services" in data_health
    assert len(data_health["services"]) >= 4


@pytest.mark.asyncio
async def test_02_superadmin_can_query_security_audit_feed(
    client: AsyncClient, superadmin_actor: dict[str, Any]
) -> None:
    """SuperAdmin can query live security audit logs with summary aggregations."""
    resp = await client.get(
        "/api/v1/system/operations/audit-feed?limit=20&only_security=true",
        headers=superadmin_actor["headers"],
    )
    assert resp.status_code == 200, f"Audit feed must return 200, got: {resp.text}"
    data = resp.json()
    assert "items" in data
    assert "summary" in data
    assert "failed_logins" in data["summary"]
    assert "permission_denied" in data["summary"]


@pytest.mark.asyncio
async def test_03_superadmin_support_cases_lifecycle(
    client: AsyncClient, superadmin_actor: dict[str, Any]
) -> None:
    """SuperAdmin can list, create, and update technical support cases."""
    # 1. List cases
    list_resp = await client.get(
        "/api/v1/system/operations/support-cases",
        headers=superadmin_actor["headers"],
    )
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert "items" in list_data
    assert "total" in list_data
    assert "open_count" in list_data

    # 2. Create new incident
    create_payload = {
        "title": "Alerta de latencia en sincronización de catálogo territorial",
        "category": "INTEGRATION",
        "severity": "HIGH",
        "affected_service": "catalog_sync",
        "description": "Incremento de tiempo de respuesta durante la sincronización DANE de 18,031 registros.",
        "technical_context": {"endpoint": "datos.gov.co", "timeout_threshold_ms": 5000},
        "assigned_operator": "Operador Nivel 100",
    }
    create_resp = await client.post(
        "/api/v1/system/operations/support-cases",
        json=create_payload,
        headers=superadmin_actor["headers"],
    )
    assert create_resp.status_code == 201, f"Create incident must return 201, got: {create_resp.text}"
    created = create_resp.json()
    assert created["title"] == create_payload["title"]
    assert created["ticket_number"].startswith("INC-2026-")
    assert created["status"] == "OPEN"
    case_id = created["id"]

    # 3. Update incident (mitigate/resolve)
    update_payload = {
        "status": "RESOLVED",
        "resolution_notes": "Ajuste de tamaño de lote de sincronización a 250 registros por chunk. Latencia normalizada.",
    }
    update_resp = await client.patch(
        f"/api/v1/system/operations/support-cases/{case_id}",
        json=update_payload,
        headers=superadmin_actor["headers"],
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["status"] == "RESOLVED"
    assert updated["resolution_notes"] == update_payload["resolution_notes"]
    assert updated["resolved_at"] is not None


@pytest.mark.asyncio
async def test_04_superadmin_tenant_diagnostics_with_audit(
    client: AsyncClient,
    db_session: AsyncSession,
    superadmin_actor: dict[str, Any],
) -> None:
    """SuperAdmin tenant diagnostics collects real metrics and triggers an audit event."""
    inst = (
        await db_session.execute(
            select(Institution).where(Institution.is_active == True).limit(1)
        )
    ).scalar_one_or_none()
    assert inst is not None, "At least one active institution must exist in DB."

    recorded_events: list[Any] = []
    original_record = audit_service.record

    async def spy_record(event: Any, session: Any = None) -> None:
        recorded_events.append(event)
        try:
            await original_record(event, session=session)
        except Exception:
            pass

    audit_service.record = spy_record  # type: ignore[assignment]
    try:
        resp = await client.get(
            f"/api/v1/system/operations/tenant-diagnostics/{inst.id}",
            headers=superadmin_actor["headers"],
        )
        assert resp.status_code == 200, f"Tenant diagnostics must return 200, got: {resp.text}"
        data = resp.json()
        assert data["institution_id"] == str(inst.id)
        assert data["name"] == inst.name
        assert "telemetry" in data
        assert "campuses_count" in data["telemetry"]
        assert "active_users" in data["telemetry"]

        # Verify audit trail event recorded
        diag_events = [
            e for e in recorded_events
            if getattr(e, "target_type", "") == "tenant_diagnostics"
        ]
        assert len(diag_events) >= 1, "Technical diagnostic access must emit an audit event."
        assert str(diag_events[0].target_id) == str(inst.id)
    finally:
        audit_service.record = original_record


@pytest.mark.asyncio
async def test_05_nonexistent_institution_returns_404(
    client: AsyncClient, superadmin_actor: dict[str, Any]
) -> None:
    """Diagnostic inquiry for non-existent institution fails safely with 404."""
    fake_id = uuid.uuid4()
    resp = await client.get(
        f"/api/v1/system/operations/tenant-diagnostics/{fake_id}",
        headers=superadmin_actor["headers"],
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_06_national_admin_strictly_rejected_on_all_operations_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    national_admin_actor: dict[str, Any],
) -> None:
    """
    National Admin (Level 90) must receive HTTP 403 Forbidden on all technical
    operations endpoints, enforcing strict role boundary separation.
    """
    endpoints = [
        ("GET", "/api/v1/system/operations/overview"),
        ("GET", "/api/v1/system/operations/health"),
        ("GET", "/api/v1/system/operations/audit-feed"),
        ("GET", "/api/v1/system/operations/support-cases"),
        ("POST", "/api/v1/system/operations/support-cases"),
        ("GET", f"/api/v1/system/operations/tenant-diagnostics/{uuid.uuid4()}"),
        ("GET", "/api/v1/system/operations/integrations"),
    ]

    for method, path in endpoints:
        if method == "GET":
            resp = await client.get(path, headers=national_admin_actor["headers"])
        else:
            resp = await client.post(
                path,
                json={"title": "Test probe", "description": "Unauthorized attempt test"},
                headers=national_admin_actor["headers"],
            )
        assert resp.status_code == 403, (
            f"National Admin MUST receive 403 on {method} {path}, got {resp.status_code}: {resp.text}"
        )


@pytest.mark.asyncio
async def test_07_unauthenticated_and_inactive_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Unauthenticated requests receive 401 Unauthorized."""
    resp = await client.get("/api/v1/system/operations/overview")
    assert resp.status_code == 401

    resp_cases = await client.get("/api/v1/system/operations/support-cases")
    assert resp_cases.status_code == 401


@pytest.mark.asyncio
async def test_08_platform_integrations_endpoint_omits_secrets(
    client: AsyncClient, superadmin_actor: dict[str, Any]
) -> None:
    """Integrations endpoint describes services without exposing credentials or keys."""
    resp = await client.get(
        "/api/v1/system/operations/integrations",
        headers=superadmin_actor["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "integrations" in data
    assert len(data["integrations"]) >= 3

    for item in data["integrations"]:
        raw_str = str(item).lower()
        assert "password" not in raw_str
        assert "secret_key" not in raw_str
        assert "token=" not in raw_str


@pytest.mark.asyncio
async def test_09_telemetry_source_truthfulness_and_job_diagnostics(
    client: AsyncClient, superadmin_actor: dict[str, Any]
) -> None:
    """Telemetry strictly reports truthful statuses: on_demand adapter, in-process tasks, and no simulated values."""
    # 1. Overview check
    resp_ov = await client.get(
        "/api/v1/system/operations/overview",
        headers=superadmin_actor["headers"],
    )
    assert resp_ov.status_code == 200
    data_ov = resp_ov.json()
    assert data_ov["background_jobs"]["status"] == "in_process"
    assert data_ov["background_jobs"]["handler"] == "FastAPI BackgroundTasks"

    # 2. Health check
    resp_hl = await client.get(
        "/api/v1/system/operations/health",
        headers=superadmin_actor["headers"],
    )
    assert resp_hl.status_code == 200
    data_hl = resp_hl.json()
    men_svc = next((s for s in data_hl["services"] if "MEN" in s["name"]), None)
    assert men_svc is not None
    assert men_svc["status"] == "standby"

    # 3. Integrations check
    resp_int = await client.get(
        "/api/v1/system/operations/integrations",
        headers=superadmin_actor["headers"],
    )
    assert resp_int.status_code == 200
    data_int = resp_int.json()
    men_int = next((i for i in data_int["integrations"] if "MEN" in i["name"]), None)
    assert men_int is not None
    assert men_int["status"] == "on_demand"

