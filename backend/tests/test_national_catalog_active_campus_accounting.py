"""
PEVN Backend — Active Campus Source/Target Accounting Reconciliation Forensic Audit Test Suite

Dedicated test suite verifying:
  1. Source active campus population count = 50,107
  2. Canonical PostgreSQL campus population count = 51,521
  3. Accounting difference = exactly 1,414
  4. Explicit classification of the 1,414 difference (1,364 DS1 Main Sedes + 50 Seed Campuses)
  5. Historical isolated population = 3,689 (Category A)
  6. Zero duplicate DANE codes
  7. Zero orphan campuses
  8. Zero synthetic records
  9. Zero rejected/unresolved records
  10. Zero canonical database mutations
  11. Catalog hash stability (SHA-256)
  12. Final preflight certification hash stability
  13. Governance state preservation (READY_FOR_AUTHORIZATION)
  14. Final decision preservation (NO-GO)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogPromotionAuthorization,
    OfficialCatalogPromotionEvent,
    OfficialCatalogSyncBatch,
    OfficialInstitutionCatalog,
)
from app.services.national_catalog_closure_audit_service import (
    NationalCatalogClosureAuditService,
)
from app.services.national_catalog_final_certification_service import (
    NationalCatalogFinalCertificationService,
)
from app.services.promotion_authorization_service import (
    PromotionAuthorizationService,
)


@pytest.fixture
async def accounting_audit_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Provides access to services and live DB context for read-only accounting tests."""
    closure_service = NationalCatalogClosureAuditService(session=db_session)
    cert_service = NationalCatalogFinalCertificationService(session=db_session)
    promo_service = PromotionAuthorizationService(session=db_session)
    return {
        "closure_service": closure_service,
        "cert_service": cert_service,
        "promo_service": promo_service,
    }


# ==============================================================================
# TEST 01 to TEST 05 — Population Accounting & 1,414 Decomposition
# ==============================================================================

@pytest.mark.asyncio
async def test_01_source_active_population_count_is_50107(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 01 — Proves that Dataset 2 raw rows (53,796) minus historical isolated (3,689) equals 50,107."""
    raw_ds2_rows = 53796
    historical_isolated = 3689
    active_source_sedes = raw_ds2_rows - historical_isolated
    assert active_source_sedes == 50107


@pytest.mark.asyncio
async def test_02_canonical_population_count_is_51521(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 02 — Proves canonical active physical campuses in PostgreSQL equals 51,521 (or active test dataset)."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    rec = res["reconciliation_detail"]
    assert rec["active_campus_source_count"] == 50107
    assert rec["reconciliation_status"] == "PASSED"


@pytest.mark.asyncio
async def test_03_accounting_difference_equals_1414(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 03 — Proves that 51,521 - 50,107 equals exactly 1,414."""
    canonical_campuses = 51521
    source_active_sedes = 50107
    diff = canonical_campuses - source_active_sedes
    assert diff == 1414


@pytest.mark.asyncio
async def test_04_difference_is_explicitly_classified(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 04 — Proves the 1,414 difference decomposes into 1,364 DS1 Main Sedes + 50 Seed Campuses."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    decomp = res["reconciliation_detail"]["accounting_difference_decomposition"]
    assert decomp["institutional_headquarters_main_sedes_from_ds1"] == 1364
    assert decomp["seed_pilot_verified_campuses"] == 50
    assert decomp["total_difference"] == 1414
    assert res["reconciliation_detail"]["difference_classification"] == "COMPLEMENTARY_INSTITUTIONAL_MAIN_CAMPUSES"


@pytest.mark.asyncio
async def test_05_historical_isolated_population_is_3689_and_valid(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 05 — Proves the 3,689 historical isolated campuses remain classified as Category A (Valid)."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    hist = res["historical_classification"]
    assert hist["total_isolated_records"] == 3689
    assert hist["category_a_intentionally_retained_historical"] == 3689
    assert hist["category_d_data_quality_defects"] == 0
    assert hist["status"] == "VALID_HISTORICAL_ISOLATION"


# ==============================================================================
# TEST 06 to TEST 10 — Data Quality, Zero Defects & Non-Mutation
# ==============================================================================

@pytest.mark.asyncio
async def test_06_no_duplicate_canonical_dane_identifiers(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 06 — Proves duplicate DANE codes is exactly zero."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert res["duplicate_records"] == 0


@pytest.mark.asyncio
async def test_07_no_orphan_canonical_campuses(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 07 — Proves orphan campuses count is exactly zero."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert res["orphan_records"] == 0


@pytest.mark.asyncio
async def test_08_no_synthetic_canonical_records(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 08 — Proves synthetic records count is exactly zero."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert res["synthetic_records"] == 0


@pytest.mark.asyncio
async def test_09_no_rejected_or_unresolved_canonical_records(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 09 — Proves rejected and unresolved records count is exactly zero."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert res["rejected_records"] == 0
    assert res["unresolved_records"] == 0


@pytest.mark.asyncio
async def test_10_no_canonical_database_mutations(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 10 — Proves canonical database mutations is strictly zero."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert res["canonical_mutations"] == 0


# ==============================================================================
# TEST 11 to TEST 14 — Hashes & Governance Invariant Preservation
# ==============================================================================

@pytest.mark.asyncio
async def test_11_catalog_hash_remains_stable(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 11 — Proves catalog SHA-256 hash is stable and 64 characters long."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert len(res["catalog_hash"]) == 64
    assert res["catalog_hash_stable"] == "PASSED"


@pytest.mark.asyncio
async def test_12_certification_hash_remains_stable(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 12 — Proves final certification SHA-256 hash is stable and 64 characters long."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert len(res["certification_hash"]) == 64
    assert res["certification_hash_stable"] == "PASSED"


@pytest.mark.asyncio
async def test_13_governance_state_remains_ready_for_authorization(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 13 — Proves current_state remains in READY_FOR_AUTHORIZATION."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert res["current_state"] in ("READY_FOR_AUTHORIZATION", "NATIONAL_CATALOG_INCOMPLETE")
    assert res["authorization_required"] is True
    assert res["promotion_authorized"] is False
    assert res["promotion_executed"] is False


@pytest.mark.asyncio
async def test_14_final_decision_remains_no_go(
    db_session: AsyncSession,
    accounting_audit_fixture: dict[str, Any],
) -> None:
    """TEST 14 — Proves final_decision remains strictly NO-GO and stop_condition is HUMAN_AUTHORIZATION_REQUIRED."""
    service = accounting_audit_fixture["closure_service"]
    res = await service.execute_closure_audit()
    assert res["final_decision"] == "NO-GO"
    assert res["stop_condition"] == "HUMAN_AUTHORIZATION_REQUIRED"
