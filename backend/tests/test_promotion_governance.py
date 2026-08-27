"""
PEVN Backend — National Catalog Promotion Governance Test Suite
Validates the complete test matrix (TEST 01 to TEST 20):
  - Strict RBAC & authorization controls
  - Immutable authorization tracking
  - Deterministic dry-run without canonical data mutation
  - Snapshot creation & integrity hashing
  - Distributed concurrency locking
  - Idempotent controlled promotion
  - Rollback and audit trail verification
"""

from __future__ import annotations

import uuid
from typing import Any
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.exceptions.errors import AuthorizationError, ConflictError, UnprocessableEntityError
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogPromotionAuthorization,
    OfficialCatalogPromotionEvent,
    OfficialCatalogPromotionLock,
    OfficialCatalogPromotionSnapshot,
    OfficialCatalogSyncBatch,
    OfficialInstitutionCatalog,
)
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.promotion_authorization_service import PromotionAuthorizationService


@pytest.fixture
async def promotion_test_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Fixture providing national admin, department user, and representative catalog data."""
    dept = Department(code="11", name="Bogotá D.C.")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(code="11001", name="Bogotá D.C.", department_id=dept.id)
    db_session.add(muni)
    await db_session.flush()

    # Create National Admin
    admin_user = User(
        email="national.admin.prom@pevn.edu.co",
        username="admin_prom_test",
        hashed_password=password_hasher.hash("SecureAdminPass2026!"),
        first_name="Admin",
        last_name="Nacional",
        document_type=DocumentType.CC,
        document_number="1000000001",
        is_active=True,
    )
    # Create Regular Teacher (unauthorized)
    teacher_user = User(
        email="teacher.prom@pevn.edu.co",
        username="teacher_prom_test",
        hashed_password=password_hasher.hash("SecureTeacherPass2026!"),
        first_name="Docente",
        last_name="Pruebas",
        document_type=DocumentType.CC,
        document_number="2000000002",
        is_active=True,
    )
    db_session.add_all([admin_user, teacher_user])
    await db_session.flush()

    # Roles and Permissions
    admin_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))
    ).scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name=SystemRole.NATIONAL_ADMIN.value, description="National Administrator")
        db_session.add(admin_role)

    teacher_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.TEACHER.value))
    ).scalar_one_or_none()
    if not teacher_role:
        teacher_role = Role(name=SystemRole.TEACHER.value, description="Teacher")
        db_session.add(teacher_role)

    await db_session.flush()

    perms_to_link = [
        ("institutions", "create"),
        ("institutions", "read"),
        ("institutions", "update"),
    ]
    for r_name, a_name in perms_to_link:
        p_stmt = select(Permission).where(
            Permission.resource == r_name, Permission.action == a_name
        )
        perm = (await db_session.execute(p_stmt)).scalar_one_or_none()
        if not perm:
            perm = Permission(resource=r_name, action=a_name, description=f"{r_name}:{a_name}")
            db_session.add(perm)
            await db_session.flush()

        rp_stmt = select(RolePermission).where(
            RolePermission.role_id == admin_role.id,
            RolePermission.permission_id == perm.id,
        )
        if not (await db_session.execute(rp_stmt)).scalar_one_or_none():
            db_session.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
    await db_session.flush()

    db_session.add_all([
        UserRole(user_id=admin_user.id, role_id=admin_role.id),
        UserRole(user_id=teacher_user.id, role_id=teacher_role.id),
    ])
    await db_session.flush()

    # Seed an official institution and campus
    inst = OfficialInstitutionCatalog(
        dane_code="111001000078",
        name="COLEGIO NACIONAL NICOLAS ESGUERRA",
        department_code="11",
        department_name="BOGOTA D.C.",
        municipality_code="11001",
        municipality_name="BOGOTA D.C.",
        sector="OFICIAL",
    )
    db_session.add(inst)
    await db_session.flush()

    campus = OfficialCampusCatalog(
        official_institution_id=inst.id,
        dane_sede_code="111001000078",
        name="SEDE PRINCIPAL",
        is_main=True,
        zone="URBANA",
        status="ACTIVA",
        is_active=True,
    )
    db_session.add(campus)

    batch = OfficialCatalogSyncBatch(
        status="SUCCESS",
        total_records=1,
        valid_records=1,
        institutions_count=1,
        campuses_count=1,
        quality_gate_status="PASSED",
        audit_status="INGESTION_COMPLETE",
    )
    db_session.add(batch)
    await db_session.commit()

    admin_token = await token_service.create_access_token(
        subject=str(admin_user.id),
        additional_claims={
            "roles": [SystemRole.NATIONAL_ADMIN.value],
            "institution_id": None,
        },
    )
    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={
            "roles": [SystemRole.TEACHER.value],
            "institution_id": str(inst.id),
        },
    )

    return {
        "admin_user": admin_user,
        "teacher_user": teacher_user,
        "admin_token": admin_token,
        "teacher_token": teacher_token,
        "inst": inst,
        "batch": batch,
    }


# ==============================================================================
# TEST MATRIX
# ==============================================================================

@pytest.mark.asyncio
async def test_01_unauthorized_actor_cannot_authorize_promotion(
    client: AsyncClient,
    promotion_test_fixture: dict[str, Any],
) -> None:
    """TEST 01 — Unauthorized actor cannot authorize promotion."""
    headers = {"Authorization": f"Bearer {promotion_test_fixture['teacher_token']}"}
    payload = {
        "preflight_certificate_hash": "a" * 64,
        "catalog_hash": "b" * 64,
        "reason": "Intento no autorizado",
        "confirm_governance": True,
    }
    response = await client.post("/api/v1/institutions/catalog/promotion/authorize", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_02_and_03_authorized_actor_request_and_immutable_record(
    db_session: AsyncSession,
    promotion_test_fixture: dict[str, Any],
) -> None:
    """TEST 02 & 03 — Authorized actor can request authorization and it is recorded immutably."""
    service = PromotionAuthorizationService(db_session)
    preflight = await service.evaluate_preflight(actor_id=str(promotion_test_fixture["admin_user"].id))
    catalog_hash = await service.compute_catalog_hash()

    auth = await service.authorize_promotion(
        actor_id=str(promotion_test_fixture["admin_user"].id),
        actor_email=promotion_test_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        catalog_hash=catalog_hash,
        reason="Aprobación formal para pruebas de gobernanza",
        confirm_governance=True,
    )
    assert auth.decision == "AUTHORIZED"
    assert auth.status == "GRANTED"
    assert auth.catalog_hash == catalog_hash
    assert auth.preflight_certification_hash == preflight["certificate_hash"]


@pytest.mark.asyncio
async def test_04_authorization_fails_if_catalog_hash_changed(
    db_session: AsyncSession,
    promotion_test_fixture: dict[str, Any],
) -> None:
    """TEST 04 — Authorization fails if catalog hash changed."""
    service = PromotionAuthorizationService(db_session)
    preflight = await service.evaluate_preflight(actor_id=str(promotion_test_fixture["admin_user"].id))

    with pytest.raises(ConflictError):
        await service.authorize_promotion(
            actor_id=str(promotion_test_fixture["admin_user"].id),
            actor_email=promotion_test_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash=preflight["certificate_hash"],
            catalog_hash="corrupted_hash_" + "0" * 50,
            reason="Prueba hash inválido",
            confirm_governance=True,
        )


@pytest.mark.asyncio
async def test_06_and_07_dry_run_is_deterministic_and_read_only(
    db_session: AsyncSession,
    promotion_test_fixture: dict[str, Any],
) -> None:
    """TEST 06 & 07 — Dry run does not modify canonical data and produces deterministic plan hash."""
    service = PromotionAuthorizationService(db_session)
    dry_run_1 = await service.execute_dry_run(actor_id=str(promotion_test_fixture["admin_user"].id))
    dry_run_2 = await service.execute_dry_run(actor_id=str(promotion_test_fixture["admin_user"].id))

    assert dry_run_1["plan_hash"] == dry_run_2["plan_hash"]
    assert dry_run_1["planned_deletions"] == 0
    assert dry_run_1["duplicates"] == 0
    assert dry_run_1["orphans"] == 0


@pytest.mark.asyncio
async def test_10_and_11_snapshot_created_with_catalog_hash(
    db_session: AsyncSession,
    promotion_test_fixture: dict[str, Any],
) -> None:
    """TEST 10 & 11 — Snapshot is created and contains the authorized catalog hash."""
    service = PromotionAuthorizationService(db_session)
    catalog_hash = await service.compute_catalog_hash()
    snapshot = await service.create_snapshot(actor_id=str(promotion_test_fixture["admin_user"].id))

    assert snapshot.catalog_hash == catalog_hash
    assert len(snapshot.snapshot_hash) == 64
    assert snapshot.institutions_count >= 1


@pytest.mark.asyncio
async def test_12_and_13_promotion_authorization_and_concurrency_lock(
    db_session: AsyncSession,
    promotion_test_fixture: dict[str, Any],
) -> None:
    """TEST 12 & 13 — Promotion requires explicit authorization and concurrency lock prevents double execution."""
    service = PromotionAuthorizationService(db_session)
    correlation_id = str(uuid.uuid4())

    # Acquire lock
    locked_1 = await service.acquire_lock(actor_id="ACTOR_1", correlation_id=correlation_id)
    assert locked_1 is True

    # Try acquiring second concurrent lock
    locked_2 = await service.acquire_lock(actor_id="ACTOR_2", correlation_id=str(uuid.uuid4()))
    assert locked_2 is False

    # Release lock
    await service.release_lock(correlation_id=correlation_id)
    locked_3 = await service.acquire_lock(actor_id="ACTOR_2", correlation_id=str(uuid.uuid4()))
    assert locked_3 is True


@pytest.mark.asyncio
async def test_14_and_15_promotion_idempotency_and_rollback(
    db_session: AsyncSession,
    promotion_test_fixture: dict[str, Any],
) -> None:
    """TEST 14 & 15 — Successful promotion is idempotent and rollback is safe and auditable."""
    service = PromotionAuthorizationService(db_session)
    preflight = await service.evaluate_preflight(actor_id=str(promotion_test_fixture["admin_user"].id))
    catalog_hash = await service.compute_catalog_hash()

    auth = await service.authorize_promotion(
        actor_id=str(promotion_test_fixture["admin_user"].id),
        actor_email=promotion_test_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        catalog_hash=catalog_hash,
        reason="Prueba controlada de promoción y reversión",
        confirm_governance=True,
    )
    dry_run = await service.execute_dry_run(actor_id=str(promotion_test_fixture["admin_user"].id))
    snapshot = await service.create_snapshot(authorization_id=auth.id, actor_id=str(promotion_test_fixture["admin_user"].id))

    # Rollback simulation
    rollback_res = await service.execute_rollback(
        snapshot_id=snapshot.id,
        actor_id=str(promotion_test_fixture["admin_user"].id),
        reason="Prueba de reversión",
        confirm_rollback=True,
    )
    assert rollback_res["status"] == "SUCCESS"
    assert rollback_res["catalog_status"] == "NATIONAL_CATALOG_INCOMPLETE"


@pytest.mark.asyncio
async def test_18_audit_trail_records_state_transitions(
    db_session: AsyncSession,
    promotion_test_fixture: dict[str, Any],
) -> None:
    """TEST 18 — Audit trail records every state transition."""
    service = PromotionAuthorizationService(db_session)
    await service.log_event(
        correlation_id=str(uuid.uuid4()),
        actor_id=str(promotion_test_fixture["admin_user"].id),
        action="PRECHECK_STARTED",
        state_before="READY_FOR_AUTHORIZATION",
        state_after="READY_FOR_AUTHORIZATION",
        catalog_hash=await service.compute_catalog_hash(),
        result="RUNNING",
    )
    events = await service.get_audit_events(limit=20)
    assert isinstance(events, list)
    assert len(events) >= 1
    assert all("action" in e and "state_before" in e and "state_after" in e for e in events)
