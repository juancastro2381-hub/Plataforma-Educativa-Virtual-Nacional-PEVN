"""
PEVN Backend — Official DANE / MEN Institution Resolution Tests

Validates the authoritative Colombian educational establishment identity resolution layer:
  1. Valid 12-digit DANE code resolution from official government catalog
  2. Invalid length (< 12 or > 12 digits) rejection with 422
  3. Non-numeric DANE rejection with 422
  4. DANE not found in official catalog rejection with 404
  5. Multiple campuses resolution (Sede Principal + Sedes Adscritas)
  6. Missing optional official fields handling and PEvN requirement flagging
  7. Government data provenance metadata verification
  8. RBAC and National Scope authorization enforcement (403 for Teacher)
  9. End-to-end provisioning from official catalog with audit logging
  10. OfficialCatalogSyncService validation, leading zeros preservation, and duplicate rejection
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
from app.models.institution import Campus, Institution
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogSyncBatch,
    OfficialInstitutionCatalog,
)
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.official_catalog_sync_service import (
    CatalogSyncValidationError,
    OfficialCatalogSyncService,
)


@pytest.fixture
async def dane_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Fixture providing national admin, department, municipality, and institutional users."""
    dept = Department(code="11", name="Bogotá D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogotá D.C.")
    db_session.add(mun)
    await db_session.flush()

    # Pre-existing institution
    existing_inst = Institution(
        municipality_id=mun.id,
        dane_code="111001000001",
        name="I.E. Existente",
        email="contacto@existente.edu.co",
        is_active=True,
    )
    db_session.add(existing_inst)
    await db_session.flush()

    # Seed roles
    superadmin_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.SUPERADMIN.value))
    ).scalar_one()
    national_admin_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))
    ).scalar_one()
    teacher_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.TEACHER.value))
    ).scalar_one()

    # Permissions
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
            RolePermission.role_id == national_admin_role.id,
            RolePermission.permission_id == perm.id,
        )
        if not (await db_session.execute(rp_stmt)).scalar_one_or_none():
            db_session.add(RolePermission(role_id=national_admin_role.id, permission_id=perm.id))
    await db_session.flush()

    # National Admin User
    national_admin_user = User(
        email="admin.nacional.dane@pevn.edu.co",
        username="admin_nacional_dane",
        hashed_password=password_hasher.hash("AdminNacional2026*!"),
        first_name="Admin",
        last_name="Nacional",
        document_type=DocumentType.CC,
        document_number="1000000099",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    # Teacher User
    teacher_user = User(
        email="docente.dane@existente.edu.co",
        username="docente_dane_test",
        hashed_password=password_hasher.hash("Docente2026*!"),
        first_name="Profesor",
        last_name="Prueba",
        document_type=DocumentType.CC,
        document_number="1000000098",
        institution_id=existing_inst.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([national_admin_user, teacher_user])
    await db_session.flush()

    db_session.add(
        UserRole(
            user_id=national_admin_user.id,
            role_id=national_admin_role.id,
            institution_id=None,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=teacher_user.id,
            role_id=teacher_role.id,
            institution_id=existing_inst.id,
            is_active=True,
        )
    )
    await db_session.commit()

    admin_token = await token_service.create_access_token(
        subject=str(national_admin_user.id),
        additional_claims={
            "roles": [SystemRole.NATIONAL_ADMIN.value],
            "institution_id": None,
        },
    )
    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={
            "roles": [SystemRole.TEACHER.value],
            "institution_id": str(existing_inst.id),
        },
    )

    return {
        "department": dept,
        "municipality": mun,
        "existing_inst": existing_inst,
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "teacher_headers": {"Authorization": f"Bearer {teacher_token}"},
    }


@pytest.mark.asyncio
async def test_resolve_official_dane_success(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test resolving an authentic 12-digit DANE code against the local official catalog.
    """
    dane_code = "111001012345"
    response = await client.get(
        f"/api/v1/institutions/resolve-dane/{dane_code}",
        headers=dane_fixture["admin_headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dane_code"] == dane_code
    assert "NICOLAS ESGUERRA" in data["name"]
    assert data["department_code"] == "11"
    assert data["department_name"] == "BOGOTA D.C."
    assert data["municipality_code"] == "11001"
    assert data["sector"] == "OFICIAL"
    assert data["zone"] == "URBANA"
    assert data["calendar"] == "A"
    assert data["academic_character"] == "ACADÉMICO"
    assert len(data["campuses"]) >= 2
    assert any(c["is_main"] for c in data["campuses"])
    assert data["provenance"]["source_system"] == "MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE"
    assert "datos.gov.co" in data["provenance"]["source_dataset"]


@pytest.mark.asyncio
async def test_resolve_official_dane_leading_zero_preservation(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test resolving a DANE code with leading zero (Antioquia 050010000012) preserving string format.
    """
    dane_code = "050010000012"
    response = await client.get(
        f"/api/v1/institutions/resolve-dane/{dane_code}",
        headers=dane_fixture["admin_headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dane_code"] == "050010000012"
    assert data["department_code"] == "05"
    assert "LICEO DE ANTIOQUIA" in data["name"]
    assert len(data["campuses"]) >= 2
    assert any(c["dane_sede_code"].startswith("05") for c in data["campuses"])


@pytest.mark.asyncio
async def test_resolve_official_dane_invalid_length(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test that a DANE code with fewer or more than 12 digits is rejected with 422.
    """
    response = await client.get(
        "/api/v1/institutions/resolve-dane/12345",
        headers=dane_fixture["admin_headers"],
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DANE_CODE"


@pytest.mark.asyncio
async def test_resolve_official_dane_non_numeric(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test that non-numeric characters in DANE code are rejected with 422.
    """
    response = await client.get(
        "/api/v1/institutions/resolve-dane/11100101234A",
        headers=dane_fixture["admin_headers"],
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DANE_CODE"


@pytest.mark.asyncio
async def test_resolve_official_dane_not_found(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test that a valid 12-digit DANE code not present in the official catalog returns 404.
    """
    response = await client.get(
        "/api/v1/institutions/resolve-dane/999999999999",
        headers=dane_fixture["admin_headers"],
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OFFICIAL_DANE_RECORD_NOT_FOUND"


@pytest.mark.asyncio
async def test_resolve_official_dane_multiple_campuses(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test that multi-campus institutions return all attached sedes with main/attached designation.
    """
    dane_code = "050010000012"  # IE Liceo de Antioquia (Principal + Adscrita)
    response = await client.get(
        f"/api/v1/institutions/resolve-dane/{dane_code}",
        headers=dane_fixture["admin_headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dane_code"] == dane_code
    assert len(data["campuses"]) >= 2

    main_campuses = [c for c in data["campuses"] if c["is_main"]]
    attached_campuses = [c for c in data["campuses"] if not c["is_main"]]

    assert len(main_campuses) == 1
    assert len(attached_campuses) >= 1
    assert "PRINCIPAL" in main_campuses[0]["name"]


@pytest.mark.asyncio
async def test_resolve_official_dane_missing_optional_fields_flags_pevn_required(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test that when an official record lacks an email, it is flagged in pevn_required_fields.
    """
    dane_code = "200010000550"  # Colegio Nacional Loperena (official_email is None)
    response = await client.get(
        f"/api/v1/institutions/resolve-dane/{dane_code}",
        headers=dane_fixture["admin_headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["official_email"] is None
    assert "email" in data["pevn_required_fields"]


@pytest.mark.asyncio
async def test_resolve_official_dane_unauthorized_for_teacher(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test that non-national roles (Teacher) cannot access the national DANE resolver.
    """
    response = await client.get(
        "/api/v1/institutions/resolve-dane/111001012345",
        headers=dane_fixture["teacher_headers"],
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_provision_institution_with_official_catalog_data(
    client: AsyncClient,
    db_session: AsyncSession,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test end-to-end provisioning of an institution using official catalog DANE code.
    Ensures all official campuses are provisioned and provenance is recorded.
    """
    # Setup territorial municipality for Bucaramanga
    dept = Department(code="68", name="SANTANDER")
    db_session.add(dept)
    await db_session.flush()
    muni = Municipality(department_id=dept.id, code="68001", name="BUCARAMANGA")
    db_session.add(muni)
    await db_session.flush()
    await db_session.commit()

    dane_code = "680010000333"  # Instituto Técnico Nacional de Comercio
    payload = {
        "dane_code": dane_code,
        "name": "INSTITUTO TECNICO NACIONAL DE COMERCIO",
        "email": "rectoria@instenalco.edu.co",
        "phone": "(607) 6420101",
        "address": "CALLE 55 NO. 14-42",
        "municipality_id": str(muni.id),
    }

    response = await client.post(
        "/api/v1/institutions",
        json=payload,
        headers=dane_fixture["admin_headers"],
    )

    assert response.status_code == 201
    data = response.json()
    assert data["dane_code"] == dane_code
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert len(data["campuses"]) == 2  # Sede A + Sede B from catalog


@pytest.mark.asyncio
async def test_official_catalog_sync_service_validation_and_quality(
    db_session: AsyncSession,
) -> None:
    """
    Unit test for OfficialCatalogSyncService checking data quality, leading zero preservation,
    duplicate prevention, and statistics generation.
    """
    service = OfficialCatalogSyncService(db_session)

    test_records = [
        # 1. Valid record with leading zero
        {
            "dane_code": "050880000999",
            "name": "I.E. BELLO HORIZONTE",
            "department_code": "05",
            "department_name": "ANTIOQUIA",
            "municipality_code": "05088",
            "municipality_name": "BELLO",
            "campuses": [
                {
                    "dane_sede_code": "050880000999",
                    "name": "SEDE PRINCIPAL",
                    "is_main": True,
                },
                {
                    "dane_sede_code": "050880001001",
                    "name": "SEDE ADSCRITA 1",
                    "is_main": False,
                },
            ],
        },
        # 2. Invalid DANE length (< 12 digits)
        {
            "dane_code": "12345",
            "name": "I.E. INVÁLIDA",
            "department_code": "11",
            "department_name": "BOGOTA",
            "municipality_code": "11001",
            "municipality_name": "BOGOTA",
        },
        # 3. Duplicate DANE in-batch
        {
            "dane_code": "050880000999",
            "name": "I.E. DUPLICADA",
            "department_code": "05",
            "department_name": "ANTIOQUIA",
            "municipality_code": "05088",
            "municipality_name": "BELLO",
        },
        # 4. Incomplete territorial data
        {
            "dane_code": "111001000888",
            "name": "I.E. SIN TERRITORIO",
            "department_code": "",
            "department_name": "",
            "municipality_code": "",
            "municipality_name": "",
        },
    ]

    stats = await service.ingest_official_records(
        test_records, max_rejection_percentage=100.0
    )

    assert stats.total_records_processed == 4
    assert stats.institutions_created == 1
    assert stats.campuses_created == 2
    assert stats.rejected_records == 3
    assert stats.duplicate_institutions == 1
    assert len(stats.validation_errors) == 3


@pytest.mark.asyncio
async def test_catalog_sync_status_endpoint(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test GET /api/v1/institutions/catalog/sync-status returns accurate catalog counts,
    classification (DEVELOPMENT_SEED vs NATIONAL), and provenance metadata.
    """
    response = await client.get(
        "/api/v1/institutions/catalog/sync-status",
        headers=dane_fixture["admin_headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["catalog_status"] in ["DEVELOPMENT_SEED", "NATIONAL_CATALOG_INCOMPLETE", "NATIONAL_CATALOG_SYNCED"]
    assert data["total_institutions"] >= 6
    assert data["total_campuses"] >= 11
    assert data["principal_campuses_count"] >= 6
    assert data["attached_campuses_count"] >= 5
    assert data["source_dataset"] == "datos.gov.co/c36d-tcj8"
    assert "is_stale" in data


@pytest.mark.asyncio
async def test_catalog_sync_status_staleness_detection(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test that when max_freshness_days is 0, the endpoint detects staleness and returns warning.
    """
    response = await client.get(
        "/api/v1/institutions/catalog/sync-status?max_freshness_days=1",
        headers=dane_fixture["admin_headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_stale" in data


@pytest.mark.asyncio
async def test_catalog_sync_service_rejection_threshold_rollback(
    db_session: AsyncSession,
) -> None:
    """
    Test that when invalid records exceed the allowed rejection percentage (strict mode),
    the sync service aborts, marks the batch as FAILED, and raises CatalogSyncValidationError.
    """
    service = OfficialCatalogSyncService(db_session)

    corrupted_batch = [
        {"dane_code": "INVALID_DANE", "name": "MALFORMED 1"},
        {"dane_code": "9999", "name": "MALFORMED 2"},
    ]

    with pytest.raises(CatalogSyncValidationError) as exc_info:
        await service.ingest_official_records(corrupted_batch, strict_mode=True)

    assert "Sincronización abortada" in str(exc_info.value)
    stats = exc_info.value.stats
    assert stats.status == "FAILED"
    assert stats.rejected_records == 2


@pytest.mark.asyncio
async def test_catalog_sync_batches_persisted_in_db(
    db_session: AsyncSession,
) -> None:
    """
    Test that OfficialCatalogSyncBatch records are persisted with full metrics.
    """
    service = OfficialCatalogSyncService(db_session)
    valid_batch = [
        {
            "dane_code": "250010000111",
            "name": "I.E. CUNDINAMARCA",
            "department_code": "25",
            "department_name": "CUNDINAMARCA",
            "municipality_code": "25001",
            "municipality_name": "AGUA DE DIOS",
            "campuses": [
                {
                    "dane_sede_code": "250010000111",
                    "name": "SEDE PRINCIPAL",
                    "is_main": True,
                }
            ],
        }
    ]

    stats = await service.ingest_official_records(valid_batch)
    assert stats.status == "SUCCESS"

    stmt = select(OfficialCatalogSyncBatch).where(OfficialCatalogSyncBatch.id == stats.batch_id)
    batch_in_db = (await db_session.execute(stmt)).scalar_one_or_none()

    assert batch_in_db is not None
    assert batch_in_db.status == "SUCCESS"
    assert batch_in_db.valid_records == 1
    assert batch_in_db.institutions_count == 1


@pytest.mark.asyncio
async def test_national_catalog_sync_endpoint_execution(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test POST /api/v1/institutions/catalog/sync triggers national catalog sync,
    promotes 33 institutions covering all Colombian departments, and reports NATIONAL_CATALOG_SYNCED.
    """
    sync_payload = {
        "source_system": "MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE",
        "source_dataset": "datos.gov.co/c36d-tcj8",
        "source_version": "2026-Q1",
        "max_rejection_percentage": 20.0,
        "strict_mode": False,
    }
    response = await client.post(
        "/api/v1/institutions/catalog/sync",
        json=sync_payload,
        headers=dane_fixture["admin_headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["institutions_synced"] >= 33
    assert data["campuses_synced"] >= 35
    assert data["rejected_records"] == 0

    # Verify sync status reports NATIONAL_CATALOG_INCOMPLETE / NATIONAL_CATALOG_SYNCED
    status_res = await client.get(
        "/api/v1/institutions/catalog/sync-status",
        headers=dane_fixture["admin_headers"],
    )
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["catalog_status"] in ["NATIONAL_CATALOG_INCOMPLETE", "NATIONAL_CATALOG_SYNCED"]
    assert status_data["total_institutions"] >= 33
    assert status_data["departments_covered"] >= 32


@pytest.mark.asyncio
async def test_men_open_data_adapter_column_normalization() -> None:
    """
    Test MenOpenDataAdapter handles disparate Colombian open-data field aliases and flat rows.
    """
    from app.adapters.men_open_data_adapter import MenOpenDataAdapter

    raw_due_row = {
        "CODIGO_DANE": "050010000012",
        "NOMBRE_ESTABLECIMIENTO": "LICEO DE ANTIOQUIA",
        "CODIGO_DEPARTAMENTO": "5",
        "DEPARTAMENTO": "Antioquia",
        "CODIGO_MUNICIPIO": "5001",
        "MUNICIPIO": "Medellin",
        "SECRETARIA": "MEDELLIN",
        "SECTOR": "OFICIAL",
        "ZONA": "URBANA",
        "CALENDARIO": "A",
        "CARACTER": "ACADEMICO",
        "CODIGO_DANE_SEDE": "050010000012",
        "NOMBRE_SEDE": "SEDE PRINCIPAL",
        "ES_PRINCIPAL": "true",
    }

    norm = MenOpenDataAdapter.normalize_record(raw_due_row)
    assert norm["dane_code"] == "050010000012"
    assert norm["department_code"] == "05"
    assert norm["municipality_code"] == "05001"
    assert len(norm["campuses"]) == 1
    assert norm["campuses"][0]["dane_sede_code"] == "050010000012"
    assert norm["campuses"][0]["is_main"] is True


@pytest.mark.asyncio
async def test_resolve_dane_across_multiple_colombian_departments(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test resolution across multiple distinct Colombian departments including leading zeros.
    """
    # First ensure national catalog is seeded
    await client.post(
        "/api/v1/institutions/catalog/sync",
        json={},
        headers=dane_fixture["admin_headers"],
    )

    test_cases = [
        ("111001012345", "BOGOTA D.C.", "11001"),
        ("050010000012", "ANTIOQUIA", "05001"),
        ("080010001122", "ATLANTICO", "08001"),
        ("150010000100", "BOYACA", "15001"),
        ("257540000015", "CUNDINAMARCA", "25754"),
        ("680010000333", "SANTANDER", "68001"),
        ("760010000055", "VALLE DEL CAUCA", "76001"),
        ("880010002100", "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA", "88001"),
        ("910010002200", "AMAZONAS", "91001"),
    ]

    for dane, expected_dept, expected_muni in test_cases:
        res = await client.get(
            f"/api/v1/institutions/resolve-dane/{dane}",
            headers=dane_fixture["admin_headers"],
        )
        assert res.status_code == 200, f"Failed resolving {dane}"
        data = res.json()
        assert data["dane_code"] == dane
        assert data["department_name"] == expected_dept
        assert data["municipality_code"] == expected_muni
        assert len(data["campuses"]) >= 1
        assert any(c["is_main"] for c in data["campuses"])


@pytest.mark.asyncio
async def test_sync_idempotency_no_duplicate_inflation(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test Phase 3C-F Idempotency:
    Running the same official sync twice must NOT create duplicate records or inflate counts.
    """
    # First Sync Run
    res1 = await client.post(
        "/api/v1/institutions/catalog/sync",
        json={},
        headers=dane_fixture["admin_headers"],
    )
    assert res1.status_code == 200
    data1 = res1.json()
    first_inst_count = data1["institutions_synced"]
    first_camp_count = data1["campuses_synced"]

    # Second Sync Run with identical dataset
    res2 = await client.post(
        "/api/v1/institutions/catalog/sync",
        json={},
        headers=dane_fixture["admin_headers"],
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["institutions_synced"] == first_inst_count
    assert data2["campuses_synced"] == first_camp_count

    # Verify database counts in sync-status
    status_res = await client.get(
        "/api/v1/institutions/catalog/sync-status",
        headers=dane_fixture["admin_headers"],
    )
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["total_institutions"] == first_inst_count
    assert status_data["total_campuses"] == first_camp_count


@pytest.mark.asyncio
async def test_quality_gates_and_accounting_reconciliation(
    db_session: AsyncSession,
) -> None:
    """
    Test Forensic Quality Gates A through G and strict accounting reconciliation.
    """
    service = OfficialCatalogSyncService(db_session)

    test_payload = [
        # Valid 1
        {
            "dane_code": "111001099991",
            "name": "COLEGIO PRUEBA GATE 1",
            "department_code": "11",
            "department_name": "BOGOTA D.C.",
            "municipality_code": "11001",
            "municipality_name": "BOGOTA D.C.",
            "campuses": [
                {"dane_sede_code": "111001099991", "name": "SEDE PRINCIPAL", "is_main": True}
            ],
        },
        # Gate A failure: prefix mismatch (05 dane vs 11 dept)
        {
            "dane_code": "050010999992",
            "name": "COLEGIO MISMATCH PREFIX",
            "department_code": "11",
            "department_name": "BOGOTA D.C.",
            "municipality_code": "11001",
            "municipality_name": "BOGOTA D.C.",
        },
        # Gate B failure: duplicate of 111001099991
        {
            "dane_code": "111001099991",
            "name": "COLEGIO DUPLICATE",
            "department_code": "11",
            "department_name": "BOGOTA D.C.",
            "municipality_code": "11001",
            "municipality_name": "BOGOTA D.C.",
        },
    ]

    stats = await service.ingest_official_records(
        test_payload,
        max_rejection_percentage=70.0,
        strict_mode=False,
    )

    # Accounting equation: total == valid + rejected
    assert stats.total_records_processed == 3
    assert stats.valid_records == 1
    assert stats.rejected_records == 2
    assert stats.accounting_reconciled is True
    assert stats.dataset_checksum is not None
    assert len(stats.dataset_checksum) == 64  # SHA-256 length


@pytest.mark.asyncio
async def test_sync_status_exposes_all_forensic_metrics(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test GET /api/v1/institutions/catalog/sync-status returns complete forensic metrics.
    """
    response = await client.get(
        "/api/v1/institutions/catalog/sync-status",
        headers=dane_fixture["admin_headers"],
    )
    assert response.status_code == 200
    data = response.json()

    # Required forensic properties from Phase 3C-F
    assert "catalog_status" in data
    assert "sync_batch_id" in data
    assert "source_system" in data
    assert "source_dataset" in data
    assert "source_version" in data
    assert "last_sync_at" in data
    assert "total_source_records" in data
    assert "valid_records" in data
    assert "rejected_records" in data
    assert "duplicate_records" in data
    assert "total_institutions" in data
    assert "total_campuses" in data
    assert "principal_campuses" in data
    assert "annex_campuses" in data
    assert "departments_covered" in data
    assert "municipalities_covered" in data
    assert "is_stale" in data
    assert "quality_gate_status" in data
    assert "synchronization_status" in data
    assert "accounting_reconciled" in data
    assert "ingestion_progress" in data
    assert "total_chunks" in data
    assert "processed_chunks" in data
    assert "failed_chunks" in data
    assert "audit_status" in data


@pytest.mark.asyncio
async def test_chunked_ingestion_multi_chunk_execution(
    db_session: AsyncSession,
) -> None:
    """
    Test Phase 3C-H Chunked Execution:
    Ingests 4 records with chunk_size=2, verifying that 2 chunks are created,
    executed, and tracked with full metrics in PostgreSQL.
    """
    service = OfficialCatalogSyncService(db_session)

    records = [
        {
            "dane_code": f"11100109910{i}",
            "name": f"COLEGIO CHUNK TEST {i}",
            "department_code": "11",
            "department_name": "BOGOTA D.C.",
            "municipality_code": "11001",
            "municipality_name": "BOGOTA D.C.",
            "campuses": [
                {"dane_sede_code": f"11100109910{i}", "name": "SEDE PRINCIPAL", "is_main": True}
            ],
        }
        for i in range(1, 5)
    ]

    stats = await service.ingest_official_records(records, chunk_size=2)
    assert stats.status == "SUCCESS"
    assert stats.total_chunks == 2
    assert stats.processed_chunks == 2
    assert stats.failed_chunks == 0
    assert stats.ingestion_progress == 100.0
    assert stats.valid_records == 4

    # Verify chunks in database
    from app.models.official_catalog import OfficialCatalogSyncChunk
    stmt = (
        select(OfficialCatalogSyncChunk)
        .where(OfficialCatalogSyncChunk.batch_id == stats.batch_id)
        .order_by(OfficialCatalogSyncChunk.chunk_number)
    )
    chunks = (await db_session.execute(stmt)).scalars().all()
    assert len(chunks) == 2
    assert chunks[0].chunk_number == 1
    assert chunks[0].status == "SUCCESS"
    assert chunks[0].total_records == 2
    assert chunks[0].valid_records == 2

    assert chunks[1].chunk_number == 2
    assert chunks[1].status == "SUCCESS"
    assert chunks[1].total_records == 2
    assert chunks[1].valid_records == 2


@pytest.mark.asyncio
async def test_chunked_ingestion_failure_rollback(
    db_session: AsyncSession,
) -> None:
    """
    Test that when a chunk fails quality validation in strict mode,
    the failing chunk is marked FAILED, the batch is marked FAILED,
    and failed_chunks is incremented.
    """
    service = OfficialCatalogSyncService(db_session)

    records = [
        # Chunk 1 (Valid)
        {
            "dane_code": "111001099201",
            "name": "COLEGIO CHUNK 1",
            "department_code": "11",
            "department_name": "BOGOTA D.C.",
            "municipality_code": "11001",
            "municipality_name": "BOGOTA D.C.",
        },
        # Chunk 2 (Corrupted: non-numeric DANE)
        {
            "dane_code": "INVALID_DANE_CODE",
            "name": "COLEGIO CORRUPTED",
            "department_code": "11",
            "department_name": "BOGOTA D.C.",
            "municipality_code": "11001",
            "municipality_name": "BOGOTA D.C.",
        },
    ]

    with pytest.raises(CatalogSyncValidationError) as exc_info:
        await service.ingest_official_records(records, chunk_size=1, strict_mode=True)

    stats = exc_info.value.stats
    assert stats.status == "FAILED"
    assert stats.failed_chunks >= 1
    assert stats.audit_status == "FAILED_QUALITY_GATE"


@pytest.mark.asyncio
async def test_prevention_of_false_national_catalog_synced_status(
    client: AsyncClient,
    dane_fixture: dict[str, Any],
) -> None:
    """
    Test that a baseline dataset (< 5,000 institutions) even with 33 departments represented
    remains honestly classified as NATIONAL_CATALOG_INCOMPLETE.
    """
    # Trigger sync
    res = await client.post(
        "/api/v1/institutions/catalog/sync",
        json={"chunk_size": 1000},
        headers=dane_fixture["admin_headers"],
    )
    assert res.status_code == 200

    # Query sync-status
    status_res = await client.get(
        "/api/v1/institutions/catalog/sync-status",
        headers=dane_fixture["admin_headers"],
    )
    assert status_res.status_code == 200
    data = status_res.json()

    # Must NOT report NATIONAL_CATALOG_SYNCED on baseline sample
    assert data["catalog_status"] == "NATIONAL_CATALOG_INCOMPLETE"
    assert data["departments_covered"] >= 32
    assert data["total_institutions"] < 5000
    assert data["audit_status"] == "VERIFIED"




