import asyncio
import uuid
import httpx
from app.main import app
from app.core.security.tokens import token_service
from app.core.security.interfaces import SystemRole
from app.db.session import get_session_factory
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.role import UserRole, Role

async def run_verification():
    session_maker = get_session_factory()
    async with session_maker() as db:
        # Load department_admin, national_admin, admin_nacional
        users = {}
        for uname in ["department_admin", "national_admin", "admin_nacional"]:
            stmt = (
                select(User)
                .where(User.username == uname)
                .options(
                    selectinload(User.user_roles).selectinload(UserRole.role),
                    selectinload(User.user_roles).selectinload(UserRole.department),
                )
            )
            users[uname] = (await db.execute(stmt)).scalar_one()

        # Load departments
        depts_res = await db.execute(text("SELECT id, code, name FROM departments ORDER BY code;"))
        depts = {row.code: (str(row.id), row.name) for row in depts_res.fetchall()}

        # Load institutions grouped by dept code
        insts_res = await db.execute(text("""
            SELECT i.id, i.name, i.dane_code, d.code as dept_code, d.name as dept_name
            FROM institutions i
            JOIN municipalities m ON i.municipality_id = m.id
            JOIN departments d ON m.department_id = d.id;
        """))
        insts_by_dept = {}
        for r in insts_res.fetchall():
            insts_by_dept.setdefault(r.dept_code, []).append((str(r.id), r.name, r.dane_code))

        # Check total users in DB vs users in Dept 11
        total_users_count = (await db.execute(text("SELECT count(*) FROM users;"))).scalar()
        dept11_users_count = (await db.execute(text("""
            SELECT count(*)
            FROM users u
            JOIN institutions i ON u.institution_id = i.id
            JOIN municipalities m ON i.municipality_id = m.id
            WHERE m.department_id = '7b774116-56f1-4199-ac63-ff646e7e327b';
        """))).scalar()
        dept11_active_users_count = (await db.execute(text("""
            SELECT count(*)
            FROM users u
            JOIN institutions i ON u.institution_id = i.id
            JOIN municipalities m ON i.municipality_id = m.id
            WHERE m.department_id = '7b774116-56f1-4199-ac63-ff646e7e327b'
              AND u.is_active = true;
        """))).scalar()

    print("\n" + "="*80)
    print("PEVN — REMEDIATION VERIFICATION SUITE (TESTS 1 TO 13)")
    print("="*80)
    print(f"Database Stats: Total Users={total_users_count}, Dept 11 Users={dept11_users_count} (Active={dept11_active_users_count})")
    print(f"Institutions in Dept 11: {len(insts_by_dept.get('11', []))}")
    print(f"Institutions in Dept 25: {len(insts_by_dept.get('25', []))}")

    # Generate tokens
    dept_token = await token_service.create_access_token(
        subject=str(users["department_admin"].id),
        additional_claims={"username": "department_admin", "roles": ["department_admin"]},
    )
    dept_headers = {"Authorization": f"Bearer {dept_token}"}

    nat_token = await token_service.create_access_token(
        subject=str(users["national_admin"].id),
        additional_claims={"username": "national_admin", "roles": ["national_admin"]},
    )
    nat_headers = {"Authorization": f"Bearer {nat_token}"}

    super_token = await token_service.create_access_token(
        subject=str(users["admin_nacional"].id),
        additional_claims={"username": "admin_nacional", "roles": ["superadmin"]},
    )
    super_headers = {"Authorization": f"Bearer {super_token}"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
        # TEST 1: Read institution inside DANE 11
        dept11_id = depts["11"][0]
        r1 = await client.get(f"/api/v1/institutions?department_id={dept11_id}", headers=dept_headers)
        print(f"\n[TEST 1] Read institutions in Dept 11:")
        print(f"  Status: {r1.status_code}")
        print(f"  Total items: {r1.json().get('total')}")
        assert r1.status_code == 200
        assert r1.json().get("total") == 32

        # TEST 2: Read institution from Cundinamarca DANE 25 via filter
        dept25_id = depts["25"][0]
        r2 = await client.get(f"/api/v1/institutions?department_id={dept25_id}", headers=dept_headers)
        print(f"\n[TEST 2] Read institutions in Dept 25 (Cundinamarca) via filter:")
        print(f"  Status: {r2.status_code}")
        print(f"  Body: {r2.json()}")
        assert r2.status_code == 403
        assert r2.json()["error"]["code"] == "PERMISSION_DENIED"

        # TEST 3: Read institution from Antioquia DANE 05 via filter
        # If Antioquia is in catalog or fake UUID
        fake_antioquia_id = str(uuid.uuid4())
        r3 = await client.get(f"/api/v1/institutions?department_id={fake_antioquia_id}", headers=dept_headers)
        print(f"\n[TEST 3] Read institutions outside Dept 11 via filter:")
        print(f"  Status: {r3.status_code}")
        print(f"  Body: {r3.json()}")
        assert r3.status_code == 403

        # TEST 4: GET /institutions without department filter
        r4 = await client.get("/api/v1/institutions", headers=dept_headers)
        print(f"\n[TEST 4] GET /institutions without department filter:")
        print(f"  Status: {r4.status_code}")
        print(f"  Total items: {r4.json().get('total')} (Expected: 32 Bogotá records only)")
        assert r4.status_code == 200
        assert r4.json().get("total") == 32

        # TEST 5: GET /institutions?department_id=<Cundinamarca>
        r5 = await client.get(f"/api/v1/institutions?department_id={dept25_id}", headers=dept_headers)
        print(f"\n[TEST 5] Tamper attempt with foreign department_id:")
        print(f"  Status: {r5.status_code}")
        assert r5.status_code == 403

        # TEST 6: GET /institutions/{Cundinamarca institution UUID}
        inst_25_id = insts_by_dept["25"][0][0]
        inst_11_id = insts_by_dept["11"][0][0]
        r6_foreign = await client.get(f"/api/v1/institutions/{inst_25_id}", headers=dept_headers)
        r6_own = await client.get(f"/api/v1/institutions/{inst_11_id}", headers=dept_headers)
        print(f"\n[TEST 6] Direct institutional record access by ID:")
        print(f"  Own Dept 11 Inst ({inst_11_id}): Status={r6_own.status_code}, Name='{r6_own.json().get('name')}'")
        print(f"  Foreign Dept 25 Inst ({inst_25_id}): Status={r6_foreign.status_code}, Error={r6_foreign.json().get('error', {}).get('code')}")
        assert r6_own.status_code == 200
        assert r6_foreign.status_code == 403

        # TEST 7: GET /users within authorized territorial boundary
        r7 = await client.get("/api/v1/users", headers=dept_headers)
        print(f"\n[TEST 7] GET /users for department_admin:")
        print(f"  Status: {r7.status_code}")
        print(f"  Total users returned: {r7.json().get('total')} (Active Dept 11 users in DB: {dept11_active_users_count}, Total in DB: {dept11_users_count})")
        assert r7.status_code == 200
        assert r7.json().get("total") == dept11_active_users_count
        assert r7.json().get("total") < total_users_count

        # TEST 8: GET /analytics/territorial/summary
        r8 = await client.get("/api/v1/analytics/territorial/summary", headers=dept_headers)
        print(f"\n[TEST 8] GET /analytics/territorial/summary:")
        print(f"  Status: {r8.status_code}")
        print(f"  scope_level: {r8.json().get('scope_level')}")
        print(f"  jurisdiction_name: {r8.json().get('jurisdiction_name')}")
        print(f"  total_departments: {r8.json().get('total_departments')}")
        print(f"  total_institutions: {r8.json().get('total_institutions')}")
        print(f"  provisioned_institutions: {r8.json().get('provisioned_institutions')}")
        assert r8.status_code == 200
        assert r8.json()["scope_level"] == "DEPARTMENT"
        assert r8.json()["jurisdiction_name"] == "CAPITAL BOGOTÁ, D.C."
        assert r8.json()["total_departments"] == 1

        # TEST 9: GET /analytics/territorial/departments
        r9 = await client.get("/api/v1/analytics/territorial/departments", headers=dept_headers)
        print(f"\n[TEST 9] GET /analytics/territorial/departments:")
        print(f"  Status: {r9.status_code}")
        print(f"  total_count: {r9.json().get('total_count')}")
        print(f"  departments returned: {[d['department_code'] for d in r9.json().get('items', [])]}")
        assert r9.status_code == 200
        assert r9.json()["total_count"] == 1
        assert r9.json()["items"][0]["department_code"] == "11"

        # TEST 10: Attempt mutation outside department 11
        r10 = await client.patch(f"/api/v1/institutions/{inst_25_id}/status", json={"is_active": False}, headers=dept_headers)
        print(f"\n[TEST 10] Mutation outside department 11 (PATCH /institutions/{inst_25_id}/status):")
        print(f"  Status: {r10.status_code}, Error: {r10.json().get('error', {}).get('code')}")
        assert r10.status_code == 403

        # TEST 11: Attempt mutation inside department 11
        r11 = await client.patch(f"/api/v1/institutions/{inst_11_id}/status", json={"is_active": False}, headers=dept_headers)
        print(f"\n[TEST 11] Mutation inside department 11 (PATCH /institutions/{inst_11_id}/status):")
        print(f"  Status: {r11.status_code}, Error: {r11.json().get('error', {}).get('code')}")
        assert r11.status_code == 403

        # TEST 12: Verify NATIONAL_ADMIN behavior
        r12_insts = await client.get("/api/v1/institutions", headers=nat_headers)
        r12_summary = await client.get("/api/v1/analytics/territorial/summary", headers=nat_headers)
        r12_depts = await client.get("/api/v1/analytics/territorial/departments", headers=nat_headers)
        print(f"\n[TEST 12] Verify NATIONAL_ADMIN:")
        print(f"  GET /institutions: Status={r12_insts.status_code}, Total={r12_insts.json().get('total')}")
        print(f"  Summary scope_level={r12_summary.json().get('scope_level')}, jurisdiction={r12_summary.json().get('jurisdiction_name')}")
        print(f"  Departments count={r12_depts.json().get('total_count')}")
        assert r12_insts.status_code == 200
        assert r12_insts.json().get("total") == 33  # All institutions in DB
        assert r12_summary.json()["scope_level"] == "NATIONAL"
        assert r12_summary.json()["jurisdiction_name"] == "República de Colombia"
        assert r12_depts.json()["total_count"] >= 2

        # TEST 13: Verify SUPER_ADMIN behavior
        r13_insts = await client.get("/api/v1/institutions", headers=super_headers)
        r13_me = await client.get("/api/v1/auth/me", headers=super_headers)
        print(f"\n[TEST 13] Verify SUPER_ADMIN:")
        print(f"  GET /institutions: Status={r13_insts.status_code}, Total={r13_insts.json().get('total')}")
        print(f"  Roles={r13_me.json().get('roles')}, Perms={r13_me.json().get('permissions')[:3]}")
        assert r13_insts.status_code == 200
        assert "*:*" in r13_me.json()["permissions"]
        assert "superadmin" in r13_me.json()["roles"]

    print("\n" + "="*80)
    print("ALL 13 TESTS PASSED WITH 100% SUCCESS!")
    print("="*80 + "\n")

if __name__ == '__main__':
    asyncio.run(run_verification())
