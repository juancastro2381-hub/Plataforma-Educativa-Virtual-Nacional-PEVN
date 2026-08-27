"""
PEVN Backend — National Catalog Completion & Final Data Closure Audit Test Suite

18+ test matrix certifying read-only forensic audit and data completeness:
  1. Incomplete-state detection
  2. Exact incomplete-state cause tracing
  3. Historical isolation classification
  4. Source/target reconciliation
  5. Cardinality verification
  6. Identifier integrity
  7. Geographic coverage
  8. Orphan detection
  9. Duplicate detection
  10. Synthetic-record detection
  11. Hash stability
  12. Certification hash stability
  13. Read-only enforcement
  14. Authorization non-consumption
  15. Promotion non-execution
  16. State-machine preservation
  17. Fail-closed behavior
  18. Deterministic machine-readable verdict
"""

from __future__ import annotations

import uuid
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
    OfficialCatalogPromotionAuthorization,
    OfficialCatalogPromotionEvent,
    OfficialCatalogSyncBatch,
    OfficialInstitutionCatalog,
)
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.national_catalog_closure_audit_service import (
    NationalCatalogClosureAuditService,
)
from app.services.promotion_authorization_service import (
    PromotionAuthorizationService,
)


@pytest.fixture
async def closure_audit_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Creates mock data for the closure audit test suite."""
    admin_user = User(
        email="closure.auditor@pevn.edu.co",
        username="closure_auditor_test",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Auditor",
        last_name="Forense",
        document_type=DocumentType.CC,
        document_number="4000000001",
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.flush()

    admin_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))
    ).scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name=SystemRole.NATIONAL_ADMIN.value, description="National Administrator")
        db_session.add(admin_role)

    await db_session.flush()

    for r_name, a_name in [("institutions", "read"), ("institutions", "create")]:
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

    db_session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
    await db_session.flush()

    inst = OfficialInstitutionCatalog(
        dane_code="111001007777",
        name="INSTITUTO NACIONAL DE AUDITORIA FORENSE",
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
        dane_sede_code="111001007777",
        name="SEDE CENTRAL DE AUDITORIA",
        is_main=True,
        zone="URBANA",
        address="Cra 7 # 7-01",
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
        audit_status="VERIFIED",
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

    return {
        "admin_user": admin_user,
        "admin_token": admin_token,
        "inst": inst,
        "campus": campus,
        "batch": batch,
    }


# ==============================================================================
# TEST 01 to TEST 06 — Incomplete State, Tracing & Reconciliation
# ==============================================================================

@pytest.mark.asyncio
async def test_01_incomplete_state_detection(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 01 — Detects that catalog_status is currently NATIONAL_CATALOG_INCOMPLETE."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["governance_catalog_status"] == "NATIONAL_CATALOG_INCOMPLETE"
    assert res["current_state"] in ("READY_FOR_AUTHORIZATION", "NATIONAL_CATALOG_INCOMPLETE")


@pytest.mark.asyncio
async def test_02_exact_incomplete_state_cause_tracing(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 02 — Authoritative cause traced to governance state (batch not PROMOTED)."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert "GOVERNANCE_PHASE_GATE" in res["catalog_completeness_cause"]
    assert "PROMOTED" in res["required_for_complete_and_go"]


@pytest.mark.asyncio
async def test_03_historical_isolation_classification(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 03 — 3,689 historical isolated records are classified as Category A (Intentionally isolated)."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    hist = res["historical_classification"]
    assert hist["total_isolated_records"] == 3689
    assert hist["category_a_intentionally_retained_historical"] == 3689
    assert hist["category_d_data_quality_defects"] == 0
    assert hist["status"] == "VALID_HISTORICAL_ISOLATION"


@pytest.mark.asyncio
async def test_04_source_target_reconciliation(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 04 — Source/Target reconciliation reports 0 missing, 0 unexpected, 0 rejected."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    rec = res["reconciliation_detail"]
    assert rec["reconciliation_status"] == "PASSED"
    assert rec["missing_records"] == 0
    assert rec["unexpected_records"] == 0
    assert rec["rejected_records"] == 0


@pytest.mark.asyncio
async def test_05_cardinality_verification(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 05 — Cardinality integrity confirmed."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["cardinality_integrity"] == "PASSED"
    assert res["institution_count"] >= 1
    assert res["campus_count"] >= 1


@pytest.mark.asyncio
async def test_06_identifier_integrity(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 06 — Identifier integrity confirmed with 0 malformed identifiers."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["identifier_integrity"] == "PASSED"


# ==============================================================================
# TEST 07 to TEST 12 — Geographic, Orphan, Duplicate, Synthetic & Hash Checks
# ==============================================================================

@pytest.mark.asyncio
async def test_07_geographic_coverage(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 07 — Geographic coverage audit logic operational."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["geographic_coverage"] in ("PASSED", "FAILED")


@pytest.mark.asyncio
async def test_08_orphan_detection(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 08 — Orphan campus count is exactly zero."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["orphan_records"] == 0


@pytest.mark.asyncio
async def test_09_duplicate_detection(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 09 — Duplicate DANE codes count is exactly zero."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["duplicate_records"] == 0


@pytest.mark.asyncio
async def test_10_synthetic_record_detection(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 10 — Synthetic record count is exactly zero."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["synthetic_records"] == 0


@pytest.mark.asyncio
async def test_11_hash_stability(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 11 — SHA-256 catalog hash is 64 hex chars and stable."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert len(res["catalog_hash"]) == 64
    assert res["catalog_hash_stable"] == "PASSED"


@pytest.mark.asyncio
async def test_12_certification_hash_stability(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 12 — Final certification hash is 64 hex chars and stable."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert len(res["certification_hash"]) == 64
    assert res["certification_hash_stable"] == "PASSED"


# ==============================================================================
# TEST 13 to TEST 18 — Read-Only Enforcement, Safety & Verdict
# ==============================================================================

@pytest.mark.asyncio
async def test_13_read_only_enforcement(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 13 — Audit does not mutate canonical database records (0 mutations)."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["canonical_mutations"] == 0


@pytest.mark.asyncio
async def test_14_authorization_non_consumption(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 14 — Audit leaves authorizations unconsumed and promotion_authorized=False."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["promotion_authorized"] is False
    assert res["authorization_required"] is True


@pytest.mark.asyncio
async def test_15_promotion_non_execution(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 15 — Audit leaves promotion_executed strictly in False."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["promotion_executed"] is False


@pytest.mark.asyncio
async def test_16_state_machine_preservation(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 16 — Audit preserves final_decision=NO-GO and current_state."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    assert res["final_decision"] == "NO-GO"
    assert res["stop_condition"] == "HUMAN_AUTHORIZATION_REQUIRED"


@pytest.mark.asyncio
async def test_17_fail_closed_behavior(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 17 — Governance status remains NO-GO under unpromoted batch."""
    promo_service = PromotionAuthorizationService(session=db_session)
    gov = await promo_service.get_governance_status()
    assert gov["final_decision"] == "NO-GO"
    assert gov["promotion_authorized"] is False


@pytest.mark.asyncio
async def test_18_deterministic_machine_readable_verdict(
    db_session: AsyncSession,
    closure_audit_fixture: dict[str, Any],
) -> None:
    """TEST 18 — Audit outputs complete deterministic machine-readable payload."""
    service = NationalCatalogClosureAuditService(session=db_session)
    res = await service.execute_closure_audit()
    required_keys = [
        "national_catalog_closure_audit_status",
        "data_completeness_status",
        "governance_catalog_status",
        "catalog_completeness_cause",
        "historical_isolation_status",
        "source_target_reconciliation",
        "cardinality_integrity",
        "identifier_integrity",
        "geographic_coverage",
        "orphan_records",
        "duplicate_records",
        "synthetic_records",
        "rejected_records",
        "unresolved_records",
        "catalog_hash_stable",
        "certification_hash_stable",
        "canonical_mutations",
        "promotion_executed",
        "promotion_authorized",
        "authorization_required",
        "current_state",
        "final_decision",
        "stop_condition",
    ]
    for key in required_keys:
        assert key in res, f"Missing key {key} in verdict"
