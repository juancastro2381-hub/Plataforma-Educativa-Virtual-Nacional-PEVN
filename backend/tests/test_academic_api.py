"""
PEVN Backend — Academic Management REST API Integration Tests

Comprehensive end-to-end integration tests for all academic endpoints:
  - Academic Years lifecycle
  - Groups & capacity querying
  - Students & Guardian associations
  - Teachers & eligibility
  - Enrollments & Group transfers
  - Academic workload assignments & teacher replacement
  - Security authentication, authorization, and cross-tenant barrier enforcement.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.grade import EducationalLevel, Grade
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.subject import KnowledgeArea, Subject
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def academic_api_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Fixture providing full institutional hierarchy and authorized tokens."""
    dept = Department(code="76", name="Valle del Cauca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="76001", name="Cali")
    db_session.add(mun)
    await db_session.flush()

    # Institution 1 (Santa Librada)
    inst1 = Institution(
        municipality_id=mun.id,
        dane_code="17600100001",
        name="Colegio Santa Librada",
        email="rectoria@librada.edu.co",
        is_active=True,
    )
    # Institution 2 (San Luis Gonzaga - for cross-tenant tests)
    inst2 = Institution(
        municipality_id=mun.id,
        dane_code="17600100002",
        name="Colegio San Luis",
        email="rectoria@sanluis.edu.co",
        is_active=True,
    )
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    campus1 = Campus(
        institution_id=inst1.id,
        dane_sede_code="17600100001-01",
        name="Sede Principal Librada",
        is_active=True,
    )
    campus2 = Campus(
        institution_id=inst2.id,
        dane_sede_code="17600100002-01",
        name="Sede Principal San Luis",
        is_active=True,
    )
    db_session.add_all([campus1, campus2])
    await db_session.flush()

    # Grade & Subject catalogs
    grade = Grade(
        code="10",
        name="Décimo Grado",
        level=EducationalLevel.MEDIA,
        ordinal_order=10,
    )
    db_session.add(grade)
    await db_session.flush()

    area = KnowledgeArea(
        institution_id=inst1.id,
        name="Matemáticas",
        is_mandatory=True,
    )
    db_session.add(area)
    await db_session.flush()

    subject = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area.id,
        grade_id=grade.id,
        name="Cálculo y Trigonometría",
        weekly_hours=4,
    )
    db_session.add(subject)
    await db_session.flush()

    # Create All Permissions for Rector / Admin Role
    all_perm_specs = [
        ("academic_years", "read"),
        ("academic_years", "create"),
        ("academic_years", "update"),
        ("academic_years", "close"),
        ("groups", "read"),
        ("groups", "create"),
        ("groups", "update"),
        ("groups", "assign_director"),
        ("students", "read"),
        ("students", "create"),
        ("teachers", "read"),
        ("teachers", "create"),
        ("guardians", "read"),
        ("guardians", "create"),
        ("guardians", "link_student"),
        ("enrollments", "read"),
        ("enrollments", "create"),
        ("enrollments", "transfer"),
        ("enrollments", "withdraw"),
        ("academic_assignments", "read"),
        ("academic_assignments", "create"),
        ("academic_assignments", "update"),
        ("subjects", "read"),
        ("subjects", "create"),
    ]

    rector_role_stmt = select(Role).where(Role.name == SystemRole.RECTOR.value)
    rector_role = (await db_session.execute(rector_role_stmt)).scalar_one()

    for res, act in all_perm_specs:
        p_stmt = select(Permission).where(
            Permission.resource == res, Permission.action == act
        )
        perm = (await db_session.execute(p_stmt)).scalar_one_or_none()
        if not perm:
            perm = Permission(resource=res, action=act, description=f"{res}:{act}")
            db_session.add(perm)
            await db_session.flush()

        rp_stmt = select(RolePermission).where(
            RolePermission.role_id == rector_role.id,
            RolePermission.permission_id == perm.id,
        )
        if not (await db_session.execute(rp_stmt)).scalar_one_or_none():
            db_session.add(
                RolePermission(role_id=rector_role.id, permission_id=perm.id)
            )
    await db_session.flush()

    # Rector User in Inst1
    rector1 = User(
        email="rector1@librada.edu.co",
        username="rector1",
        hashed_password=password_hasher.hash("SecureRector123!"),
        first_name="Rector",
        last_name="Librada",
        document_type=DocumentType.CC,
        document_number="80100200",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    # Teacher User in Inst1
    teacher_u1 = User(
        email="prof1@librada.edu.co",
        username="prof1",
        hashed_password=password_hasher.hash("SecureProf123!"),
        first_name="Guillermo",
        last_name="Valencia",
        document_type=DocumentType.CC,
        document_number="79100200",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    # Another Teacher User in Inst1 (for replacement)
    teacher_u2 = User(
        email="prof2@librada.edu.co",
        username="prof2",
        hashed_password=password_hasher.hash("SecureProf123!"),
        first_name="Jorge",
        last_name="Isaacs",
        document_type=DocumentType.CC,
        document_number="79100201",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    # Student User 1
    student_u1 = User(
        email="alum1@librada.edu.co",
        username="alum1",
        hashed_password=password_hasher.hash("SecureAlum123!"),
        first_name="Mateo",
        last_name="Morales",
        document_type=DocumentType.TI,
        document_number="1005112233",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    # Rector User in Inst2 (for cross-tenant tests)
    rector2 = User(
        email="rector2@sanluis.edu.co",
        username="rector2",
        hashed_password=password_hasher.hash("SecureRector123!"),
        first_name="Rector",
        last_name="San Luis",
        document_type=DocumentType.CC,
        document_number="80100202",
        institution_id=inst2.id,
        is_active=True,
        is_verified=True,
    )

    db_session.add_all([rector1, teacher_u1, teacher_u2, student_u1, rector2])
    await db_session.flush()

    # Assign Rector roles
    db_session.add(
        UserRole(
            user_id=rector1.id,
            role_id=rector_role.id,
            institution_id=inst1.id,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=rector2.id,
            role_id=rector_role.id,
            institution_id=inst2.id,
            is_active=True,
        )
    )
    await db_session.commit()

    # Generate access tokens
    rector1_token = await token_service.create_access_token(
        subject=str(rector1.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst1.id),
        },
    )
    rector2_token = await token_service.create_access_token(
        subject=str(rector2.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst2.id),
        },
    )

    return {
        "inst1": inst1,
        "inst2": inst2,
        "campus1": campus1,
        "campus2": campus2,
        "grade": grade,
        "subject": subject,
        "rector1": rector1,
        "teacher_u1": teacher_u1,
        "teacher_u2": teacher_u2,
        "student_u1": student_u1,
        "rector1_headers": {"Authorization": f"Bearer {rector1_token}"},
        "rector2_headers": {"Authorization": f"Bearer {rector2_token}"},
    }


# ===========================================================================
# 1. Authentication & Security Invariant Tests
# ===========================================================================


async def test_academic_endpoints_require_authentication(
    client: AsyncClient,
) -> None:
    """Verify that unauthenticated requests are strictly rejected with 401."""
    res = await client.get("/api/v1/academic-years")
    assert res.status_code == 401
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"


# ===========================================================================
# 2. Academic Year REST API Tests
# ===========================================================================


async def test_academic_year_crud_and_lifecycle_api(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Test full lifecycle of academic years through REST API."""
    headers = academic_api_fixture["rector1_headers"]

    # 1. Create Academic Year
    create_payload = {
        "year": 2026,
        "name": "Año Escolar 2026",
        "start_date": "2026-02-01",
        "end_date": "2026-11-30",
        "calendar_type": "CALENDAR_A",
        "status": "PLANNING",
    }
    res = await client.post(
        "/api/v1/academic-years", json=create_payload, headers=headers
    )
    assert res.status_code == 201
    ay_data = res.json()
    year_id = ay_data["id"]
    assert ay_data["year"] == 2026
    assert ay_data["status"] == "PLANNING"

    # 2. Retrieve by ID
    res = await client.get(f"/api/v1/academic-years/{year_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Año Escolar 2026"

    # 3. List
    res = await client.get("/api/v1/academic-years", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1

    # 4. Activate
    res = await client.post(
        f"/api/v1/academic-years/{year_id}/activate", headers=headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ACTIVE"

    # 5. Close
    res = await client.post(f"/api/v1/academic-years/{year_id}/close", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "CLOSED"


# ===========================================================================
# 3. Groups & Teachers REST API Tests
# ===========================================================================


async def test_teachers_and_groups_api(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Test Teachers, Groups, Capacity, and Director Assignment via REST API."""
    headers = academic_api_fixture["rector1_headers"]
    campus1: Campus = academic_api_fixture["campus1"]
    grade: Grade = academic_api_fixture["grade"]
    teacher_u1: User = academic_api_fixture["teacher_u1"]

    # 1. Create Academic Year for testing groups
    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "year": 2027,
            "name": "Año Escolar 2027",
            "start_date": "2027-02-01",
            "end_date": "2027-11-30",
        },
        headers=headers,
    )
    ay_id = ay_res.json()["id"]

    # 2. Create Teacher Profile
    teacher_res = await client.post(
        "/api/v1/teachers",
        json={
            "user_id": str(teacher_u1.id),
            "specialty_area": "Licenciatura en Matemáticas",
            "contract_type": "PROPIEDAD",
            "escalafon_grade": "14",
        },
        headers=headers,
    )
    assert teacher_res.status_code == 201
    teacher_id = teacher_res.json()["id"]

    # 3. Validate Teacher Eligibility
    elig_res = await client.get(
        f"/api/v1/teachers/{teacher_id}/eligibility", headers=headers
    )
    assert elig_res.status_code == 200
    assert elig_res.json()["is_eligible"] is True

    # 4. Create Group
    group_res = await client.post(
        "/api/v1/groups",
        json={
            "campus_id": str(campus1.id),
            "academic_year_id": ay_id,
            "grade_id": str(grade.id),
            "name": "10-01",
            "shift": "MANANA",
            "capacity_limit": 30,
            "director_teacher_id": teacher_id,
        },
        headers=headers,
    )
    assert group_res.status_code == 201
    group_id = group_res.json()["id"]
    assert group_res.json()["name"] == "10-01"

    # 5. Check Group Capacity
    cap_res = await client.get(f"/api/v1/groups/{group_id}/capacity", headers=headers)
    assert cap_res.status_code == 200
    assert cap_res.json()["capacity_limit"] == 30
    assert cap_res.json()["available_slots"] == 30


# ===========================================================================
# 4. Students & Guardians REST API Tests
# ===========================================================================


async def test_students_and_guardians_api(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Test Student creation, Guardian creation, and association via REST API."""
    headers = academic_api_fixture["rector1_headers"]
    student_u1: User = academic_api_fixture["student_u1"]

    # 1. Create Student Profile
    student_res = await client.post(
        "/api/v1/students",
        json={
            "user_id": str(student_u1.id),
            "code_simat": "SIMAT-CALI-2026-API-01",
            "birth_date": "2009-08-15",
            "gender": "M",
            "stratum": 3,
            "eps_health_provider": "Sura EPS",
        },
        headers=headers,
    )
    assert student_res.status_code == 201
    student_id = student_res.json()["id"]
    assert student_res.json()["code_simat"] == "SIMAT-CALI-2026-API-01"

    # 2. Create Guardian without mandatory email (per OPEN-DECISION-3A-01)
    guardian_res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Esperanza",
            "last_name": "Morales",
            "document_type": "CC",
            "document_number": f"31{uuid.uuid4().hex[:6]}",
            "phone": "3185551234",
            "email": None,
            "address": "Carrera 4 # 12-40",
            "relationship_type": "MADRE",
        },
        headers=headers,
    )
    assert guardian_res.status_code == 201
    guardian_id = guardian_res.json()["id"]

    # 3. Associate Guardian with Student
    assoc_res = await client.post(
        f"/api/v1/guardians/{guardian_id}/students/{student_id}",
        json={
            "relationship_type": "MADRE",
            "is_primary_contact": True,
            "is_authorized_pickup": True,
        },
        headers=headers,
    )
    assert assoc_res.status_code == 201
    assert assoc_res.json()["is_primary_contact"] is True

    # 4. Query student guardians
    guardians_list_res = await client.get(
        f"/api/v1/students/{student_id}/guardians", headers=headers
    )
    assert guardians_list_res.status_code == 200
    assert len(guardians_list_res.json()) >= 1


# ===========================================================================
# 5. Enrollments, Transfers & Academic Assignments REST API Tests
# ===========================================================================


async def test_enrollments_transfers_and_assignments_api(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Test full Enrollment lifecycle, Group transfers, and Teacher Assignments."""
    headers = academic_api_fixture["rector1_headers"]
    campus1: Campus = academic_api_fixture["campus1"]
    grade: Grade = academic_api_fixture["grade"]
    subject: Subject = academic_api_fixture["subject"]
    teacher_u1: User = academic_api_fixture["teacher_u1"]
    teacher_u2: User = academic_api_fixture["teacher_u2"]
    student_u1: User = academic_api_fixture["student_u1"]

    # Setup AY 2028
    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "year": 2028,
            "name": "Año Escolar 2028",
            "start_date": "2028-02-01",
            "end_date": "2028-11-30",
        },
        headers=headers,
    )
    ay_id = ay_res.json()["id"]

    # Activate Academic Year to allow enrollments
    act_res = await client.post(
        f"/api/v1/academic-years/{ay_id}/activate",
        headers=headers,
    )
    assert act_res.status_code == 200

    # Setup Group A (capacity 2) and Group B (capacity 5)
    grp_a_res = await client.post(
        "/api/v1/groups",
        json={
            "campus_id": str(campus1.id),
            "academic_year_id": ay_id,
            "grade_id": str(grade.id),
            "name": "10-A",
            "capacity_limit": 2,
        },
        headers=headers,
    )
    grp_a_id = grp_a_res.json()["id"]

    grp_b_res = await client.post(
        "/api/v1/groups",
        json={
            "campus_id": str(campus1.id),
            "academic_year_id": ay_id,
            "grade_id": str(grade.id),
            "name": "10-B",
            "capacity_limit": 5,
        },
        headers=headers,
    )
    grp_b_id = grp_b_res.json()["id"]

    # Setup Teachers 1 and 2
    t1_res = await client.post(
        "/api/v1/teachers",
        json={
            "user_id": str(teacher_u1.id),
            "specialty_area": "Matemáticas",
        },
        headers=headers,
    )
    t1_id = t1_res.json()["id"]

    t2_res = await client.post(
        "/api/v1/teachers",
        json={
            "user_id": str(teacher_u2.id),
            "specialty_area": "Física",
        },
        headers=headers,
    )
    t2_id = t2_res.json()["id"]

    # Setup Student 1
    stud_res = await client.post(
        "/api/v1/students",
        json={
            "user_id": str(student_u1.id),
            "code_simat": f"SIMAT-{uuid.uuid4().hex[:8]}",
            "birth_date": "2009-03-12",
        },
        headers=headers,
    )
    stud_id = stud_res.json()["id"]

    # 1. Create Enrollment in Group A
    enroll_res = await client.post(
        "/api/v1/enrollments",
        json={
            "student_id": stud_id,
            "group_id": grp_a_id,
            "academic_year_id": ay_id,
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert enroll_res.status_code == 201
    enroll_id = enroll_res.json()["id"]

    # 2. Reject Duplicate Active Enrollment (Inviolable Invariant) -> 409 Conflict
    dup_res = await client.post(
        "/api/v1/enrollments",
        json={
            "student_id": stud_id,
            "group_id": grp_b_id,
            "academic_year_id": ay_id,
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "STUDENT_ALREADY_ENROLLED_ACTIVE"

    # 3. Transfer Student to Group B
    transfer_res = await client.post(
        "/api/v1/transfers",
        json={
            "enrollment_id": enroll_id,
            "target_group_id": grp_b_id,
            "reason": "Cambio de salón solicitado por acudiente",
        },
        headers=headers,
    )
    assert transfer_res.status_code == 200
    assert transfer_res.json()["enrollment"]["group_id"] == grp_b_id
    assert transfer_res.json()["transfer_history"]["new_group_id"] == grp_b_id

    # 4. Query Transfer History
    hist_res = await client.get(
        f"/api/v1/transfers/enrollments/{enroll_id}/history", headers=headers
    )
    assert hist_res.status_code == 200
    assert hist_res.json()["total"] == 1

    # 5. Create Academic Assignment (Teacher 1 -> Subject in Group A)
    assign_res = await client.post(
        "/api/v1/academic-assignments",
        json={
            "teacher_id": t1_id,
            "subject_id": str(subject.id),
            "group_id": grp_a_id,
            "academic_year_id": ay_id,
            "weekly_hours": 4,
            "is_active": True,
        },
        headers=headers,
    )
    assert assign_res.status_code == 201
    assign_id = assign_res.json()["id"]

    # 6. Reject duplicate active assignment -> 409 Conflict
    dup_assign_res = await client.post(
        "/api/v1/academic-assignments",
        json={
            "teacher_id": t2_id,
            "subject_id": str(subject.id),
            "group_id": grp_a_id,
            "academic_year_id": ay_id,
            "weekly_hours": 4,
            "is_active": True,
        },
        headers=headers,
    )
    assert dup_assign_res.status_code == 409
    assert dup_assign_res.json()["error"]["code"] == "DUPLICATE_ACTIVE_ASSIGNMENT"

    # 7. Atomically Replace Teacher (Teacher 1 -> Teacher 2)
    replace_res = await client.post(
        f"/api/v1/academic-assignments/{assign_id}/replace-teacher",
        json={"new_teacher_id": t2_id},
        headers=headers,
    )
    assert replace_res.status_code == 200
    assert replace_res.json()["previous_assignment"]["is_active"] is False
    assert replace_res.json()["new_assignment"]["is_active"] is True
    assert replace_res.json()["new_assignment"]["teacher_id"] == t2_id

    # 8. Withdraw & Graduate endpoints
    with_res = await client.post(
        f"/api/v1/enrollments/{enroll_id}/withdraw",
        json={"reason": "Cambio de domicilio fuera de la ciudad"},
        headers=headers,
    )
    assert with_res.status_code == 200
    assert with_res.json()["status"] == "WITHDRAWN"


# ===========================================================================
# 6. Cross-Tenant Barrier Enforcement REST API Tests
# ===========================================================================


async def test_cross_tenant_isolation_barrier(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Verify that Rector in Institution 2 cannot access Institution 1 records."""
    rector2_headers = academic_api_fixture["rector2_headers"]
    rector1_headers = academic_api_fixture["rector1_headers"]

    # Inst 1 creates an academic year
    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "year": 2029,
            "name": "Año 2029 Inst 1",
            "start_date": "2029-02-01",
            "end_date": "2029-11-30",
        },
        headers=rector1_headers,
    )
    ay1_id = ay_res.json()["id"]

    # Inst 2 Rector tries to access Inst 1 Academic Year -> 404 (Not Found in tenant)
    res = await client.get(
        f"/api/v1/academic-years/{ay1_id}",
        headers=rector2_headers,
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ACADEMIC_YEAR_NOT_FOUND"


# ===========================================================================
# 7. Phase 12B — Unified Teacher Provisioning API Tests
# ===========================================================================


async def test_provision_new_teacher_api(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Test creating a completely new teacher with on-the-fly User + Role provisioning."""
    headers = academic_api_fixture["rector1_headers"]
    inst1: Institution = academic_api_fixture["inst1"]

    new_teacher_payload = {
        "new_user": {
            "first_name": "Carlos Alberto",
            "last_name": "Gómez Restrepo",
            "document_type": "CC",
            "document_number": "20202020",
            "email": "carlos.gomez@librada.edu.co",
            "phone": "3001234567",
        },
        "specialty_area": "Licenciatura en Física y Química",
        "contract_type": "PROPIEDAD",
        "escalafon_grade": "2A",
    }

    res = await client.post("/api/v1/teachers", json=new_teacher_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["specialty_area"] == "Licenciatura en Física y Química"
    assert data["contract_type"] == "PROPIEDAD"
    assert data["escalafon_grade"] == "2A"
    assert data["user"] is not None
    assert data["user"]["document_number"] == "20202020"
    assert data["user"]["email"] == "carlos.gomez@librada.edu.co"
    assert data["user"]["first_name"] == "Carlos Alberto"

    # Verify User in Database
    user_id = uuid.UUID(data["user"]["id"])
    user_stmt = select(User).where(User.id == user_id)
    user = (await db_session.execute(user_stmt)).scalar_one_or_none()
    assert user is not None
    assert user.institution_id == inst1.id
    assert user.is_active is True
    assert user.is_verified is False
    assert user.must_change_password is True

    # Verify UserRole in Database
    ur_stmt = select(UserRole).join(Role).where(
        UserRole.user_id == user_id,
        Role.name == "teacher",
    )
    ur = (await db_session.execute(ur_stmt)).scalar_one_or_none()
    assert ur is not None
    assert ur.institution_id == inst1.id
    assert ur.is_active is True


async def test_provision_new_teacher_duplicate_prevention_api(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Test duplicate document and email rejection returning HTTP 409."""
    headers = academic_api_fixture["rector1_headers"]

    payload1 = {
        "new_user": {
            "first_name": "Ana",
            "last_name": "Ruiz",
            "document_type": "CC",
            "document_number": "30303030",
            "email": "ana.ruiz@librada.edu.co",
        },
        "specialty_area": "Humanidades",
        "contract_type": "PROVISIONAL",
    }
    res1 = await client.post("/api/v1/teachers", json=payload1, headers=headers)
    assert res1.status_code == 201

    # Duplicate Document Number -> 409 Conflict
    payload_dup_doc = {
        "new_user": {
            "first_name": "Otro",
            "last_name": "Docente",
            "document_type": "CC",
            "document_number": "30303030",
            "email": "otro.docente@librada.edu.co",
        },
        "specialty_area": "Filosofía",
        "contract_type": "PROVISIONAL",
    }
    res_dup_doc = await client.post("/api/v1/teachers", json=payload_dup_doc, headers=headers)
    assert res_dup_doc.status_code == 409
    assert res_dup_doc.json()["error"]["code"] == "IDENTITY_CONFLICT"

    # Duplicate Email -> 409 Conflict
    payload_dup_email = {
        "new_user": {
            "first_name": "Tercero",
            "last_name": "Docente",
            "document_type": "CC",
            "document_number": "40404040",
            "email": "ana.ruiz@librada.edu.co",
        },
        "specialty_area": "Música",
        "contract_type": "PROVISIONAL",
    }
    res_dup_email = await client.post("/api/v1/teachers", json=payload_dup_email, headers=headers)
    assert res_dup_email.status_code == 409
    assert res_dup_email.json()["error"]["code"] == "IDENTITY_CONFLICT"


async def test_list_grades_api(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Test querying the standardized national grade catalog via GET /api/v1/grades."""
    headers = academic_api_fixture["rector1_headers"]

    response = await client.get("/api/v1/grades", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["total"] >= 12
    assert len(data["items"]) == data["total"]

    # Verify sorting by ordinal_order ascending
    orders = [g["ordinal_order"] for g in data["items"]]
    assert orders == sorted(orders)

    # Verify first grade is Transición (order 0) and contains canonical fields
    transicion = data["items"][0]
    assert transicion["code"] == "TRANSICION"
    assert transicion["name"] == "Transición"
    assert transicion["level"] == "PREESCOLAR"
    assert transicion["ordinal_order"] == 0
    assert "id" in transicion

    # Verify unauthenticated call is rejected
    unauth_res = await client.get("/api/v1/grades")
    assert unauth_res.status_code == 401


# ===========================================================================
# 7. Unified Student Provisioning Tests (Phase 13D.2)
# ===========================================================================


async def test_unified_student_provisioning_api(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Test full unified student provisioning lifecycle (Phase 13D.2)."""
    headers = academic_api_fixture["rector1_headers"]
    rector2_headers = academic_api_fixture["rector2_headers"]
    student_u1: User = academic_api_fixture["student_u1"]

    # 1. Existing-user mode: create Student profile linked to existing user
    res_existing = await client.post(
        "/api/v1/students",
        json={
            "user_id": str(student_u1.id),
            "code_simat": "SIMAT-2026-EXISTING-01",
            "birth_date": "2010-03-15",
            "gender": "M",
            "blood_type": "O+",
            "stratum": 2,
        },
        headers=headers,
    )
    assert res_existing.status_code == 201
    assert res_existing.json()["user_id"] == str(student_u1.id)
    assert res_existing.json()["code_simat"] == "SIMAT-2026-EXISTING-01"

    # 2. New-user mode (Natalia Castro): on-the-fly User + Student provisioning
    res_new = await client.post(
        "/api/v1/students",
        json={
            "new_user": {
                "first_name": "Natalia",
                "last_name": "Castro",
                "document_type": "TI",
                "document_number": "1098765432",
                "email": "natalia.castro@librada.edu.co",
                "phone": "3159998877",
            },
            "code_simat": "SIMAT-2026-NATALIA-01",
            "birth_date": "2011-05-20",
            "gender": "F",
            "blood_type": "A+",
            "stratum": 3,
            "eps_health_provider": "Sanitas EPS",
        },
        headers=headers,
    )
    assert res_new.status_code == 201
    new_student_data = res_new.json()
    new_user_id = new_student_data["user_id"]
    assert new_student_data["code_simat"] == "SIMAT-2026-NATALIA-01"

    # Verify created User in DB has role 'student' and correct tenant
    user_stmt = select(User).where(User.id == uuid.UUID(new_user_id))
    user_obj = (await db_session.execute(user_stmt)).scalar_one()
    assert user_obj.first_name == "Natalia"
    assert user_obj.last_name == "Castro"
    assert user_obj.email == "natalia.castro@librada.edu.co"
    assert str(user_obj.institution_id) == str(academic_api_fixture["inst1"].id)

    # 3. Full-Name Search: Verify GET /api/v1/users?search=Natalia+Castro returns the user
    search_res = await client.get("/api/v1/users?search=Natalia+Castro", headers=headers)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1
    matched_ids = [u["id"] for u in search_data["items"]]
    assert new_user_id in matched_ids

    # 4. Mutually Exclusive Validation: both provided -> 422 Unprocessable Entity
    res_both = await client.post(
        "/api/v1/students",
        json={
            "user_id": str(student_u1.id),
            "new_user": {
                "first_name": "Invalido",
                "last_name": "Ambos",
                "document_type": "TI",
                "document_number": "11111111",
                "email": "ambos@librada.edu.co",
            },
            "code_simat": "SIMAT-2026-BOTH",
            "birth_date": "2010-01-01",
        },
        headers=headers,
    )
    assert res_both.status_code == 422

    # 5. Mutually Exclusive Validation: neither provided -> 422 Unprocessable Entity
    res_neither = await client.post(
        "/api/v1/students",
        json={
            "code_simat": "SIMAT-2026-NEITHER",
            "birth_date": "2010-01-01",
        },
        headers=headers,
    )
    assert res_neither.status_code == 422

    # 6. Tenant Isolation: Rector from Inst2 cannot link user from Inst1
    res_cross_tenant = await client.post(
        "/api/v1/students",
        json={
            "user_id": str(student_u1.id),
            "code_simat": "SIMAT-CROSS-INST",
            "birth_date": "2010-01-01",
        },
        headers=rector2_headers,
    )
    assert res_cross_tenant.status_code in [400, 403, 404]

    # 7. Duplicate User Identity Conflict: creating new_user with duplicate document -> 409
    res_dup_doc = await client.post(
        "/api/v1/students",
        json={
            "new_user": {
                "first_name": "Duplicado",
                "last_name": "Documento",
                "document_type": "TI",
                "document_number": "1098765432",  # Same as Natalia Castro
                "email": "otro.correo@librada.edu.co",
            },
            "code_simat": "SIMAT-2026-DUP-DOC",
            "birth_date": "2010-01-01",
        },
        headers=headers,
    )
    assert res_dup_doc.status_code == 409
    assert res_dup_doc.json()["error"]["code"] == "IDENTITY_CONFLICT"

    # 8. Transaction Rollback: Force domain failure during Student creation (duplicate SIMAT)
    res_rollback = await client.post(
        "/api/v1/students",
        json={
            "new_user": {
                "first_name": "Rollback",
                "last_name": "Test",
                "document_type": "TI",
                "document_number": "9988776655",
                "email": "rollback.test@librada.edu.co",
            },
            "code_simat": "SIMAT-2026-NATALIA-01",  # Duplicate SIMAT -> AcademicDomainError (400)
            "birth_date": "2010-01-01",
            "stratum": 2,
        },
        headers=headers,
    )
    assert res_rollback.status_code == 400

    # Verify that the user "9988776655" was NOT persisted (rolled back atomically)
    orphan_stmt = select(User).where(User.document_number == "9988776655")
    orphan_user = (await db_session.execute(orphan_stmt)).scalar_one_or_none()
    assert orphan_user is None


@pytest.mark.asyncio
async def test_subjects_api_and_academic_assignments(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Verify Subjects catalog listing, creation, and Academic Assignment workflow."""
    headers = academic_api_fixture["rector1_headers"]
    campus1: Campus = academic_api_fixture["campus1"]
    grade: Grade = academic_api_fixture["grade"]
    existing_subject: Subject = academic_api_fixture["subject"]

    # 1. GET /api/v1/subjects (List subjects with grade filter)
    res_subjects = await client.get(
        f"/api/v1/subjects?grade_id={grade.id}",
        headers=headers,
    )
    assert res_subjects.status_code == 200
    data_subjects = res_subjects.json()
    assert data_subjects["total"] >= 1
    assert any(s["name"] == "Cálculo y Trigonometría" for s in data_subjects["items"])

    # 2. POST /api/v1/subjects (Create custom subject)
    res_new_sub = await client.post(
        "/api/v1/subjects",
        json={
            "knowledge_area_id": str(existing_subject.knowledge_area_id),
            "grade_id": str(grade.id),
            "name": "Estadística Aplicada",
            "weekly_hours": 3,
        },
        headers=headers,
    )
    assert res_new_sub.status_code == 201
    assert res_new_sub.json()["name"] == "Estadística Aplicada"
    custom_subject_id = res_new_sub.json()["id"]

    # 3. Setup AY 2029, Teacher, and Group for Academic Assignment
    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "year": 2029,
            "name": "Año Escolar 2029",
            "start_date": "2029-02-01",
            "end_date": "2029-11-30",
        },
        headers=headers,
    )
    assert ay_res.status_code == 201
    ay_id = ay_res.json()["id"]

    t_res = await client.post(
        "/api/v1/teachers",
        json={
            "new_user": {
                "first_name": "Profesor",
                "last_name": "Asignaciones",
                "document_type": "CC",
                "document_number": "7788990011",
                "email": "prof.asg@librada.edu.co",
            },
            "specialty_area": "Estadística y Probabilidad",
        },
        headers=headers,
    )
    assert t_res.status_code == 201
    teacher_id = t_res.json()["id"]

    grp_res = await client.post(
        "/api/v1/groups",
        json={
            "campus_id": str(campus1.id),
            "academic_year_id": ay_id,
            "grade_id": str(grade.id),
            "name": "10-C",
            "capacity_limit": 30,
        },
        headers=headers,
    )
    assert grp_res.status_code == 201
    group_id = grp_res.json()["id"]

    # 4. POST /api/v1/academic-assignments (Create assignment with canonical UUIDs)
    res_assignment = await client.post(
        "/api/v1/academic-assignments",
        json={
            "teacher_id": teacher_id,
            "subject_id": custom_subject_id,
            "group_id": group_id,
            "academic_year_id": ay_id,
            "weekly_hours": 3,
            "is_active": True,
        },
        headers=headers,
    )
    assert res_assignment.status_code == 201
    assignment_data = res_assignment.json()
    assert assignment_data["teacher_id"] == teacher_id
    assert assignment_data["subject_id"] == custom_subject_id
    assert assignment_data["weekly_hours"] == 3
    assert assignment_data["is_active"] is True
    assignment_id = assignment_data["id"]

    # 5. Duplicate active assignment rejection -> 409
    res_dup = await client.post(
        "/api/v1/academic-assignments",
        json={
            "teacher_id": teacher_id,
            "subject_id": custom_subject_id,
            "group_id": group_id,
            "academic_year_id": ay_id,
            "weekly_hours": 3,
            "is_active": True,
        },
        headers=headers,
    )
    assert res_dup.status_code == 409

    # 6. Invalid UUID format rejection -> 422
    res_invalid_uuid = await client.post(
        "/api/v1/academic-assignments",
        json={
            "teacher_id": "invalid-teacher-uuid",
            "subject_id": "3000022",
            "group_id": "003332",
            "academic_year_id": "2026",
            "weekly_hours": 5,
        },
        headers=headers,
    )
    assert res_invalid_uuid.status_code == 422


# ===========================================================================
# 12. Phase 13E.5 Regressions: Guardian "ABUELO_A" / "TIO_A" & Auto-Seeded Curriculum
# ===========================================================================


async def test_phase13e5_guardian_abuelo_and_tio_registration(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Verify registration of guardians with ABUELO_A and TIO_A relationships."""
    headers = academic_api_fixture["rector1_headers"]

    # 1. Register guardian as ABUELO_A
    doc_num_abuelo = f"88{uuid.uuid4().hex[:6]}"
    res_abuelo = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Guillermo",
            "last_name": "Castro",
            "document_type": "CC",
            "document_number": doc_num_abuelo,
            "phone": "3119876543",
            "email": "guillermo@correo.com",
            "relationship_type": "ABUELO_A",
        },
        headers=headers,
    )
    assert res_abuelo.status_code == 201
    abuelo_data = res_abuelo.json()
    assert abuelo_data["relationship_type"] == "ABUELO_A"
    assert abuelo_data["document_number"] == doc_num_abuelo

    # 2. Register guardian as TIO_A
    doc_num_tio = f"89{uuid.uuid4().hex[:6]}"
    res_tio = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Carlos",
            "last_name": "Castro",
            "document_type": "CC",
            "document_number": doc_num_tio,
            "phone": "3119876544",
            "email": "carlos@correo.com",
            "relationship_type": "TIO_A",
        },
        headers=headers,
    )
    assert res_tio.status_code == 201
    tio_data = res_tio.json()
    assert tio_data["relationship_type"] == "TIO_A"


async def test_phase13e5_assignment_creation_with_auto_seeded_curriculum(
    client: AsyncClient,
    academic_api_fixture: dict[str, Any],
) -> None:
    """Verify that auto-seeded statutory subjects are committed and valid for AcademicAssignment creation."""
    headers = academic_api_fixture["rector1_headers"]
    campus1: Campus = academic_api_fixture["campus1"]
    grade: Grade = academic_api_fixture["grade"]
    teacher_u1: User = academic_api_fixture["teacher_u1"]

    # 1. Call GET /api/v1/subjects (triggers auto-seeding of statutory curriculum)
    res_subjects = await client.get("/api/v1/subjects", headers=headers)
    assert res_subjects.status_code == 200
    subjects_list = res_subjects.json()["items"]
    assert len(subjects_list) >= 1
    selected_subject = subjects_list[0]

    # 2. Create an academic year and group
    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "year": 2029,
            "name": "Año Escolar 2029",
            "start_date": "2029-02-01",
            "end_date": "2029-11-30",
        },
        headers=headers,
    )
    assert ay_res.status_code == 201
    ay_id = ay_res.json()["id"]

    group_res = await client.post(
        "/api/v1/groups",
        json={
            "campus_id": str(campus1.id),
            "academic_year_id": ay_id,
            "grade_id": str(grade.id),
            "name": "Grupo 10-A-2029",
            "shift": "MANANA",
            "capacity_limit": 35,
        },
        headers=headers,
    )
    assert group_res.status_code == 201
    group_id = group_res.json()["id"]

    # 3. Create Teacher profile
    teacher_res = await client.post(
        "/api/v1/teachers",
        json={
            "user_id": str(teacher_u1.id),
            "specialty_area": "Ciencias Básicas",
            "contract_type": "PROPIEDAD",
        },
        headers=headers,
    )
    assert teacher_res.status_code in (201, 409)
    if teacher_res.status_code == 201:
        teacher_id = teacher_res.json()["id"]
    else:
        # Fetch existing teacher
        teachers_list = await client.get("/api/v1/teachers", headers=headers)
        teacher_id = teachers_list.json()["items"][0]["id"]

    # 4. Create Academic Assignment using the auto-seeded subject
    res_assignment = await client.post(
        "/api/v1/academic-assignments",
        json={
            "teacher_id": teacher_id,
            "subject_id": selected_subject["id"],
            "group_id": group_id,
            "academic_year_id": ay_id,
            "weekly_hours": 4,
            "is_active": True,
        },
        headers=headers,
    )
    assert res_assignment.status_code == 201
    assignment_data = res_assignment.json()
    assert assignment_data["subject_id"] == selected_subject["id"]
    assert assignment_data["group_id"] == group_id
    assert assignment_data["weekly_hours"] == 4





