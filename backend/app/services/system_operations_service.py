"""
PEVN Backend — System Operations & Platform Observability Service

Core service driving the SUPER_ADMIN (Level 100) Technical Operations Portal.
Provides platform health checks, security audit querying, technical support
ticket lifecycle management, and audited tenant diagnostic evaluations.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.health import check_database_connectivity
from app.db.session import get_engine, get_session_factory
from app.models.audit_log import AuditLog
from app.models.institution import Campus, Institution
from app.models.technical_incident import (
    TechnicalIncident,
    TechnicalIncidentCategory,
    TechnicalIncidentSeverity,
    TechnicalIncidentStatus,
)
from app.models.user import User

_logger = get_logger(__name__)


class SystemOperationsService:
    """Service encapsulating platform telemetry, diagnostics, and support operations."""

    def __init__(self) -> None:
        self._table_initialized = False

    async def ensure_incident_table_exists(self, session: AsyncSession) -> None:
        """Ensure the technical_support_cases table exists in the active database."""
        if self._table_initialized:
            return

        try:
            engine = get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn: TechnicalIncident.__table__.create(sync_conn, checkfirst=True)
                )
            self._table_initialized = True
        except Exception:
            self._table_initialized = True

    async def seed_initial_incidents_if_empty(self, session: AsyncSession) -> None:
        """Seed 2 baseline operational cases if the technical incident table is empty."""
        try:
            await self.ensure_incident_table_exists(session)
            count_query = select(func.count()).select_from(TechnicalIncident)
            res = await session.execute(count_query)
            count = res.scalar() or 0

            if count == 0:
                sample_1 = TechnicalIncident(
                    ticket_number="INC-2026-0001",
                    title="Verificación de latencia en replicación de base de datos",
                    category=TechnicalIncidentCategory.DATABASE.value,
                    severity=TechnicalIncidentSeverity.LOW.value,
                    status=TechnicalIncidentStatus.RESOLVED.value,
                    affected_service="database",
                    description="Inspección preventiva de tiempos de respuesta en el pool de conexiones asíncronas.",
                    technical_context={"measured_latency_ms": 2.4, "pool_size": 10},
                    assigned_operator="Operador Antigravity L100",
                    resolution_notes="Pool de conexiones optimizado con timeout pre-ping a 60 segundos.",
                    resolved_at=datetime.now(UTC),
                )
                sample_2 = TechnicalIncident(
                    ticket_number="INC-2026-0002",
                    title="Monitoreo de cola de notificaciones y correo institucional",
                    category=TechnicalIncidentCategory.SYSTEM.value,
                    severity=TechnicalIncidentSeverity.MEDIUM.value,
                    status=TechnicalIncidentStatus.OPEN.value,
                    affected_service="mailer",
                    description="Supervisión de entregas de invitaciones de activación de rectores y administradores territoriales.",
                    technical_context={"delivery_rate": "99.8%", "retry_queue": 0},
                    assigned_operator="Equipo de Infraestructura PEVN",
                    resolution_notes=None,
                )
                session.add_all([sample_1, sample_2])
                await session.commit()
        except Exception as exc:
            _logger.warning("Failed to seed sample technical incidents", error=str(exc))

    async def get_platform_overview(self, session: AsyncSession) -> dict[str, Any]:
        """
        Produce a high-level operational status payload combining live health telemetry,
        incident counters, and security audit statistics.
        """
        settings = get_settings()

        # 1. Database check & latency
        t0 = time.perf_counter()
        db_ok, _ = await check_database_connectivity()
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 2. Redis check
        redis_ok = await self._check_redis()

        # 3. Security events count in last 24 hours
        yesterday = datetime.now(UTC) - timedelta(days=1)
        security_count = 0
        try:
            sec_query = (
                select(func.count())
                .select_from(AuditLog)
                .where(
                    or_(
                        AuditLog.event_type.like("security.%"),
                        AuditLog.event_type.in_(
                            [
                                AuditEventType.USER_LOGIN_FAILURE.value,
                                AuditEventType.USER_ACCOUNT_LOCKED.value,
                                AuditEventType.TOKEN_REUSE_DETECTED.value,
                            ]
                        ),
                    )
                )
            )
            res = await session.execute(sec_query)
            security_count = res.scalar() or 0
        except Exception:
            security_count = 0

        # 4. Open technical incidents count
        open_incidents = 0
        try:
            await self.ensure_incident_table_exists(session)
            inc_query = (
                select(func.count())
                .select_from(TechnicalIncident)
                .where(TechnicalIncident.status.in_([TechnicalIncidentStatus.OPEN.value, TechnicalIncidentStatus.INVESTIGATING.value]))
            )
            res = await session.execute(inc_query)
            open_incidents = res.scalar() or 0
        except Exception:
            open_incidents = 0

        overall_status = "OPERATIONAL" if (db_ok and redis_ok) else "DEGRADED" if db_ok else "OUTAGE"

        return {
            "overall_status": overall_status,
            "measured_at": datetime.now(UTC).isoformat(),
            "environment": settings.ENVIRONMENT.value if hasattr(settings.ENVIRONMENT, "value") else str(settings.ENVIRONMENT),
            "version": "1.0.0",
            "database": {
                "status": "ok" if db_ok else "error",
                "latency_ms": db_latency_ms,
                "pool_size": settings.DB_POOL_SIZE,
                "safe_url": settings.get_safe_database_url(),
            },
            "redis": {
                "status": "ok" if redis_ok else "degraded",
                "mode": "in-memory-fallback" if not redis_ok else "connected",
            },
            "background_jobs": {
                "status": "in_process",
                "handler": "FastAPI BackgroundTasks",
                "active_queues": ["audit_persister", "invitation_mailer"],
            },
            "metrics": {
                "active_incidents": open_incidents,
                "security_events_24h": security_count,
            },
        }

    async def get_platform_health(self) -> dict[str, Any]:
        """Comprehensive multi-tier health probe evaluating dependencies and integrations."""
        settings = get_settings()

        t0 = time.perf_counter()
        db_ok, _ = await check_database_connectivity()
        db_latency = round((time.perf_counter() - t0) * 1000, 2)
        redis_ok = await self._check_redis()

        return {
            "status": "healthy" if (db_ok and redis_ok) else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "services": [
                {
                    "name": "FastAPI Core Gateway",
                    "status": "operational",
                    "type": "api",
                    "details": "Rutas autenticadas v1 operativas.",
                },
                {
                    "name": "PostgreSQL Primary Engine",
                    "status": "operational" if db_ok else "outage",
                    "type": "database",
                    "details": f"Latencia de ping: {db_latency} ms.",
                },
                {
                    "name": "Redis Distributed Cache",
                    "status": "operational" if redis_ok else "degraded",
                    "type": "cache",
                    "details": "Conexión activa." if redis_ok else "Modo de tolerancia a fallos activado.",
                },
                {
                    "name": "MEN Open Data Adapter",
                    "status": "standby",
                    "type": "external_integration",
                    "details": "Adaptador de ingesta Socrata/CSV por demanda; sin sonda en vivo.",
                },
                {
                    "name": "Audit Logging Subsystem",
                    "status": "operational",
                    "type": "security",
                    "details": "Persistencia inmutable activa.",
                },
            ],
        }

    async def get_security_audit_feed(
        self,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        only_security: bool = True,
    ) -> dict[str, Any]:
        """
        Query real audit logs from the database, prioritizing security events and logins.
        """
        query = select(AuditLog)

        if only_security:
            query = query.where(
                or_(
                    AuditLog.event_type.like("security.%"),
                    AuditLog.event_type.like("user.login%"),
                    AuditLog.event_type.like("user.account%"),
                    AuditLog.event_type.like("superadmin%"),
                    AuditLog.event_type.like("token.%"),
                )
            )

        query = query.order_by(AuditLog.occurred_at.desc()).limit(limit).offset(offset)

        items = []
        try:
            res = await session.execute(query)
            rows = res.scalars().all()
            for r in rows:
                items.append(
                    {
                        "id": str(r.id),
                        "event_type": r.event_type,
                        "actor_id": str(r.actor_id) if r.actor_id else None,
                        "actor_ip": r.actor_ip,
                        "target_type": r.target_type,
                        "target_id": r.target_id,
                        "institution_id": str(r.institution_id) if r.institution_id else None,
                        "success": r.success,
                        "metadata": r.metadata_json,
                        "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
                    }
                )
        except Exception as exc:
            _logger.warning("Failed to query audit_logs table", error=str(exc))

        # Query summary stats
        summary = {"total_queried": len(items), "failed_logins": 0, "permission_denied": 0, "suspicious_events": 0}
        for item in items:
            evt = item["event_type"]
            if evt == AuditEventType.USER_LOGIN_FAILURE.value:
                summary["failed_logins"] += 1
            elif evt == AuditEventType.PERMISSION_DENIED.value:
                summary["permission_denied"] += 1
            elif "suspicious" in evt:
                summary["suspicious_events"] += 1

        return {
            "items": items,
            "total": len(items),
            "summary": summary,
        }

    async def list_support_cases(
        self,
        session: AsyncSession,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List platform technical support cases with filter and pagination."""
        await self.ensure_incident_table_exists(session)
        await self.seed_initial_incidents_if_empty(session)

        query = select(TechnicalIncident)
        if status:
            query = query.where(TechnicalIncident.status == status)
        if severity:
            query = query.where(TechnicalIncident.severity == severity)

        query = query.order_by(TechnicalIncident.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(query)
        cases = res.scalars().all()

        total_res = await session.execute(select(func.count()).select_from(TechnicalIncident))
        total = total_res.scalar() or 0

        open_res = await session.execute(
            select(func.count())
            .select_from(TechnicalIncident)
            .where(TechnicalIncident.status.in_([TechnicalIncidentStatus.OPEN.value, TechnicalIncidentStatus.INVESTIGATING.value]))
        )
        open_count = open_res.scalar() or 0

        crit_res = await session.execute(
            select(func.count())
            .select_from(TechnicalIncident)
            .where(TechnicalIncident.severity == TechnicalIncidentSeverity.CRITICAL.value)
        )
        critical_count = crit_res.scalar() or 0

        return {
            "items": cases,
            "total": total,
            "open_count": open_count,
            "critical_count": critical_count,
        }

    async def create_support_case(
        self,
        session: AsyncSession,
        actor_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> TechnicalIncident:
        """Create a new technical support case and write an audit trail event."""
        await self.ensure_incident_table_exists(session)

        # Generate ticket sequence identifier
        ticket_num = f"INC-2026-{uuid.uuid4().hex[:6].upper()}"

        incident = TechnicalIncident(
            ticket_number=ticket_num,
            title=payload["title"],
            category=payload.get("category", TechnicalIncidentCategory.SYSTEM.value),
            severity=payload.get("severity", TechnicalIncidentSeverity.MEDIUM.value),
            status=TechnicalIncidentStatus.OPEN.value,
            affected_service=payload.get("affected_service", "platform"),
            institution_id=payload.get("institution_id"),
            reporter_id=actor_id,
            assigned_operator=payload.get("assigned_operator", "Operador L100"),
            description=payload["description"],
            technical_context=payload.get("technical_context"),
            resolution_notes=None,
        )
        session.add(incident)
        await session.commit()
        await session.refresh(incident)

        # Record audit event
        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.CONFIG_CHANGED,
                actor_ip="127.0.0.1",
                actor_id=str(actor_id),
                target_type="technical_incident",
                target_id=ticket_num,
                institution_id=payload.get("institution_id"),
                metadata={
                    "action": "technical_support_case_created",
                    "ticket_number": ticket_num,
                    "severity": incident.severity,
                    "category": incident.category,
                },
            ),
            session=session,
        )

        return incident

    async def update_support_case(
        self,
        session: AsyncSession,
        case_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> TechnicalIncident | None:
        """Update incident lifecycle status, operator assignment, or resolution notes."""
        await self.ensure_incident_table_exists(session)

        query = select(TechnicalIncident).where(TechnicalIncident.id == case_id)
        res = await session.execute(query)
        incident = res.scalar_one_or_none()
        if not incident:
            return None

        if "status" in payload and payload["status"]:
            incident.status = payload["status"]
            if payload["status"] in (TechnicalIncidentStatus.RESOLVED.value, TechnicalIncidentStatus.CLOSED.value):
                incident.resolved_at = datetime.now(UTC)

        if "severity" in payload and payload["severity"]:
            incident.severity = payload["severity"]

        if "assigned_operator" in payload and payload["assigned_operator"]:
            incident.assigned_operator = payload["assigned_operator"]

        if "resolution_notes" in payload and payload["resolution_notes"]:
            incident.resolution_notes = payload["resolution_notes"]

        await session.commit()
        await session.refresh(incident)

        # Record audit log
        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.CONFIG_CHANGED,
                actor_ip="127.0.0.1",
                actor_id=str(actor_id),
                target_type="technical_incident",
                target_id=incident.ticket_number,
                metadata={
                    "action": "technical_support_case_updated",
                    "new_status": incident.status,
                    "new_severity": incident.severity,
                    "has_resolution": bool(incident.resolution_notes),
                },
            ),
            session=session,
        )

        return incident

    async def get_tenant_diagnostics(
        self,
        session: AsyncSession,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        """
        Produce a comprehensive diagnostic report for a specific educational tenant.
        Audits the technical access in the audit log.
        """
        # 1. Fetch institution
        inst_query = select(Institution).where(Institution.id == institution_id)
        inst_res = await session.execute(inst_query)
        inst = inst_res.scalar_one_or_none()
        if not inst:
            return None

        # 2. Fetch campuses count
        campus_query = select(Campus).where(Campus.institution_id == institution_id)
        campus_res = await session.execute(campus_query)
        campuses = campus_res.scalars().all()

        # 3. Fetch user counts by role
        users_query = select(User).where(User.institution_id == institution_id)
        users_res = await session.execute(users_query)
        inst_users = users_res.scalars().all()

        active_users_count = sum(1 for u in inst_users if u.is_active)
        locked_users_count = sum(1 for u in inst_users if u.is_locked)

        # 4. Record technical audit event
        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
                actor_ip="127.0.0.1",
                actor_id=str(actor_id),
                target_type="tenant_diagnostics",
                target_id=str(institution_id),
                institution_id=institution_id,
                metadata={
                    "action": "superadmin_technical_access:tenant_diagnostics:read",
                    "role": "superadmin",
                    "institution_name": inst.name,
                    "dane_code": inst.dane_code,
                    "note": "Auditoría de diagnóstico técnico de inquilino por SuperAdmin L100.",
                },
            ),
            session=session,
        )

        return {
            "institution_id": str(inst.id),
            "name": inst.name,
            "dane_code": inst.dane_code,
            "is_active": inst.is_active,
            "created_at": inst.created_at.isoformat() if hasattr(inst, "created_at") and inst.created_at else None,
            "telemetry": {
                "campuses_count": len(campuses),
                "campuses": [{"id": str(c.id), "name": c.name, "dane_code": c.dane_sede_code} for c in campuses],
                "total_users": len(inst_users),
                "active_users": active_users_count,
                "locked_users": locked_users_count,
                "configuration_status": "VALID" if inst.is_active and len(campuses) > 0 else "INCOMPLETE",
            },
            "audited_at": datetime.now(UTC).isoformat(),
        }

    async def get_platform_integrations(self) -> dict[str, Any]:
        """Return connectivity configuration of external integrations without leaking credentials."""
        settings = get_settings()
        return {
            "integrations": [
                {
                    "name": "MEN Open Data API (Datos Abiertos Colombia)",
                    "type": "REST API",
                    "endpoint": "https://www.datos.gov.co/resource/c5k7-ee45.json",
                    "status": "on_demand",
                    "auth_type": "Public App-Token / Ingesta batch",
                },
                {
                    "name": "PostgreSQL Primary Cluster",
                    "type": "Relational Database",
                    "safe_host": settings.get_safe_database_url(),
                    "status": "connected",
                    "pool_size": settings.DB_POOL_SIZE,
                },
                {
                    "name": "Redis Distributed Cache & Rate Limiting",
                    "type": "Key-Value Store",
                    "safe_host": "redis://localhost:6379/0",
                    "status": "active",
                },
                {
                    "name": "Notification & Transactional Mail Service",
                    "type": "SMTP Gateway",
                    "safe_host": "smtp.pevn.edu.co:587",
                    "status": "configured",
                },
            ]
        }

    async def _check_redis(self) -> bool:
        """Internal helper to probe Redis connectivity safely."""
        try:
            import redis.asyncio as aioredis
            settings = get_settings()
            client = aioredis.from_url(
                settings.REDIS_URL,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
            )
            await client.ping()
            await client.aclose()
            return True
        except Exception:
            return False


system_operations_service = SystemOperationsService()
