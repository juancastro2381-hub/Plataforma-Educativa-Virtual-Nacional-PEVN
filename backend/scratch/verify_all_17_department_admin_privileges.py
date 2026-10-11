"""
PEVN — COMPREHENSIVE PRIVILEGE EXPOSURE & FUNCTIONAL COVERAGE AUDIT
Verifies all 17 atomic read permissions, write rejections, Anti-IDOR enforcement,
and exact catalog governance for DEPARTMENT_ADMIN (AI Software Factory v1.2).
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete

from app.main import app
from app.core.security.tokens import token_service
from app.core.security.interfaces import SystemRole
from app.models.user import User
from app.models.role import UserRole
from app.models.invitation import DepartmentAdminInvitation
from app.models.territory import Department, Municipality
from app.models.institution import Institution

DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"

CERTIFIED_17_PERMISSIONS = {
    "academic_assignments:read",
    "academic_periods:read",
    "academic_years:read",
    "communications:read",
    "enrollments:read",
    "grades:read",
    "groups:read",
    "guardians:read",
    "incidents:read",
    "institutions:read",
    "news:read",
    "recordings:read",
    "students:read",
    "subjects:read",
    "teachers:read",
    "users:read",
    "virtual_classrooms:read",
}

async def run_privilege_audit():
    print("=" * 80)
    print("PEVN — DEPARTMENT_ADMIN 17-PERMISSION AUDIT & FUNCTIONAL COVERAGE")
    print("=" * 80)

    engine = create_async_engine(DB_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    created_user_ids = []

    try:
        async with session_factory() as session:
            # 1. Fetch national admin and canonical departments
            na_user = (await session.execute(select(User).where(User.username == "national_admin"))).scalar_one()

            atlantico = (await session.execute(select(Department).where(Department.code == "08"))).scalar_one()
            bogota = (await session.execute(select(Department).where(Department.code == "11"))).scalar_one()

            # Fetch an Atlántico institution
            atl_muni_ids = (await session.execute(select(Municipality.id).where(Municipality.department_id == atlantico.id))).scalars().all()
            atl_inst = (await session.execute(select(Institution).where(Institution.municipality_id.in_(atl_muni_ids)))).scalars().first()
            assert atl_inst is not None, "Atlántico institution not found in database"
            atl_inst_id = str(atl_inst.id)

            # Fetch a Bogotá institution for Cross-Department Anti-IDOR test
            bog_muni_ids = (await session.execute(select(Municipality.id).where(Municipality.department_id == bogota.id))).scalars().all()
            bog_inst = (await session.execute(select(Institution).where(Institution.municipality_id.in_(bog_muni_ids)))).scalars().first()
            assert bog_inst is not None, "Bogotá institution not found in database"
            bog_inst_id = str(bog_inst.id)

        na_token = await token_service.create_access_token(
            subject=str(na_user.id),
            additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
        )
        na_headers = {"Authorization": f"Bearer {na_token}"}

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:

            # -----------------------------------------------------------------
            # SETUP: Provision & Activate Atlántico DEPARTMENT_ADMIN
            # -----------------------------------------------------------------
            print("\n--- [SETUP: PROVISIONING ATLÁNTICO DEPARTMENT_ADMIN] ---")
            temp_username = f"audit.da.{uuid.uuid4().hex[:6]}"
            temp_email = f"{temp_username}@sedatlantico.gov.co"
            resp_prov = await client.post(
                "/api/v1/department-admins",
                json={
                    "first_name": "Audit",
                    "last_name": "DepartmentAdmin",
                    "email": temp_email,
                    "username": temp_username,
                    "department_id": str(atlantico.id),
                },
                headers=na_headers,
            )
            assert resp_prov.status_code == 201, f"Failed to provision DA: {resp_prov.text}"
            prov_data = resp_prov.json()
            created_user_ids.append(prov_data["id"])
            raw_token = prov_data["raw_invitation_token"]

            # Accept invitation
            temp_password = "Secure#Audit2026!Password"
            resp_accept = await client.post(
                "/api/v1/auth/accept-invitation",
                json={
                    "token": raw_token,
                    "password": temp_password,
                    "password_confirmation": temp_password,
                },
            )
            assert resp_accept.status_code == 200, f"Failed to accept invitation: {resp_accept.text}"

            # Login
            resp_login = await client.post(
                "/api/v1/auth/login",
                json={"username": temp_username, "password": temp_password},
            )
            assert resp_login.status_code == 200, f"Failed to login: {resp_login.text}"
            da_jwt = resp_login.json()["access_token"]
            da_headers = {
                "Authorization": f"Bearer {da_jwt}",
                "X-Institution-Context": atl_inst_id,
            }
            print(f"[OK] Authenticated as {temp_username} with Atlántico jurisdiction.")

            # -----------------------------------------------------------------
            # CHECK 0: Role & Permission Catalog Governance
            # -----------------------------------------------------------------
            print("\n--- [CHECK 0: RBAC CATALOG INTEGRITY] ---")
            resp_me = await client.get("/api/v1/auth/me", headers=da_headers)
            assert resp_me.status_code == 200, f"Auth me failed: {resp_me.text}"
            me_data = resp_me.json()
            perms = set(me_data.get("permissions", []))

            assert perms == CERTIFIED_17_PERMISSIONS, f"Permissions mismatch! Expected {CERTIFIED_17_PERMISSIONS}, got {perms}"
            assert len(perms) == 17, f"Expected 17 permissions, got {len(perms)}"
            assert not any("*" in p for p in perms), "Wildcard permissions detected!"
            assert not any(p.endswith((":create", ":update", ":delete", ":write", ":manage")) for p in perms), "Write permissions detected!"
            print(f"[PASS] Exact 17-permission certified catalog verified with zero wildcards and zero write grants.")

            # -----------------------------------------------------------------
            # CHECK 1-17: All 17 Atomic Read Endpoints
            # -----------------------------------------------------------------
            print("\n--- [CHECK 1-17: ALL 17 ATOMIC READ PERMISSIONS] ---")
            results = {}

            endpoints_to_test = [
                ("institutions:read", "/api/v1/institutions", {}),
                ("academic_years:read", "/api/v1/academic-years", {"institution_id": atl_inst_id}),
                ("academic_periods:read", "/api/v1/academic-periods", {"institution_id": atl_inst_id}),
                ("grades:read", "/api/v1/grades", {}),
                ("subjects:read", "/api/v1/subjects", {"institution_id": atl_inst_id}),
                ("groups:read", "/api/v1/groups", {"institution_id": atl_inst_id}),
                ("teachers:read", "/api/v1/teachers", {"institution_id": atl_inst_id}),
                ("students:read", "/api/v1/students", {"institution_id": atl_inst_id}),
                ("guardians:read", "/api/v1/guardians", {"institution_id": atl_inst_id}),
                ("enrollments:read", "/api/v1/enrollments", {"institution_id": atl_inst_id}),
                ("academic_assignments:read", "/api/v1/academic-assignments", {"institution_id": atl_inst_id}),
                ("virtual_classrooms:read", "/api/v1/virtual-classrooms", {"institution_id": atl_inst_id}),
                ("recordings:read", "/api/v1/recordings", {"institution_id": atl_inst_id}),
                ("communications:read", "/api/v1/communications", {"institution_id": atl_inst_id}),
                ("news:read", "/api/v1/news", {}),
                ("incidents:read", "/api/v1/incidents", {"institution_id": atl_inst_id}),
                ("users:read", "/api/v1/users", {}),
            ]

            for perm_name, path, query_params in endpoints_to_test:
                res = await client.get(path, params=query_params, headers=da_headers)
                status_ok = res.status_code == 200
                results[perm_name] = "PASS" if status_ok else f"FAIL ({res.status_code})"
                print(f"  [{'PASS' if status_ok else 'FAIL'}] {perm_name:28} -> GET {path:32} (HTTP {res.status_code})")
                assert status_ok, f"Failed {perm_name} at {path}: {res.status_code} {res.text}"

            # -----------------------------------------------------------------
            # CHECK 18: Territorial Security & Anti-IDOR Enforcement
            # -----------------------------------------------------------------
            print("\n--- [CHECK 18: ANTI-IDOR & TERRITORIAL SCOPING] ---")
            # Attempt to access Bogotá institution using Atlántico department_admin credentials
            idor_test_paths = [
                ("/api/v1/academic-years", {"institution_id": bog_inst_id}),
                ("/api/v1/groups", {"institution_id": bog_inst_id}),
                ("/api/v1/teachers", {"institution_id": bog_inst_id}),
                ("/api/v1/students", {"institution_id": bog_inst_id}),
                ("/api/v1/virtual-classrooms", {"institution_id": bog_inst_id}),
                ("/api/v1/incidents", {"institution_id": bog_inst_id}),
            ]

            for path, qparams in idor_test_paths:
                idor_res = await client.get(path, params=qparams, headers=da_headers)
                assert idor_res.status_code in (403, 404), f"IDOR Vulnerability at {path}! Expected 403/404, got {idor_res.status_code}"
                print(f"  [PASS] Anti-IDOR blocked cross-territory access to {path:28} (HTTP {idor_res.status_code})")

            # -----------------------------------------------------------------
            # CHECK 19: Write Operations Rejection (HTTP 403 Forbidden)
            # -----------------------------------------------------------------
            print("\n--- [CHECK 19: WRITE OPERATIONS REJECTION (HTTP 403)] ---")
            write_attempts = [
                ("POST", "/api/v1/institutions", {"dane_code": "123456789012", "name": "Illegal School", "municipality_id": "08001"}),
                ("POST", "/api/v1/academic-years", {"year": 2026, "name": "2026", "start_date": "2026-01-15", "end_date": "2026-11-30"}),
                ("POST", "/api/v1/subjects", {"name": "Hacking 101", "grade_id": str(uuid.uuid4()), "knowledge_area_id": str(uuid.uuid4())}),
                ("POST", "/api/v1/groups", {"name": "11-01", "academic_year_id": str(uuid.uuid4()), "grade_id": str(uuid.uuid4())}),
                ("POST", "/api/v1/virtual-classrooms", {"title": "Rogue Class", "group_id": str(uuid.uuid4())}),
                ("POST", "/api/v1/communications", {"title": "Spam", "content": "Spam", "category": "OTRO", "priority": "BAJA"}),
                ("POST", "/api/v1/incidents", {"student_id": str(uuid.uuid4()), "situation_type": "TIPO_I", "description": "Illegal incident", "pedagogical_measures": "None"}),
            ]

            for method, path, body in write_attempts:
                w_res = await client.request(method, path, json=body, headers=da_headers)
                assert w_res.status_code in (401, 403), f"Write bypass vulnerability! Expected 403, got {w_res.status_code}: {w_res.text}"
                print(f"  [PASS] Write blocked for {method} {path:30} (HTTP {w_res.status_code})")

        print("\n" + "=" * 80)
        print("ALL 17 DEPARTMENT_ADMIN PERMISSIONS VERIFIED WITH 100% SUCCESS!")
        print("=" * 80)
        for perm, status in results.items():
            print(f"  {perm:30} : {status}")

    finally:
        print("\n--- [TEARDOWN] Cleaning up temporary test user... ---")
        async with session_factory() as session:
            for uid in created_user_ids:
                u_uuid = uuid.UUID(uid)
                await session.execute(delete(DepartmentAdminInvitation).where(DepartmentAdminInvitation.user_id == u_uuid))
                await session.execute(delete(UserRole).where(UserRole.user_id == u_uuid))
                await session.execute(delete(User).where(User.id == u_uuid))
            await session.commit()
        print("[OK] Teardown complete. Database hygiene preserved.")

if __name__ == "__main__":
    asyncio.run(run_privilege_audit())
