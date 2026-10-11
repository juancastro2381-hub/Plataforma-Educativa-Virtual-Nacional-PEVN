"""
PEVN Backend — MUNICIPALITY_ADMIN RBAC & Territorial Scope Tests
AI Software Factory Standard v1.2

Validates canonical MUNICIPALITY_ADMIN behavior:
  - Scope resolution (is_national=False, is_department=False, is_municipality=True)
  - Own municipality institution visibility
  - Same department / foreign municipality IDOR block (403)
  - Foreign department access block (403)
  - Scope parameter tampering rejection (403)
  - Mutation & escalation attempt rejection (403)
"""

from __future__ import annotations

import uuid
import secrets
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security.interfaces import SystemRole, OrganizationalScope
from app.core.security.authorization import scope_contains
from app.core.security.tokens import token_service
from app.core.security.password import password_hasher
from app.models.institution import Institution
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.mark.asyncio
async def test_scope_contains_municipal_hierarchy():
    """Unit test: OrganizationalScope hierarchy evaluation for municipality scope."""
    dept_a_id = str(uuid.uuid4())
    dept_b_id = str(uuid.uuid4())
    muni_1_id = str(uuid.uuid4())
    muni_2_id = str(uuid.uuid4())
    inst_1_id = str(uuid.uuid4())
    inst_2_id = str(uuid.uuid4())

    actor_muni_1 = OrganizationalScope(
        country_code="CO",
        department_id=dept_a_id,
        municipality_id=muni_1_id,
    )
    assert actor_muni_1.is_municipality() is True
    assert actor_muni_1.is_national() is False
    assert actor_muni_1.is_department() is False

    # 1. Target inside same municipality -> Contained
    target_inside_muni = OrganizationalScope(
        country_code="CO",
        department_id=dept_a_id,
        municipality_id=muni_1_id,
        institution_id=inst_1_id,
    )
    assert scope_contains(actor_muni_1, target_inside_muni) is True

    # 2. Target in same department but different municipality -> Rejected
    target_same_dept_other_muni = OrganizationalScope(
        country_code="CO",
        department_id=dept_a_id,
        municipality_id=muni_2_id,
        institution_id=inst_2_id,
    )
    assert scope_contains(actor_muni_1, target_same_dept_other_muni) is False

    # 3. Target in different department -> Rejected
    target_other_dept = OrganizationalScope(
        country_code="CO",
        department_id=dept_b_id,
        municipality_id=muni_2_id,
        institution_id=inst_2_id,
    )
    assert scope_contains(actor_muni_1, target_other_dept) is False

    # 4. Department admin targeting municipality in own department -> Contained
    actor_dept = OrganizationalScope(
        country_code="CO",
        department_id=dept_a_id,
    )
    assert scope_contains(actor_dept, target_inside_muni) is True
    assert scope_contains(actor_dept, target_same_dept_other_muni) is True
    assert scope_contains(actor_dept, target_other_dept) is False


@pytest.mark.asyncio
async def test_municipality_admin_api_matrix(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Integration test: API enforcement of MUNICIPALITY_ADMIN isolation and anti-IDOR."""
    # 1. Create test departments
    dept_11 = Department(code="11", name="Bogotá D.C.")
    dept_25 = Department(code="25", name="Cundinamarca")
    db_session.add_all([dept_11, dept_25])
    await db_session.flush()

    # 2. Create test municipalities
    muni_bogota = Municipality(department_id=dept_11.id, code="11001", name="Bogotá D.C.")
    muni_facatativa = Municipality(department_id=dept_25.id, code="25269", name="Facatativá")
    muni_funza = Municipality(department_id=dept_25.id, code="25286", name="Funza")
    db_session.add_all([muni_bogota, muni_facatativa, muni_funza])
    await db_session.flush()

    # 3. Create institutions
    inst_bogota = Institution(
        municipality_id=muni_bogota.id,
        dane_code="111001000100",
        name="Colegio Distrital Bogotá",
        email="rector@bogota.edu.co",
        is_active=True,
    )
    inst_funza = Institution(
        municipality_id=muni_funza.id,
        dane_code="125286000200",
        name="Colegio Oficial Funza",
        email="rector@funza.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_bogota, inst_funza])
    await db_session.flush()

    # 4. Role
    muni_admin_role = (await db_session.execute(select(Role).where(Role.name == "municipality_admin"))).scalar_one()

    def rand_doc():
        return str(secrets.randbelow(899999999) + 100000000)

    # 5. Provision Bogota Muni Admin
    pw_hash = password_hasher.hash("TemporalPass123#")
    bogota_user = User(
        id=uuid.uuid4(),
        email=f"pytest.bogota.{uuid.uuid4().hex[:6]}@pevn.edu.co",
        username=f"pytest.bogota.{uuid.uuid4().hex[:6]}",
        hashed_password=pw_hash,
        first_name="Admin",
        last_name="Bogota",
        document_type=DocumentType.CC,
        document_number=rand_doc(),
        is_active=True,
        is_verified=True,
    )
    db_session.add(bogota_user)
    await db_session.flush()

    ur_bogota = UserRole(
        id=uuid.uuid4(),
        user_id=bogota_user.id,
        role_id=muni_admin_role.id,
        municipality_id=muni_bogota.id,
        is_active=True,
    )
    db_session.add(ur_bogota)

    # 6. Provision Facatativa Muni Admin
    faca_user = User(
        id=uuid.uuid4(),
        email=f"pytest.faca.{uuid.uuid4().hex[:6]}@pevn.edu.co",
        username=f"pytest.faca.{uuid.uuid4().hex[:6]}",
        hashed_password=pw_hash,
        first_name="Admin",
        last_name="Facatativa",
        document_type=DocumentType.CC,
        document_number=rand_doc(),
        is_active=True,
        is_verified=True,
    )
    db_session.add(faca_user)
    await db_session.flush()

    ur_faca = UserRole(
        id=uuid.uuid4(),
        user_id=faca_user.id,
        role_id=muni_admin_role.id,
        municipality_id=muni_facatativa.id,
        is_active=True,
    )
    db_session.add(ur_faca)
    await db_session.commit()

    token_bogota = await token_service.create_access_token(
        subject=str(bogota_user.id),
        additional_claims={"roles": [SystemRole.MUNICIPALITY_ADMIN.value], "institution_id": None},
    )
    token_faca = await token_service.create_access_token(
        subject=str(faca_user.id),
        additional_claims={"roles": [SystemRole.MUNICIPALITY_ADMIN.value], "institution_id": None},
    )
    headers_bogota = {"Authorization": f"Bearer {token_bogota}"}
    headers_faca = {"Authorization": f"Bearer {token_faca}"}

    # 1. Scope resolution in /auth/me
    r_me = await client.get("/api/v1/auth/me", headers=headers_bogota)
    assert r_me.status_code == 200
    scope_data = r_me.json()["scope"]
    assert scope_data["is_national"] is False
    assert scope_data["is_department"] is False
    assert scope_data["is_municipality"] is True
    assert scope_data["municipality_id"] == str(muni_bogota.id)
    assert scope_data["municipality_code"] == "11001"

    # 2. Own institutions access (Bogota)
    r_inst = await client.get("/api/v1/institutions", headers=headers_bogota)
    assert r_inst.status_code == 200
    assert r_inst.json()["total"] == 1
    assert r_inst.json()["items"][0]["id"] == str(inst_bogota.id)

    # 3. Same dept / foreign municipality access denied (Facatativa -> Funza)
    r_foreign_same_dept = await client.get(f"/api/v1/institutions/{inst_funza.id}", headers=headers_faca)
    assert r_foreign_same_dept.status_code == 403
    assert r_foreign_same_dept.json()["error"]["code"] == "PERMISSION_DENIED"

    # 4. Foreign dept access denied (Bogota -> Funza)
    r_foreign_dept = await client.get(f"/api/v1/institutions/{inst_funza.id}", headers=headers_bogota)
    assert r_foreign_dept.status_code == 403
    assert r_foreign_dept.json()["error"]["code"] == "PERMISSION_DENIED"

    # 5. Scope filter tampering denied (Bogota -> ?municipality_id=Funza)
    r_tamper = await client.get(f"/api/v1/institutions?municipality_id={muni_funza.id}", headers=headers_bogota)
    assert r_tamper.status_code == 403

    # 6. Role escalation mutation denied
    r_create = await client.post(
        "/api/v1/institutions",
        json={
            "dane_code": "999999999999",
            "name": "Institución Falsa",
            "email": "falsa@pevn.edu.co",
            "municipality_id": str(muni_bogota.id),
            "sector": "OFICIAL",
            "zone": "URBANA",
        },
        headers=headers_bogota,
    )
    assert r_create.status_code == 403
