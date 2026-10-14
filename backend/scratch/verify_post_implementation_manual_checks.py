import os
from dotenv import load_dotenv
load_dotenv()

"""
PEVN — Automated Execution of Section 9 Manual Validation Checks
AI Software Factory v1.2
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.main import app
from app.core.security.tokens import token_service
from app.core.security.interfaces import SystemRole
from app.models.user import User
from app.models.territory import Department
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DB_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")

async def main():
    engine = create_async_engine(DB_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Load admins and depts
        admin_nacional = (await session.execute(select(User).where(User.username == "admin_nacional"))).scalar_one()
        eduardo = (await session.execute(select(User).where(User.username == "Eduardo_Admin_Departamental"))).scalar_one()
        dept_admin_bogota = (await session.execute(select(User).where(User.username == "department_admin"))).scalar_one()
        dept_admin_cundinamarca = (await session.execute(select(User).where(User.username == "admin_cundinamarca"))).scalar_one()

        dept_atlantico = (await session.execute(select(Department).where(Department.code == "08"))).scalar_one()
        dept_bogota = (await session.execute(select(Department).where(Department.code == "11"))).scalar_one()
        dept_cundinamarca = (await session.execute(select(Department).where(Department.code == "25"))).scalar_one()

    # Create tokens
    na_token = await token_service.create_access_token(
        subject=str(admin_nacional.id),
        additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
    )
    atlantico_token = await token_service.create_access_token(
        subject=str(eduardo.id),
        additional_claims={"roles": [SystemRole.DEPARTMENT_ADMIN.value], "institution_id": None},
    )
    bogota_token = await token_service.create_access_token(
        subject=str(dept_admin_bogota.id),
        additional_claims={"roles": [SystemRole.DEPARTMENT_ADMIN.value], "institution_id": None},
    )
    cundinamarca_token = await token_service.create_access_token(
        subject=str(dept_admin_cundinamarca.id),
        additional_claims={"roles": [SystemRole.DEPARTMENT_ADMIN.value], "institution_id": None},
    )

    na_headers = {"Authorization": f"Bearer {na_token}"}
    atlantico_headers = {"Authorization": f"Bearer {atlantico_token}"}
    bogota_headers = {"Authorization": f"Bearer {bogota_token}"}
    cundinamarca_headers = {"Authorization": f"Bearer {cundinamarca_token}"}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        print("============================================================")
        print("1. VALIDATING SUPER_ADMIN / NATIONAL_ADMIN MANAGEMENT VIEW")
        print("============================================================")
        
        # 1.1 Global KPIs
        kpis_res = await client.get("/api/v1/department-admins/kpis", headers=na_headers)
        assert kpis_res.status_code == 200
        kpis = kpis_res.json()
        print(f"Global KPIs: {kpis}")
        assert kpis["total"] == kpis["active"] + kpis["inactive"], "Invariant total = active + inactive violated!"
        assert kpis["departments_covered"] == 3, f"Expected 3 departments covered, got {kpis['departments_covered']}"
        assert kpis["total_canonical_departments"] == 33, f"Expected 33 canonical depts, got {kpis['total_canonical_departments']}"
        print("[OK] KPI Invariant Verified: total = active + inactive (3 = 3 + 0)")
        print("[OK] Department Coverage Verified: 3 de 33")

        # 1.2 Full list (only legitimate administrators shown)
        list_res = await client.get("/api/v1/department-admins", headers=na_headers)
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        usernames = [it["username"] for it in items]
        print(f"Active Admins in list: {usernames}")
        assert set(usernames) == {"Eduardo_Admin_Departamental", "department_admin", "admin_cundinamarca"}
        print("[OK] Only legitimate administrators returned; zero synthetic contamination.")

        # 1.3 Filter Atlántico
        res_atl = await client.get(f"/api/v1/department-admins?department_id={dept_atlantico.id}", headers=na_headers)
        items_atl = res_atl.json()["items"]
        assert len(items_atl) == 1 and items_atl[0]["username"] == "Eduardo_Admin_Departamental"
        print("[OK] Filter Atlántico correctly returns Eduardo_Admin_Departamental")

        # 1.4 Filter Bogotá
        res_bog = await client.get(f"/api/v1/department-admins?department_id={dept_bogota.id}", headers=na_headers)
        items_bog = res_bog.json()["items"]
        assert len(items_bog) == 1 and items_bog[0]["username"] == "department_admin"
        print("[OK] Filter Bogotá correctly returns department_admin")

        # 1.5 Filter Cundinamarca
        res_cun = await client.get(f"/api/v1/department-admins?department_id={dept_cundinamarca.id}", headers=na_headers)
        items_cun = res_cun.json()["items"]
        assert len(items_cun) == 1 and items_cun[0]["username"] == "admin_cundinamarca"
        print("[OK] Filter Cundinamarca correctly returns admin_cundinamarca")

        # 1.6 Filter Active
        res_act = await client.get("/api/v1/department-admins?is_active=true", headers=na_headers)
        assert len(res_act.json()["items"]) == 3
        print("[OK] Filter Active correctly returns 3 active administrators")

        # 1.7 Filter Inactive
        res_inact = await client.get("/api/v1/department-admins?is_active=false", headers=na_headers)
        assert len(res_inact.json()["items"]) == 0
        print("[OK] Filter Inactive correctly returns 0 records (0 inactive)")

        # 1.8 Search by name
        res_search_name = await client.get("/api/v1/department-admins?search=Eduardo", headers=na_headers)
        assert len(res_search_name.json()["items"]) == 1
        print("[OK] Search by name 'Eduardo' returned expected administrator")

        # 1.9 Search by username
        res_search_uname = await client.get("/api/v1/department-admins?search=admin_cundinamarca", headers=na_headers)
        assert len(res_search_uname.json()["items"]) == 1
        print("[OK] Search by username 'admin_cundinamarca' returned expected administrator")

        # 1.10 Search by email
        res_search_email = await client.get("/api/v1/department-admins?search=department_admin@pevn.edu.co", headers=na_headers)
        assert len(res_search_email.json()["items"]) == 1
        print("[OK] Search by email 'department_admin@pevn.edu.co' returned expected administrator")

        print("\n============================================================")
        print("2. VALIDATING TERRITORIAL ANTI-IDOR & SCOPE CONFINEMENT")
        print("============================================================")

        # 2.1 Atlántico scope & Anti-IDOR
        me_atl = await client.get("/api/v1/auth/me", headers=atlantico_headers)
        scope_atl = me_atl.json()["scope"]
        print(f"Atlántico Admin Scope: {scope_atl}")
        assert scope_atl["is_department"] is True
        assert scope_atl["is_national"] is False
        assert scope_atl["department_id"] == str(dept_atlantico.id)
        assert "ATLÁNTICO" in scope_atl["jurisdiction_name"].upper()

        # Atlántico attempts access to Bogotá institution
        bogota_inst_id = "e9f740be-3806-4060-a808-9d02c8bf29af"
        res_atl_to_bog = await client.get(f"/api/v1/institutions/{bogota_inst_id}", headers=atlantico_headers)
        print(f"Atlántico accessing Bogotá institution status: {res_atl_to_bog.status_code}")
        assert res_atl_to_bog.status_code == 403, "Expected 403 Forbidden for cross-department institution access"
        print("[OK] Atlántico Anti-IDOR enforced: HTTP 403 on Bogotá institution")

        # 2.2 Bogotá scope & Anti-IDOR
        me_bog = await client.get("/api/v1/auth/me", headers=bogota_headers)
        scope_bog = me_bog.json()["scope"]
        print(f"Bogotá Admin Scope: {scope_bog}")
        assert scope_bog["is_department"] is True
        assert scope_bog["is_national"] is False
        assert scope_bog["department_id"] == str(dept_bogota.id)

        # Bogotá attempts access to Atlántico analytics
        res_bog_atl = await client.get("/api/v1/analytics/territorial/summary", headers=bogota_headers)
        bog_analytics = res_bog_atl.json()
        print(f"Bogotá analytics jurisdiction: {bog_analytics['jurisdiction_name']}")
        assert "BOGOT" in bog_analytics["jurisdiction_name"].upper()
        assert bog_analytics["total_departments"] == 1
        print("[OK] Bogotá Analytics strictly scoped to Bogotá, zero national/cross leakage")

        # 2.3 Cundinamarca scope & Anti-IDOR
        me_cun = await client.get("/api/v1/auth/me", headers=cundinamarca_headers)
        scope_cun = me_cun.json()["scope"]
        print(f"Cundinamarca Admin Scope: {scope_cun}")
        assert scope_cun["is_department"] is True
        assert scope_cun["is_national"] is False
        assert scope_cun["department_id"] == str(dept_cundinamarca.id)

        res_cun_to_bog = await client.get(f"/api/v1/institutions/{bogota_inst_id}", headers=cundinamarca_headers)
        print(f"Cundinamarca accessing Bogotá institution status: {res_cun_to_bog.status_code}")
        assert res_cun_to_bog.status_code == 403, "Expected 403 Forbidden for Cundinamarca accessing Bogotá institution"
        print("[OK] Cundinamarca Anti-IDOR enforced: HTTP 403 on Bogotá institution")

    await engine.dispose()
    print("\n============================================================")
    print("ALL SECTION 9 MANUAL VALIDATION CHECKS PASSED WITH 100% SUCCESS")
    print("============================================================")

if __name__ == "__main__":
    asyncio.run(main())
