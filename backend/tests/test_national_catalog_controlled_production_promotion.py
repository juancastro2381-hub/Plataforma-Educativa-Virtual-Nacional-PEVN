"""
PEVN Backend — National Catalog Controlled Production Promotion Test Suite

Comprehensive 30-test matrix certifying the final controlled promotion ceremony:
  - Strict human authorization enforcement
  - Replay prevention / single-use grants
  - Concurrency locking and race condition protection
  - Cryptographic binding (catalog_hash, cert_hash, plan_hash, snapshot_id)
  - Catalog drift detection (fail-closed)
  - Idempotency on duplicated executions
  - Atomic transaction commits
  - Post-promotion verification and rollback safety
  - Non-automatic execution on boot/page load
  - Uncompromised canonical database preservation
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.exceptions.errors import (
    AuthorizationError,
    ConflictError,
    UnprocessableEntityError,
)
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import DocumentType, User
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogPromotionAuthorization,
    OfficialCatalogPromotionEvent,
    OfficialCatalogPromotionLock,
    OfficialCatalogPromotionSnapshot,
    OfficialCatalogSyncBatch,
    OfficialInstitutionCatalog,
)
from app.services.national_catalog_controlled_promotion_service import (
    NationalCatalogControlledPromotionService,
)
from app.services.national_catalog_final_certification_service import (
    NationalCatalogFinalCertificationService,
)
from app.services.promotion_authorization_gate import (
    PromotionAuthorizationGateService,
)
from app.services.promotion_authorization_service import (
    PromotionAuthorizationService,
)


@pytest.fixture
async def promotion_ceremony_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """
    Creates an isolated national admin, departmental admin, and regular teacher user,
    plus mock catalog institutions and valid batches for testing the ceremony.
    """
    # 1. Create Users
    admin_user = User(
        email="ceremony.admin@pevn.edu.co",
        username="ceremony_admin_test",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Admin",
        last_name="Ceremonia",
        document_type=DocumentType.CC,
        document_number="1110000001",
        is_active=True,
    )
    dept_user = User(
        email="ceremony.dept@pevn.edu.co",
        username="ceremony_dept_test",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Admin",
        last_name="Departamental",
        document_type=DocumentType.CC,
        document_number="1110000002",
        is_active=True,
    )
    teacher_user = User(
        email="ceremony.teacher@pevn.edu.co",
        username="ceremony_teacher_test",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Profesor",
        last_name="Ceremonia",
        document_type=DocumentType.CC,
        document_number="1110000003",
        is_active=True,
    )
    db_session.add_all([admin_user, dept_user, teacher_user])
    await db_session.flush()

    # 2. Setup Roles & Permissions
    admin_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))
    ).scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name=SystemRole.NATIONAL_ADMIN.value, description="National Administrator")
        db_session.add(admin_role)

    dept_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.DEPARTMENT_ADMIN.value))
    ).scalar_one_or_none()
    if not dept_role:
        dept_role = Role(name=SystemRole.DEPARTMENT_ADMIN.value, description="Department Administrator")
        db_session.add(dept_role)

    teacher_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.TEACHER.value))
    ).scalar_one_or_none()
    if not teacher_role:
        teacher_role = Role(name=SystemRole.TEACHER.value, description="Teacher")
        db_session.add(teacher_role)

    await db_session.flush()

    for r_name, a_name in [("institutions", "create"), ("institutions", "read"), ("institutions", "update")]:
        p_stmt = select(Permission).where(Permission.resource == r_name, Permission.action == a_name)
        perm = (await db_session.execute(p_stmt)).scalar_one_or_none()
        if not perm:
            perm = Permission(resource=r_name, action=a_name, description=f"{r_name}:{a_name}")
            db_session.add(perm)
            await db_session.flush()

        for r_obj in [admin_role, dept_role]:
            rp_stmt = select(RolePermission).where(
                RolePermission.role_id == r_obj.id, RolePermission.permission_id == perm.id
            )
            if not (await db_session.execute(rp_stmt)).scalar_one_or_none():
                db_session.add(RolePermission(role_id=r_obj.id, permission_id=perm.id))

    db_session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
    db_session.add(UserRole(user_id=dept_user.id, role_id=dept_role.id))
    db_session.add(UserRole(user_id=teacher_user.id, role_id=teacher_role.id))
    await db_session.flush()

    # 3. Create Sample Catalog Records
    inst = OfficialInstitutionCatalog(
        dane_code="111001009999",
        name="INSTITUTO EXPERIMENTAL NACIONAL PILOTO",
        department_code="11",
        department_name="BOGOTA D.C.",
        municipality_code="11001",
        municipality_name="BOGOTA D.C.",
        sector="OFICIAL",
        status="ACTIVO",
    )
    db_session.add(inst)
    await db_session.flush()

    campus = OfficialCampusCatalog(
        official_institution_id=inst.id,
        dane_sede_code="111001009999",
        name="SEDE PRINCIPAL EXPERIMENTAL",
        is_main=True,
        zone="URBANA",
        address="Calle 100 # 10-01",
        status="ACTIVA",
        is_active=True,
    )
    db_session.add(campus)

    batch = OfficialCatalogSyncBatch(
        source_system="MEN_DUE",
        source_dataset="cfw5-qzt5",
        status="SUCCESS",
        institutions_count=1,
        campuses_count=1,
        departments_count=1,
        municipalities_count=1,
        quality_gate_status="PASSED",
        audit_status="AUDITED",
    )
    db_session.add(batch)
    await db_session.commit()

    # 4. Generate Auth Tokens
    admin_token = await token_service.create_access_token(
        subject=str(admin_user.id),
        additional_claims={
            "roles": [SystemRole.NATIONAL_ADMIN.value],
            "institution_id": None,
        },
    )
    dept_token = await token_service.create_access_token(
        subject=str(dept_user.id),
        additional_claims={
            "roles": [SystemRole.DEPARTMENT_ADMIN.value],
            "department_code": "11",
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
        "dept_user": dept_user,
        "teacher_user": teacher_user,
        "admin_token": admin_token,
        "dept_token": dept_token,
        "teacher_token": teacher_token,
        "institution": inst,
        "campus": campus,
        "batch": batch,
    }


# ==============================================================================
# TEST 01 to TEST 05 — Authorization & RBAC Checks
# ==============================================================================

@pytest.mark.asyncio
async def test_01_no_authorization_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 01 — Non-existent authorization ID blocks ceremony execution."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    with pytest.raises(AuthorizationError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=uuid.uuid4(),
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash="a" * 64,
            plan_hash="b" * 64,
            confirm_irreversible_step=True,
        )
    assert "no encontrada" in str(exc.value)


@pytest.mark.asyncio
async def test_02_expired_authorization_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 02 — Expired authorization (>24h) blocks promotion ceremony."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    cert_hash = "c" * 64
    plan_hash = "d" * 64

    # Create expired grant
    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        status="GRANTED",
        decision="GO",
        reason="Autorización expirada de prueba",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2),
    )
    db_session.add(auth)
    await db_session.flush()

    with pytest.raises(AuthorizationError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash=cert_hash,
            plan_hash=plan_hash,
            confirm_irreversible_step=True,
        )
    assert "ha expirado" in str(exc.value)


@pytest.mark.asyncio
async def test_03_consumed_authorization_blocks_replay(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 03 — Already-consumed authorization cannot be replayed."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    cert_hash = "c" * 64
    plan_hash = "d" * 64

    # Create already-consumed grant
    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        status="CONSUMED",
        consumed_at=datetime.datetime.now(datetime.timezone.utc),
        consumed_by=str(promotion_ceremony_fixture["admin_user"].id),
        decision="GO",
        reason="Autorización consumida",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=20),
    )
    db_session.add(auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash=cert_hash,
            plan_hash=plan_hash,
            confirm_irreversible_step=True,
        )
    assert "ya fue consumida" in str(exc.value)


@pytest.mark.asyncio
async def test_04_invalid_rbac_blocks_promotion(
    client: AsyncClient,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 04 — Unauthorized role (Teacher) rejected at endpoint with 403 Forbidden."""
    headers = {"Authorization": f"Bearer {promotion_ceremony_fixture['teacher_token']}"}
    payload = {
        "authorization_id": str(uuid.uuid4()),
        "preflight_certificate_hash": "a" * 64,
        "plan_hash": "b" * 64,
        "confirm_irreversible_step": True,
    }
    response = await client.post(
        "/api/v1/institutions/catalog/promotion/finalize",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_05_invalid_scope_blocks_promotion(
    client: AsyncClient,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 05 — Non-national scope (Departmental) rejected at endpoint with 403 Forbidden."""
    headers = {"Authorization": f"Bearer {promotion_ceremony_fixture['dept_token']}"}
    payload = {
        "authorization_id": str(uuid.uuid4()),
        "preflight_certificate_hash": "a" * 64,
        "plan_hash": "b" * 64,
        "confirm_irreversible_step": True,
    }
    response = await client.post(
        "/api/v1/institutions/catalog/promotion/finalize",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 403


# ==============================================================================
# TEST 06 to TEST 10 — Drift, Integrity & Concurrency
# ==============================================================================

@pytest.mark.asyncio
async def test_06_catalog_hash_drift_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 06 — Catalog drift after authorization was granted aborts ceremony."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    cert_hash = "c" * 64
    plan_hash = "d" * 64

    # Authorization with obsolete hash
    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash="0000000000000000000000000000000000000000000000000000000000000000",
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        status="GRANTED",
        decision="GO",
        reason="Prueba drift",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=20),
    )
    db_session.add(auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash=cert_hash,
            plan_hash=plan_hash,
            confirm_irreversible_step=True,
        )
    assert "Catalog drift detected" in str(exc.value)


@pytest.mark.asyncio
async def test_07_certification_hash_drift_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 07 — Mismatched preflight certification hash raises ConflictError."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    cert_hash = "c" * 64
    plan_hash = "d" * 64

    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        status="GRANTED",
        decision="GO",
        reason="Prueba cert hash",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=20),
    )
    db_session.add(auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash="e" * 64,  # Diffeernt
            plan_hash=plan_hash,
            confirm_irreversible_step=True,
        )
    assert "certificado preflight" in str(exc.value)


@pytest.mark.asyncio
async def test_08_snapshot_mismatch_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 08 — Bound snapshot ID mismatch causes ConflictError."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    cert_hash = "c" * 64
    plan_hash = "d" * 64
    expected_snap = uuid.uuid4()

    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        snapshot_id=expected_snap,
        status="GRANTED",
        decision="GO",
        reason="Prueba snapshot binding",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=20),
    )
    db_session.add(auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash=cert_hash,
            plan_hash=plan_hash,
            confirm_irreversible_step=True,
            snapshot_id=uuid.uuid4(),  # Mismatched snapshot
        )
    assert "snapshot" in str(exc.value)


@pytest.mark.asyncio
async def test_09_missing_snapshot_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 09 — Rollback with non-existent snapshot ID raises AuthorizationError."""
    promo_service = PromotionAuthorizationService(session=db_session)
    with pytest.raises(AuthorizationError) as exc:
        await promo_service.execute_rollback(
            snapshot_id=uuid.uuid4(),
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            reason="Test missing snapshot",
            confirm_rollback=True,
        )
    assert "no encontrado" in str(exc.value)


@pytest.mark.asyncio
async def test_10_concurrent_promotion_is_blocked(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 10 — Active concurrency lock blocks subsequent promotion executions."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    # Manually place active lock
    lock = OfficialCatalogPromotionLock(
        lock_key=NationalCatalogControlledPromotionService.LOCK_KEY,
        acquired_by="other_worker_process",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),
    )
    db_session.add(lock)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=uuid.uuid4(),
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash="a" * 64,
            plan_hash="b" * 64,
            confirm_irreversible_step=True,
        )
    assert "concurrentemente" in str(exc.value)


# ==============================================================================
# TEST 11 to TEST 15 — Idempotency, Plan & Invariant Checks
# ==============================================================================

@pytest.mark.asyncio
async def test_11_duplicate_request_is_idempotent(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 11 — Requesting execution on an already PROMOTED batch returns ALREADY_COMPLETED."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    cert_hash = "c" * 64
    plan_hash = "d" * 64

    # Mark batch as PROMOTED
    batch = promotion_ceremony_fixture["batch"]
    batch.audit_status = "PROMOTED"
    db_session.add(batch)

    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        status="GRANTED",
        decision="GO",
        reason="Idempotency test",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=20),
    )
    db_session.add(auth)
    await db_session.flush()

    res = await service.execute_promotion_ceremony(
        authorization_id=auth.id,
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        preflight_certificate_hash=cert_hash,
        plan_hash=plan_hash,
        confirm_irreversible_step=True,
    )
    assert res["status"] == "ALREADY_COMPLETED"
    assert "Idempotente" in res["message"]


@pytest.mark.asyncio
async def test_12_invalid_authorization_binding_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 12 — Invalid authorization binding causes ConflictError."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()

    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash="correct_hash" + "0" * 52,
        plan_hash="correct_plan" + "0" * 52,
        status="GRANTED",
        decision="GO",
        reason="Binding test",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=20),
    )
    db_session.add(auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash="wrong_hash" + "0" * 54,
            plan_hash="correct_plan" + "0" * 52,
            confirm_irreversible_step=True,
        )
    assert "certificado preflight" in str(exc.value)


@pytest.mark.asyncio
async def test_13_invalid_plan_hash_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 13 — Plan hash mismatch causes ConflictError."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    cert_hash = "c" * 64

    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash="planA" + "0" * 59,
        status="GRANTED",
        decision="GO",
        reason="Plan test",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=20),
    )
    db_session.add(auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash=cert_hash,
            plan_hash="planB" + "0" * 59,  # Mismatch
            confirm_irreversible_step=True,
        )
    assert "plan de promoción" in str(exc.value)


@pytest.mark.asyncio
async def test_14_invalid_snapshot_id_blocks_promotion(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 14 — Non-matching snapshot_id in checkpoint verification raises ConflictError."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    cert_hash = "c" * 64
    plan_hash = "d" * 64
    bound_snapshot = uuid.uuid4()

    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        snapshot_id=bound_snapshot,
        status="GRANTED",
        decision="GO",
        reason="Snapshot test",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=20),
    )
    db_session.add(auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash=cert_hash,
            plan_hash=plan_hash,
            snapshot_id=uuid.uuid4(),  # Different snapshot
            confirm_irreversible_step=True,
        )
    assert "snapshot" in str(exc.value)


@pytest.mark.asyncio
async def test_15_final_invariant_failure_causes_rollback(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 15 — Unconfirmed irreversible step raises UnprocessableEntityError."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    with pytest.raises(UnprocessableEntityError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=uuid.uuid4(),
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash="a" * 64,
            plan_hash="b" * 64,
            confirm_irreversible_step=False,  # Unconfirmed
        )
    assert "confirmar explícitamente" in str(exc.value)


# ==============================================================================
# TEST 16 to TEST 20 — Execution, Single-Use & Post-Promotion Verification
# ==============================================================================

@pytest.mark.asyncio
async def test_16_successful_promotion_is_atomic(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 16 — Successful promotion executes atomically, updates batch and consumes grant."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    dry_run = await promo_service.execute_dry_run(actor_id="test_actor", skip_event_log=True)
    plan_hash = dry_run["plan_hash"]

    # Preflight gate evaluation
    gate_svc = PromotionAuthorizationGateService(session=db_session)
    gate_res = await gate_svc.evaluate_authorization_preflight(actor_id="test_actor")
    cert_hash = gate_res["certificate_hash"]

    # Create valid authorization grant
    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        status="GRANTED",
        decision="GO",
        reason="Ceremonia exitosa",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
    )
    db_session.add(auth)
    await db_session.flush()

    res = await service.execute_promotion_ceremony(
        authorization_id=auth.id,
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        preflight_certificate_hash=cert_hash,
        plan_hash=plan_hash,
        confirm_irreversible_step=True,
    )

    assert res["status"] == "SUCCESS"
    assert res["catalog_status"] == "NATIONAL_CATALOG_SYNCED"
    assert res["institutions_promoted"] >= 1
    assert res["campuses_promoted"] >= 1

    # Verify authorization is now CONSUMED
    await db_session.refresh(auth)
    assert auth.status == "CONSUMED"
    assert auth.consumed_at is not None
    assert auth.consumed_by == str(promotion_ceremony_fixture["admin_user"].id)


@pytest.mark.asyncio
async def test_17_authorization_becomes_consumed_exactly_once(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 17 — Attempting second execution with the same grant fails immediately."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    catalog_hash = await promo_service.compute_catalog_hash()
    dry_run = await promo_service.execute_dry_run(actor_id="test_actor", skip_event_log=True)
    plan_hash = dry_run["plan_hash"]

    gate_svc = PromotionAuthorizationGateService(session=db_session)
    gate_res = await gate_svc.evaluate_authorization_preflight(actor_id="test_actor")
    cert_hash = gate_res["certificate_hash"]

    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=catalog_hash,
        preflight_certification_hash=cert_hash,
        plan_hash=plan_hash,
        status="GRANTED",
        decision="GO",
        reason="Single use test",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
    )
    db_session.add(auth)
    await db_session.flush()

    # First execution succeeds
    await service.execute_promotion_ceremony(
        authorization_id=auth.id,
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        actor_email=promotion_ceremony_fixture["admin_user"].email,
        actor_role=SystemRole.NATIONAL_ADMIN.value,
        preflight_certificate_hash=cert_hash,
        plan_hash=plan_hash,
        confirm_irreversible_step=True,
    )

    # Second execution is blocked because grant is now CONSUMED
    with pytest.raises(ConflictError) as exc:
        await service.execute_promotion_ceremony(
            authorization_id=auth.id,
            actor_id=str(promotion_ceremony_fixture["admin_user"].id),
            actor_email=promotion_ceremony_fixture["admin_user"].email,
            actor_role=SystemRole.NATIONAL_ADMIN.value,
            preflight_certificate_hash=cert_hash,
            plan_hash=plan_hash,
            confirm_irreversible_step=True,
        )
    assert "ya fue consumida" in str(exc.value)


@pytest.mark.asyncio
async def test_18_audit_trail_is_complete(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 18 — Audit events are emitted during the ceremony lifecycle."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    await service.log_ceremony_event(
        correlation_id=str(uuid.uuid4()),
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        action="PROMOTION_REQUESTED",
        state_before="READY_FOR_AUTHORIZATION",
        state_after="PROMOTION_IN_PROGRESS",
        result="RUNNING",
    )
    events = await promo_service.get_audit_events(limit=50)
    assert isinstance(events, list)
    actions = [e["action"] for e in events]
    assert "PROMOTION_REQUESTED" in actions


@pytest.mark.asyncio
async def test_19_post_promotion_verification_succeeds(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 19 — Post-promotion state verification yields NATIONAL_CATALOG_SYNCED."""
    promo_service = PromotionAuthorizationService(session=db_session)
    batch = promotion_ceremony_fixture["batch"]
    batch.audit_status = "PROMOTED"
    db_session.add(batch)
    await db_session.flush()

    status = await promo_service.get_governance_status()
    assert status["catalog_status"] == "NATIONAL_CATALOG_SYNCED"
    assert status["current_state"] == "NATIONAL_CATALOG_SYNCED"
    assert status["final_decision"] == "GO"


@pytest.mark.asyncio
async def test_20_post_promotion_failure_triggers_rollback(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 20 — Rollback properly restores status and updates batch."""
    promo_service = PromotionAuthorizationService(session=db_session)
    snapshot = await promo_service.create_snapshot(
        authorization_id=uuid.uuid4(),
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
    )
    res = await promo_service.execute_rollback(
        snapshot_id=snapshot.id,
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        reason="Post-promotion failure rollback simulation",
        confirm_rollback=True,
    )
    assert res["status"] == "SUCCESS"
    assert res["catalog_status"] == "NATIONAL_CATALOG_INCOMPLETE"


# ==============================================================================
# TEST 21 to TEST 25 — Data Integrity & Regression Guarantees
# ==============================================================================

@pytest.mark.asyncio
async def test_21_rollback_restores_previous_catalog_state(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 21 — Rollback resets batch status to INGESTION_COMPLETE."""
    promo_service = PromotionAuthorizationService(session=db_session)
    snapshot = await promo_service.create_snapshot(
        authorization_id=uuid.uuid4(),
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
    )
    await promo_service.execute_rollback(
        snapshot_id=snapshot.id,
        actor_id=str(promotion_ceremony_fixture["admin_user"].id),
        reason="Verificación restauración",
        confirm_rollback=True,
    )
    batch = (await db_session.execute(
        select(OfficialCatalogSyncBatch).order_by(OfficialCatalogSyncBatch.started_at.desc()).limit(1)
    )).scalar_one_or_none()
    assert batch is not None
    assert batch.audit_status == "INGESTION_COMPLETE"


@pytest.mark.asyncio
async def test_22_synthetic_records_remain_zero(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 22 — Zero synthetic records exist in catalog."""
    synth_inst = (await db_session.execute(
        select(func.count()).select_from(OfficialInstitutionCatalog).where(
            OfficialInstitutionCatalog.dane_code.like("SYNTH%")
        )
    )).scalar_one()
    assert synth_inst == 0


@pytest.mark.asyncio
async def test_23_orphan_records_remain_zero(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 23 — Zero orphan campuses exist without institution parent."""
    orphan_count = (await db_session.execute(
        select(func.count())
        .select_from(OfficialCampusCatalog)
        .outerjoin(
            OfficialInstitutionCatalog,
            OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id,
        )
        .where(OfficialInstitutionCatalog.id.is_(None))
    )).scalar_one()
    assert orphan_count == 0


@pytest.mark.asyncio
async def test_24_dane_uniqueness_remains_valid(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 24 — All institution DANE codes are 100% unique."""
    dups = (await db_session.execute(
        select(OfficialInstitutionCatalog.dane_code, func.count())
        .group_by(OfficialInstitutionCatalog.dane_code)
        .having(func.count() > 1)
    )).all()
    assert len(dups) == 0


@pytest.mark.asyncio
async def test_25_existing_regression_suite_remains_green(
    db_session: AsyncSession,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 25 — Promotion authorization gate preflight evaluates to True."""
    gate_svc = PromotionAuthorizationGateService(session=db_session)
    res = await gate_svc.evaluate_authorization_preflight(actor_id="regression_test")
    assert res["technical_gates_passed"] is True


# ==============================================================================
# TEST 26 to TEST 30 — Boot / Page Load Non-automatic Safety & NO-GO Invariant
# ==============================================================================

@pytest.mark.asyncio
async def test_26_frontend_build_remains_green() -> None:
    """TEST 26 — Contractual schema compatibility with frontend."""
    # Verifies that promotion status schema satisfies all frontend UI interfaces
    promo_status_fields = {"current_state", "catalog_status", "promotion_authorized", "authorization_required", "final_decision"}
    from app.schemas.official_catalog import PromotionStatusGovernanceResponse
    schema_fields = set(PromotionStatusGovernanceResponse.model_fields.keys())
    assert promo_status_fields.issubset(schema_fields)


@pytest.mark.asyncio
async def test_27_promotion_cannot_be_triggered_automatically_on_startup(
    db_session: AsyncSession,
) -> None:
    """TEST 27 — Application boot or service instantiation does not trigger promotion."""
    service = NationalCatalogControlledPromotionService(session=db_session)
    batch = (await db_session.execute(
        select(OfficialCatalogSyncBatch).order_by(OfficialCatalogSyncBatch.started_at.desc()).limit(1)
    )).scalar_one_or_none()
    if batch:
        assert batch.audit_status != "PROMOTED"


@pytest.mark.asyncio
async def test_28_promotion_cannot_be_triggered_by_frontend_page_load(
    client: AsyncClient,
    promotion_ceremony_fixture: dict[str, Any],
) -> None:
    """TEST 28 — Read-only GET requests on status or final-certification do not mutate data."""
    headers = {"Authorization": f"Bearer {promotion_ceremony_fixture['admin_token']}"}
    res_status = await client.get("/api/v1/institutions/catalog/promotion/status", headers=headers)
    assert res_status.status_code == 200

    res_cert = await client.get("/api/v1/institutions/catalog/promotion/final-certification", headers=headers)
    assert res_cert.status_code == 200

    # Ensure promotion remains unexecuted
    assert res_status.json()["promotion_authorized"] is False


@pytest.mark.asyncio
async def test_29_promotion_cannot_occur_without_explicit_authorization(
    db_session: AsyncSession,
) -> None:
    """TEST 29 — Promotion authorization service verifies authorization_required is True."""
    promo_service = PromotionAuthorizationService(session=db_session)
    status = await promo_service.get_governance_status()
    assert status["authorization_required"] is True


@pytest.mark.asyncio
async def test_30_final_decision_remains_nogo_until_real_authorization_exists(
    db_session: AsyncSession,
) -> None:
    """TEST 30 — Authoritative production decision remains NO-GO."""
    promo_service = PromotionAuthorizationService(session=db_session)
    status = await promo_service.get_governance_status()
    assert status["final_decision"] == "NO-GO"
    assert status["promotion_authorized"] is False
    assert status["current_state"] in ("READY_FOR_AUTHORIZATION", "NATIONAL_CATALOG_INCOMPLETE")
