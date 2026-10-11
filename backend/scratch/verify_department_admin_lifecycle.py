"""
PEVN — Verification Script for DEPARTMENT_ADMIN Lifecycle & Territorial Provisioning
Authoritative backend validation of all 17 mandatory security test scenarios.
"""

import asyncio
import os
import sys
import uuid

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.main import app
from app.core.security.tokens import token_service
from app.core.security.interfaces import SystemRole
from app.models.user import User
from app.models.role import Role, UserRole, Permission, RolePermission
from app.models.territory import Department

DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"

async def run_lifecycle_security_tests():
    print("=" * 80)
    print("PEVN — DEPARTMENT ADMINISTRATOR LIFECYCLE: MANDATORY SECURITY TESTS (01 - 17)")
    print("=" * 80)

    engine = create_async_engine(DB_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Fetch base users and departments
        sa_res = await session.execute(select(User).where(User.username == "admin_nacional"))
        superadmin = sa_res.scalar_one()

        na_res = await session.execute(select(User).where(User.username == "national_admin"))
        national_admin = na_res.scalar_one()

        da_res = await session.execute(select(User).where(User.username == "department_admin"))
        dept_admin_bogota = da_res.scalar_one()

        # Departments
        bogota_dept = (await session.execute(select(Department).where(Department.code == "11"))).scalar_one()
        atlantico_dept = (await session.execute(select(Department).where(Department.code == "08"))).scalar_one()
        cundinamarca_dept = (await session.execute(select(Department).where(Department.code == "25"))).scalar_one()

    # Generate JWT tokens
    sa_token = await token_service.create_access_token(
        subject=str(superadmin.id),
        additional_claims={"roles": [SystemRole.SUPERADMIN.value], "institution_id": None},
    )
    na_token = await token_service.create_access_token(
        subject=str(national_admin.id),
        additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
    )
    da_token = await token_service.create_access_token(
        subject=str(dept_admin_bogota.id),
        additional_claims={"roles": [SystemRole.DEPARTMENT_ADMIN.value], "institution_id": None},
    )

    sa_headers = {"Authorization": f"Bearer {sa_token}"}
    na_headers = {"Authorization": f"Bearer {na_token}"}
    da_headers = {"Authorization": f"Bearer {da_token}"}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        test_results = {}

        # -------------------------------------------------------------------
        # TEST 01: SUPER_ADMIN creates DEPARTMENT_ADMIN for Bogotá (DANE 11)
        # -------------------------------------------------------------------
        print("\n[TEST 01] SUPER_ADMIN creates DEPARTMENT_ADMIN for Bogotá...")
        bogota_user_payload = {
            "first_name": "AdminBogota",
            "last_name": "Test01",
            "email": f"admin.bogota.{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "username": f"admin.bogota.{uuid.uuid4().hex[:6]}",
            "password": "BogotaAdminPass2026*!",
            "department_id": str(bogota_dept.id),
        }
        res01 = await client.post("/api/v1/department-admins", json=bogota_user_payload, headers=sa_headers)
        print(f"Status: {res01.status_code}")
        assert res01.status_code == 201, f"Expected 201, got {res01.status_code}: {res01.text}"
        data01 = res01.json()
        assert data01["role_code"] == "department_admin"
        assert data01["department_code"] == "11"
        assert data01["department_id"] == str(bogota_dept.id)
        test_results["TEST_01"] = "PASS"
        print("[OK] TEST 01 PASSED")
        bogota_admin_created = data01

        # -------------------------------------------------------------------
        # TEST 02: NATIONAL_ADMIN creates DEPARTMENT_ADMIN for Atlántico (DANE 08)
        # -------------------------------------------------------------------
        print("\n[TEST 02] NATIONAL_ADMIN creates DEPARTMENT_ADMIN for Atlántico...")
        atlantico_user_payload = {
            "first_name": "AdminAtlantico",
            "last_name": "Test02",
            "email": f"admin.atlantico.{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "username": f"admin.atlantico.{uuid.uuid4().hex[:6]}",
            "password": "AtlanticoAdminPass2026*!",
            "department_id": str(atlantico_dept.id),
        }
        res02 = await client.post("/api/v1/department-admins", json=atlantico_user_payload, headers=na_headers)
        print(f"Status: {res02.status_code}")
        assert res02.status_code == 201, f"Expected 201, got {res02.status_code}: {res02.text}"
        data02 = res02.json()
        assert data02["role_code"] == "department_admin"
        assert data02["department_code"] == "08"
        assert data02["department_id"] == str(atlantico_dept.id)
        test_results["TEST_02"] = "PASS"
        print("[OK] TEST 02 PASSED")
        atlantico_admin_created = data02

        # -------------------------------------------------------------------
        # TEST 03: NATIONAL_ADMIN creates DEPARTMENT_ADMIN for Cundinamarca (DANE 25)
        # -------------------------------------------------------------------
        print("\n[TEST 03] NATIONAL_ADMIN creates DEPARTMENT_ADMIN for Cundinamarca...")
        cundinamarca_user_payload = {
            "first_name": "AdminCundinamarca",
            "last_name": "Test03",
            "email": f"admin.cundinamarca.{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "username": f"admin.cundinamarca.{uuid.uuid4().hex[:6]}",
            "password": "CundinamarcaAdminPass2026*!",
            "department_id": str(cundinamarca_dept.id),
        }
        res03 = await client.post("/api/v1/department-admins", json=cundinamarca_user_payload, headers=na_headers)
        print(f"Status: {res03.status_code}")
        assert res03.status_code == 201, f"Expected 201, got {res03.status_code}: {res03.text}"
        data03 = res03.json()
        assert data03["role_code"] == "department_admin"
        assert data03["department_code"] == "25"
        assert data03["department_id"] == str(cundinamarca_dept.id)
        test_results["TEST_03"] = "PASS"
        print("[OK] TEST 03 PASSED")

        # -------------------------------------------------------------------
        # TEST 04: DEPARTMENT_ADMIN attempts to create another DEPARTMENT_ADMIN
        # -------------------------------------------------------------------
        print("\n[TEST 04] DEPARTMENT_ADMIN attempts to create another DEPARTMENT_ADMIN...")
        res04 = await client.post("/api/v1/department-admins", json={
            "first_name": "Illegal",
            "last_name": "Admin",
            "email": "illegal.admin@pevn.edu.co",
            "username": "illegal.admin",
            "password": "IllegalPassword2026*!",
            "department_id": str(bogota_dept.id),
        }, headers=da_headers)
        print(f"Status: {res04.status_code}")
        assert res04.status_code == 403, f"Expected 403 Forbidden, got {res04.status_code}"
        test_results["TEST_04"] = "PASS"
        print("[OK] TEST 04 PASSED (HTTP 403 Forbidden)")

        # -------------------------------------------------------------------
        # TEST 05: DEPARTMENT_ADMIN attempts to change their own department
        # -------------------------------------------------------------------
        print("\n[TEST 05] DEPARTMENT_ADMIN attempts to change their own department...")
        res05 = await client.patch(
            f"/api/v1/department-admins/{dept_admin_bogota.id}/department",
            json={"new_department_id": str(atlantico_dept.id)},
            headers=da_headers,
        )
        print(f"Status: {res05.status_code}")
        assert res05.status_code == 403, f"Expected 403 Forbidden, got {res05.status_code}"
        test_results["TEST_05"] = "PASS"
        print("[OK] TEST 05 PASSED (HTTP 403 Forbidden)")

        # -------------------------------------------------------------------
        # TEST 06: DEPARTMENT_ADMIN Bogotá attempts to modify Atlántico DEPARTMENT_ADMIN
        # -------------------------------------------------------------------
        print("\n[TEST 06] DEPARTMENT_ADMIN Bogotá attempts to modify Atlántico DEPARTMENT_ADMIN...")
        res06 = await client.patch(
            f"/api/v1/department-admins/{atlantico_admin_created['id']}",
            json={"first_name": "HackedName"},
            headers=da_headers,
        )
        print(f"Status: {res06.status_code}")
        assert res06.status_code == 403, f"Expected 403 Forbidden, got {res06.status_code}"
        test_results["TEST_06"] = "PASS"
        print("[OK] TEST 06 PASSED (HTTP 403 Forbidden)")

        # -------------------------------------------------------------------
        # TEST 07: NATIONAL_ADMIN changes a Bogotá administrator to Cundinamarca
        # -------------------------------------------------------------------
        print("\n[TEST 07] NATIONAL_ADMIN reassigns Bogotá administrator to Cundinamarca...")
        res07 = await client.patch(
            f"/api/v1/department-admins/{bogota_admin_created['id']}/department",
            json={"new_department_id": str(cundinamarca_dept.id)},
            headers=na_headers,
        )
        print(f"Status: {res07.status_code}")
        assert res07.status_code == 200, f"Expected 200, got {res07.status_code}: {res07.text}"
        data07 = res07.json()
        assert data07["department_code"] == "25"
        assert data07["department_id"] == str(cundinamarca_dept.id)

        # Verify audit log in database
        async with session_factory() as session:
            audit_q = await session.execute(text("""
                SELECT event_type, actor_id, target_id, metadata
                FROM audit_logs
                WHERE event_type = 'department_admin.department_changed'
                  AND target_id = :tid
                ORDER BY created_at DESC LIMIT 1
            """), {"tid": bogota_admin_created["id"]})
            audit_ev = audit_q.fetchone()
            assert audit_ev is not None, "Audit event for department reassignment not found"
            print(f"Audit event recorded: {audit_ev.event_type} | Metadata: {audit_ev.metadata}")
            assert str(audit_ev.metadata.get("new_department_code")) == "25"

        test_results["TEST_07"] = "PASS"
        print("[OK] TEST 07 PASSED")

        # -------------------------------------------------------------------
        # TEST 08: Attempt to create DEPARTMENT_ADMIN with nonexistent department_id
        # -------------------------------------------------------------------
        print("\n[TEST 08] Attempt to create DEPARTMENT_ADMIN with nonexistent department_id...")
        bad_uuid = "00000000-0000-0000-0000-000000000000"
        dummy_uname = f"nonexistent.{uuid.uuid4().hex[:6]}"
        res08 = await client.post("/api/v1/department-admins", json={
            "first_name": "Test",
            "last_name": "Nonexistent",
            "email": f"{dummy_uname}@pevn.edu.co",
            "username": dummy_uname,
            "password": "Password123*!",
            "department_id": bad_uuid,
        }, headers=sa_headers)
        print(f"Status: {res08.status_code}")
        assert res08.status_code in (400, 404), f"Expected 400/404, got {res08.status_code}"

        # Verify no database mutation
        async with session_factory() as session:
            user_check = (await session.execute(select(User).where(User.username == dummy_uname))).scalar_one_or_none()
            assert user_check is None, "User should NOT exist in database after failed creation"

        test_results["TEST_08"] = "PASS"
        print("[OK] TEST 08 PASSED (No database mutation)")

        # -------------------------------------------------------------------
        # TEST 09: Attempt to create DEPARTMENT_ADMIN with malformed department_id
        # -------------------------------------------------------------------
        print("\n[TEST 09] Attempt to create DEPARTMENT_ADMIN with malformed department_id...")
        res09 = await client.post("/api/v1/department-admins", json={
            "first_name": "Test",
            "last_name": "Malformed",
            "email": "malformed@pevn.edu.co",
            "username": "malformed.admin",
            "password": "Password123*!",
            "department_id": "not-a-valid-uuid",
        }, headers=sa_headers)
        print(f"Status: {res09.status_code}")
        assert res09.status_code in (400, 422), f"Expected 400/422 validation error, got {res09.status_code}"
        test_results["TEST_09"] = "PASS"
        print("[OK] TEST 09 PASSED (Validation error caught)")

        # -------------------------------------------------------------------
        # TEST 10: Attempt to create DEPARTMENT_ADMIN while pretending to be SUPER_ADMIN in body
        # -------------------------------------------------------------------
        print("\n[TEST 10] Client tries to pass role='superadmin' in request body...")
        spoofed_uname = f"spoofed.{uuid.uuid4().hex[:6]}"
        res10 = await client.post("/api/v1/department-admins", json={
            "first_name": "Spoofed",
            "last_name": "Role",
            "email": f"{spoofed_uname}@pevn.edu.co",
            "username": spoofed_uname,
            "password": "SpoofedPassword2026*!",
            "department_id": str(atlantico_dept.id),
            "role": "superadmin",
            "roles": ["superadmin"],
        }, headers=na_headers)
        print(f"Status: {res10.status_code}")
        assert res10.status_code == 201, f"Expected 201, got {res10.status_code}"
        data10 = res10.json()
        assert data10["role_code"] == "department_admin", f"Role must be department_admin, got {data10['role_code']}"

        # Verify DB persisted role is department_admin, not superadmin
        async with session_factory() as session:
            role_q = await session.execute(text("""
                SELECT r.name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = :uid
            """), {"uid": data10["id"]})
            persisted_roles = [r[0] for r in role_q.fetchall()]
            assert "department_admin" in persisted_roles
            assert "superadmin" not in persisted_roles
            print(f"Persisted roles in DB: {persisted_roles}")

        test_results["TEST_10"] = "PASS"
        print("[OK] TEST 10 PASSED (Server-side role enforcement verified)")

        # -------------------------------------------------------------------
        # TEST 11: Create administrator for Atlántico and authenticate
        # -------------------------------------------------------------------
        print("\n[TEST 11] Authenticate Atlántico administrator and verify scope...")
        login_res = await client.post("/api/v1/auth/login", json={
            "username": atlantico_user_payload["username"],
            "password": atlantico_user_payload["password"],
        })
        print(f"Login status: {login_res.status_code}")
        assert login_res.status_code == 200, f"Expected 200 on login, got {login_res.status_code}: {login_res.text}"
        login_data = login_res.json()
        atlantico_jwt = login_data["access_token"]
        atlantico_headers = {"Authorization": f"Bearer {atlantico_jwt}"}

        # Check /api/v1/auth/me
        me_res = await client.get("/api/v1/auth/me", headers=atlantico_headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        print(f"Scope: {me_data['scope']}")
        assert me_data["scope"]["is_national"] is False, "Scope must NOT be national"
        assert me_data["scope"]["is_department"] is True, "Scope MUST be departmental"
        assert me_data["scope"]["department_id"] == str(atlantico_dept.id), f"Expected {atlantico_dept.id}, got {me_data['scope']['department_id']}"
        test_results["TEST_11"] = "PASS"
        print("[OK] TEST 11 PASSED (Territorial scope correctly resolved)")

        # -------------------------------------------------------------------
        # TEST 12: Atlántico DEPARTMENT_ADMIN requests Bogotá institution
        # -------------------------------------------------------------------
        print("\n[TEST 12] Atlántico DEPARTMENT_ADMIN requests Bogotá institution...")
        # e9f740be-3806-4060-a808-9d02c8bf29af is COLEGIO FRIEDRICH NAUMANN in Bogotá
        bogota_inst_id = "e9f740be-3806-4060-a808-9d02c8bf29af"
        res12 = await client.get(f"/api/v1/institutions/{bogota_inst_id}", headers=atlantico_headers)
        print(f"Status: {res12.status_code}")
        assert res12.status_code == 403, f"Expected 403 Forbidden for cross-department institution, got {res12.status_code}"
        test_results["TEST_12"] = "PASS"
        print("[OK] TEST 12 PASSED (Cross-department institution access blocked with HTTP 403)")

        # -------------------------------------------------------------------
        # TEST 13: Atlántico DEPARTMENT_ADMIN requests Bogotá user
        # -------------------------------------------------------------------
        print("\n[TEST 13] Atlántico DEPARTMENT_ADMIN requests Bogotá user...")
        res13 = await client.get(f"/api/v1/users?institution_id={bogota_inst_id}", headers=atlantico_headers)
        print(f"Status: {res13.status_code}")
        assert res13.status_code == 403, f"Expected 403 Forbidden for cross-department users, got {res13.status_code}"
        test_results["TEST_13"] = "PASS"
        print("[OK] TEST 13 PASSED (Cross-department user access blocked with HTTP 403)")

        # -------------------------------------------------------------------
        # TEST 14: Atlántico DEPARTMENT_ADMIN requests national analytics
        # -------------------------------------------------------------------
        print("\n[TEST 14] Atlántico DEPARTMENT_ADMIN requests national analytics...")
        res14 = await client.get("/api/v1/analytics/territorial/summary", headers=atlantico_headers)
        print(f"Status: {res14.status_code}")
        assert res14.status_code == 200, f"Expected 200, got {res14.status_code}"
        analytics_data = res14.json()
        print(f"Analytics scope: {analytics_data['scope_level']} | Jurisdiction: {analytics_data['jurisdiction_name']} | Depts covered: {analytics_data['total_departments']}")
        assert analytics_data["scope_level"] == "DEPARTMENT"
        assert analytics_data["total_departments"] == 1
        assert "ATLÁNTICO" in analytics_data["jurisdiction_name"].upper()
        test_results["TEST_14"] = "PASS"
        print("[OK] TEST 14 PASSED (Analytics strictly scoped to Atlántico, zero national leakage)")

        # -------------------------------------------------------------------
        # TEST 15: Deactivate DEPARTMENT_ADMIN
        # -------------------------------------------------------------------
        print("\n[TEST 15] Deactivate DEPARTMENT_ADMIN and verify login is blocked...")
        res15_deact = await client.patch(
            f"/api/v1/department-admins/{atlantico_admin_created['id']}/status",
            json={"is_active": False},
            headers=na_headers,
        )
        print(f"Deactivation status: {res15_deact.status_code}")
        assert res15_deact.status_code == 200
        assert res15_deact.json()["is_active"] is False

        # Attempt login with deactivated credentials
        res15_login = await client.post("/api/v1/auth/login", json={
            "username": atlantico_user_payload["username"],
            "password": atlantico_user_payload["password"],
        })
        print(f"Deactivated login status: {res15_login.status_code}")
        assert res15_login.status_code in (400, 401, 403), f"Expected login rejection, got {res15_login.status_code}"
        test_results["TEST_15"] = "PASS"
        print("[OK] TEST 15 PASSED (Deactivated user login strictly blocked)")

        # -------------------------------------------------------------------
        # TEST 16: Reassign DEPARTMENT_ADMIN from Bogotá to Cundinamarca: verify scope
        # -------------------------------------------------------------------
        print("\n[TEST 16] Verify reassigned administrator resolves new scope and loses old...")
        # Authenticate bogota_user_payload (which was reassigned to Cundinamarca in TEST 07)
        login_reassigned = await client.post("/api/v1/auth/login", json={
            "username": bogota_user_payload["username"],
            "password": bogota_user_payload["password"],
        })
        assert login_reassigned.status_code == 200, f"Expected 200 login for reassigned user: {login_reassigned.text}"
        reassigned_jwt = login_reassigned.json()["access_token"]
        reassigned_headers = {"Authorization": f"Bearer {reassigned_jwt}"}

        reassigned_me = await client.get("/api/v1/auth/me", headers=reassigned_headers)
        assert reassigned_me.status_code == 200
        reassigned_scope = reassigned_me.json()["scope"]
        print(f"Reassigned user scope: {reassigned_scope}")
        assert reassigned_scope["department_id"] == str(cundinamarca_dept.id), "Must resolve Cundinamarca UUID"

        # Verify old Bogotá institution is forbidden
        res16_bogota_inst = await client.get(f"/api/v1/institutions/{bogota_inst_id}", headers=reassigned_headers)
        print(f"Access to old Bogotá institution status: {res16_bogota_inst.status_code}")
        assert res16_bogota_inst.status_code == 403, f"Expected 403 for old Bogotá institution, got {res16_bogota_inst.status_code}"

        test_results["TEST_16"] = "PASS"
        print("[OK] TEST 16 PASSED (Old scope revoked, new Cundinamarca scope active)")

        # -------------------------------------------------------------------
        # TEST 17: Verify existing certified Bogotá DEPARTMENT_ADMIN behavior remains intact
        # -------------------------------------------------------------------
        print("\n[TEST 17] Verify existing certified Bogotá DEPARTMENT_ADMIN behavior remains intact...")
        async with session_factory() as session:
            da_user_res = await session.execute(
                select(User).where(User.username == "department_admin")
            )
            da_user = da_user_res.scalar_one()

            da_role_res = await session.execute(text("""
                SELECT r.name, r.level, ur.department_id, d.code as dept_code, d.name as dept_name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                JOIN departments d ON ur.department_id = d.id
                WHERE ur.user_id = :uid
            """), {"uid": da_user.id})
            da_role = da_role_res.fetchone()
            assert da_role.name == "department_admin"
            assert da_role.level == 80
            assert da_role.dept_code == "11"
            assert da_role.department_id == bogota_dept.id

            da_perms_res = await session.execute(text("""
                SELECT p.resource, p.action
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN roles r ON rp.role_id = r.id
                WHERE r.name = 'department_admin'
            """))
            da_perms = [f"{p.resource}:{p.action}" for p in da_perms_res.fetchall()]
            print(f"Certified DEPARTMENT_ADMIN permissions count: {len(da_perms)}")
            assert len(da_perms) == 17, f"Expected exactly 17 permissions, got {len(da_perms)}"
            assert "*:*" not in da_perms, "Wildcard must NOT exist in DEPARTMENT_ADMIN"

        # Check live auth me
        res17_me = await client.get("/api/v1/auth/me", headers=da_headers)
        assert res17_me.status_code == 200
        da_me_scope = res17_me.json()["scope"]
        assert da_me_scope["is_national"] is False
        assert da_me_scope["is_department"] is True
        assert da_me_scope["department_id"] == str(bogota_dept.id)

        test_results["TEST_17"] = "PASS"
        print("✓ TEST 17 PASSED (Certified Bogotá DEPARTMENT_ADMIN remains intact and secure)")

        # -------------------------------------------------------------------
        # TEARDOWN: Clean up temporary test identities created during this run
        # -------------------------------------------------------------------
        print("\n[TEARDOWN] Cleaning up temporary test identities from this run...")
        created_test_uids = [
            uuid.UUID(bogota_admin_created["id"]),
            uuid.UUID(atlantico_admin_created["id"]),
            uuid.UUID(data03["id"]),
            uuid.UUID(data10["id"]),
        ]
        async with session_factory() as session:
            await session.execute(
                text("DELETE FROM refresh_tokens WHERE user_id = ANY(:uids)"),
                {"uids": created_test_uids},
            )
            await session.execute(
                text("DELETE FROM user_roles WHERE user_id = ANY(:uids)"),
                {"uids": created_test_uids},
            )
            await session.execute(
                text("UPDATE audit_logs SET actor_id = NULL WHERE actor_id = ANY(:uids)"),
                {"uids": created_test_uids},
            )
            await session.execute(
                text("DELETE FROM users WHERE id = ANY(:uids)"),
                {"uids": created_test_uids},
            )
            await session.commit()
        print("[OK] Temporary test identities successfully cleaned up. Database hygiene preserved.")

    await engine.dispose()

    print("\n" + "=" * 80)
    print("MANDATORY SECURITY TESTING SUMMARY:")
    print("=" * 80)
    all_passed = True
    for test_name, result in test_results.items():
        print(f"  {test_name.ljust(12)}: {result}")
        if result != "PASS":
            all_passed = False

    print("=" * 80)
    if all_passed and len(test_results) == 17:
        print("ALL 17 MANDATORY SECURITY TESTS PASSED PERFECTLY (100% SUCCESS)!")
    else:
        print("SOME TESTS FAILED! CHECK OUTPUT ABOVE.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_lifecycle_security_tests())
