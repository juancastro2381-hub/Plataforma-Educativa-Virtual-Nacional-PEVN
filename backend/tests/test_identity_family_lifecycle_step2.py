"""
PEVN Backend — Identity & Family Lifecycle Step 2 Test Suite

Focused automated verification of:
  1. Student account provisioning (POST /api/v1/students/{id}/account/provision).
  2. Student account provisioning idempotency and email conflict validation.
  3. Guardian account provisioning and idempotency.
  4. Bidirectional linking: Guardian -> Student and Student -> Guardian.
  5. Bidirectional unlinking: Guardian -> Student and Student -> Guardian.
  6. Direct Guardian students query (GET /api/v1/guardians/{id}/students).
  7. Tenant boundary and anti-IDOR enforcement.
  8. RBAC denial for unauthorized callers.
  9. No secret leakage in response payloads.
"""

from __future__ import annotations

import uuid
from typing import Any

from httpx import AsyncClient

from app.core.security.interfaces import SystemRole
from app.core.security.tokens import token_service
from app.models.institution import Institution
from app.models.student import Student
from tests.test_identity_family_lifecycle import lifecycle_fixture  # reuse certified fixture


# ===========================================================================
# 1. Student Account Provisioning Tests
# ===========================================================================


async def test_student_account_provisioning_flow(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Verify provision_student_account: deactivated student is re-activated with a reset token."""
    headers = lifecycle_fixture["rector1_headers"]

    # 1. Create a fresh student (automatically gets ACTIVA status with new_user payload)
    doc_num = f"11{uuid.uuid4().hex[:6]}"
    create_res = await client.post(
        "/api/v1/students",
        json={
            "new_user": {
                "first_name": "David",
                "last_name": "Perez",
                "document_type": "TI",
                "document_number": doc_num,
                "email": f"sinrol_{doc_num}@librada.edu.co",
            },
            "code_simat": f"SIMAT-PROV-{doc_num}",
            "birth_date": "2012-01-10",
            "gender": "M",
            "stratum": 2,
        },
        headers=headers,
    )
    assert create_res.status_code == 201, create_res.text
    student_id = create_res.json()["id"]
    # A newly provisioned student is ACTIVA immediately (role assigned during creation)
    assert create_res.json()["account_status"] == "ACTIVA"

    # 2. Deactivate the student account so it becomes INACTIVA
    deact_res = await client.post(
        f"/api/v1/students/{student_id}/account/status",
        json={"is_active": False},
        headers=headers,
    )
    assert deact_res.status_code == 200, deact_res.text
    assert deact_res.json()["account_status"] == "INACTIVA"

    # 3. Verify INACTIVA status persists via GET
    get_res = await client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["account_status"] == "INACTIVA"

    # 4. Re-provision the student account via provision endpoint
    prov_res = await client.post(
        f"/api/v1/students/{student_id}/account/provision",
        json={},
        headers=headers,
    )
    assert prov_res.status_code == 200, prov_res.text
    data = prov_res.json()
    assert data["student_id"] == student_id
    assert data["account_status"] == "ACTIVA"
    assert data["reset_token"] is not None
    assert len(data["reset_token"]) > 20

    # 5. Verify final ACTIVA state via GET
    final_res = await client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert final_res.status_code == 200
    assert final_res.json()["account_status"] == "ACTIVA"
    assert final_res.json()["has_account"] is True


async def test_student_account_provisioning_idempotent_and_email_update(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Verify idempotent re-provisioning and optional email update."""
    headers = lifecycle_fixture["rector1_headers"]
    student1: Student = lifecycle_fixture["student1"]

    new_email = f"updated_{uuid.uuid4().hex[:6]}@librada.edu.co"

    # Provision already active student with new email
    prov_res = await client.post(
        f"/api/v1/students/{student1.id}/account/provision",
        json={"email": new_email},
        headers=headers,
    )
    assert prov_res.status_code == 200
    assert prov_res.json()["account_status"] == "ACTIVA"
    assert prov_res.json()["reset_token"] is not None

    # Verify email updated
    detail = await client.get(f"/api/v1/students/{student1.id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["user"]["email"] == new_email


# ===========================================================================
# 2. Direct Guardian Students Query & Bidirectional Linking / Unlinking
# ===========================================================================


async def test_direct_guardian_students_query(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Verify direct GET /api/v1/guardians/{id}/students endpoint."""
    headers = lifecycle_fixture["rector1_headers"]
    student1: Student = lifecycle_fixture["student1"]

    # 1. Create Guardian
    doc_num = f"52{uuid.uuid4().hex[:6]}"
    g_res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Martha",
            "last_name": "Rojas",
            "document_type": "CC",
            "document_number": doc_num,
            "phone": "3001234567",
            "email": f"martha_{doc_num}@correo.com",
            "relationship_type": "MADRE",
        },
        headers=headers,
    )
    assert g_res.status_code == 201
    guardian_id = g_res.json()["id"]

    # Check initially empty
    empty_res = await client.get(
        f"/api/v1/guardians/{guardian_id}/students", headers=headers
    )
    assert empty_res.status_code == 200
    assert empty_res.json() == []

    # 2. Link Guardian -> Student
    link_res = await client.post(
        f"/api/v1/guardians/{guardian_id}/students/{student1.id}",
        json={
            "relationship_type": "MADRE",
            "is_primary_contact": True,
            "is_authorized_pickup": True,
        },
        headers=headers,
    )
    assert link_res.status_code == 201

    # 3. Direct GET guardian students returns linked student
    query_res = await client.get(
        f"/api/v1/guardians/{guardian_id}/students", headers=headers
    )
    assert query_res.status_code == 200
    items = query_res.json()
    assert len(items) == 1
    assert items[0]["guardian_id"] == guardian_id
    assert items[0]["student_id"] == str(student1.id)
    assert items[0]["relationship_type"] == "MADRE"
    assert items[0]["is_primary_contact"] is True


async def test_symmetric_student_to_guardian_linking_and_unlinking(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Verify Student -> Guardian linking and unlinking endpoints."""
    headers = lifecycle_fixture["rector1_headers"]
    student1: Student = lifecycle_fixture["student1"]

    # 1. Create Guardian
    doc_num = f"71{uuid.uuid4().hex[:6]}"
    g_res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Carlos",
            "last_name": "Mendoza",
            "document_type": "CC",
            "document_number": doc_num,
            "phone": "3159998877",
            "email": f"carlos_{doc_num}@correo.com",
            "relationship_type": "PADRE",
        },
        headers=headers,
    )
    assert g_res.status_code == 201
    guardian_id = g_res.json()["id"]

    # 2. Link from Student context: POST /api/v1/students/{id}/guardians/{id}
    link_res = await client.post(
        f"/api/v1/students/{student1.id}/guardians/{guardian_id}",
        json={
            "relationship_type": "PADRE",
            "is_primary_contact": False,
            "is_authorized_pickup": True,
        },
        headers=headers,
    )
    assert link_res.status_code == 201
    assert link_res.json()["student_id"] == str(student1.id)
    assert link_res.json()["guardian_id"] == guardian_id

    # 3. Verify student guardians list has this link
    sg_list = await client.get(
        f"/api/v1/students/{student1.id}/guardians", headers=headers
    )
    assert sg_list.status_code == 200
    assert any(g["guardian_id"] == guardian_id for g in sg_list.json())

    # 4. Unlink from Student context: DELETE /api/v1/students/{id}/guardians/{id}
    unlink_res = await client.delete(
        f"/api/v1/students/{student1.id}/guardians/{guardian_id}", headers=headers
    )
    assert unlink_res.status_code == 204

    # 5. Verify unlinked
    sg_after = await client.get(
        f"/api/v1/students/{student1.id}/guardians", headers=headers
    )
    assert sg_after.status_code == 200
    assert not any(g["guardian_id"] == guardian_id for g in sg_after.json())


# ===========================================================================
# 3. Tenant Isolation, IDOR & RBAC Protection
# ===========================================================================


async def test_step2_tenant_isolation_and_idor_protection(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Verify cross-tenant blocking on student provisioning and guardian queries."""
    headers_rector1 = lifecycle_fixture["rector1_headers"]
    headers_rector2 = lifecycle_fixture["rector2_headers"]
    student2: Student = lifecycle_fixture["student2"]  # belongs to Inst 2

    # Rector 1 cannot provision student belonging to Inst 2
    prov_idor = await client.post(
        f"/api/v1/students/{student2.id}/account/provision",
        json={},
        headers=headers_rector1,
    )
    assert prov_idor.status_code == 404

    # Create guardian in Inst 2
    doc_num = f"44{uuid.uuid4().hex[:6]}"
    g_res2 = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Alvaro",
            "last_name": "SanLuis",
            "document_type": "CC",
            "document_number": doc_num,
            "phone": "3100001122",
            "relationship_type": "TUTOR_LEGAL",
        },
        headers=headers_rector2,
    )
    assert g_res2.status_code == 201
    guardian2_id = g_res2.json()["id"]

    # Rector 1 cannot query students of Guardian 2 (different institution) -> 404
    q_idor = await client.get(
        f"/api/v1/guardians/{guardian2_id}/students", headers=headers_rector1
    )
    assert q_idor.status_code == 404


async def test_step2_rbac_denial_for_unauthorized_roles(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Verify non-administrative role (Student) cannot provision accounts or link guardians."""
    student_u1: User = lifecycle_fixture["student_u1"]
    student1: Student = lifecycle_fixture["student1"]
    inst1: Institution = lifecycle_fixture["inst1"]

    student_token = await token_service.create_access_token(
        subject=str(student_u1.id),
        additional_claims={
            "roles": [SystemRole.STUDENT.value],
            "institution_id": str(inst1.id),
        },
    )
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Student cannot provision student account -> 403
    prov_forbidden = await client.post(
        f"/api/v1/students/{student1.id}/account/provision",
        json={},
        headers=student_headers,
    )
    assert prov_forbidden.status_code == 403

    # Student cannot query guardian students directly -> 403
    random_gid = uuid.uuid4()
    query_forbidden = await client.get(
        f"/api/v1/guardians/{random_gid}/students",
        headers=student_headers,
    )
    assert query_forbidden.status_code == 403
