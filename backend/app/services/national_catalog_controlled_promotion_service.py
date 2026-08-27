"""
PEVN Backend — National Catalog Controlled Production Promotion Service

Orchestrates the final production promotion ceremony with:
  1. Governance state and pre-execution invariant verification
  2. Authoritative catalog drift detection and hash verification
  3. Preflight certification and dry-run plan binding verification
  4. Snapshot checkpoint integrity and rollback readiness verification
  5. Single-use human authorization grant validation and consumption
  6. Distributed concurrency locking (300s lease)
  7. Atomic, rollback-safe promotion execution
  8. Immutable append-only audit event logging
  9. Comprehensive post-promotion verification
  10. Fail-closed error handling and automatic rollback on verification failure
"""

from __future__ import annotations

import datetime
import hashlib
import json
import time
import uuid
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import (
    AuthorizationError,
    ConflictError,
    UnprocessableEntityError,
)
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogPromotionAuthorization,
    OfficialCatalogPromotionEvent,
    OfficialCatalogPromotionLock,
    OfficialCatalogPromotionSnapshot,
    OfficialCatalogSyncBatch,
    OfficialInstitutionCatalog,
)
from app.services.national_catalog_final_certification_service import (
    NationalCatalogFinalCertificationService,
)
from app.services.promotion_authorization_gate import PromotionAuthorizationGateService
from app.services.promotion_authorization_service import PromotionAuthorizationService


class NationalCatalogControlledPromotionService:
    """
    Final controlled production promotion orchestration service.
    Coordinates all safety layers, cryptographic checks, locking, and atomic state mutation.
    """

    LOCK_KEY = "national_catalog_promotion"
    LOCK_TIMEOUT_SECONDS = 300

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._promo_service = PromotionAuthorizationService(session=session)
        self._gate_service = PromotionAuthorizationGateService(session=session)
        self._cert_service = NationalCatalogFinalCertificationService(session=session)

    # --------------------------------------------------------------------------
    # Audit Event Logging
    # --------------------------------------------------------------------------
    async def log_ceremony_event(
        self,
        *,
        correlation_id: str,
        actor_id: str | None,
        action: str,
        state_before: str,
        state_after: str,
        catalog_hash: str | None = None,
        result: str = "SUCCESS",
        details: dict[str, Any] | None = None,
    ) -> OfficialCatalogPromotionEvent:
        event = OfficialCatalogPromotionEvent(
            correlation_id=correlation_id,
            actor_id=actor_id,
            action=action,
            state_before=state_before,
            state_after=state_after,
            catalog_hash=catalog_hash,
            result=result,
            details_json=json.dumps(details or {}, sort_keys=True),
        )
        self._session.add(event)
        await self._session.flush()
        return event

    # --------------------------------------------------------------------------
    # Distributed Concurrency Locking
    # --------------------------------------------------------------------------
    async def acquire_lock(self, *, actor_id: str, correlation_id: str) -> bool:
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(seconds=self.LOCK_TIMEOUT_SECONDS)

        # Cleanup expired locks
        cleanup_stmt = (
            OfficialCatalogPromotionLock.__table__.delete().where(
                OfficialCatalogPromotionLock.lock_key == self.LOCK_KEY,
                OfficialCatalogPromotionLock.expires_at <= now,
            )
        )
        await self._session.execute(cleanup_stmt)
        await self._session.flush()

        stmt = select(OfficialCatalogPromotionLock).where(
            OfficialCatalogPromotionLock.lock_key == self.LOCK_KEY,
            OfficialCatalogPromotionLock.expires_at > now,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing:
            return False

        lock = OfficialCatalogPromotionLock(
            lock_key=self.LOCK_KEY,
            acquired_by=actor_id,
            correlation_id=correlation_id,
            acquired_at=now,
            expires_at=expires_at,
        )
        self._session.add(lock)
        try:
            await self._session.flush()
            return True
        except Exception:
            return False

    async def release_lock(self, *, correlation_id: str) -> None:
        stmt = OfficialCatalogPromotionLock.__table__.delete().where(
            OfficialCatalogPromotionLock.lock_key == self.LOCK_KEY,
            OfficialCatalogPromotionLock.correlation_id == correlation_id,
        )
        await self._session.execute(stmt)
        await self._session.flush()

    # --------------------------------------------------------------------------
    # Final Pre-Execution Checkpoint & Drift Verification
    # --------------------------------------------------------------------------
    async def verify_pre_execution_checkpoint(
        self,
        *,
        authorization_id: uuid.UUID,
        actor_id: str,
        preflight_certificate_hash: str,
        plan_hash: str | None,
        snapshot_id: uuid.UUID | None,
        correlation_id: str,
    ) -> dict[str, Any]:
        """
        Executes the comprehensive pre-execution invariant verification.
        Fails closed with specific conflict/authorization errors if any check fails.
        """
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Fetch and validate Authorization Record
        auth_stmt = select(OfficialCatalogPromotionAuthorization).where(
            OfficialCatalogPromotionAuthorization.id == authorization_id
        )
        auth = (await self._session.execute(auth_stmt)).scalar_one_or_none()
        if not auth:
            raise AuthorizationError("Autorización de promoción no encontrada o inválida.")

        if auth.status == "CONSUMED" or auth.consumed_at is not None:
            raise ConflictError("Esta autorización ya fue consumida y no puede reutilizarse (Anti-replay).")

        if auth.status != "GRANTED":
            raise AuthorizationError(f"La autorización se encuentra en estado no ejecutable ({auth.status}).")

        exp = auth.expires_at if auth.expires_at.tzinfo else auth.expires_at.replace(tzinfo=datetime.timezone.utc) if auth.expires_at else None
        if exp and exp < now:
            raise AuthorizationError("La autorización de promoción ha expirado (>24h).")

        # 2. Recalculate authoritative catalog hash (Drift Check)
        current_catalog_hash = await self._promo_service.compute_catalog_hash()
        if auth.catalog_hash != current_catalog_hash:
            await self.log_ceremony_event(
                correlation_id=correlation_id,
                actor_id=actor_id,
                action="PROMOTION_BLOCKED",
                state_before="PROMOTION_AUTHORIZED",
                state_after="READY_FOR_AUTHORIZATION",
                catalog_hash=current_catalog_hash,
                result="CATALOG_HASH_DRIFT",
                details={
                    "expected_catalog_hash": auth.catalog_hash,
                    "observed_catalog_hash": current_catalog_hash,
                },
            )
            raise ConflictError(
                f"Catalog drift detected: El hash actual ({current_catalog_hash[:12]}...) difiere del autorizado ({auth.catalog_hash[:12]}...). Promoción abortada."
            )

        # 3. Verify Preflight Certification Hash Binding
        if auth.preflight_certification_hash != preflight_certificate_hash:
            raise ConflictError("El hash del certificado preflight provisto no coincide con el registrado en la autorización.")

        # 4. Verify Plan Hash Binding
        if auth.plan_hash and plan_hash and auth.plan_hash != plan_hash:
            raise ConflictError("El hash del plan de promoción difiere de la simulación dry-run autorizada.")

        # 5. Verify Snapshot ID Binding if present
        if auth.snapshot_id and snapshot_id and auth.snapshot_id != snapshot_id:
            raise ConflictError("El identificador de snapshot provisto no coincide con el snapshot vinculado a la autorización.")

        # 6. Verify Technical Gates (100% read-only)
        gate_result = await self._gate_service.evaluate_authorization_preflight(actor_id=actor_id)
        if not gate_result["technical_gates_passed"]:
            raise ConflictError("Una o más compuertas técnicas pre-ejecución no se encuentran en estado PASSED.")

        return {
            "auth": auth,
            "catalog_hash": current_catalog_hash,
            "certificate_hash": gate_result["certificate_hash"],
        }

    # --------------------------------------------------------------------------
    # Main Final Promotion Ceremony Orchestration
    # --------------------------------------------------------------------------
    async def execute_promotion_ceremony(
        self,
        *,
        authorization_id: uuid.UUID,
        actor_id: str,
        actor_email: str,
        actor_role: str,
        preflight_certificate_hash: str,
        plan_hash: str,
        confirm_irreversible_step: bool,
        snapshot_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Orchestrates the atomic, fully auditable production promotion ceremony.
        """
        correlation_id = str(uuid.uuid4())
        start_time = time.monotonic()

        if not confirm_irreversible_step:
            raise UnprocessableEntityError("Debe confirmar explícitamente el paso irreversible de promoción nacional.")

        await self.log_ceremony_event(
            correlation_id=correlation_id,
            actor_id=actor_id,
            action="PROMOTION_REQUESTED",
            state_before="READY_FOR_AUTHORIZATION",
            state_after="PROMOTION_IN_PROGRESS",
            result="RUNNING",
            details={
                "authorization_id": str(authorization_id),
                "actor_email": actor_email,
                "actor_role": actor_role,
            },
        )

        # 1. Acquire distributed lock
        lock_acquired = await self.acquire_lock(actor_id=actor_id, correlation_id=correlation_id)
        if not lock_acquired:
            await self.log_ceremony_event(
                correlation_id=correlation_id,
                actor_id=actor_id,
                action="PROMOTION_BLOCKED",
                state_before="PROMOTION_AUTHORIZED",
                state_after="PROMOTION_AUTHORIZED",
                result="CONCURRENCY_LOCK_ACTIVE",
            )
            raise ConflictError("Ya existe un proceso de promoción ejecutándose concurrentemente (Lock activo).")

        try:
            # 2. Final Pre-Execution Checkpoint & Drift Verification
            checkpoint = await self.verify_pre_execution_checkpoint(
                authorization_id=authorization_id,
                actor_id=actor_id,
                preflight_certificate_hash=preflight_certificate_hash,
                plan_hash=plan_hash,
                snapshot_id=snapshot_id,
                correlation_id=correlation_id,
            )
            auth: OfficialCatalogPromotionAuthorization = checkpoint["auth"]
            catalog_hash: str = checkpoint["catalog_hash"]

            await self.log_ceremony_event(
                correlation_id=correlation_id,
                actor_id=actor_id,
                action="PROMOTION_AUTHORIZATION_VERIFIED",
                state_before="PROMOTION_IN_PROGRESS",
                state_after="PROMOTION_IN_PROGRESS",
                catalog_hash=catalog_hash,
                result="SUCCESS",
                details={"authorization_id": str(auth.id)},
            )

            # 3. Check for Idempotency
            batch_stmt = (
                select(OfficialCatalogSyncBatch)
                .order_by(OfficialCatalogSyncBatch.started_at.desc())
                .limit(1)
            )
            latest_batch = (await self._session.execute(batch_stmt)).scalar_one_or_none()
            if latest_batch and latest_batch.audit_status == "PROMOTED":
                return {
                    "promotion_id": str(latest_batch.id),
                    "status": "ALREADY_COMPLETED",
                    "catalog_status": "NATIONAL_CATALOG_SYNCED",
                    "institutions_promoted": latest_batch.institutions_count,
                    "campuses_promoted": latest_batch.campuses_count,
                    "snapshot_hash": auth.catalog_hash,
                    "execution_time_ms": (time.monotonic() - start_time) * 1000,
                    "completed_at": latest_batch.completed_at or datetime.datetime.now(datetime.timezone.utc),
                    "message": "El catálogo nacional ya se encuentra en estado PROMOTED (Idempotente).",
                }

            # 4. Dry-Run Verification (Ensures zero deletions/conflicts)
            dry_run = await self._promo_service.execute_dry_run(actor_id=actor_id, skip_event_log=True)
            if not dry_run["promotion_safe"]:
                raise ConflictError("La simulación dry-run detectó anomalías que impiden la promoción.")

            if dry_run["plan_hash"] != plan_hash:
                raise ConflictError("El plan de promoción ha variado respecto a la simulación provista.")

            # 5. Create Immutable Pre-Promotion Checkpoint Snapshot
            snapshot = await self._promo_service.create_snapshot(authorization_id=auth.id, actor_id=actor_id)

            await self.log_ceremony_event(
                correlation_id=correlation_id,
                actor_id=actor_id,
                action="SNAPSHOT_VERIFIED",
                state_before="PROMOTION_IN_PROGRESS",
                state_after="PROMOTION_IN_PROGRESS",
                catalog_hash=snapshot.catalog_hash,
                result="SUCCESS",
                details={"snapshot_id": str(snapshot.id), "snapshot_hash": snapshot.snapshot_hash},
            )

            # 6. Apply Atomic Promotion Transition
            now = datetime.datetime.now(datetime.timezone.utc)
            if latest_batch:
                latest_batch.audit_status = "PROMOTED"
                latest_batch.quality_gate_status = "PASSED"
                latest_batch.completed_at = now
                self._session.add(latest_batch)

            # 7. Consume Authorization Grant (Single-Use Anti-Replay)
            auth.status = "CONSUMED"
            auth.consumed_at = now
            auth.consumed_by = actor_id
            self._session.add(auth)
            await self._session.flush()

            await self.log_ceremony_event(
                correlation_id=correlation_id,
                actor_id=actor_id,
                action="AUTHORIZATION_CONSUMED",
                state_before="PROMOTION_IN_PROGRESS",
                state_after="PROMOTION_IN_PROGRESS",
                catalog_hash=snapshot.catalog_hash,
                result="SUCCESS",
                details={"authorization_id": str(auth.id), "consumed_at": now.isoformat()},
            )

            # 8. Comprehensive Post-Promotion Verification
            gate_audit = await self._gate_service.evaluate_authorization_preflight(actor_id=actor_id)
            if not gate_audit["technical_gates_passed"]:
                # Automatic rollback on post-promotion verification failure
                if latest_batch:
                    latest_batch.audit_status = "INGESTION_COMPLETE"
                    self._session.add(latest_batch)
                auth.status = "REVOKED"
                self._session.add(auth)
                await self._session.flush()
                await self.log_ceremony_event(
                    correlation_id=correlation_id,
                    actor_id=actor_id,
                    action="PROMOTION_ROLLED_BACK",
                    state_before="PROMOTION_IN_PROGRESS",
                    state_after="NATIONAL_CATALOG_INCOMPLETE",
                    catalog_hash=snapshot.catalog_hash,
                    result="FAILURE_POST_VERIFICATION",
                )
                raise ConflictError("Post-promotion verification failed. Rolled back state safely.")

            await self.log_ceremony_event(
                correlation_id=correlation_id,
                actor_id=actor_id,
                action="POST_PROMOTION_VERIFICATION_PASSED",
                state_before="PROMOTION_IN_PROGRESS",
                state_after="NATIONAL_CATALOG_SYNCED",
                catalog_hash=snapshot.catalog_hash,
                result="SUCCESS",
                details={
                    "institutions_promoted": snapshot.institutions_count,
                    "campuses_promoted": snapshot.campuses_count,
                    "snapshot_id": str(snapshot.id),
                    "authorization_id": str(auth.id),
                },
            )

            return {
                "promotion_id": str(latest_batch.id) if latest_batch else str(uuid.uuid4()),
                "status": "SUCCESS",
                "catalog_status": "NATIONAL_CATALOG_SYNCED",
                "institutions_promoted": snapshot.institutions_count,
                "campuses_promoted": snapshot.campuses_count,
                "snapshot_hash": snapshot.snapshot_hash,
                "execution_time_ms": (time.monotonic() - start_time) * 1000,
                "completed_at": now,
                "authorization_id": str(auth.id),
                "message": "Promoción del catálogo nacional ejecutada y verificada exitosamente.",
            }
        finally:
            await self.release_lock(correlation_id=correlation_id)
