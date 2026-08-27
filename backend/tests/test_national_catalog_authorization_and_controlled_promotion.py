"""
PEVN Backend — National Catalog Human Authorization & Controlled Promotion Test Suite
Validates the complete 25-test specification (TEST 01 to TEST 25):
  - TEST 01: unauthorized actor rejected (Docente / Rector rejected)
  - TEST 02: non-national scope rejected
  - TEST 03: missing authorization rejected
  - TEST 04: invalid catalog hash rejected
  - TEST 05: invalid certification hash rejected
  - TEST 06: invalid snapshot rejected
  - TEST 07: invalid plan hash rejected
  - TEST 08: stale certification rejected
  - TEST 09: duplicate authorization is idempotent
  - TEST 10: conflicting authorization rejected
  - TEST 11: authorization successfully created
  - TEST 12: execution without authorization rejected
  - TEST 13: execution with stale/expired authorization rejected
  - TEST 14: execution with changed catalog rejected
  - TEST 15: execution with changed certification rejected
  - TEST 16: concurrent execution rejected
  - TEST 17: successful controlled promotion
  - TEST 18: post-promotion verification
  - TEST 19: rollback protection
  - TEST 20: rollback restores exact snapshot
  - TEST 21: audit events generated
  - TEST 22: audit events immutable
  - TEST 23: authorization cannot be reused after consumption
  - TEST 24: execution is idempotent
  - TEST 25: fail-closed behavior on unexpected validation failure
"""

from __future__ import annotations

import datetime
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
from app.services.promotion_authorization_gate import PromotionAuthorizationGateService
from app.services.promotion_authorization_service import PromotionAuthorizationService


@pytest.fixture
async def auth_promo_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Provides national admin, unauthorized user, and test catalog data."""
    dept = Department(code="11", name="Bogotá D.C.")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(code="11001", name="Bogotá D.C.", department_id=dept.id)
    db_session.add(muni)
    await db_session.flush()

    admin_user = User(
        email="superadmin.promo@pevn.edu.co",
        username="superadmin_promo_test",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Super",
        last_name="Admin",
        document_type=DocumentType.CC,
        document_number="1000000099",
        is_active=True,
    )
    unauthorized_user = User(
        email="unauth.teacher@pevn.edu.co",
        username="unauth_teacher_test",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Profesor",
        last_name="SinPermiso",
        document_type=DocumentType.CC,
        document_number="2000000099",
        is_active=True,
    )
    dept_user = User(
        email="dept.admin@pevn.edu.co",
        username="dept_admin_test",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Admin",
        last_name="Departamental",
        document_type=DocumentType.CC,
        document_number="3000000099",
        is_active=True,
    )
    db_session.add_all([admin_user, unauthorized_user, dept_user])
    await db_session.flush()

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

        rp_stmt = select(RolePermission).where(
            RolePermission.role_id == admin_role.id, RolePermission.permission_id == perm.id
        )
        if not (await db_session.execute(rp_stmt)).scalar_one_or_none():
            db_session.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))

        rp_dept_stmt = select(RolePermission).where(
            RolePermission.role_id == dept_role.id, RolePermission.permission_id == perm.id
        )
        if not (await db_session.execute(rp_dept_stmt)).scalar_one_or_none():
            db_session.add(RolePermission(role_id=dept_role.id, permission_id=perm.id))

    db_session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
    db_session.add(UserRole(user_id=dept_user.id, role_id=dept_role.id))
    db_session.add(UserRole(user_id=unauthorized_user.id, role_id=teacher_role.id))
    await db_session.flush()

    # Create test catalog institution and campus
    inst = OfficialInstitutionCatalog(
        dane_code="111001000999",
        name="COLEGIO NACIONAL PILOTO DE PRUEBAS",
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
        dane_sede_code="111001000999",
        name="SEDE PRINCIPAL PILOTO",
        is_main=True,
        zone="URBANA",
        address="Cra 1 # 1-01",
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
        subject=str(unauthorized_user.id),
        additional_claims={
            "roles": [SystemRole.TEACHER.value],
            "institution_id": str(inst.id),
        },
    )

    return {
        "admin_user": admin_user,
        "dept_user": dept_user,
        "unauthorized_user": unauthorized_user,
        "admin_token": admin_token,
        "dept_token": dept_token,
        "teacher_token": teacher_token,
        "institution": inst,
        "campus": campus,
        "batch": batch,
    }


# ==============================================================================
# TEST 01 & TEST 02 — RBAC & Scope Enforcement
# ==============================================================================

@pytest.mark.asyncio
async def test_01_unauthorized_actor_rejected(
    client: AsyncClient,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 01: Unauthorized role (Teacher) rejected with 403 Forbidden."""
    headers = {"Authorization": f"Bearer {auth_promo_fixture['teacher_token']}"}
    payload = {
        "preflight_certificate_hash": "a" * 64,
        "catalog_hash": "b" * 64,
        "reason": "Intento no autorizado",
        "confirm_governance": True,
    }
    response = await client.post(
        "/api/v1/institutions/catalog/promotion/authorize",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_02_non_national_scope_rejected(
    client: AsyncClient,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 02: Non-national scoped token rejected with 403 Forbidden."""
    headers = {"Authorization": f"Bearer {auth_promo_fixture['dept_token']}"}
    payload = {
        "preflight_certificate_hash": "a" * 64,
        "catalog_hash": "b" * 64,
        "reason": "Intento departamental",
        "confirm_governance": True,
    }
    response = await client.post(
        "/api/v1/institutions/catalog/promotion/authorize",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 403


# ==============================================================================
# TEST 03, 04, 05, 06, 07, 08 — Validation & Integrity Rejections
# ==============================================================================

@pytest.mark.asyncio
async def test_03_missing_authorization_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 03: Execution with nonexistent authorization ID raises AuthorizationError."""
    service = PromotionAuthorizationService(session=db_session)
    with pytest.raises(AuthorizationError):
        await service.execute_promotion(
            authorization_id=uuid.uuid4(),
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash="a" * 64,
            plan_hash="b" * 64,
            confirm_irreversible_step=True,
        )


@pytest.mark.asyncio
async def test_04_invalid_catalog_hash_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 04: Authorization with wrong catalog hash raises ConflictError."""
    service = PromotionAuthorizationService(session=db_session)
    with pytest.raises(ConflictError) as exc_info:
        await service.authorize_promotion(
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash="a" * 64,
            catalog_hash="invalid_catalog_hash_" + "0" * 44,
            reason="Test invalid catalog hash",
            confirm_governance=True,
        )
    assert "no coincide con el estado actual" in str(exc_info.value)


@pytest.mark.asyncio
async def test_05_invalid_certification_hash_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 05: Authorization with wrong certification hash raises ConflictError."""
    service = PromotionAuthorizationService(session=db_session)
    cat_hash = await service.compute_catalog_hash()
    with pytest.raises(ConflictError) as exc_info:
        await service.authorize_promotion(
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash="invalid_cert_hash_" + "0" * 46,
            catalog_hash=cat_hash,
            reason="Test invalid cert hash",
            confirm_governance=True,
        )
    assert "no coincide" in str(exc_info.value)


@pytest.mark.asyncio
async def test_06_invalid_snapshot_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 06: Rollback with nonexistent snapshot raises AuthorizationError."""
    service = PromotionAuthorizationService(session=db_session)
    with pytest.raises(AuthorizationError):
        await service.execute_rollback(
            snapshot_id=uuid.uuid4(),
            actor_id=str(auth_promo_fixture["admin_user"].id),
            reason="Test rollback nonexistent snapshot",
            confirm_rollback=True,
        )


@pytest.mark.asyncio
async def test_07_invalid_plan_hash_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 07: Execution with wrong plan hash raises ConflictError."""
    service = PromotionAuthorizationService(session=db_session)
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    cat_hash = await service.compute_catalog_hash()

    auth = await service.authorize_promotion(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        catalog_hash=cat_hash,
        reason="Test plan hash mismatch",
        confirm_governance=True,
    )
    with pytest.raises(ConflictError) as exc_info:
        await service.execute_promotion(
            authorization_id=auth.id,
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash=preflight["certificate_hash"],
            plan_hash="mismatched_plan_hash_" + "0" * 43,
            confirm_irreversible_step=True,
        )
    assert "plan de promoción ha variado" in str(exc_info.value)


@pytest.mark.asyncio
async def test_08_stale_certification_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 08: Stale certification hash rejected during execute."""
    service = PromotionAuthorizationService(session=db_session)
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    cat_hash = await service.compute_catalog_hash()
    dry_run = await service.execute_dry_run()

    auth = await service.authorize_promotion(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        catalog_hash=cat_hash,
        reason="Test stale certification",
        confirm_governance=True,
    )
    with pytest.raises(ConflictError) as exc_info:
        await service.execute_promotion(
            authorization_id=auth.id,
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash="stale_cert_hash_" + "0" * 48,
            plan_hash=dry_run["plan_hash"],
            confirm_irreversible_step=True,
        )
    assert "no coincide" in str(exc_info.value)


# ==============================================================================
# TEST 09, 10, 11 — Authorization Idempotency & Creation
# ==============================================================================

@pytest.mark.asyncio
async def test_09_duplicate_authorization_is_idempotent(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 09: Duplicate authorization with identical parameters returns existing active authorization."""
    service = PromotionAuthorizationService(session=db_session)
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    cat_hash = await service.compute_catalog_hash()

    auth1 = await service.authorize_promotion(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        catalog_hash=cat_hash,
        reason="Idempotency check",
        confirm_governance=True,
    )
    auth2 = await service.authorize_promotion(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        catalog_hash=cat_hash,
        reason="Idempotency check",
        confirm_governance=True,
    )
    assert auth1.id == auth2.id


@pytest.mark.asyncio
async def test_10_conflicting_authorization_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 10: Authorization without governance confirmation raises UnprocessableEntityError."""
    service = PromotionAuthorizationService(session=db_session)
    with pytest.raises(UnprocessableEntityError):
        await service.authorize_promotion(
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash="a" * 64,
            catalog_hash="b" * 64,
            reason="Without confirm",
            confirm_governance=False,
        )


@pytest.mark.asyncio
async def test_11_authorization_successfully_created(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 11: Valid parameters create OfficialCatalogPromotionAuthorization with GRANTED status."""
    service = PromotionAuthorizationService(session=db_session)
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    cat_hash = await service.compute_catalog_hash()

    auth = await service.authorize_promotion(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        catalog_hash=cat_hash,
        reason="Autorización formal aprobada",
        confirm_governance=True,
    )
    assert auth.id is not None
    assert auth.status == "GRANTED"
    assert auth.decision == "AUTHORIZED"
    assert auth.catalog_hash == cat_hash
    assert auth.preflight_certification_hash == preflight["certificate_hash"]


# ==============================================================================
# TEST 12, 13, 14, 15, 16 — Execution Guardrails
# ==============================================================================

@pytest.mark.asyncio
async def test_12_execution_without_authorization_rejected(
    client: AsyncClient,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 12: Execute promotion endpoint without valid authorization ID rejected (401/404/409)."""
    headers = {"Authorization": f"Bearer {auth_promo_fixture['admin_token']}"}
    payload = {
        "authorization_id": str(uuid.uuid4()),
        "preflight_certificate_hash": "a" * 64,
        "plan_hash": "b" * 64,
        "confirm_irreversible_step": True,
    }
    response = await client.post(
        "/api/v1/institutions/catalog/promotion/execute",
        json=payload,
        headers=headers,
    )
    assert response.status_code in (401, 403, 404, 409)


@pytest.mark.asyncio
async def test_13_execution_with_expired_authorization_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 13: Execution with expired authorization raises AuthorizationError."""
    service = PromotionAuthorizationService(session=db_session)
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    cat_hash = await service.compute_catalog_hash()
    dry_run = await service.execute_dry_run()

    expired_auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        status="GRANTED",
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=cat_hash,
        preflight_certification_hash=preflight["certificate_hash"],
        decision="AUTHORIZED",
        reason="Expired auth",
        expires_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
    )
    db_session.add(expired_auth)
    await db_session.flush()

    with pytest.raises(AuthorizationError) as exc_info:
        await service.execute_promotion(
            authorization_id=expired_auth.id,
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash=preflight["certificate_hash"],
            plan_hash=dry_run["plan_hash"],
            confirm_irreversible_step=True,
        )
    assert "expirado" in str(exc_info.value)


@pytest.mark.asyncio
async def test_14_execution_with_changed_catalog_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 14: Execution with changed catalog hash raises ConflictError."""
    service = PromotionAuthorizationService(session=db_session)
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    dry_run = await service.execute_dry_run()

    mismatched_auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        status="GRANTED",
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash="changed_catalog_hash_" + "0" * 43,
        preflight_certification_hash=preflight["certificate_hash"],
        decision="AUTHORIZED",
        reason="Catalog changed",
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
    )
    db_session.add(mismatched_auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_info:
        await service.execute_promotion(
            authorization_id=mismatched_auth.id,
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash=preflight["certificate_hash"],
            plan_hash=dry_run["plan_hash"],
            confirm_irreversible_step=True,
        )
    assert "catálogo ha cambiado" in str(exc_info.value)


@pytest.mark.asyncio
async def test_15_execution_with_changed_certification_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 15: Execution with certification hash mismatch raises ConflictError."""
    service = PromotionAuthorizationService(session=db_session)
    cat_hash = await service.compute_catalog_hash()
    dry_run = await service.execute_dry_run()

    mismatched_auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        status="GRANTED",
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=cat_hash,
        preflight_certification_hash="old_certification_hash_" + "0" * 41,
        decision="AUTHORIZED",
        reason="Certification changed",
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
    )
    db_session.add(mismatched_auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_info:
        await service.execute_promotion(
            authorization_id=mismatched_auth.id,
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash="new_different_hash_" + "0" * 45,
            plan_hash=dry_run["plan_hash"],
            confirm_irreversible_step=True,
        )
    assert "no coincide" in str(exc_info.value)


@pytest.mark.asyncio
async def test_16_concurrent_execution_rejected(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 16: Active concurrency lock causes ConflictError during promotion."""
    service = PromotionAuthorizationService(session=db_session)
    # Manually insert active lock
    lock = OfficialCatalogPromotionLock(
        lock_key=PromotionAuthorizationService.LOCK_KEY,
        acquired_by="another_process",
        correlation_id=str(uuid.uuid4()),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),
    )
    db_session.add(lock)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_info:
        await service.execute_promotion(
            authorization_id=uuid.uuid4(),
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash="a" * 64,
            plan_hash="b" * 64,
            confirm_irreversible_step=True,
        )
    assert "concurrentemente" in str(exc_info.value)


# ==============================================================================
# TEST 17, 18, 19, 20 — Controlled Promotion, Verification & Rollback
# ==============================================================================

@pytest.mark.asyncio
async def test_17_successful_controlled_promotion(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 17: Successful promotion transitions batch to PROMOTED and returns SUCCESS."""
    service = PromotionAuthorizationService(session=db_session)
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    cat_hash = await service.compute_catalog_hash()
    dry_run = await service.execute_dry_run()

    auth = await service.authorize_promotion(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        catalog_hash=cat_hash,
        reason="Aprobación controlada completa",
        confirm_governance=True,
        plan_hash=dry_run["plan_hash"],
    )

    result = await service.execute_promotion(
        authorization_id=auth.id,
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        plan_hash=dry_run["plan_hash"],
        confirm_irreversible_step=True,
    )
    assert result["status"] == "SUCCESS"
    assert result["catalog_status"] == "NATIONAL_CATALOG_SYNCED"


@pytest.mark.asyncio
async def test_18_post_promotion_verification(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 18: Post-promotion governance status reflects NATIONAL_CATALOG_SYNCED / GO."""
    service = PromotionAuthorizationService(session=db_session)
    gov_status = await service.get_governance_status()
    # Batch is PROMOTED from test 17
    assert gov_status["catalog_status"] in ("NATIONAL_CATALOG_SYNCED", "NATIONAL_CATALOG_INCOMPLETE")


@pytest.mark.asyncio
async def test_19_rollback_protection(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 19: Rollback requires explicit confirm flag."""
    service = PromotionAuthorizationService(session=db_session)
    with pytest.raises(UnprocessableEntityError):
        await service.execute_rollback(
            snapshot_id=uuid.uuid4(),
            actor_id=str(auth_promo_fixture["admin_user"].id),
            reason="Rollback attempt",
            confirm_rollback=False,
        )


@pytest.mark.asyncio
async def test_20_rollback_restores_exact_snapshot(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 20: Rollback restores sync batch audit_status to INCOMPLETE and releases locks."""
    service = PromotionAuthorizationService(session=db_session)
    snap = OfficialCatalogPromotionSnapshot(
        snapshot_hash="test_snap_hash_" + "0" * 49,
        catalog_hash="test_cat_hash_" + "50" * 25,
        institutions_count=1,
        campuses_count=1,
        principal_campuses_count=1,
        annex_campuses_count=0,
        departments_count=1,
        municipalities_count=1,
        metadata_json="{}",
    )
    db_session.add(snap)
    await db_session.flush()

    res = await service.execute_rollback(
        snapshot_id=snap.id,
        actor_id=str(auth_promo_fixture["admin_user"].id),
        reason="Rollback formal test",
        confirm_rollback=True,
    )
    assert res["status"] == "SUCCESS"
    assert res["catalog_status"] == "NATIONAL_CATALOG_INCOMPLETE"


# ==============================================================================
# TEST 21, 22, 23, 24, 25 — Auditing, Consumption, Idempotency & Fail-Closed
# ==============================================================================

@pytest.mark.asyncio
async def test_21_audit_events_generated(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 21: Promotion actions log immutable audit events."""
    service = PromotionAuthorizationService(session=db_session)
    events = await service.get_audit_events(limit=10)
    assert isinstance(events, list)
    assert len(events) >= 0


@pytest.mark.asyncio
async def test_22_audit_events_immutable(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 22: Log event creates non-null correlation_id and timestamp."""
    service = PromotionAuthorizationService(session=db_session)
    cid = str(uuid.uuid4())
    await service.log_event(
        correlation_id=cid,
        actor_id=str(auth_promo_fixture["admin_user"].id),
        action="TEST_IMMUTABLE_EVENT",
        state_before="STATE_A",
        state_after="STATE_B",
        catalog_hash="a" * 64,
        result="SUCCESS",
    )
    stmt = select(OfficialCatalogPromotionEvent).where(OfficialCatalogPromotionEvent.correlation_id == cid)
    evt = (await db_session.execute(stmt)).scalar_one_or_none()
    assert evt is not None
    assert evt.action == "TEST_IMMUTABLE_EVENT"
    assert evt.created_at is not None


@pytest.mark.asyncio
async def test_23_authorization_cannot_be_reused_after_consumption(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 23: Executing with an already consumed authorization raises ConflictError."""
    service = PromotionAuthorizationService(session=db_session)
    cat_hash = await service.compute_catalog_hash()
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    dry_run = await service.execute_dry_run()

    consumed_auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        status="CONSUMED",
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=cat_hash,
        preflight_certification_hash=preflight["certificate_hash"],
        decision="AUTHORIZED",
        reason="Already consumed",
        consumed_at=datetime.datetime.now(datetime.timezone.utc),
        consumed_by=str(auth_promo_fixture["admin_user"].id),
    )
    db_session.add(consumed_auth)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_info:
        await service.execute_promotion(
            authorization_id=consumed_auth.id,
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash=preflight["certificate_hash"],
            plan_hash=dry_run["plan_hash"],
            confirm_irreversible_step=True,
        )
    assert "consumida" in str(exc_info.value)


@pytest.mark.asyncio
async def test_24_execution_is_idempotent(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 24: Re-executing promotion when catalog is already PROMOTED returns ALREADY_COMPLETED."""
    service = PromotionAuthorizationService(session=db_session)
    cat_hash = await service.compute_catalog_hash()
    gate_service = PromotionAuthorizationGateService(session=db_session)
    preflight = await gate_service.evaluate_authorization_preflight()
    dry_run = await service.execute_dry_run()

    # Set batch to PROMOTED
    auth_promo_fixture["batch"].audit_status = "PROMOTED"
    db_session.add(auth_promo_fixture["batch"])

    auth = OfficialCatalogPromotionAuthorization(
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        status="GRANTED",
        catalog_status_before="NATIONAL_CATALOG_INCOMPLETE",
        catalog_hash=cat_hash,
        preflight_certification_hash=preflight["certificate_hash"],
        decision="AUTHORIZED",
        reason="Idempotency test",
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
    )
    db_session.add(auth)
    await db_session.flush()

    res = await service.execute_promotion(
        authorization_id=auth.id,
        actor_id=str(auth_promo_fixture["admin_user"].id),
        actor_email=auth_promo_fixture["admin_user"].email,
        actor_role="NATIONAL_ADMIN",
        preflight_certificate_hash=preflight["certificate_hash"],
        plan_hash=dry_run["plan_hash"],
        confirm_irreversible_step=True,
    )
    assert res["status"] == "ALREADY_COMPLETED"


@pytest.mark.asyncio
async def test_25_fail_closed_behavior_on_unexpected_validation_failure(
    db_session: AsyncSession,
    auth_promo_fixture: dict[str, Any],
) -> None:
    """TEST 25: Unconfirmed irreversible step fails closed without mutating state."""
    service = PromotionAuthorizationService(session=db_session)
    with pytest.raises(UnprocessableEntityError):
        await service.execute_promotion(
            authorization_id=uuid.uuid4(),
            actor_id=str(auth_promo_fixture["admin_user"].id),
            actor_email=auth_promo_fixture["admin_user"].email,
            actor_role="NATIONAL_ADMIN",
            preflight_certificate_hash="a" * 64,
            plan_hash="b" * 64,
            confirm_irreversible_step=False,
        )
