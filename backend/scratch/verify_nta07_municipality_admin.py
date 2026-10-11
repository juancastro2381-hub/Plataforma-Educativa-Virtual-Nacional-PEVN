"""
PEVN — Verification Suite for NTA-07: MUNICIPALITY_ADMIN RBAC IMPLEMENTATION
AI Software Factory Standard v1.2

Executes the Controlled Validation Matrix:
  A. Own municipality (GET own institutions, own detail, municipal analytics)
  B. Same department / foreign municipality (Anti-IDOR denial 403)
  C. Foreign department (Cross-territory denial 403)
  D. IDOR & Scope tampering (UUID tampering, query parameter tampering rejected 403)
  E. Role escalation (Mutation denial 403)
  F. Existing role regression (NATIONAL_ADMIN and DEPARTMENT_ADMIN remain intact)
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.main import app
from app.db.session import get_session_factory
from app.core.security.tokens import token_service
from app.core.security.password import password_hasher
from app.core.security.interfaces import SystemRole
from app.models.user import User, DocumentType
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.institution import Institution


async def run_verification_matrix():
    print("=" * 80)
    print("PEVN — NTA-07: MUNICIPALITY_ADMIN CONTROLLED VALIDATION MATRIX")
    print("=" * 80)

    session_maker = get_session_factory()
    created_user_ids: list[uuid.UUID] = []

    try:
        async with session_maker() as session:
            # 1. Fetch canonical territorial entities
            dept_11 = (await session.execute(select(Department).where(Department.code == "11"))).scalar_one()
            dept_25 = (await session.execute(select(Department).where(Department.code == "25"))).scalar_one()

            muni_bogota = (await session.execute(
                select(Municipality).where(Municipality.code == "11001").options(selectinload(Municipality.department))
            )).scalar_one()
            muni_facatativa = (await session.execute(
                select(Municipality).where(Municipality.code == "25269").options(selectinload(Municipality.department))
            )).scalar_one()
            muni_funza = (await session.execute(
                select(Municipality).where(Municipality.code == "25286").options(selectinload(Municipality.department))
            )).scalar_one()

            # Funza institution (in Dept 25, Municipality 25286 Funza)
            funza_inst_id = uuid.UUID("1fb1a84a-4647-4cd6-b38b-7923d1c0d864")
            funza_inst = (await session.execute(select(Institution).where(Institution.id == funza_inst_id))).scalar_one()

            # Bogotá institution (in Dept 11, Municipality 11001 Bogotá)
            bogota_inst = (await session.execute(
                select(Institution).where(Institution.municipality_id == muni_bogota.id).limit(1)
            )).scalar_one()
            bogota_inst_id = bogota_inst.id

            # Roles
            muni_admin_role = (await session.execute(select(Role).where(Role.name == "municipality_admin"))).scalar_one()
            dept_admin_role = (await session.execute(select(Role).where(Role.name == "department_admin"))).scalar_one()
            nat_admin_role = (await session.execute(select(Role).where(Role.name == "national_admin"))).scalar_one()

            print(f"[PREFLIGHT OK] Territorial baseline loaded:")
            print(f"  Dept 11: {dept_11.name} (Bogotá D.C. muni: {muni_bogota.id})")
            print(f"  Dept 25: {dept_25.name} (Facatativá: {muni_facatativa.id}, Funza: {muni_funza.id})")
            print(f"  Sample Inst Funza (Dept 25): {funza_inst.name} ({funza_inst_id})")
            print(f"  Sample Inst Bogotá (Dept 11): {bogota_inst.name} ({bogota_inst_id})")

            import secrets
            def rand_doc():
                return str(secrets.randbelow(899999999) + 100000000)

            # 2. Provision Test Users
            # User 1: Municipality Admin Bogotá (Dept 11, Muni 11001)
            test_pw_hash = password_hasher.hash("TemporalPassword123#")
            bogota_muni_user = User(
                id=uuid.uuid4(),
                email=f"test.muni.bogota.{uuid.uuid4().hex[:6]}@pevn.edu.co",
                username=f"test.muni.bogota.{uuid.uuid4().hex[:6]}",
                hashed_password=test_pw_hash,
                first_name="Admin",
                last_name="Municipal Bogotá",
                document_type=DocumentType.CC,
                document_number=rand_doc(),
                is_active=True,
                is_verified=True,
                must_change_password=False,
            )
            session.add(bogota_muni_user)
            await session.flush()
            created_user_ids.append(bogota_muni_user.id)

            ur_bogota = UserRole(
                id=uuid.uuid4(),
                user_id=bogota_muni_user.id,
                role_id=muni_admin_role.id,
                municipality_id=muni_bogota.id,
                is_active=True,
            )
            session.add(ur_bogota)

            # User 2: Municipality Admin Facatativá (Dept 25, Muni 25269)
            faca_muni_user = User(
                id=uuid.uuid4(),
                email=f"test.muni.faca.{uuid.uuid4().hex[:6]}@pevn.edu.co",
                username=f"test.muni.faca.{uuid.uuid4().hex[:6]}",
                hashed_password=test_pw_hash,
                first_name="Admin",
                last_name="Municipal Facatativá",
                document_type=DocumentType.CC,
                document_number=rand_doc(),
                is_active=True,
                is_verified=True,
                must_change_password=False,
            )
            session.add(faca_muni_user)
            await session.flush()
            created_user_ids.append(faca_muni_user.id)

            ur_faca = UserRole(
                id=uuid.uuid4(),
                user_id=faca_muni_user.id,
                role_id=muni_admin_role.id,
                municipality_id=muni_facatativa.id,
                is_active=True,
            )
            session.add(ur_faca)

            # User 3: Department Admin Bogotá (Dept 11)
            dept_admin_user = User(
                id=uuid.uuid4(),
                email=f"test.dept.bogota.{uuid.uuid4().hex[:6]}@pevn.edu.co",
                username=f"test.dept.bogota.{uuid.uuid4().hex[:6]}",
                hashed_password=test_pw_hash,
                first_name="Admin",
                last_name="Departamental Bogotá",
                document_type=DocumentType.CC,
                document_number=rand_doc(),
                is_active=True,
                is_verified=True,
                must_change_password=False,
            )
            session.add(dept_admin_user)
            await session.flush()
            created_user_ids.append(dept_admin_user.id)

            ur_dept = UserRole(
                id=uuid.uuid4(),
                user_id=dept_admin_user.id,
                role_id=dept_admin_role.id,
                department_id=dept_11.id,
                is_active=True,
            )
            session.add(ur_dept)

            # User 4: National Admin
            nat_admin_user = User(
                id=uuid.uuid4(),
                email=f"test.nat.admin.{uuid.uuid4().hex[:6]}@pevn.edu.co",
                username=f"test.nat.admin.{uuid.uuid4().hex[:6]}",
                hashed_password=test_pw_hash,
                first_name="Admin",
                last_name="Nacional PEVN",
                document_type=DocumentType.CC,
                document_number=rand_doc(),
                is_active=True,
                is_verified=True,
                must_change_password=False,
            )
            session.add(nat_admin_user)
            await session.flush()
            created_user_ids.append(nat_admin_user.id)

            ur_nat = UserRole(
                id=uuid.uuid4(),
                user_id=nat_admin_user.id,
                role_id=nat_admin_role.id,
                is_active=True,
            )
            session.add(ur_nat)

            await session.commit()
            print(f"[PROVISIONING OK] Test accounts committed:")
            print(f"  Muni Admin Bogotá: {bogota_muni_user.username} (ID: {bogota_muni_user.id})")
            print(f"  Muni Admin Facatativá: {faca_muni_user.username} (ID: {faca_muni_user.id})")
            print(f"  Dept Admin Bogotá: {dept_admin_user.username} (ID: {dept_admin_user.id})")
            print(f"  National Admin: {nat_admin_user.username} (ID: {nat_admin_user.id})")

        # Generate tokens
        token_bogota_muni = await token_service.create_access_token(
            subject=str(bogota_muni_user.id),
            additional_claims={"roles": [SystemRole.MUNICIPALITY_ADMIN.value], "institution_id": None},
        )
        token_faca_muni = await token_service.create_access_token(
            subject=str(faca_muni_user.id),
            additional_claims={"roles": [SystemRole.MUNICIPALITY_ADMIN.value], "institution_id": None},
        )
        token_dept = await token_service.create_access_token(
            subject=str(dept_admin_user.id),
            additional_claims={"roles": [SystemRole.DEPARTMENT_ADMIN.value], "institution_id": None},
        )
        token_nat = await token_service.create_access_token(
            subject=str(nat_admin_user.id),
            additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
        )

        headers_bogota_muni = {"Authorization": f"Bearer {token_bogota_muni}"}
        headers_faca_muni = {"Authorization": f"Bearer {token_faca_muni}"}
        headers_dept = {"Authorization": f"Bearer {token_dept}"}
        headers_nat = {"Authorization": f"Bearer {token_nat}"}

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:

            # =========================================================================
            # MATRIX A: OWN MUNICIPALITY
            # =========================================================================
            print("\n" + "=" * 60)
            print("MATRIX A: OWN MUNICIPALITY")
            print("=" * 60)

            # A.1 GET /auth/me
            r = await client.get("/api/v1/auth/me", headers=headers_bogota_muni)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            me_data = r.json()
            scope = me_data["scope"]
            assert scope["is_national"] is False, "is_national must be False"
            assert scope["is_department"] is False, "is_department must be False"
            assert scope["is_municipality"] is True, "is_municipality must be True"
            assert scope["municipality_id"] == str(muni_bogota.id), f"Mismatch municipality_id"
            assert scope["department_id"] == str(dept_11.id), f"Mismatch department_id"
            assert scope["municipality_code"] == "11001", f"Mismatch municipality_code"
            assert "BOGOTÁ" in scope["jurisdiction_name"].upper(), f"Mismatch jurisdiction_name"
            print(f"[PASS] A.1: GET /auth/me resolves server-authoritative municipal context:")
            print(f"       is_national={scope['is_national']}, is_department={scope['is_department']}, is_municipality={scope['is_municipality']}")
            print(f"       municipality_code={scope['municipality_code']}, jurisdiction={scope['jurisdiction_name']}")

            # A.2 GET /institutions (own municipality)
            r = await client.get("/api/v1/institutions?page_size=100", headers=headers_bogota_muni)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            data_inst = r.json()
            assert data_inst["total"] == 32, f"Expected total 32 Bogotá institutions, got {data_inst['total']}"
            inst_list = data_inst["items"]
            assert len(inst_list) == 32, f"Expected 32 Bogotá institutions, got {len(inst_list)}"
            for inst in inst_list:
                assert inst["municipality_id"] == str(muni_bogota.id), f"Leaked foreign institution: {inst}"
            print(f"[PASS] A.2: GET /institutions returns exactly 32 institutions belonging strictly to Bogotá D.C. (total: {data_inst['total']})")

            # A.3 GET /institutions/{bogota_inst_id} (own institution detail & campuses)
            r = await client.get(f"/api/v1/institutions/{bogota_inst_id}", headers=headers_bogota_muni)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            inst_detail = r.json()
            assert "campuses" in inst_detail, "Campuses must be included in institution detail"
            print(f"[PASS] A.3: GET /institutions/{bogota_inst_id} accesses own institution detail and subordinate campuses (200 OK)")

            # A.5 GET /analytics/territorial/summary (municipal summary)
            r = await client.get("/api/v1/analytics/territorial/summary", headers=headers_bogota_muni)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            summ = r.json()
            assert summ["scope_level"] == "MUNICIPALITY", f"Expected MUNICIPALITY, got {summ['scope_level']}"
            assert "BOGOTÁ" in summ["jurisdiction_name"].upper()
            assert summ["provisioned_institutions"] == 29, f"Expected 29 active provisioned, got {summ['provisioned_institutions']}"
            print(f"[PASS] A.5: GET /analytics/territorial/summary returns scoped municipal KPIs (total_cat: {summ['total_institutions']}, provisioned: {summ['provisioned_institutions']}, level={summ['scope_level']})")

            # A.6 GET /analytics/territorial/municipalities (own municipality distribution)
            r = await client.get("/api/v1/analytics/territorial/municipalities", headers=headers_bogota_muni)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            mun_items = r.json()["items"]
            assert len(mun_items) == 1, f"Expected 1 municipality item, got {len(mun_items)}"
            assert mun_items[0]["municipality_code"] == "11001"
            print(f"[PASS] A.6: GET /analytics/territorial/municipalities returns strictly own municipality (11001)")

            # =========================================================================
            # MATRIX B: SAME DEPARTMENT / FOREIGN MUNICIPALITY
            # =========================================================================
            print("\n" + "=" * 60)
            print("MATRIX B: SAME DEPARTMENT / FOREIGN MUNICIPALITY")
            print("=" * 60)
            # faca_muni_user is in Facatativá (25269, Dept 25).
            # Funza is in Funza (25286, Dept 25). Both in Cundinamarca!

            # B.1 GET foreign institution in same department
            r = await client.get(f"/api/v1/institutions/{funza_inst_id}", headers=headers_faca_muni)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
            print(f"[PASS] B.1: GET foreign institution in same dept denied with 403: {r.json()['error']['code']}")

            # B.2 GET foreign institution KPIs in same department
            r = await client.get(f"/api/v1/analytics/territorial/institutions/{funza_inst_id}", headers=headers_faca_muni)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
            print(f"[PASS] B.2: GET foreign institution KPIs in same dept denied with 403: {r.json()['error']['code']}")

            # B.3 Query municipality distribution in same dept
            r = await client.get("/api/v1/analytics/territorial/municipalities?department_code=25", headers=headers_faca_muni)
            assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
            mun_items_faca = r.json()["items"]
            # Must strictly contain only Facatativá (25269), Funza (25286) must be excluded!
            for m in mun_items_faca:
                assert m["municipality_code"] == "25269", f"Foreign municipality {m['municipality_code']} leaked in same dept query!"
            print(f"[PASS] B.3: Querying same dept distribution strictly excludes foreign municipality 25286 Funza")

            # =========================================================================
            # MATRIX C: FOREIGN DEPARTMENT
            # =========================================================================
            print("\n" + "=" * 60)
            print("MATRIX C: FOREIGN DEPARTMENT")
            print("=" * 60)
            # bogota_muni_user is in Bogotá (Dept 11).
            # Funza is in Cundinamarca (Dept 25).

            # C.1 GET institution from another department
            r = await client.get(f"/api/v1/institutions/{funza_inst_id}", headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
            print(f"[PASS] C.1: GET institution from foreign dept denied with 403: {r.json()['error']['code']}")

            # C.2 GET department analytics distribution (departments endpoint)
            r = await client.get("/api/v1/analytics/territorial/departments", headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
            print(f"[PASS] C.2: GET /analytics/territorial/departments denied with 403: {r.json()['error']['code']}")

            # C.3 GET municipality distribution for another department
            r = await client.get("/api/v1/analytics/territorial/municipalities?department_code=25", headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
            print(f"[PASS] C.3: GET municipality distribution for foreign dept 25 denied with 403: {r.json()['error']['code']}")

            # =========================================================================
            # MATRIX D: IDOR & SCOPE TAMPERING
            # =========================================================================
            print("\n" + "=" * 60)
            print("MATRIX D: IDOR & SCOPE TAMPERING")
            print("=" * 60)

            # D.1 Manipulate municipality_id query param to foreign municipality (Funza)
            r = await client.get(f"/api/v1/institutions?municipality_id={muni_funza.id}", headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403 on municipality_id tampering, got {r.status_code}: {r.text}"
            print(f"[PASS] D.1: Query parameter municipality_id tampering rejected with 403: {r.json()['error']['code']}")

            # D.2 Manipulate department_id query param to foreign department (Cundinamarca)
            r = await client.get(f"/api/v1/institutions?department_id={dept_25.id}", headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403 on department_id tampering, got {r.status_code}: {r.text}"
            print(f"[PASS] D.2: Query parameter department_id tampering rejected with 403: {r.json()['error']['code']}")

            # D.3 Manipulate both department_id and municipality_id
            r = await client.get(f"/api/v1/institutions?department_id={dept_25.id}&municipality_id={muni_funza.id}", headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403 on double tampering, got {r.status_code}: {r.text}"
            print(f"[PASS] D.3: Dual query parameter tampering rejected with 403: {r.json()['error']['code']}")

            # D.4 Direct access to foreign user profile
            r = await client.get(f"/api/v1/users/{faca_muni_user.id}", headers=headers_bogota_muni)
            assert r.status_code in (403, 404), f"Expected 403 or 404 on cross-scope user access, got {r.status_code}: {r.text}"
            print(f"[PASS] D.4: Direct foreign user UUID inspection blocked (Status: {r.status_code})")

            # =========================================================================
            # MATRIX E: ROLE ESCALATION
            # =========================================================================
            print("\n" + "=" * 60)
            print("MATRIX E: ROLE ESCALATION")
            print("=" * 60)

            # E.1 Attempt to create institution (POST /institutions)
            create_inst_payload = {
                "dane_code": "999999999999",
                "name": "Institución No Autorizada",
                "email": "hacked@pevn.edu.co",
                "municipality_id": str(muni_bogota.id),
                "sector": "OFICIAL",
                "zone": "URBANA",
            }
            r = await client.post("/api/v1/institutions", json=create_inst_payload, headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403 on institution creation, got {r.status_code}: {r.text}"
            print(f"[PASS] E.1: POST /institutions denied with 403: {r.json()['error']['code']}")

            # E.2 Attempt to modify institution status (PATCH /institutions/{id}/status)
            r = await client.patch(f"/api/v1/institutions/{bogota_inst_id}/status", json={"is_active": False}, headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403 on status patch, got {r.status_code}: {r.text}"
            print(f"[PASS] E.2: PATCH /institutions/status denied with 403: {r.json()['error']['code']}")

            # E.3 Attempt onboarding request (POST /onboarding/requests)
            onb_payload = {
                "catalog_institution_id": str(uuid.uuid4()),
                "contact_email": "test@pevn.edu.co",
            }
            r = await client.post("/api/v1/onboarding/requests", json=onb_payload, headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403 on onboarding mutation, got {r.status_code}: {r.text}"
            print(f"[PASS] E.3: POST /onboarding/requests denied with 403: {r.json()['error']['code']}")

            # E.4 Attempt department admin provisioning (POST /department-admins)
            dept_admin_payload = {
                "first_name": "Fake",
                "last_name": "Admin",
                "email": "fake.dept@pevn.edu.co",
                "username": "fake_dept_user",
                "department_id": str(dept_11.id),
            }
            r = await client.post("/api/v1/department-admins", json=dept_admin_payload, headers=headers_bogota_muni)
            assert r.status_code == 403, f"Expected 403 on department-admin provisioning, got {r.status_code}: {r.text}"
            print(f"[PASS] E.4: POST /department-admins denied with 403: {r.json()['error']['code']}")

            # =========================================================================
            # MATRIX F: EXISTING ROLE REGRESSION
            # =========================================================================
            print("\n" + "=" * 60)
            print("MATRIX F: EXISTING ROLE REGRESSION")
            print("=" * 60)

            # F.1 NATIONAL_ADMIN scope integrity
            r = await client.get("/api/v1/auth/me", headers=headers_nat)
            assert r.status_code == 200
            nat_me = r.json()["scope"]
            assert nat_me["is_national"] is True
            assert nat_me["is_department"] is False
            assert nat_me["is_municipality"] is False

            r = await client.get("/api/v1/institutions?page_size=100", headers=headers_nat)
            assert r.status_code == 200
            nat_data = r.json()
            assert nat_data["total"] == 34, f"Expected total 34 institutions for NATIONAL_ADMIN, got {nat_data['total']}"
            assert len(nat_data["items"]) == 34

            r = await client.get("/api/v1/analytics/territorial/departments", headers=headers_nat)
            assert r.status_code == 200
            nat_dept_count = len(r.json()["items"])
            assert nat_dept_count == 33, f"Expected 33 departments, got {nat_dept_count}"
            print(f"[PASS] F.1: NATIONAL_ADMIN retains national scope: 33 departments, 34 institutions visible")

            # F.2 DEPARTMENT_ADMIN scope integrity
            r = await client.get("/api/v1/auth/me", headers=headers_dept)
            assert r.status_code == 200
            dept_me = r.json()["scope"]
            assert dept_me["is_national"] is False
            assert dept_me["is_department"] is True
            assert dept_me["is_municipality"] is False
            assert dept_me["department_id"] == str(dept_11.id)

            r = await client.get("/api/v1/institutions?page_size=100", headers=headers_dept)
            assert r.status_code == 200
            dept_data = r.json()
            assert dept_data["total"] == 32, f"Expected total 32 institutions for Bogotá Dept Admin, got {dept_data['total']}"
            assert len(dept_data["items"]) == 32

            # Department Admin attempting cross-department access to Funza (Dept 25)
            r = await client.get(f"/api/v1/institutions/{funza_inst_id}", headers=headers_dept)
            assert r.status_code == 403, f"Expected 403 on cross-dept access by DEPARTMENT_ADMIN, got {r.status_code}"

            r = await client.get("/api/v1/analytics/territorial/departments", headers=headers_dept)
            assert r.status_code == 200
            dept_depts = r.json()["items"]
            assert len(dept_depts) == 1 and dept_depts[0]["department_code"] == "11"
            print(f"[PASS] F.2: DEPARTMENT_ADMIN retains department scope: 32 Bogotá insts, Cundinamarca blocked (403), 1 dept visible")

        print("\n" + "=" * 80)
        print("ALL 6 MATRIX SECTIONS (A, B, C, D, E, F) PASSED WITH ZERO FAILURES!")
        print("=" * 80)

    finally:
        # Cleanup synthetic test users created for validation
        print(f"\n[CLEANUP] Removing {len(created_user_ids)} synthetic test users...")
        async with session_maker() as session:
            for uid in created_user_ids:
                await session.execute(delete(UserRole).where(UserRole.user_id == uid))
                await session.execute(delete(User).where(User.id == uid))
            await session.commit()
        print("[CLEANUP OK] Database restored to baseline.")


if __name__ == "__main__":
    asyncio.run(run_verification_matrix())
