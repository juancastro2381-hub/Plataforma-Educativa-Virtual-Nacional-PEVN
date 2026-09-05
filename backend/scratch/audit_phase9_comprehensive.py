"""
PEVN Phase 9 — Comprehensive Role, Permission & User-Lifecycle Integrity Audit

Tests real database persistence, authentication, session restoration,
tenant isolation, teacher creation lifecycle, negative authorization gates,
and all canonical roles.
"""

import asyncio
import uuid
from datetime import date, datetime, timezone

import httpx
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security.interfaces import SystemRole
from app.core.security.password import Argon2PasswordHasher
from app.db.session import get_session_factory
from app.main import create_application
from app.models.academic_year import AcademicYear, AcademicYearCalendarType, AcademicYearStatus
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.teacher import Teacher, TeacherContractType
from app.models.user import DocumentType, User
from app.schemas.academic import TeacherCreateRequest
from app.services.auth_service import AuthService
from app.services.rbac_bootstrap_service import CANONICAL_ROLES, ROLE_PERMISSIONS_CONFIG, RbacBootstrapService
from app.services.teacher_service import TeacherService


async def run_phase9_audit():
    print("=" * 80)
    print("PEVN PHASE 9 — ROLE, PERMISSION & USER-LIFECYCLE INTEGRITY AUDIT")
    print("=" * 80)

    factory = get_session_factory()
    app = create_application()

    results = {}

    async with factory() as session:
        # -------------------------------------------------------------------
        # 1. Audit Canonical RBAC Catalog in Database
        # -------------------------------------------------------------------
        print("\n[1] Auditing Canonical RBAC Database Catalog...")
        bootstrap = RbacBootstrapService(session=session)
        await bootstrap.seed_canonical_rbac_if_needed()
        await session.commit()

        db_roles = (await session.execute(select(Role))).scalars().all()
        db_perms = (await session.execute(select(Permission))).scalars().all()
        db_role_perms = (await session.execute(select(RolePermission))).scalars().all()

        print(f" - Canonical Roles in DB: {len(db_roles)} (Expected: >= 11)")
        print(f" - Canonical Permissions in DB: {len(db_perms)} (Expected: >= 59)")
        print(f" - Role-Permission mappings in DB: {len(db_role_perms)} (Expected: >= 303)")

        role_names = {r.name for r in db_roles}
        missing_roles = [r["name"] for r in CANONICAL_ROLES if r["name"] not in role_names]
        assert not missing_roles, f"Missing canonical roles: {missing_roles}"
        results["RBAC_CATALOG_AUDIT"] = "PASS"

        # -------------------------------------------------------------------
        # 2. Setup Test Tenants (Institution A & Institution B)
        # -------------------------------------------------------------------
        print("\n[2] Setting up Multi-Tenant Fixtures (Inst A & Inst B)...")
        inst_a_id = uuid.uuid4()
        inst_b_id = uuid.uuid4()

        from app.models.territory import Department, Municipality
        muni = (await session.execute(select(Municipality))).scalars().first()
        if not muni:
            dept = Department(code="11", name="Bogota D.C.")
            session.add(dept)
            await session.flush()
            muni = Municipality(department_id=dept.id, code="11001", name="Bogota D.C.")
            session.add(muni)
            await session.flush()

        dane_a = f"{uuid.uuid4().int % 1000000000000:012d}"
        dane_b = f"{uuid.uuid4().int % 1000000000000:012d}"

        inst_a = Institution(
            id=inst_a_id,
            municipality_id=muni.id,
            dane_code=dane_a,
            name="Colegio San Pedro A",
            email=f"sanpedro_{dane_a[:6]}@pevn.edu.co",
            is_active=True,
        )
        inst_b = Institution(
            id=inst_b_id,
            municipality_id=muni.id,
            dane_code=dane_b,
            name="Colegio Santa Clara B",
            email=f"santaclara_{dane_b[:6]}@pevn.edu.co",
            is_active=True,
        )
        session.add_all([inst_a, inst_b])
        await session.flush()

        hasher = Argon2PasswordHasher()
        password_hash = hasher.hash("TestPass123!_Secure")

        # -------------------------------------------------------------------
        # 3. Create and Validate Every Role (Lifecycle & Session Restoration)
        # -------------------------------------------------------------------
        print("\n[3] Auditing User Lifecycle, Authentication & Session Restoration for all Roles...")
        role_map = {r.name: r for r in db_roles}
        created_users = {}

        for r_info in CANONICAL_ROLES:
            r_name = r_info["name"]
            user_inst = None if r_info["level"] >= 90 else inst_a_id
            
            test_user = User(
                id=uuid.uuid4(),
                institution_id=user_inst,
                email=f"user_{r_name}_{uuid.uuid4().hex[:6]}@pevn.edu.co",
                username=f"usr_{r_name[:10]}_{uuid.uuid4().hex[:4]}",
                hashed_password=password_hash,
                first_name="Test",
                last_name=r_name.capitalize(),
                document_type=DocumentType.CC,
                document_number=f"{uuid.uuid4().int % 1000000000:010d}",
                is_active=True,
                is_verified=True,
            )
            session.add(test_user)
            await session.flush()

            user_role = UserRole(
                user_id=test_user.id,
                role_id=role_map[r_name].id,
                institution_id=user_inst,
            )
            session.add(user_role)
            await session.flush()
            created_users[r_name] = test_user

        await session.commit()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://localhost:8000",
        ) as client:
            # Audit auth flow for every single created role
            for r_name, u in created_users.items():
                login_resp = await client.post(
                    "/api/v1/auth/login",
                    json={"username": u.email, "password": "TestPass123!_Secure"},
                )
                assert login_resp.status_code == 200, f"Role {r_name} failed login: {login_resp.text}"
                login_data = login_resp.json()
                access_token = login_data["access_token"]
                refresh_cookie = login_resp.cookies.get("pevn_refresh_token")
                assert access_token, f"Role {r_name} missing access_token"
                assert refresh_cookie, f"Role {r_name} missing refresh cookie"

                # Verify Session Restore (Silent Refresh -> /auth/me)
                refresh_resp = await client.post(
                    "/api/v1/auth/refresh",
                    cookies={"pevn_refresh_token": refresh_cookie},
                )
                assert refresh_resp.status_code == 200, f"Role {r_name} failed refresh: {refresh_resp.text}"
                new_token = refresh_resp.json()["access_token"]

                me_resp = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {new_token}"},
                )
                assert me_resp.status_code == 200, f"Role {r_name} failed /auth/me: {me_resp.text}"
                me_data = me_resp.json()
                assert me_data["id"] == str(u.id)
                assert me_data["email"] == u.email
                assert r_name in me_data["roles"]
                print(f"   [OK] Role '{r_name:22}' -> Auth OK | Refresh OK | /auth/me OK (Roles: {me_data['roles']})")

            results["ROLE_AUTHENTICATION_AND_SESSION_RESTORE"] = "PASS"

            # -------------------------------------------------------------------
            # 4. Teacher Creation Lifecycle & Validation Forensic Audit
            # -------------------------------------------------------------------
            print("\n[4] Teacher Specific Validation & Error Handling Forensic Audit...")
            rector_user = created_users["rector"]
            rector_login = await client.post(
                "/api/v1/auth/login",
                json={"username": rector_user.email, "password": "TestPass123!_Secure"},
            )
            rector_token = rector_login.json()["access_token"]
            rector_headers = {"Authorization": f"Bearer {rector_token}"}

            # Scenario 1: user_id="8788" (non-UUID format string)
            resp_non_uuid = await client.post(
                "/api/v1/teachers",
                headers=rector_headers,
                json={
                    "user_id": "8788",
                    "specialty_area": "Licenciatura en Ciencias Básicas",
                    "contract_type": "PROPIEDAD",
                    "escalafon_grade": "14",
                },
            )
            print(f" - Case 1: user_id='8788' -> Status: {resp_non_uuid.status_code} (Expected: 422)")
            assert resp_non_uuid.status_code == 422
            err_details = resp_non_uuid.json().get("error", {}).get("details", [])
            print(f"   Validation error count: {len(err_details)}")
            assert any("user_id" in d.get("field", "") for d in err_details)

            # Scenario 2: user_id of user belonging to Institution B (Cross-tenant attempt)
            user_inst_b = User(
                id=uuid.uuid4(),
                institution_id=inst_b_id,
                email=f"teacher_inst_b_{uuid.uuid4().hex[:6]}@pevn.edu.co",
                username=f"usr_b_{uuid.uuid4().hex[:4]}",
                hashed_password=password_hash,
                first_name="Docente",
                last_name="InstB",
                document_type=DocumentType.CC,
                document_number=f"{uuid.uuid4().int % 1000000000:010d}",
                is_active=True,
                is_verified=True,
            )
            session.add(user_inst_b)
            await session.commit()

            resp_cross_tenant = await client.post(
                "/api/v1/teachers",
                headers=rector_headers,
                json={
                    "user_id": str(user_inst_b.id),
                    "specialty_area": "Licenciatura en Ciencias Básicas",
                    "contract_type": "PROPIEDAD",
                    "escalafon_grade": "14",
                },
            )
            print(f" - Case 2: user from Institution B into Inst A -> Status: {resp_cross_tenant.status_code} (Expected: 400/403)")
            assert resp_cross_tenant.status_code in (400, 403)

            # Scenario 3: Valid user belonging to Institution A
            teacher_user_a = created_users["teacher"]
            resp_valid_teacher = await client.post(
                "/api/v1/teachers",
                headers=rector_headers,
                json={
                    "user_id": str(teacher_user_a.id),
                    "specialty_area": "Licenciatura en Matemáticas",
                    "contract_type": "PROPIEDAD",
                    "escalafon_grade": "14",
                },
            )
            print(f" - Case 3: Valid user from Institution A -> Status: {resp_valid_teacher.status_code} (Expected: 201)")
            assert resp_valid_teacher.status_code == 201
            teacher_data = resp_valid_teacher.json()
            assert teacher_data["user_id"] == str(teacher_user_a.id)
            assert teacher_data["institution_id"] == str(inst_a_id)
            assert teacher_data["contract_type"] == "PROPIEDAD"
            assert teacher_data["escalafon_grade"] == "14"

            # Scenario 4: Duplicate teacher profile creation for same user
            resp_dup = await client.post(
                "/api/v1/teachers",
                headers=rector_headers,
                json={
                    "user_id": str(teacher_user_a.id),
                    "specialty_area": "Otra Area",
                    "contract_type": "PROVISIONAL",
                },
            )
            print(f" - Case 4: Duplicate teacher profile -> Status: {resp_dup.status_code} (Expected: 400)")
            assert resp_dup.status_code == 400

            # Scenario 5: Nonexistent user UUID
            resp_nonexistent = await client.post(
                "/api/v1/teachers",
                headers=rector_headers,
                json={
                    "user_id": str(uuid.uuid4()),
                    "specialty_area": "Física",
                    "contract_type": "PROPIEDAD",
                },
            )
            print(f" - Case 5: Nonexistent user UUID -> Status: {resp_nonexistent.status_code} (Expected: 400/403)")
            assert resp_nonexistent.status_code in (400, 403)

            results["TEACHER_LIFECYCLE_VALIDATION"] = "PASS"

            # -------------------------------------------------------------------
            # 5. Negative Authorization Gates & Tenant Isolation
            # -------------------------------------------------------------------
            print("\n[5] Negative Authorization Gates & Multi-Tenant Boundaries...")

            # Student tries to create teacher -> 403
            student_user = created_users["student"]
            student_login = await client.post(
                "/api/v1/auth/login",
                json={"username": student_user.email, "password": "TestPass123!_Secure"},
            )
            student_token = student_login.json()["access_token"]
            student_headers = {"Authorization": f"Bearer {student_token}"}

            resp_student_create_teacher = await client.post(
                "/api/v1/teachers",
                headers=student_headers,
                json={"user_id": str(uuid.uuid4())},
            )
            print(f" - Student attempts POST /teachers -> Status: {resp_student_create_teacher.status_code} (Expected: 403)")
            assert resp_student_create_teacher.status_code == 403

            # Guardian tries to create academic years -> 403
            guardian_user = created_users["guardian"]
            guardian_login = await client.post(
                "/api/v1/auth/login",
                json={"username": guardian_user.email, "password": "TestPass123!_Secure"},
            )
            guardian_token = guardian_login.json()["access_token"]
            guardian_headers = {"Authorization": f"Bearer {guardian_token}"}

            resp_guardian_academic = await client.post(
                "/api/v1/academic-years",
                headers=guardian_headers,
                json={
                    "year": 2026,
                    "name": "Año 2026",
                    "start_date": "2026-01-20",
                    "end_date": "2026-11-30",
                },
            )
            print(f" - Guardian attempts POST /academic-years -> Status: {resp_guardian_academic.status_code} (Expected: 403)")
            assert resp_guardian_academic.status_code == 403

            # Teacher tries to provision institution -> 403
            teacher_login = await client.post(
                "/api/v1/auth/login",
                json={"username": teacher_user_a.email, "password": "TestPass123!_Secure"},
            )
            teacher_token = teacher_login.json()["access_token"]
            teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

            resp_teacher_inst = await client.post(
                "/api/v1/institutions",
                headers=teacher_headers,
                json={"dane_code": "999999999999", "name": "Colegio Ilegal", "consecutive": 99},
            )
            print(f" - Teacher attempts POST /institutions -> Status: {resp_teacher_inst.status_code} (Expected: 403)")
            assert resp_teacher_inst.status_code == 403

            # Rector from Institution A tries to query/access Institution B data
            resp_rector_inst_b = await client.get(
                f"/api/v1/institutions/{inst_b_id}",
                headers=rector_headers,
            )
            print(f" - Rector A queries Inst B -> Status: {resp_rector_inst_b.status_code} (Expected: 403/404)")
            assert resp_rector_inst_b.status_code in (403, 404)

            results["NEGATIVE_AUTHORIZATION_GATES"] = "PASS"

        # -------------------------------------------------------------------
        # 6. Cleanup transient test entities
        # -------------------------------------------------------------------
        print("\n[6] Cleaning up test fixtures cleanly...")
        await session.execute(delete(Teacher).where(Teacher.institution_id.in_([inst_a_id, inst_b_id])))
        for u in created_users.values():
            await session.execute(delete(UserRole).where(UserRole.user_id == u.id))
            await session.execute(delete(User).where(User.id == u.id))
        await session.execute(delete(User).where(User.id == user_inst_b.id))
        await session.execute(delete(Institution).where(Institution.id.in_([inst_a_id, inst_b_id])))
        await session.commit()
        print("   [OK] Multi-tenant audit fixtures safely cleaned up.")

    print("\n" + "=" * 80)
    print("PHASE 9 AUDIT RESULTS SUMMARY:")
    for k, v in results.items():
        print(f" - {k:45}: {v}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_phase9_audit())
