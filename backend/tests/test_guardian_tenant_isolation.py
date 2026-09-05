"""
PEVN Backend — Multi-Tenant Guardian Isolation Security Test Suite (Phase 13E.4)

Authoritative verification of server-side data isolation for the Legal Guardian (Acudiente) domain:
  - TEST-GUARDIAN-TENANT-01: Institution A only sees Institution A Guardians.
  - TEST-GUARDIAN-TENANT-02: Institution B initially sees [].
  - TEST-GUARDIAN-TENANT-03: Institution B sees only its own newly-created Guardians.
  - TEST-GUARDIAN-TENANT-04: Institution A cannot retrieve Institution B Guardian by ID (404 Not Found).
  - TEST-GUARDIAN-TENANT-05: Institution B cannot retrieve Institution A Guardian by ID (404 Not Found).
  - TEST-GUARDIAN-TENANT-06: Cross-tenant Guardian/Student relationship is rejected (404 Not Found).
  - TEST-GUARDIAN-TENANT-07: Guardian search is institutionally scoped.
  - TEST-GUARDIAN-TENANT-08: Guardian creation derives institutional ownership from authenticated context.
  - TEST-GUARDIAN-TENANT-09: Guardian update/link cannot change institutional ownership.
  - TEST-GUARDIAN-TENANT-10: Student Guardians endpoint is tenant scoped.
"""

from __future__ import annotations

from datetime import date
from typing import Any
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.tokens import token_service
from app.models.guardian import Guardian, GuardianRelationshipType, StudentGuardian
from app.models.institution import Institution
from app.models.role import Role, UserRole
from app.models.student import Student, StudentGender
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


@pytest.fixture
async def tenant_isolation_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """
    Sets up two completely isolated institutions:
      - Institution A with Rector A, Student A1, Student A2, Guardian A1, Guardian A2
      - Institution B with Rector B, Student B1 (initially zero guardians)
    """
    # 1. Ensure RBAC roles and permissions are bootstrapped
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    dept = Department(code=f"D{uuid.uuid4().hex[:4]}", name="Bogota D.C.")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, code=f"M{uuid.uuid4().hex[:4]}", name="Bogota")
    db_session.add(muni)
    await db_session.flush()

    role_rector = (
        await db_session.execute(select(Role).where(Role.name == "rector"))
    ).scalar_one()

    # 2. Institution A
    inst_a = Institution(
        municipality_id=muni.id,
        name="Institución Educativa Tenant A",
        dane_code=f"110001{uuid.uuid4().hex[:6]}",
        address="Calle 100 # 10-20, Bogotá",
        phone="3101112233",
        email=f"rector_a_{uuid.uuid4().hex[:6]}@colegio-a.edu.co",
        is_active=True,
    )
    # 3. Institution B
    inst_b = Institution(
        municipality_id=muni.id,
        name="Institución Educativa Tenant B",
        dane_code=f"110002{uuid.uuid4().hex[:6]}",
        address="Carrera 50 # 30-40, Medellín",
        phone="3109998877",
        email=f"rector_b_{uuid.uuid4().hex[:6]}@colegio-b.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    # Users: Rector A and Rector B
    rector_a = User(
        email=f"rector_a_{uuid.uuid4().hex[:6]}@colegio-a.edu.co",
        username=f"rector_a_{uuid.uuid4().hex[:6]}",
        hashed_password="placeholder_hash",
        first_name="Rector",
        last_name="Alpha",
        document_type=DocumentType.CC,
        document_number=f"70{uuid.uuid4().hex[:6]}",
        institution_id=inst_a.id,
        is_active=True,
    )
    rector_b = User(
        email=f"rector_b_{uuid.uuid4().hex[:6]}@colegio-b.edu.co",
        username=f"rector_b_{uuid.uuid4().hex[:6]}",
        hashed_password="placeholder_hash",
        first_name="Rector",
        last_name="Beta",
        document_type=DocumentType.CC,
        document_number=f"80{uuid.uuid4().hex[:6]}",
        institution_id=inst_b.id,
        is_active=True,
    )
    db_session.add_all([rector_a, rector_b])
    await db_session.flush()

    # User Roles
    db_session.add(
        UserRole(
            user_id=rector_a.id,
            role_id=role_rector.id,
            institution_id=inst_a.id,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=rector_b.id,
            role_id=role_rector.id,
            institution_id=inst_b.id,
            is_active=True,
        )
    )

    # Students in Inst A
    student_user_a1 = User(
        email=f"stu_a1_{uuid.uuid4().hex[:6]}@colegio-a.edu.co",
        username=f"stu_a1_{uuid.uuid4().hex[:6]}",
        hashed_password="placeholder_hash",
        first_name="Estudiante",
        last_name="A Uno",
        document_type=DocumentType.TI,
        document_number=f"100{uuid.uuid4().hex[:6]}",
        institution_id=inst_a.id,
    )
    student_user_a2 = User(
        email=f"stu_a2_{uuid.uuid4().hex[:6]}@colegio-a.edu.co",
        username=f"stu_a2_{uuid.uuid4().hex[:6]}",
        hashed_password="placeholder_hash",
        first_name="Estudiante",
        last_name="A Dos",
        document_type=DocumentType.TI,
        document_number=f"101{uuid.uuid4().hex[:6]}",
        institution_id=inst_a.id,
    )
    # Student in Inst B
    student_user_b1 = User(
        email=f"stu_b1_{uuid.uuid4().hex[:6]}@colegio-b.edu.co",
        username=f"stu_b1_{uuid.uuid4().hex[:6]}",
        hashed_password="placeholder_hash",
        first_name="Estudiante",
        last_name="B Uno",
        document_type=DocumentType.TI,
        document_number=f"200{uuid.uuid4().hex[:6]}",
        institution_id=inst_b.id,
    )
    db_session.add_all([student_user_a1, student_user_a2, student_user_b1])
    await db_session.flush()

    student_a1 = Student(
        user_id=student_user_a1.id,
        institution_id=inst_a.id,
        code_simat=f"SIMAT-A1-{uuid.uuid4().hex[:6]}",
        birth_date=date(2010, 3, 15),
        gender=StudentGender.M,
    )
    student_a2 = Student(
        user_id=student_user_a2.id,
        institution_id=inst_a.id,
        code_simat=f"SIMAT-A2-{uuid.uuid4().hex[:6]}",
        birth_date=date(2010, 6, 20),
        gender=StudentGender.F,
    )
    student_b1 = Student(
        user_id=student_user_b1.id,
        institution_id=inst_b.id,
        code_simat=f"SIMAT-B1-{uuid.uuid4().hex[:6]}",
        birth_date=date(2010, 9, 10),
        gender=StudentGender.M,
    )
    db_session.add_all([student_a1, student_a2, student_b1])
    await db_session.flush()

    # Pre-register 2 Guardians under Institution A
    guardian_a1 = Guardian(
        institution_id=inst_a.id,
        first_name="Acudiente",
        last_name="Alpha Uno",
        document_type=DocumentType.CC,
        document_number=f"51{uuid.uuid4().hex[:6]}",
        phone="3110000001",
        email=f"guardian_a1_{uuid.uuid4().hex[:4]}@correo.com",
        relationship_type=GuardianRelationshipType.MADRE,
    )
    guardian_a2 = Guardian(
        institution_id=inst_a.id,
        first_name="Acudiente",
        last_name="Alpha Dos",
        document_type=DocumentType.CC,
        document_number=f"52{uuid.uuid4().hex[:6]}",
        phone="3110000002",
        email=f"guardian_a2_{uuid.uuid4().hex[:4]}@correo.com",
        relationship_type=GuardianRelationshipType.PADRE,
    )
    db_session.add_all([guardian_a1, guardian_a2])
    await db_session.flush()

    # Link Guardian A1 -> Student A1
    link_a1 = StudentGuardian(
        student_id=student_a1.id,
        guardian_id=guardian_a1.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
        is_authorized_pickup=True,
    )
    db_session.add(link_a1)
    await db_session.commit()

    # Generate auth tokens
    token_rector_a = await token_service.create_access_token(
        subject=str(rector_a.id),
        additional_claims={"roles": ["rector"], "institution_id": str(inst_a.id)},
    )
    token_rector_b = await token_service.create_access_token(
        subject=str(rector_b.id),
        additional_claims={"roles": ["rector"], "institution_id": str(inst_b.id)},
    )

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "rector_a": rector_a,
        "rector_b": rector_b,
        "rector_a_headers": {"Authorization": f"Bearer {token_rector_a}"},
        "rector_b_headers": {"Authorization": f"Bearer {token_rector_b}"},
        "student_a1": student_a1,
        "student_a2": student_a2,
        "student_b1": student_b1,
        "guardian_a1": guardian_a1,
        "guardian_a2": guardian_a2,
    }


# ===========================================================================
# 1. TEST-GUARDIAN-TENANT-01: Institution A only sees Institution A Guardians
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_01_institution_a_lists_only_its_guardians(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-01: Rector A lists guardians and receives strictly Inst A guardians."""
    headers_a = tenant_isolation_fixture["rector_a_headers"]
    inst_a = tenant_isolation_fixture["inst_a"]
    guardian_a1 = tenant_isolation_fixture["guardian_a1"]
    guardian_a2 = tenant_isolation_fixture["guardian_a2"]

    res = await client.get("/api/v1/guardians", headers=headers_a)
    assert res.status_code == 200
    data = res.json()
    items = data["items"]

    assert len(items) >= 2
    returned_ids = [item["id"] for item in items]
    assert str(guardian_a1.id) in returned_ids
    assert str(guardian_a2.id) in returned_ids

    # All returned guardians must belong to Institution A
    for item in items:
        assert item["institution_id"] == str(inst_a.id)


# ===========================================================================
# 2. TEST-GUARDIAN-TENANT-02: Institution B initially sees []
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_02_institution_b_initially_sees_empty_list(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-02: Rector B opens module and sees [] (zero guardians from Inst A)."""
    headers_b = tenant_isolation_fixture["rector_b_headers"]
    guardian_a1 = tenant_isolation_fixture["guardian_a1"]
    guardian_a2 = tenant_isolation_fixture["guardian_a2"]

    res = await client.get("/api/v1/guardians", headers=headers_b)
    assert res.status_code == 200
    data = res.json()

    assert data["total"] == 0
    assert data["items"] == []

    # Verify explicitly that neither Guardian A1 nor A2 is leaked
    returned_ids = [item["id"] for item in data["items"]]
    assert str(guardian_a1.id) not in returned_ids
    assert str(guardian_a2.id) not in returned_ids


# ===========================================================================
# 3. TEST-GUARDIAN-TENANT-03: Institution B sees only its own newly-created Guardians
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_03_institution_b_creates_and_sees_only_own_guardians(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-03: Rector B creates Guardian B1 and verifies strict tenant partition."""
    headers_a = tenant_isolation_fixture["rector_a_headers"]
    headers_b = tenant_isolation_fixture["rector_b_headers"]
    inst_b = tenant_isolation_fixture["inst_b"]
    guardian_a1 = tenant_isolation_fixture["guardian_a1"]

    # 1. Rector B creates Guardian B1
    create_payload = {
        "first_name": "Bernardo",
        "last_name": "Beta",
        "document_type": "CC",
        "document_number": f"60{uuid.uuid4().hex[:6]}",
        "phone": "3205559999",
        "email": "bernardo.beta@correo.com",
        "address": "Avenida El Poblado # 10-50",
        "relationship_type": "PADRE",
    }
    create_res = await client.post("/api/v1/guardians", json=create_payload, headers=headers_b)
    assert create_res.status_code == 201
    guardian_b1 = create_res.json()
    assert guardian_b1["institution_id"] == str(inst_b.id)

    # 2. Rector B queries list -> sees [B1] only
    list_b_res = await client.get("/api/v1/guardians", headers=headers_b)
    assert list_b_res.status_code == 200
    items_b = list_b_res.json()["items"]
    assert len(items_b) == 1
    assert items_b[0]["id"] == guardian_b1["id"]
    assert items_b[0]["institution_id"] == str(inst_b.id)

    # 3. Rector A queries list -> sees [A1, A2] only (never B1)
    list_a_res = await client.get("/api/v1/guardians", headers=headers_a)
    assert list_a_res.status_code == 200
    items_a = list_a_res.json()["items"]
    ids_a = [i["id"] for i in items_a]
    assert guardian_b1["id"] not in ids_a
    assert str(guardian_a1.id) in ids_a


# ===========================================================================
# 4. TEST-GUARDIAN-TENANT-04: Institution A cannot retrieve Institution B Guardian by ID (404)
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_04_institution_a_cannot_access_guardian_b_by_id(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-04: Cross-tenant direct ID access from Inst A to Guardian B returns 404."""
    headers_a = tenant_isolation_fixture["rector_a_headers"]
    headers_b = tenant_isolation_fixture["rector_b_headers"]

    # Create Guardian B under Inst B
    create_res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Beatriz",
            "last_name": "Benitez",
            "document_type": "CC",
            "document_number": f"61{uuid.uuid4().hex[:6]}",
            "phone": "3201112233",
            "email": "beatriz.b@correo.com",
            "relationship_type": "MADRE",
        },
        headers=headers_b,
    )
    assert create_res.status_code == 201
    guardian_b_id = create_res.json()["id"]

    # Rector A attempts direct access to Guardian B
    get_res = await client.get(f"/api/v1/guardians/{guardian_b_id}", headers=headers_a)
    assert get_res.status_code == 404
    error_json = get_res.json()
    assert error_json.get("error", {}).get("code") == "GUARDIAN_NOT_FOUND" or "error" in error_json


# ===========================================================================
# 5. TEST-GUARDIAN-TENANT-05: Institution B cannot retrieve Institution A Guardian by ID (404)
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_05_institution_b_cannot_access_guardian_a_by_id(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-05: Cross-tenant direct ID access from Inst B to Guardian A returns 404."""
    headers_b = tenant_isolation_fixture["rector_b_headers"]
    guardian_a1 = tenant_isolation_fixture["guardian_a1"]

    # Rector B attempts direct access to Guardian A1
    get_res = await client.get(f"/api/v1/guardians/{guardian_a1.id}", headers=headers_b)
    assert get_res.status_code == 404
    error_json = get_res.json()
    assert error_json.get("error", {}).get("code") == "GUARDIAN_NOT_FOUND" or "error" in error_json


# ===========================================================================
# 6. TEST-GUARDIAN-TENANT-06: Cross-tenant Guardian/Student relationship is rejected (404)
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_06_cross_tenant_association_rejected(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-06: Linking Guardian A to Student B or Guardian B to Student A is blocked (404)."""
    headers_a = tenant_isolation_fixture["rector_a_headers"]
    headers_b = tenant_isolation_fixture["rector_b_headers"]
    student_a1 = tenant_isolation_fixture["student_a1"]
    student_b1 = tenant_isolation_fixture["student_b1"]
    guardian_a1 = tenant_isolation_fixture["guardian_a1"]

    # 1. Rector A attempts to link Guardian A1 to Student B1 (Student in another institution)
    res_a_to_b = await client.post(
        f"/api/v1/guardians/{guardian_a1.id}/students/{student_b1.id}",
        json={"relationship_type": "MADRE", "is_primary_contact": True, "is_authorized_pickup": True},
        headers=headers_a,
    )
    assert res_a_to_b.status_code == 404

    # 2. Rector B attempts to link Guardian A1 (Guardian in another institution) to Student B1
    res_b_to_a = await client.post(
        f"/api/v1/guardians/{guardian_a1.id}/students/{student_b1.id}",
        json={"relationship_type": "PADRE", "is_primary_contact": True, "is_authorized_pickup": True},
        headers=headers_b,
    )
    assert res_b_to_a.status_code == 404

    # 3. Rector A attempts to link Guardian A1 to Student A1 -> Allowed (201 or conflict if already linked)
    student_a2 = tenant_isolation_fixture["student_a2"]
    res_valid = await client.post(
        f"/api/v1/guardians/{guardian_a1.id}/students/{student_a2.id}",
        json={"relationship_type": "MADRE", "is_primary_contact": True, "is_authorized_pickup": True},
        headers=headers_a,
    )
    assert res_valid.status_code == 201


# ===========================================================================
# 7. TEST-GUARDIAN-TENANT-07: Guardian search is institutionally scoped
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_07_search_is_institutionally_scoped(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-07: Search by document number only returns matches within caller's institution."""
    headers_a = tenant_isolation_fixture["rector_a_headers"]
    headers_b = tenant_isolation_fixture["rector_b_headers"]
    guardian_a1 = tenant_isolation_fixture["guardian_a1"]

    shared_prefix = guardian_a1.document_number[:6]

    # Rector A searches with prefix -> finds Guardian A1
    res_a = await client.get(f"/api/v1/guardians?document_number={shared_prefix}", headers=headers_a)
    assert res_a.status_code == 200
    ids_a = [g["id"] for g in res_a.json()["items"]]
    assert str(guardian_a1.id) in ids_a

    # Rector B searches with same prefix -> returns []
    res_b = await client.get(f"/api/v1/guardians?document_number={shared_prefix}", headers=headers_b)
    assert res_b.status_code == 200
    assert res_b.json()["items"] == []


# ===========================================================================
# 8. TEST-GUARDIAN-TENANT-08: Guardian creation derives institutional ownership from authenticated context
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_08_creation_derives_authenticated_institution(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-08: Client cannot inject a forged institution_id during creation."""
    headers_a = tenant_isolation_fixture["rector_a_headers"]
    inst_a = tenant_isolation_fixture["inst_a"]
    inst_b = tenant_isolation_fixture["inst_b"]

    # Rector A attempts to create a guardian while attempting to spoof institution_id override to Inst B
    # Non-superadmin callers have query override ignored by _resolve_institution_id
    payload = {
        "first_name": "Camila",
        "last_name": "Castillo",
        "document_type": "CC",
        "document_number": f"75{uuid.uuid4().hex[:6]}",
        "phone": "3155554321",
        "email": "camila.c@correo.com",
        "relationship_type": "MADRE",
    }
    res = await client.post(
        f"/api/v1/guardians?institution_id={inst_b.id}",
        json=payload,
        headers=headers_a,
    )
    assert res.status_code == 201
    created_guardian = res.json()

    # Ownership MUST be derived from Rector A's token (inst_a.id), NOT the spoofed inst_b.id
    assert created_guardian["institution_id"] == str(inst_a.id)
    assert created_guardian["institution_id"] != str(inst_b.id)


# ===========================================================================
# 9. TEST-GUARDIAN-TENANT-09: Guardian update/link cannot change institutional ownership
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_09_institution_ownership_immutable(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-09: Linking student does not alter guardian's immutable institutional ownership."""
    headers_a = tenant_isolation_fixture["rector_a_headers"]
    inst_a = tenant_isolation_fixture["inst_a"]
    guardian_a2 = tenant_isolation_fixture["guardian_a2"]
    student_a1 = tenant_isolation_fixture["student_a1"]

    # Link Guardian A2 to Student A1
    link_res = await client.post(
        f"/api/v1/guardians/{guardian_a2.id}/students/{student_a1.id}",
        json={"relationship_type": "PADRE", "is_primary_contact": False, "is_authorized_pickup": True},
        headers=headers_a,
    )
    assert link_res.status_code == 201

    # Fetch Guardian A2 again and confirm institution_id is intact
    get_res = await client.get(f"/api/v1/guardians/{guardian_a2.id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["institution_id"] == str(inst_a.id)


# ===========================================================================
# 10. TEST-GUARDIAN-TENANT-10: Student Guardians endpoint is tenant scoped
# ===========================================================================


@pytest.mark.asyncio
async def test_guardian_tenant_10_student_guardians_endpoint_is_tenant_scoped(
    client: AsyncClient,
    tenant_isolation_fixture: dict[str, Any],
) -> None:
    """TEST-GUARDIAN-TENANT-10: GET /students/{id}/guardians is strictly isolated per tenant."""
    headers_a = tenant_isolation_fixture["rector_a_headers"]
    headers_b = tenant_isolation_fixture["rector_b_headers"]
    student_a1 = tenant_isolation_fixture["student_a1"]

    # 1. Rector A can query guardians of Student A1 -> 200 OK with records
    res_a = await client.get(f"/api/v1/students/{student_a1.id}/guardians", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert len(data_a) >= 1
    assert data_a[0]["student_id"] == str(student_a1.id)

    # 2. Rector B attempts to query guardians of Student A1 (cross-tenant) -> 404 Not Found
    res_b = await client.get(f"/api/v1/students/{student_a1.id}/guardians", headers=headers_b)
    assert res_b.status_code == 404
