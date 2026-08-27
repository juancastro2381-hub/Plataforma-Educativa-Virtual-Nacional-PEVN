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
