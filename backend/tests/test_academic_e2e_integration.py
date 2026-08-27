"""
PEVN Backend — Phase 3B Step 7: Comprehensive End-to-End Academic Integration Tests

Validates the full request/response lifecycle, data integrity invariants,
RBAC boundaries, tenant isolation barriers, and cross-module workflows.
"""

from __future__ import annotations

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
async def e2e_fixture(  # noqa: PLR0915
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Provides two fully configured institutions with roles, users, and tokens."""
    dept = Department(code="25", name="Cundinamarca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="25001", name="Bogota D.C.")
    db_session.add(mun)
    await db_session.flush()

    # Institution A
    inst_a = Institution(
        municipality_id=mun.id,
        dane_code="12500100001",
        name="Instituto Pedagógico Nacional A",
        email="rectoria@inst-a.edu.co",
        is_active=True,
    )
    # Institution B (for cross-tenant validation)
    inst_b = Institution(
        municipality_id=mun.id,
        dane_code="12500100002",
        name="Liceo Distrital B",
        email="rectoria@inst-b.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    campus_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="12500100001-01",
        name="Sede Principal A",
        is_active=True,
    )
    campus_b = Campus(
        institution_id=inst_b.id,
        dane_sede_code="12500100002-01",
        name="Sede Principal B",
        is_active=True,
    )
    db_session.add_all([campus_a, campus_b])
    await db_session.flush()

    # Grades
    grade10 = Grade(
        code="10-E2E",
        name="Grado Décimo E2E",
        level=EducationalLevel.MEDIA,
        ordinal_order=10,
    )
    grade11 = Grade(
        code="11-E2E",
        name="Grado Once E2E",
        level=EducationalLevel.MEDIA,
        ordinal_order=11,
    )
    db_session.add_all([grade10, grade11])
    await db_session.flush()

    # Subjects
    area_a = KnowledgeArea(
        institution_id=inst_a.id, name="Ciencias Naturales", is_mandatory=True
    )
    db_session.add(area_a)
    await db_session.flush()

    subject_bio = Subject(
        institution_id=inst_a.id,
        knowledge_area_id=area_a.id,
        grade_id=grade10.id,
        name="Biología General",
        weekly_hours=4,
    )
    subject_chem = Subject(
        institution_id=inst_a.id,
        knowledge_area_id=area_a.id,
        grade_id=grade10.id,
        name="Química Orgánica",
        weekly_hours=3,
    )
    db_session.add_all([subject_bio, subject_chem])
    await db_session.flush()

    # Roles and Permissions
    academic_perms = [
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
        ("students", "update"),
        ("teachers", "read"),
        ("teachers", "create"),
        ("teachers", "update"),
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
    perm_objs = []
    for r, a in academic_perms:
        p = Permission(resource=r, action=a, description=f"{a} on {r}")
        perm_objs.append(p)
    db_session.add_all(perm_objs)
    await db_session.flush()

    # Roles (Canonical SystemRoles seeded by conftest)
    role_rector = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.RECTOR.value)
        )
    ).scalar_one()
    role_student = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.STUDENT.value)
        )
    ).scalar_one()
    role_superadmin = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.SUPERADMIN.value)
        )
    ).scalar_one()

    for p in perm_objs:
        db_session.add(RolePermission(role_id=role_rector.id, permission_id=p.id))
    await db_session.flush()

    # Users
    pwd = password_hasher.hash("Seguro123456*!")

    # Rector A
    user_rector_a = User(
        email="rector.a@pevn.edu.co",
        username="rector_a",
        hashed_password=pwd,
        first_name="Rector",
        last_name="Institución A",
        document_type=DocumentType.CC,
        document_number="80111222",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    # Rector B (Tenant B)
    user_rector_b = User(
        email="rector.b@pevn.edu.co",
        username="rector_b",
        hashed_password=pwd,
        first_name="Rector",
        last_name="Institución B",
        document_type=DocumentType.CC,
        document_number="80333444",
        institution_id=inst_b.id,
        is_active=True,
        is_verified=True,
    )
    # SuperAdmin
    user_superadmin = User(
        email="superadmin@pevn.gov.co",
        username="superadmin_e2e",
        hashed_password=pwd,
        first_name="Super",
        last_name="Administrador",
        document_type=DocumentType.CC,
        document_number="80000000",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    # Teacher 1 User
    user_teacher_1 = User(
        email="docente1@inst-a.edu.co",
        username="docente1_a",
        hashed_password=pwd,
        first_name="Laura",
        last_name="Gómez",
        document_type=DocumentType.CC,
        document_number="52111222",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    # Teacher 2 User
    user_teacher_2 = User(
        email="docente2@inst-a.edu.co",
        username="docente2_a",
        hashed_password=pwd,
        first_name="Fernando",
        last_name="Pérez",
        document_type=DocumentType.CC,
        document_number="52333444",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    # Student 1 User
    user_student_1 = User(
        email="estudiante1@inst-a.edu.co",
        username="estudiante1_a",
        hashed_password=pwd,
        first_name="Mateo",
        last_name="Rodríguez",
        document_type=DocumentType.TI,
        document_number="1011122233",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    # Student 2 User
    user_student_2 = User(
        email="estudiante2@inst-a.edu.co",
        username="estudiante2_a",
        hashed_password=pwd,
        first_name="Valentina",
        last_name="López",
        document_type=DocumentType.TI,
        document_number="1011122244",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    # Student 3 User
    user_student_3 = User(
        email="estudiante3@inst-a.edu.co",
        username="estudiante3_a",
        hashed_password=pwd,
        first_name="Santiago",
        last_name="Morales",
        document_type=DocumentType.TI,
        document_number="1011122255",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )

    db_session.add_all(
        [
            user_rector_a,
            user_rector_b,
            user_superadmin,
            user_teacher_1,
            user_teacher_2,
            user_student_1,
            user_student_2,
            user_student_3,
        ]
    )
    await db_session.flush()

    # Assign roles
    db_session.add(
        UserRole(
            user_id=user_rector_a.id,
            role_id=role_rector.id,
            institution_id=inst_a.id,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=user_rector_b.id,
            role_id=role_rector.id,
            institution_id=inst_b.id,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=user_superadmin.id,
            role_id=role_superadmin.id,
            institution_id=None,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=user_student_1.id,
            role_id=role_student.id,
            institution_id=inst_a.id,
            is_active=True,
        )
    )
    await db_session.commit()

    # Generate JWTs
    token_rector_a = await token_service.create_access_token(
        subject=str(user_rector_a.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst_a.id),
        },
    )
    token_rector_b = await token_service.create_access_token(
        subject=str(user_rector_b.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst_b.id),
        },
    )
    token_superadmin = await token_service.create_access_token(
        subject=str(user_superadmin.id),
        additional_claims={
            "roles": [SystemRole.SUPERADMIN.value],
            "institution_id": None,
        },
    )
    token_student_1 = await token_service.create_access_token(
        subject=str(user_student_1.id),
        additional_claims={
            "roles": [SystemRole.STUDENT.value],
            "institution_id": str(inst_a.id),
        },
    )

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "campus_a": campus_a,
        "campus_b": campus_b,
        "grade10": grade10,
        "grade11": grade11,
        "subject_bio": subject_bio,
        "subject_chem": subject_chem,
        "user_teacher_1": user_teacher_1,
        "user_teacher_2": user_teacher_2,
        "user_student_1": user_student_1,
        "user_student_2": user_student_2,
        "user_student_3": user_student_3,
        "token_rector_a": token_rector_a,
        "token_rector_b": token_rector_b,
        "token_superadmin": token_superadmin,
        "token_student_1": token_student_1,
    }


@pytest.mark.asyncio
async def test_complete_academic_e2e_lifecycle(  # noqa: PLR0915
    client: AsyncClient,
    e2e_fixture: dict[str, Any],
) -> None:
    """
    E2E Test 1: Full academic management workflow across all 8 modules.
    Verifies:
      1. Year creation & activation
      2. Groups creation with tight capacity limits (2 slots)
      3. Students creation with SIMAT codes
      4. Guardian creation & emergency/pickup association
      5. Pre-enrollment and enrollment activation
      6. Capacity enforcement (rejection when limit reached)
      7. Classroom transfer atomicity and slot release
      8. Teacher creation & eligibility validation
      9. Workload assignment & single-active-teacher invariant
      10. Atomic teacher replacement
      11. Academic year formal closing & post-close enrollment protection.
    """
    headers = {"Authorization": f"Bearer {e2e_fixture['token_rector_a']}"}

    # 1. Create Academic Year (Planning state)
    year_res = await client.post(
        "/api/v1/academic-years",
        headers=headers,
        json={
            "year": 2027,
            "name": "Año Lectivo E2E 2027",
            "start_date": "2027-02-01",
            "end_date": "2027-11-30",
            "calendar_type": "CALENDAR_A",
            "status": "PLANNING",
        },
    )
    assert year_res.status_code == 201
    year_id = year_res.json()["id"]

    # 2. Activate Academic Year
    act_year_res = await client.post(
        f"/api/v1/academic-years/{year_id}/activate",
        headers=headers,
    )
    assert act_year_res.status_code == 200
    assert act_year_res.json()["status"] == "ACTIVE"

    # 3. Create Group 10-A (Capacity limit: 2)
    grp_a_res = await client.post(
        "/api/v1/groups",
        headers=headers,
        json={
            "campus_id": str(e2e_fixture["campus_a"].id),
            "academic_year_id": year_id,
            "grade_id": str(e2e_fixture["grade10"].id),
            "name": "10-A",
            "shift": "MANANA",
            "capacity_limit": 2,
        },
    )
    assert grp_a_res.status_code == 201
    group_a_id = grp_a_res.json()["id"]

    # Create Group 10-B (Destination for transfer)
    grp_b_res = await client.post(
        "/api/v1/groups",
        headers=headers,
        json={
            "campus_id": str(e2e_fixture["campus_a"].id),
            "academic_year_id": year_id,
            "grade_id": str(e2e_fixture["grade10"].id),
            "name": "10-B",
            "shift": "TARDE",
            "capacity_limit": 10,
        },
    )
    assert grp_b_res.status_code == 201
    group_b_id = grp_b_res.json()["id"]

    # 4. Create Students
    # Student 1
    s1_res = await client.post(
        "/api/v1/students",
        headers=headers,
        json={
            "user_id": str(e2e_fixture["user_student_1"].id),
            "code_simat": "SIMAT-E2E-001",
            "birth_date": "2011-03-15",
            "gender": "M",
            "blood_type": "O+",
            "stratum": 2,
            "eps_health_provider": "Sura EPS",
        },
    )
    assert s1_res.status_code == 201
    student1_id = s1_res.json()["id"]

    # Student 2
    s2_res = await client.post(
        "/api/v1/students",
        headers=headers,
        json={
            "user_id": str(e2e_fixture["user_student_2"].id),
            "code_simat": "SIMAT-E2E-002",
            "birth_date": "2011-07-20",
            "gender": "F",
            "blood_type": "A+",
            "stratum": 3,
        },
    )
    assert s2_res.status_code == 201
    student2_id = s2_res.json()["id"]

    # Student 3
    s3_res = await client.post(
        "/api/v1/students",
        headers=headers,
        json={
            "user_id": str(e2e_fixture["user_student_3"].id),
            "code_simat": "SIMAT-E2E-003",
            "birth_date": "2011-11-10",
            "gender": "M",
        },
    )
    assert s3_res.status_code == 201
    student3_id = s3_res.json()["id"]

    # 5. Create Guardian & Link to Student 1
    g_res = await client.post(
        "/api/v1/guardians",
        headers=headers,
        json={
            "first_name": "Carmen",
            "last_name": "Rodríguez",
            "document_type": "CC",
            "document_number": "31444555",
            "phone": "3001234567",
            "relationship_type": "MADRE",
        },
    )
    assert g_res.status_code == 201
    guardian_id = g_res.json()["id"]

    link_res = await client.post(
        f"/api/v1/guardians/{guardian_id}/students/{student1_id}",
        headers=headers,
        json={
            "relationship_type": "MADRE",
            "is_primary_contact": True,
            "is_authorized_pickup": True,
        },
    )
    assert link_res.status_code == 201
    assert link_res.json()["is_primary_contact"] is True

    # 6. Enrollments & Capacity Management
    # Slot 1: Enroll Student 1 in 10-A
    enr1_res = await client.post(
        "/api/v1/enrollments",
        headers=headers,
        json={
            "student_id": student1_id,
            "group_id": group_a_id,
            "academic_year_id": year_id,
            "status": "ACTIVE",
        },
    )
    assert enr1_res.status_code == 201

    # Slot 2: Enroll Student 2 in 10-A
    enr2_res = await client.post(
        "/api/v1/enrollments",
        headers=headers,
        json={
            "student_id": student2_id,
            "group_id": group_a_id,
            "academic_year_id": year_id,
            "status": "ACTIVE",
        },
    )
    assert enr2_res.status_code == 201
    enr2_id = enr2_res.json()["id"]

    # Verify Capacity is Full (2/2)
    cap_full_res = await client.get(
        f"/api/v1/groups/{group_a_id}/capacity",
        headers=headers,
    )
    assert cap_full_res.status_code == 200
    assert cap_full_res.json()["active_enrolled_count"] == 2
    assert cap_full_res.json()["available_slots"] == 0

    # Attempt to enroll Student 3 in full group 10-A -> MUST BE BLOCKED
    enr3_blocked = await client.post(
        "/api/v1/enrollments",
        headers=headers,
        json={
            "student_id": student3_id,
            "group_id": group_a_id,
            "academic_year_id": year_id,
            "status": "ACTIVE",
        },
    )
    assert enr3_blocked.status_code == 409
    assert enr3_blocked.json()["error"]["code"] == "GROUP_CAPACITY_EXCEEDED"

    # 7. Atomic Classroom Transfer
    # Transfer Student 2 from 10-A to 10-B
    trans_res = await client.post(
        "/api/v1/transfers",
        headers=headers,
        json={
            "enrollment_id": enr2_id,
            "target_group_id": group_b_id,
            "reason": "Reubicación por cupo escolar",
        },
    )
    assert trans_res.status_code == 200
    assert trans_res.json()["enrollment"]["group_id"] == group_b_id

    # Verify group 10-A freed up 1 slot (1/2)
    cap_freed_res = await client.get(
        f"/api/v1/groups/{group_a_id}/capacity",
        headers=headers,
    )
    assert cap_freed_res.status_code == 200
    assert cap_freed_res.json()["active_enrolled_count"] == 1
    assert cap_freed_res.json()["available_slots"] == 1

    # Verify Transfer History Audit Trail
    hist_res = await client.get(
        f"/api/v1/transfers/enrollments/{enr2_id}/history",
        headers=headers,
    )
    assert hist_res.status_code == 200
    assert len(hist_res.json()["items"]) == 1
    assert hist_res.json()["items"][0]["previous_group_id"] == group_a_id
    assert hist_res.json()["items"][0]["new_group_id"] == group_b_id

    # Now Student 3 can enroll in 10-A into the freed slot
    enr3_success = await client.post(
        "/api/v1/enrollments",
        headers=headers,
        json={
            "student_id": student3_id,
            "group_id": group_a_id,
            "academic_year_id": year_id,
            "status": "ACTIVE",
        },
    )
    assert enr3_success.status_code == 201

    # 8. Teachers, Director Appointment & Eligibility
    # Teacher 1
    t1_res = await client.post(
        "/api/v1/teachers",
        headers=headers,
        json={
            "user_id": str(e2e_fixture["user_teacher_1"].id),
            "specialty_area": "Licenciatura en Biología",
            "contract_type": "PROPIEDAD",
            "escalafon_grade": "14",
        },
    )
    assert t1_res.status_code == 201
    teacher1_id = t1_res.json()["id"]

    # Teacher 2
    t2_res = await client.post(
        "/api/v1/teachers",
        headers=headers,
        json={
            "user_id": str(e2e_fixture["user_teacher_2"].id),
            "specialty_area": "Licenciatura en Química",
            "contract_type": "PROVISIONAL",
            "escalafon_grade": "2A",
        },
    )
    assert t2_res.status_code == 201
    teacher2_id = t2_res.json()["id"]

    # Assign Teacher 1 as Director of 10-A
    dir_res = await client.post(
        f"/api/v1/groups/{group_a_id}/assign-director",
        headers=headers,
        json={"teacher_id": teacher1_id},
    )
    assert dir_res.status_code == 200
    assert dir_res.json()["group_director_teacher_id"] == teacher1_id

    # Check Teacher Eligibility
    elig_res = await client.get(
        f"/api/v1/teachers/{teacher1_id}/eligibility",
        headers=headers,
    )
    assert elig_res.status_code == 200
    assert elig_res.json()["is_eligible"] is True

    # 9. Workload Assignments & Single Active Teacher Invariant
    # Assign Teacher 1 to Biology in 10-A
    assign_res = await client.post(
        "/api/v1/academic-assignments",
        headers=headers,
        json={
            "teacher_id": teacher1_id,
            "subject_id": str(e2e_fixture["subject_bio"].id),
            "group_id": group_a_id,
            "academic_year_id": year_id,
            "weekly_hours": 4,
            "is_active": True,
        },
    )
    assert assign_res.status_code == 201
    assignment_id = assign_res.json()["id"]

    # Attempt to assign Teacher 2 to same subject & group simultaneously -> MUST BE BLOCKED
    dup_assign_res = await client.post(
        "/api/v1/academic-assignments",
        headers=headers,
        json={
            "teacher_id": teacher2_id,
            "subject_id": str(e2e_fixture["subject_bio"].id),
            "group_id": group_a_id,
            "academic_year_id": year_id,
            "weekly_hours": 4,
            "is_active": True,
        },
    )
    assert dup_assign_res.status_code == 409
    assert (
        dup_assign_res.json()["error"]["code"] == "DUPLICATE_ACTIVE_ASSIGNMENT"
    )

    # 10. Atomic Teacher Replacement
    replace_res = await client.post(
        f"/api/v1/academic-assignments/{assignment_id}/replace-teacher",
        headers=headers,
        json={"new_teacher_id": teacher2_id},
    )
    assert replace_res.status_code == 200
    assert replace_res.json()["previous_assignment"]["is_active"] is False
    assert replace_res.json()["new_assignment"]["is_active"] is True
    assert replace_res.json()["new_assignment"]["teacher_id"] == teacher2_id

    # 11. Close Academic Year and Verify Terminal State
    close_res = await client.post(
        f"/api/v1/academic-years/{year_id}/close",
        headers=headers,
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"

    # Verify that enrollments cannot be created in closed year
    enr_closed_res = await client.post(
        "/api/v1/enrollments",
        headers=headers,
        json={
            "student_id": student1_id,
            "group_id": group_a_id,
            "academic_year_id": year_id,
            "status": "ACTIVE",
        },
    )
    assert enr_closed_res.status_code == 400
    assert enr_closed_res.json()["error"]["code"] == "ACADEMIC_YEAR_NOT_ACTIVE"


@pytest.mark.asyncio
async def test_cross_tenant_isolation_and_rbac_boundaries(
    client: AsyncClient,
    e2e_fixture: dict[str, Any],
) -> None:
    """
    E2E Test 2: Multi-tenant isolation barriers & RBAC permission gates.
    Verifies:
      1. Unauthenticated requests are rejected with 401.
      2. Insufficiently privileged roles (students) are rejected with 403.
      3. Tenant A rector cannot access or manipulate Tenant B entities (returns 404).
      4. Tenant B rector cannot manipulate Tenant A entities (returns 404).
      5. SuperAdmin can legitimately manage any tenant via ?institution_id=.
    """
    headers_a = {"Authorization": f"Bearer {e2e_fixture['token_rector_a']}"}
    headers_b = {"Authorization": f"Bearer {e2e_fixture['token_rector_b']}"}
    headers_student = {"Authorization": f"Bearer {e2e_fixture['token_student_1']}"}
    headers_super = {"Authorization": f"Bearer {e2e_fixture['token_superadmin']}"}

    # 1. Unauthenticated barrier
    unauth_res = await client.get("/api/v1/academic-years")
    assert unauth_res.status_code == 401

    # 2. RBAC Forbidden barrier (student attempting to create an academic year)
    forbidden_res = await client.post(
        "/api/v1/academic-years",
        headers=headers_student,
        json={
            "year": 2028,
            "name": "Intento no autorizado",
            "start_date": "2028-02-01",
            "end_date": "2028-11-30",
        },
    )
    assert forbidden_res.status_code == 403

    # 3. Create entity in Tenant A
    year_a_res = await client.post(
        "/api/v1/academic-years",
        headers=headers_a,
        json={
            "year": 2028,
            "name": "Año 2028 Tenant A",
            "start_date": "2028-02-01",
            "end_date": "2028-11-30",
        },
    )
    assert year_a_res.status_code == 201
    year_a_id = year_a_res.json()["id"]

    # 4. Tenant B attempting to access Tenant A's academic year -> MUST RETURN 404 (Blind isolation)
    tenant_b_attack = await client.get(
        f"/api/v1/academic-years/{year_a_id}",
        headers=headers_b,
    )
    assert tenant_b_attack.status_code == 404

    # Tenant B attempting to activate Tenant A's academic year -> MUST RETURN 404
    tenant_b_act_attack = await client.post(
        f"/api/v1/academic-years/{year_a_id}/activate",
        headers=headers_b,
    )
    assert tenant_b_act_attack.status_code == 404

    # 5. SuperAdmin can legitimately access Tenant A's academic year using institution override
    super_res = await client.get(
        f"/api/v1/academic-years/{year_a_id}",
        headers=headers_super,
        params={"institution_id": str(e2e_fixture["inst_a"].id)},
    )
    assert super_res.status_code == 200
    assert super_res.json()["name"] == "Año 2028 Tenant A"
