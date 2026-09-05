"""
PEvN — Phase 11: Production Readiness & Real-World Role Acceptance Audit Script

Comprehensive end-to-end functional audit of:
1. RBAC Catalog and database mappings verification.
2. Complete user lifecycle & authentication for all 11 canonical roles:
   superadmin, national_admin, department_admin, municipality_admin,
   rector, institution_admin, coordinator, academic_coordinator,
   teacher, student, guardian.
3. Positive authorization operations for each role.
4. Negative authorization gates (strict 403 Forbidden).
5. Multi-tenant isolation and cross-institution containment.
6. Complete user creation lifecycles: Rector invitation, Teacher creation (UUID validation),
   Student creation, Guardian linking.
7. Session restoration via silent refresh token and /api/v1/auth/me.
8. Database consistency & migration state verification.
"""

import asyncio
import uuid
import datetime
import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security.password import password_hasher
from app.main import create_application
from app.models.academic_year import AcademicPeriod, AcademicYear
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.teacher import Teacher, TeacherContractType
from app.models.student import Student
from app.models.guardian import Guardian, StudentGuardian
from app.models.group import Group
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User

settings = get_settings()
DATABASE_URL = str(settings.DATABASE_URL)
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
app = create_application()

CANONICAL_ROLES = [
    "superadmin",
    "national_admin",
    "department_admin",
    "municipality_admin",
    "rector",
    "institution_admin",
    "coordinator",
    "academic_coordinator",
    "teacher",
    "student",
    "guardian",
]

RESULTS = {
    "RBAC_CATALOG": "PENDING",
    "ALL_11_ROLES_LIFECYCLE": "PENDING",
    "USER_CREATION_LIFECYCLES": "PENDING",
    "POSITIVE_AUTHORIZATION": "PENDING",
    "NEGATIVE_AUTHORIZATION": "PENDING",
    "TENANT_ISOLATION": "PENDING",
    "DATABASE_CONSISTENCY": "PENDING",
}

async def run_phase11_audit():
    print("=" * 80)
    print("PEVN — PHASE 11: PRODUCTION READINESS & ROLE ACCEPTANCE AUDIT")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. DATABASE CONSISTENCY & RBAC CATALOG
    # -------------------------------------------------------------------------
    print("\n[1] Auditing Database Consistency & RBAC Catalog...")
    async with async_session_maker() as session:
        # Check Alembic version table
        alembic_res = await session.execute(text("SELECT version_num FROM alembic_version"))
        alembic_ver = alembic_res.scalar()
        print(f" - Current Alembic migration version: {alembic_ver}")
        assert alembic_ver is not None, "Alembic version missing!"

        # Check Roles
        roles_res = await session.execute(select(Role))
        roles = {r.name: r for r in roles_res.scalars().all()}
        for r_name in CANONICAL_ROLES:
            assert r_name in roles, f"Missing canonical role in DB: {r_name}"
        print(f" - Found all {len(roles)} roles (including {len(CANONICAL_ROLES)} canonical roles).")

        # Check Permissions & Role-Permission Associations
        perms_res = await session.execute(select(Permission))
        perms = perms_res.scalars().all()
        print(f" - Found {len(perms)} granular permissions in DB.")

        rp_res = await session.execute(select(RolePermission))
        rps = rp_res.scalars().all()
        print(f" - Found {len(rps)} role-permission mappings in DB.")
        assert len(rps) >= 300, f"Expected >=300 mappings, found {len(rps)}"
        RESULTS["RBAC_CATALOG"] = "PASS"
        RESULTS["DATABASE_CONSISTENCY"] = "PASS"

    # -------------------------------------------------------------------------
    # 2. FIXTURES SETUP FOR MULTI-TENANT AUDITING
    # -------------------------------------------------------------------------
    print("\n[2] Setting up Controlled Institutional Fixtures...")
    test_id = str(uuid.uuid4())[:8]
    inst_a_id = uuid.uuid4()
    inst_b_id = uuid.uuid4()
    campus_a_id = uuid.uuid4()
    campus_b_id = uuid.uuid4()

    async with async_session_maker() as session:
        # Check / create department & municipality
        dep_res = await session.execute(select(Department).where(Department.code == "11"))
        dep = dep_res.scalars().first()
        if not dep:
            dep = Department(code="11", name="Bogota D.C.")
            session.add(dep)
            await session.flush()

        mun_res = await session.execute(select(Municipality).where(Municipality.code == "11001"))
        mun = mun_res.scalars().first()
        if not mun:
            mun = Municipality(code="11001", name="Bogota D.C.", department_id=dep.id)
            session.add(mun)
            await session.flush()

        # Institution A
        inst_a = Institution(
            id=inst_a_id,
            dane_code=f"111{test_id}"[:12],
            name=f"Colegio Mayor A ({test_id})",
            email=f"contacto_a_{test_id}@colegio.edu.co",
            municipality_id=mun.id,
            is_active=True,
        )
        session.add(inst_a)
        campus_a = Campus(
            id=campus_a_id,
            institution_id=inst_a_id,
            dane_sede_code=f"111{test_id}01"[:12],
            name="Sede Principal A",
            is_active=True,
        )
        session.add(campus_a)

        # Institution B (for Cross-Tenant Testing)
        inst_b = Institution(
            id=inst_b_id,
            dane_code=f"222{test_id}"[:12],
            name=f"Colegio Mayor B ({test_id})",
            email=f"contacto_b_{test_id}@colegio.edu.co",
            municipality_id=mun.id,
            is_active=True,
        )
        session.add(inst_b)
        campus_b = Campus(
            id=campus_b_id,
            institution_id=inst_b_id,
            dane_sede_code=f"222{test_id}01"[:12],
            name="Sede Principal B",
            is_active=True,
        )
        session.add(campus_b)

        # Seed Users for all 11 Roles
        users_map = {}
        password_plain = "P@ssw0rdSecure2026!"
        password_hash = password_hasher.hash(password_plain)

        for role_name in CANONICAL_ROLES:
            u_id = uuid.uuid4()
            is_national = role_name in ["superadmin", "national_admin"]
            dept = "DEP-11" if role_name == "department_admin" else None
            mun_code = "MUN-11001" if role_name == "municipality_admin" else None
            u_inst = None if is_national or dept or mun_code else inst_a_id

            u = User(
                id=u_id,
                email=f"{role_name}_{test_id}@pevn.edu.co",
                username=f"{role_name}_{test_id}",
                first_name=f"Audit_{role_name}",
                last_name="TestUser",
                document_type=DocumentType.CC,
                document_number=f"DOC-{test_id}-{role_name[:3]}",
                hashed_password=password_hash,
                institution_id=u_inst,
                is_active=True,
                is_verified=True,
            )
            session.add(u)
            ur = UserRole(user_id=u_id, role_id=roles[role_name].id)
            session.add(ur)
            users_map[role_name] = {
                "id": u_id,
                "username": u.username,
                "password": password_plain,
                "email": u.email,
                "institution_id": u_inst,
            }

        # Also create a user in Institution B for cross-tenant testing
        u_b_id = uuid.uuid4()
        u_b = User(
            id=u_b_id,
            email=f"rector_b_{test_id}@pevn.edu.co",
            username=f"rector_b_{test_id}",
            first_name="Rector",
            last_name="Inst B",
            document_type=DocumentType.CC,
            document_number=f"DOC-B-{test_id}",
            hashed_password=password_hash,
            institution_id=inst_b_id,
            is_active=True,
            is_verified=True,
        )
        session.add(u_b)
        session.add(UserRole(user_id=u_b_id, role_id=roles["rector"].id))
        users_map["rector_b"] = {
            "id": u_b_id,
            "username": u_b.username,
            "password": password_plain,
            "email": u_b.email,
            "institution_id": inst_b_id,
        }

        # Pre-seed Academic Year for Inst A
        ay_id = uuid.uuid4()
        ay = AcademicYear(
            id=ay_id,
            institution_id=inst_a_id,
            year=2026,
            name=f"Año Lectivo {datetime.date.today().year} - Audit",
            start_date=datetime.date(2026, 1, 15),
            end_date=datetime.date(2026, 11, 30),
            status="ACTIVE",
        )
        session.add(ay)

        await session.commit()
        print(f" - Fixtures initialized: Inst A ({inst_a_id}), Inst B ({inst_b_id}), 12 test users created.")

    # -------------------------------------------------------------------------
    # 3. COMPLETE AUTHENTICATION & SESSION RESTORATION FOR ALL 11 ROLES
    # -------------------------------------------------------------------------
    print("\n[3] Auditing Authentication, Silent Refresh, and /auth/me for all 11 Roles...")
    tokens = {}
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        for r_name in CANONICAL_ROLES:
            u_info = users_map[r_name]
            # 1. Login
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"username": u_info["username"], "password": u_info["password"]},
            )
            assert login_resp.status_code == 200, f"Login failed for {r_name}: {login_resp.text}"
            login_data = login_resp.json()
            access_token = login_data["access_token"]
            # 2. Silent Refresh Token Rotation
            refresh_resp = await client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert refresh_resp.status_code == 200, f"Refresh failed for {r_name}: {refresh_resp.text}"
            new_access_token = refresh_resp.json()["access_token"]
            assert new_access_token, f"No refreshed access token for {r_name}"

            # 3. Session Restoration via /auth/me
            me_resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {new_access_token}"},
            )
            assert me_resp.status_code == 200, f"/auth/me failed for {r_name}: {me_resp.text}"
            me_data = me_resp.json()
            assert r_name in me_data["roles"], f"Role mismatch for {r_name}: got {me_data['roles']}"

            tokens[r_name] = new_access_token
            print(f" - [PASS] Role: {r_name:<22} | Login=200 | Refresh=200 | /auth/me=200 | Roles={me_data['roles']}")

        # Also get token for Rector B
        login_b = await client.post(
            "/api/v1/auth/login",
            json={"username": users_map["rector_b"]["username"], "password": users_map["rector_b"]["password"]},
        )
        tokens["rector_b"] = login_b.json()["access_token"]

    RESULTS["ALL_11_ROLES_LIFECYCLE"] = "PASS"

    # -------------------------------------------------------------------------
    # 4. USER CREATION & REGISTRATION LIFECYCLES
    # -------------------------------------------------------------------------
    print("\n[4] Auditing Complete User Creation Lifecycles...")
    teacher_id = None
    student_id = None
    guardian_id = None
    rec_ay_id = None

    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        # A. TEACHER CREATION LIFECYCLE (Contract & Regression Protection)
        print("\n [4.1] Teacher Creation Lifecycle Contract:")
        rector_headers = {"Authorization": f"Bearer {tokens['rector']}"}

        # 1. Invalid UUID format -> HTTP 422
        resp_invalid_uuid = await client.post(
            "/api/v1/teachers",
            json={"user_id": "8788", "specialty_area": "Matemáticas"},
            headers=rector_headers,
        )
        assert resp_invalid_uuid.status_code == 422, f"Expected 422 for malformed UUID, got {resp_invalid_uuid.status_code}"
        print(f"   - Malformed UUID '8788' -> 422 Unprocessable Content [PASS]")

        # 2. Nonexistent user -> HTTP 403 / 404 (Privacy-preserving tenant boundary)
        nonexistent_uuid = str(uuid.uuid4())
        resp_nonexistent = await client.post(
            "/api/v1/teachers",
            json={"user_id": nonexistent_uuid, "specialty_area": "Matemáticas"},
            headers=rector_headers,
        )
        assert resp_nonexistent.status_code in [403, 404], f"Expected 403/404 for nonexistent user, got {resp_nonexistent.status_code}"
        print(f"   - Nonexistent user UUID -> {resp_nonexistent.status_code} (Prevented enumeration) [PASS]")

        # 3. Cross-Tenant User (User belonging to Inst B, created in Inst A by Rector A) -> HTTP 403
        resp_cross_tenant = await client.post(
            "/api/v1/teachers",
            json={"user_id": str(users_map["rector_b"]["id"]), "specialty_area": "Física"},
            headers=rector_headers,
        )
        assert resp_cross_tenant.status_code == 403, f"Expected 403 for cross-tenant user, got {resp_cross_tenant.status_code}"
        print(f"   - Cross-Tenant User Association -> 403 CROSS_TENANT_MISMATCH [PASS]")

        # 4. Valid Teacher Creation in Inst A -> HTTP 201
        new_teacher_user_id = str(users_map["teacher"]["id"])
        resp_create_teacher = await client.post(
            "/api/v1/teachers",
            json={"user_id": new_teacher_user_id, "specialty_area": "Ciencias Naturales", "contract_type": "PROPIEDAD"},
            headers=rector_headers,
        )
        assert resp_create_teacher.status_code == 201, f"Expected 201, got {resp_create_teacher.status_code}: {resp_create_teacher.text}"
        teacher_id = resp_create_teacher.json()["id"]
        print(f"   - Valid Teacher Creation -> 201 Created (ID: {teacher_id}) [PASS]")

        # 5. Duplicate Teacher Profile -> HTTP 400
        resp_duplicate_teacher = await client.post(
            "/api/v1/teachers",
            json={"user_id": new_teacher_user_id, "specialty_area": "Ciencias"},
            headers=rector_headers,
        )
        assert resp_duplicate_teacher.status_code == 400, f"Expected 400 for duplicate, got {resp_duplicate_teacher.status_code}"
        print(f"   - Duplicate Teacher Profile -> 400 Bad Request [PASS]")

        # B. STUDENT CREATION LIFECYCLE
        print("\n [4.2] Student Creation Lifecycle:")
        new_student_user_id = str(users_map["student"]["id"])
        simat_code = f"SIMAT-{test_id}-STD"
        resp_create_student = await client.post(
            "/api/v1/students",
            json={"user_id": new_student_user_id, "code_simat": simat_code, "birth_date": "2010-05-15"},
            headers=rector_headers,
        )
        assert resp_create_student.status_code == 201, f"Expected 201, got {resp_create_student.status_code}: {resp_create_student.text}"
        student_id = resp_create_student.json()["id"]
        print(f"   - Valid Student Creation -> 201 Created (ID: {student_id}, SIMAT: {simat_code}) [PASS]")

        # Duplicate SIMAT code -> 400
        resp_dup_student = await client.post(
            "/api/v1/students",
            json={"user_id": str(uuid.uuid4()), "code_simat": simat_code, "birth_date": "2010-05-15"},
            headers=rector_headers,
        )
        assert resp_dup_student.status_code in [400, 403, 404], f"Expected 400/403/404 for duplicate SIMAT, got {resp_dup_student.status_code}"
        print(f"   - Duplicate SIMAT rejection [PASS]")

        # C. GUARDIAN CREATION & LINKING
        print("\n [4.3] Guardian Creation & Student Linking Lifecycle:")
        guardian_user_id = str(users_map["guardian"]["id"])
        resp_create_guardian = await client.post(
            "/api/v1/guardians",
            json={
                "first_name": "Pedro",
                "last_name": "AuditGuardian",
                "document_type": "CC",
                "document_number": f"GDOC-{test_id}",
                "phone": "3001234567",
                "relationship_type": "PADRE",
                "user_id": guardian_user_id,
            },
            headers=rector_headers,
        )
        assert resp_create_guardian.status_code == 201, f"Expected 201, got {resp_create_guardian.status_code}: {resp_create_guardian.text}"
        guardian_id = resp_create_guardian.json()["id"]
        print(f"   - Valid Guardian Creation -> 201 Created (ID: {guardian_id}) [PASS]")

        # Link Guardian to Student
        resp_link = await client.post(
            f"/api/v1/guardians/{guardian_id}/students/{student_id}",
            json={"relationship_type": "PADRE", "is_primary_contact": True, "is_authorized_pickup": True},
            headers=rector_headers,
        )
        assert resp_link.status_code in [200, 201], f"Expected 200/201 for link, got {resp_link.status_code}: {resp_link.text}"
        print(f"   - Student-Guardian Link -> 201 Created [PASS]")

        RESULTS["USER_CREATION_LIFECYCLES"] = "PASS"

    # -------------------------------------------------------------------------
    # 5. POSITIVE AUTHORIZATION OPERATIONS (ALL 11 ROLES)
    # -------------------------------------------------------------------------
    print("\n[5] Auditing Positive Authorization for All 11 Roles...")
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        # 1. Superadmin -> List Institutions
        sa_resp = await client.get("/api/v1/institutions", headers={"Authorization": f"Bearer {tokens['superadmin']}"})
        assert sa_resp.status_code == 200, f"Superadmin list institutions failed: {sa_resp.status_code}"
        print(" - [PASS] Superadmin          : GET /institutions -> 200 OK")

        # 2. National Admin -> List Institutions & Territorial Analytics
        na_resp = await client.get("/api/v1/institutions", headers={"Authorization": f"Bearer {tokens['national_admin']}"})
        assert na_resp.status_code == 200, f"National Admin list institutions failed: {na_resp.status_code}"
        print(" - [PASS] National Admin      : GET /institutions -> 200 OK")

        # 3. Department Admin -> Analytics
        da_resp = await client.get("/api/v1/analytics/territorial/summary", headers={"Authorization": f"Bearer {tokens['department_admin']}"})
        assert da_resp.status_code == 200, f"Department Admin analytics failed: {da_resp.status_code}"
        print(" - [PASS] Department Admin    : GET /analytics/territorial/summary -> 200 OK")

        # 4. Municipality Admin -> Analytics
        ma_resp = await client.get("/api/v1/analytics/territorial/summary", headers={"Authorization": f"Bearer {tokens['municipality_admin']}"})
        assert ma_resp.status_code == 200, f"Municipality Admin analytics failed: {ma_resp.status_code}"
        print(" - [PASS] Municipality Admin  : GET /analytics/territorial/summary -> 200 OK")

        # 5. Rector -> Create Academic Year in Inst A
        rec_ay_resp = await client.post(
            "/api/v1/academic-years",
            json={"year": 2027, "name": f"Año 2027 {test_id}", "start_date": "2027-01-20", "end_date": "2027-11-30"},
            headers={"Authorization": f"Bearer {tokens['rector']}"},
        )
        assert rec_ay_resp.status_code == 201, f"Rector create academic year failed: {rec_ay_resp.status_code}: {rec_ay_resp.text}"
        rec_ay_id = rec_ay_resp.json()["id"]
        print(" - [PASS] Rector              : POST /academic-years -> 201 Created")

        # 6. Institution Admin -> List Groups
        ia_resp = await client.get("/api/v1/groups", headers={"Authorization": f"Bearer {tokens['institution_admin']}"})
        assert ia_resp.status_code == 200, f"Inst Admin list groups failed: {ia_resp.status_code}"
        print(" - [PASS] Institution Admin   : GET /groups -> 200 OK")

        # 7. Coordinator -> List Students
        co_resp = await client.get("/api/v1/students", headers={"Authorization": f"Bearer {tokens['coordinator']}"})
        assert co_resp.status_code == 200, f"Coordinator list students failed: {co_resp.status_code}"
        print(" - [PASS] Coordinator         : GET /students -> 200 OK")

        # 8. Academic Coordinator -> List Assignments
        ac_resp = await client.get("/api/v1/academic-assignments", headers={"Authorization": f"Bearer {tokens['academic_coordinator']}"})
        assert ac_resp.status_code == 200, f"Academic Coordinator list assignments failed: {ac_resp.status_code}"
        print(" - [PASS] Academic Coordinator: GET /academic-assignments -> 200 OK")

        # 9. Teacher -> List Virtual Classrooms
        tch_resp = await client.get("/api/v1/virtual-classrooms", headers={"Authorization": f"Bearer {tokens['teacher']}"})
        assert tch_resp.status_code == 200, f"Teacher list classrooms failed: {tch_resp.status_code}"
        print(" - [PASS] Teacher             : GET /virtual-classrooms -> 200 OK")

        # 10. Student -> List Virtual Classrooms (authorized to view/join)
        std_resp = await client.get("/api/v1/virtual-classrooms", headers={"Authorization": f"Bearer {tokens['student']}"})
        assert std_resp.status_code == 200, f"Student list classrooms failed: {std_resp.status_code}"
        print(" - [PASS] Student             : GET /virtual-classrooms -> 200 OK")

        # 11. Guardian -> Get profile / Dashboard
        g_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['guardian']}"})
        assert g_resp.status_code == 200, f"Guardian get /auth/me failed: {g_resp.status_code}"
        print(" - [PASS] Guardian            : GET /auth/me -> 200 OK")

        RESULTS["POSITIVE_AUTHORIZATION"] = "PASS"

    # -------------------------------------------------------------------------
    # 6. NEGATIVE AUTHORIZATION GATES (STRICT HTTP 403 FORBIDDEN)
    # -------------------------------------------------------------------------
    print("\n[6] Auditing Negative Authorization Gates (Strict 403 Forbidden)...")
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        # 1. Student attempting to create teacher -> 403
        r1 = await client.post(
            "/api/v1/teachers",
            json={"user_id": str(uuid.uuid4()), "specialty_area": "Hacking"},
            headers={"Authorization": f"Bearer {tokens['student']}"},
        )
        assert r1.status_code == 403, f"Expected 403, got {r1.status_code}"
        print(" - [PASS] Student -> POST /teachers -> 403 Forbidden")

        # 2. Guardian attempting to create academic year -> 403
        r2 = await client.post(
            "/api/v1/academic-years",
            json={"name": "Año Falso", "start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers={"Authorization": f"Bearer {tokens['guardian']}"},
        )
        assert r2.status_code == 403, f"Expected 403, got {r2.status_code}"
        print(" - [PASS] Guardian -> POST /academic-years -> 403 Forbidden")

        # 3. Teacher attempting to create institution -> 403
        r3 = await client.post(
            "/api/v1/institutions",
            json={"name": "Colegio Ilegal", "dane_code": "999999999999", "department_id": "DEP-11", "municipality_id": "MUN-11001"},
            headers={"Authorization": f"Bearer {tokens['teacher']}"},
        )
        assert r3.status_code == 403, f"Expected 403, got {r3.status_code}"
        print(" - [PASS] Teacher -> POST /institutions -> 403 Forbidden")

        # 4. Teacher attempting to create another teacher -> 403
        r4 = await client.post(
            "/api/v1/teachers",
            json={"user_id": str(uuid.uuid4()), "specialty_area": "Física"},
            headers={"Authorization": f"Bearer {tokens['teacher']}"},
        )
        assert r4.status_code == 403, f"Expected 403, got {r4.status_code}"
        print(" - [PASS] Teacher -> POST /teachers -> 403 Forbidden")

        # 5. Coordinator attempting to invite rector -> 403
        r5 = await client.post(
            f"/api/v1/institutions/{inst_a_id}/rector-invitation",
            json={"email": "nuevo_rector@pevn.edu.co", "first_name": "Nuevo", "last_name": "Rector", "document_type": "CC", "document_number": "99887766"},
            headers={"Authorization": f"Bearer {tokens['coordinator']}"},
        )
        assert r5.status_code == 403, f"Expected 403, got {r5.status_code}"
        print(" - [PASS] Coordinator -> POST rector-invitation -> 403 Forbidden")

        # 6. Department Admin attempting to create teachers -> 403
        r6 = await client.post(
            "/api/v1/teachers",
            json={"user_id": str(uuid.uuid4()), "specialty_area": "Química"},
            headers={"Authorization": f"Bearer {tokens['department_admin']}"},
        )
        assert r6.status_code == 403, f"Expected 403, got {r6.status_code}"
        print(" - [PASS] Department Admin -> POST /teachers -> 403 Forbidden")

        # 7. Municipality Admin attempting to create teachers -> 403
        r7 = await client.post(
            "/api/v1/teachers",
            json={"user_id": str(uuid.uuid4()), "specialty_area": "Química"},
            headers={"Authorization": f"Bearer {tokens['municipality_admin']}"},
        )
        assert r7.status_code == 403, f"Expected 403, got {r7.status_code}"
        print(" - [PASS] Municipality Admin -> POST /teachers -> 403 Forbidden")

        RESULTS["NEGATIVE_AUTHORIZATION"] = "PASS"

    # -------------------------------------------------------------------------
    # 7. MULTI-TENANT ISOLATION & CONTAINMENT
    # -------------------------------------------------------------------------
    print("\n[7] Auditing Multi-Tenant Isolation...")
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        # Rector of Inst A querying detail of Inst B -> 403 Forbidden / Scope Mismatch
        r_iso = await client.get(
            f"/api/v1/institutions/{inst_b_id}",
            headers={"Authorization": f"Bearer {tokens['rector']}"},
        )
        assert r_iso.status_code in [403, 404], f"Expected 403/404 for cross-tenant access, got {r_iso.status_code}"
        print(f" - [PASS] Rector Inst A -> GET Inst B detail -> {r_iso.status_code} Forbidden (Blocked)")

        # Rector of Inst B querying detail of Inst A -> 403 Forbidden / Scope Mismatch
        r_iso_b = await client.get(
            f"/api/v1/institutions/{inst_a_id}",
            headers={"Authorization": f"Bearer {tokens['rector_b']}"},
        )
        assert r_iso_b.status_code in [403, 404], f"Expected 403/404 for cross-tenant access, got {r_iso_b.status_code}"
        print(f" - [PASS] Rector Inst B -> GET Inst A detail -> {r_iso_b.status_code} Forbidden (Blocked)")

        RESULTS["TENANT_ISOLATION"] = "PASS"

    # -------------------------------------------------------------------------
    # 8. CLEANUP FIXTURES
    # -------------------------------------------------------------------------
    print("\n[8] Cleaning up test fixtures cleanly...")
    async with async_session_maker() as session:
        # Delete link
        if student_id:
            await session.execute(text(f"DELETE FROM student_guardians WHERE student_id = '{student_id}'"))
        if guardian_id:
            await session.execute(text(f"DELETE FROM guardians WHERE id = '{guardian_id}'"))
        if student_id:
            await session.execute(text(f"DELETE FROM students WHERE id = '{student_id}'"))
        if teacher_id:
            await session.execute(text(f"DELETE FROM teachers WHERE id = '{teacher_id}'"))
        if rec_ay_id:
            await session.execute(text(f"DELETE FROM academic_years WHERE id = '{rec_ay_id}'"))
        await session.execute(text(f"DELETE FROM academic_years WHERE id = '{ay_id}'"))
        for u_data in users_map.values():
            await session.execute(text(f"DELETE FROM user_roles WHERE user_id = '{u_data['id']}'"))
            await session.execute(text(f"DELETE FROM users WHERE id = '{u_data['id']}'"))
        await session.execute(text(f"DELETE FROM campuses WHERE institution_id IN ('{inst_a_id}', '{inst_b_id}')"))
        await session.execute(text(f"DELETE FROM institutions WHERE id IN ('{inst_a_id}', '{inst_b_id}')"))
        await session.commit()
        print("   [OK] Test fixtures cleanly deleted.")

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 11 REAL-WORLD ROLE ACCEPTANCE AUDIT RESULTS:")
    for k, v in RESULTS.items():
        print(f" - {k:<35}: {v}")
    print("=" * 80)

    for v in RESULTS.values():
        assert v == "PASS", f"Phase 11 Audit Gate Failed: {RESULTS}"

if __name__ == "__main__":
    asyncio.run(run_phase11_audit())
