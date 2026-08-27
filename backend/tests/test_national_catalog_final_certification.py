"""
PEVN Backend — National Catalog Final Pre-Authorization Certification Test Suite

Validates the final pre-authorization certification engine:
  - Evaluation of Gates U through AN (20 quality gates)
  - Strict read-only transactional execution
  - Deterministic certificate SHA-256 hash generation
  - Security / RBAC controls on the certification endpoint
  - Machine-readable verdict generation
"""

from __future__ import annotations

from typing import Any
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogSyncBatch,
    OfficialInstitutionCatalog,
)
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.national_catalog_final_certification_service import (
    NationalCatalogFinalCertificationService,
)


@pytest.fixture
async def final_cert_test_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Fixture providing national admin, teacher user, and representative catalog data."""
    dept = Department(code="11", name="Bogotá D.C.")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(code="11001", name="Bogotá D.C.", department_id=dept.id)
    db_session.add(muni)
    await db_session.flush()

    # Create National Admin
    admin_user = User(
        email="national.admin.finalcert@pevn.edu.co",
        username="admin_finalcert_test",
        hashed_password=password_hasher.hash("SecureAdminPass2026!"),
        first_name="Admin",
        last_name="Nacional",
        document_type=DocumentType.CC,
        document_number="1000000009",
        is_active=True,
    )
    # Create Regular Teacher (unauthorized)
    teacher_user = User(
        email="teacher.finalcert@pevn.edu.co",
        username="teacher_finalcert_test",
        hashed_password=password_hasher.hash("SecureTeacherPass2026!"),
        first_name="Docente",
        last_name="Pruebas",
        document_type=DocumentType.CC,
        document_number="2000000008",
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
        dane_code="111001000088",
        name="INSTITUTO TECNICO CENTRAL",
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
        dane_sede_code="111001000088",
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
# TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_final_certification_evaluates_all_20_gates(
    db_session: AsyncSession,
    final_cert_test_fixture: dict[str, Any],
) -> None:
    """Validates that NationalCatalogFinalCertificationService evaluates all 20 gates (U through AN)."""
    service = NationalCatalogFinalCertificationService(db_session)
    res = await service.execute_final_certification(actor_id=str(final_cert_test_fixture["admin_user"].id))

    assert res["certification_status"] == "PASSED"
    assert len(res["gates"]) == 20

    gate_ids = [g["gate_id"] for g in res["gates"]]
    expected_gate_ids = [
        "GATE_U", "GATE_V", "GATE_W", "GATE_X", "GATE_Y", "GATE_Z",
        "GATE_AA", "GATE_AB", "GATE_AC", "GATE_AD", "GATE_AE", "GATE_AF",
        "GATE_AG", "GATE_AH", "GATE_AI", "GATE_AJ", "GATE_AK", "GATE_AL",
        "GATE_AM", "GATE_AN"
    ]
    assert gate_ids == expected_gate_ids
    assert all(g["status"] == "PASSED" for g in res["gates"])


@pytest.mark.asyncio
async def test_final_certification_hash_is_deterministic(
    db_session: AsyncSession,
    final_cert_test_fixture: dict[str, Any],
) -> None:
    """Validates that consecutive evaluations on the same data yield identical certificate hashes."""
    service = NationalCatalogFinalCertificationService(db_session)
    res1 = await service.execute_final_certification(actor_id="AUDITOR_1")
    res2 = await service.execute_final_certification(actor_id="AUDITOR_2")

    assert res1["final_certification_hash"] == res2["final_certification_hash"]
    assert len(res1["final_certification_hash"]) == 64


@pytest.mark.asyncio
async def test_final_certification_strictly_read_only(
    db_session: AsyncSession,
    final_cert_test_fixture: dict[str, Any],
) -> None:
    """Validates that executing final certification creates zero mutations in canonical tables."""
    inst_count_before = (
        await db_session.execute(select(func.count()).select_from(OfficialInstitutionCatalog))
    ).scalar_one()
    camp_count_before = (
        await db_session.execute(select(func.count()).select_from(OfficialCampusCatalog))
    ).scalar_one()

    service = NationalCatalogFinalCertificationService(db_session)
    await service.execute_final_certification(actor_id="READONLY_AUDITOR")

    inst_count_after = (
        await db_session.execute(select(func.count()).select_from(OfficialInstitutionCatalog))
    ).scalar_one()
    camp_count_after = (
        await db_session.execute(select(func.count()).select_from(OfficialCampusCatalog))
    ).scalar_one()

    assert inst_count_before == inst_count_after
    assert camp_count_before == camp_count_after


@pytest.mark.asyncio
async def test_final_certification_endpoint_rbac(
    client: AsyncClient,
    final_cert_test_fixture: dict[str, Any],
) -> None:
    """Validates RBAC access controls on GET /catalog/promotion/final-certification."""
    # 1. Unauthorized Teacher -> 403 Forbidden
    teacher_headers = {"Authorization": f"Bearer {final_cert_test_fixture['teacher_token']}"}
    teacher_resp = await client.get("/api/v1/institutions/catalog/promotion/final-certification", headers=teacher_headers)
    assert teacher_resp.status_code == 403

    # 2. Authorized National Admin -> 200 OK
    admin_headers = {"Authorization": f"Bearer {final_cert_test_fixture['admin_token']}"}
    admin_resp = await client.get("/api/v1/institutions/catalog/promotion/final-certification", headers=admin_headers)
    assert admin_resp.status_code == 200
    data = admin_resp.json()
    assert data["certification_status"] == "PASSED"
    assert len(data["gates"]) == 20
    assert "FINAL_PREAUTH_CERTIFICATION_STATUS: PASSED" in data["machine_readable_verdict"]
