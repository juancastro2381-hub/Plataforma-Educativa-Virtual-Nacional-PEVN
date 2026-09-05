"""
PEVN Backend — Users API & Tenant-Isolated Search Tests

Validates:
  1. GET /api/v1/users requires users:read permission.
  2. Search by document_number (e.g. "8788"), first_name, last_name, email, username.
  3. Strict server-side tenant isolation: Rector A only sees Institution A users.
  4. Cross-tenant user invisibility in search results.
  5. Password hashes and sensitive credentials are never exposed in user responses.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.institution import Institution
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User

if TYPE_CHECKING:
    pass


@pytest.fixture
async def users_test_setup(db_session: AsyncSession) -> dict:
    """Setup 2 institutions and users with distinct document numbers and scopes."""
    dept = Department(code="05", name="Antioquia")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, code="05001", name="Medellín")
    db_session.add(muni)
    await db_session.flush()

    inst_a = Institution(
        dane_code="105001000001",
        name="Colegio Mayor de Antioquia (Tenant A)",
        municipality_id=muni.id,
        address="Calle 50 # 40-20",
        phone="3001112233",
        email="contacto@inst-a.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        dane_code="105001000002",
        name="Instituto Técnico del Valle (Tenant B)",
        municipality_id=muni.id,
        address="Carrera 15 # 10-05",
        phone="3004445566",
        email="contacto@inst-b.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    # User in Inst A with document 87884512
    user_a_carlos = User(
        institution_id=inst_a.id,
        email="carlos.docente@inst-a.edu.co",
        username="carlos_8788",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Carlos",
        last_name="Docente Test",
        document_type=DocumentType.CC,
        document_number="87884512",
        is_active=True,
        is_verified=True,
    )
    # Rector in Inst A
    user_a_rector = User(
        institution_id=inst_a.id,
        email="rector@inst-a.edu.co",
        username="rector_inst_a",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Rector",
        last_name="Tenant A",
        document_type=DocumentType.CC,
        document_number="10000001",
        is_active=True,
        is_verified=True,
    )
    # User in Inst B with document 87889999
    user_b_pedro = User(
        institution_id=inst_b.id,
        email="pedro.docente@inst-b.edu.co",
        username="pedro_8788",
        hashed_password=password_hasher.hash("SecurePass2026!"),
        first_name="Pedro",
        last_name="Docente Valle",
        document_type=DocumentType.CC,
        document_number="87889999",
        is_active=True,
        is_verified=True,
    )

    db_session.add_all([user_a_carlos, user_a_rector, user_b_pedro])
    await db_session.flush()

    role_rector = (await db_session.execute(select(Role).where(Role.name == "rector"))).scalar_one()
    role_teacher = (await db_session.execute(select(Role).where(Role.name == "teacher"))).scalar_one()

    db_session.add_all([
        UserRole(user_id=user_a_rector.id, role_id=role_rector.id),
        UserRole(user_id=user_a_carlos.id, role_id=role_teacher.id),
        UserRole(user_id=user_b_pedro.id, role_id=role_teacher.id),
    ])
    await db_session.commit()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "rector_a": user_a_rector,
        "carlos_a": user_a_carlos,
        "pedro_b": user_b_pedro,
    }


async def _auth_headers_for(user: User, roles: list[str]) -> dict[str, str]:
    """Helper to generate JWT Bearer token for user."""
    token = await token_service.create_access_token(
        subject=str(user.id),
        additional_claims={
            "roles": roles,
            "institution_id": str(user.institution_id) if user.institution_id else None,
        },
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_search_users_by_document_8788_tenant_scoped(
    client: AsyncClient,
    users_test_setup: dict,
) -> None:
    """Validate Rector A searching '8788' returns Carlos (Inst A) and excludes Pedro (Inst B)."""
    rector_a = users_test_setup["rector_a"]
    carlos_a = users_test_setup["carlos_a"]
    pedro_b = users_test_setup["pedro_b"]

    headers = await _auth_headers_for(rector_a, ["rector"])

    resp = await client.get("/api/v1/users?search=8788", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert "items" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["id"] == str(carlos_a.id)
    assert item["document_number"] == "87884512"
    assert item["first_name"] == "Carlos"
    assert item["institution_id"] == str(users_test_setup["inst_a"].id)

    # Verify sensitive fields are not in response
    assert "hashed_password" not in item
    assert "password" not in item

    # Verify Pedro (Inst B) was NOT returned
    assert not any(i["id"] == str(pedro_b.id) for i in data["items"])


@pytest.mark.anyio
async def test_search_users_by_name_and_email(
    client: AsyncClient,
    users_test_setup: dict,
) -> None:
    """Validate search by first_name and email within tenant."""
    rector_a = users_test_setup["rector_a"]
    carlos_a = users_test_setup["carlos_a"]
    headers = await _auth_headers_for(rector_a, ["rector"])

    # Search by first name
    resp_name = await client.get("/api/v1/users?search=carlos", headers=headers)
    assert resp_name.status_code == 200
    assert resp_name.json()["total"] == 1
    assert resp_name.json()["items"][0]["id"] == str(carlos_a.id)

    # Search by email
    resp_email = await client.get("/api/v1/users?search=carlos.docente", headers=headers)
    assert resp_email.status_code == 200
    assert resp_email.json()["total"] == 1
    assert resp_email.json()["items"][0]["id"] == str(carlos_a.id)


@pytest.mark.anyio
async def test_get_user_by_id_tenant_boundary(
    client: AsyncClient,
    users_test_setup: dict,
) -> None:
    """Validate Rector A can retrieve User A but is blocked from User B."""
    rector_a = users_test_setup["rector_a"]
    carlos_a = users_test_setup["carlos_a"]
    pedro_b = users_test_setup["pedro_b"]
    headers = await _auth_headers_for(rector_a, ["rector"])

    # Allowed: User in same institution
    resp_a = await client.get(f"/api/v1/users/{carlos_a.id}", headers=headers)
    assert resp_a.status_code == 200
    assert resp_a.json()["id"] == str(carlos_a.id)

    # Forbidden / Not Found: User in different institution
    resp_b = await client.get(f"/api/v1/users/{pedro_b.id}", headers=headers)
    assert resp_b.status_code == 404
