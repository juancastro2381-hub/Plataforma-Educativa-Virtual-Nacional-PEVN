"""
PEVN Backend — Persistent Database Audit Service

Implements IAuditService with direct append-only persistence to PostgreSQL audit_logs.

SECURITY:
  - All metadata is strictly sanitized before database insert
  - Passwords, tokens, API keys, and authorization headers are permanently stripped
  - Table is append-only for the application user (no UPDATE or DELETE privileges)
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEvent, IAuditService
from app.core.logging import get_logger
from app.db.session import get_session_factory
from app.models.audit_log import AuditLog

_logger = get_logger(__name__)

# Keys that must be stripped or redacted from audit metadata
_SENSITIVE_AUDIT_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "plain_password",
        "new_password",
        "old_password",
        "current_password",
        "password_confirm",
        "token",
        "access_token",
        "refresh_token",
        "raw_token",
        "secret",
        "secret_key",
        "api_key",
        "authorization",
        "cookie",
        "cookies",
    }
)


def sanitize_audit_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively sanitize metadata dictionary to remove credentials and secrets.

    Args:
        metadata: Raw metadata dictionary from event trigger.

    Returns:
        Sanitized metadata safe for long-term audit storage.
    """
    if not isinstance(metadata, dict):
        return {}

    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        key_lower = str(key).lower()
        if key_lower in _SENSITIVE_AUDIT_KEYS or any(
            secret_word in key_lower for secret_word in ("password", "secret", "token")
        ):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_audit_metadata(value)
        elif isinstance(value, (list, tuple, set)):
            sanitized[key] = [
                sanitize_audit_metadata(v) if isinstance(v, dict) else str(v)
                for v in value
            ]
        elif isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key] = value
        else:
            sanitized[key] = str(value)

    return sanitized


class DatabaseAuditService(IAuditService):
    """
    Persistent audit service writing to the PostgreSQL audit_logs table.
    """

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session

    async def record(
        self,
        event: AuditEvent,
        session: AsyncSession | None = None,
    ) -> None:
        """
        Persist a single audit event record to PostgreSQL.

        Args:
            event: AuditEvent instance.
            session: Optional active AsyncSession to participate in current transaction.
        """
        sanitized_metadata = sanitize_audit_metadata(event.metadata)

        # Parse UUIDs safely
        actor_uuid = None
        if event.actor_id:
            try:
                actor_uuid = uuid.UUID(str(event.actor_id))
            except (ValueError, TypeError):
                actor_uuid = None

        institution_uuid = None
        if event.institution_id:
            try:
                institution_uuid = uuid.UUID(str(event.institution_id))
            except (ValueError, TypeError):
                institution_uuid = None

        audit_entry = AuditLog(
            event_type=str(event.event_type),
            actor_id=actor_uuid,
            actor_ip=event.actor_ip or "0.0.0.0",  # noqa: S104
            actor_user_agent=(
                event.metadata.get("user_agent")
                if isinstance(event.metadata, dict)
                else None
            ),
            target_id=str(event.target_id) if event.target_id is not None else None,
            target_type=event.target_type,
            institution_id=institution_uuid,
            correlation_id=event.correlation_id,
            success=event.success,
            metadata_json=sanitized_metadata,
            occurred_at=event.occurred_at,
        )

        target_session = session or self._session
        if target_session:
            target_session.add(audit_entry)
            return

        # Independent session execution if no active transaction session passed
        try:
            session_maker = get_session_factory()
            async with session_maker() as db:
                db.add(audit_entry)
                await db.commit()
        except Exception as exc:
            _logger.error(
                "CRITICAL: Failed to persist audit event to database",
                event_type=event.event_type,
                actor_id=event.actor_id,
                error=str(exc),
            )

    async def record_many(
        self,
        events: list[AuditEvent],
        session: Any | None = None,
    ) -> None:
        """Persist a batch of audit events."""
        for event in events:
            await self.record(event, session=session)


# Default audit service instance
audit_service: IAuditService = DatabaseAuditService()
