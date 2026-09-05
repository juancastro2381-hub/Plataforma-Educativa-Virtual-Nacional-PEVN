"""
PEVN Backend — Teacher Academic Scope Integration Tests (Phase 13E.1)

Authoritative verification of Anti-IDOR and Least Privilege enforcement:
- Generic endpoints (/api/v1/students, /api/v1/groups, /api/v1/enrollments)
- Single-resource access (/api/v1/students/{id}, /api/v1/groups/{id}, /api/v1/enrollments/{id})
- Multi-teacher segregation within the same institution
- Group director access exception
- Multi-group assignment unions
- Rector / directive roles full institutional visibility preservation
- Cross-tenant strict isolation
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def academic_scope_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """
    Sets up a comprehensive institutional test environment:
    - Institution 1 (Colegio Central) & Institution 2 (Colegio Norte - Cross Tenant)
    - Rector with full permissions
    - Teacher A (Assigned to Grade 3A - Math)
    - Teacher B (Assigned to Grade 5B - Science)
    - Teacher C (New Teacher with 0 assignments)
    - Teacher D (Assigned to Grade 3A - Spanish, sharing group with Teacher A)
    - Teacher E (Group Director of Grade 4A without subject assignment)
    - Teacher F (Multi-group: Assigned to 3A and 5B)
    - Students in 3A (Student 1, Student 2), 5B (Student 3), 4A (Student 4), Inst2 (Student 5)
    """
    dept = Department(code="11", name="Bogota D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogota")
    db_session.add(mun)
    await db_session.flush()

    # Institutions
    inst1 = Institution(
        municipality_id=mun.id,
        dane_code="11100100001",
        name="Colegio Central Bogotá",
        email="rectoria@central.edu.co",
        is_active=True,
    )
    inst2 = Institution(
        municipality_id=mun.id,
        dane_code="11100100002",
        name="Colegio Norte Bogotá",
        email="rectoria@norte.edu.co",
        is_active=True,
    )
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    campus1 = Campus(
        institution_id=inst1.id,
        dane_sede_code="11100100001-01",
        name="Sede Principal Central",
        is_active=True,
    )
    campus2 = Campus(
        institution_id=inst2.id,
        dane_sede_code="11100100002-01",
        name="Sede Principal Norte",
        is_active=True,
    )
    db_session.add_all([campus1, campus2])
    await db_session.flush()

    # Academic Year
    ay1 = AcademicYear(
        institution_id=inst1.id,
        name="Año 2026 Central",
        year=2026,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 11, 30),
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
    )
    ay2 = AcademicYear(
        institution_id=inst2.id,
        name="Año 2026 Norte",
        year=2026,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 11, 30),
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
    )
    db_session.add_all([ay1, ay2])
    await db_session.flush()

    # Grades
    grade3 = Grade(code="03", name="Tercero", level=EducationalLevel.PRIMARIA, ordinal_order=3)
    grade4 = Grade(code="04", name="Cuarto", level=EducationalLevel.PRIMARIA, ordinal_order=4)
    grade5 = Grade(code="05", name="Quinto", level=EducationalLevel.PRIMARIA, ordinal_order=5)
    db_session.add_all([grade3, grade4, grade5])
    await db_session.flush()

    # Knowledge Areas & Subjects
    area_math = KnowledgeArea(institution_id=inst1.id, name="Matemáticas", is_mandatory=True)
    area_sci = KnowledgeArea(institution_id=inst1.id, name="Ciencias", is_mandatory=True)
    area_spa = KnowledgeArea(institution_id=inst1.id, name="Humanidades", is_mandatory=True)
    db_session.add_all([area_math, area_sci, area_spa])
    await db_session.flush()

    subj_math_3a = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area_math.id,
        grade_id=grade3.id,
        name="Matemáticas 3",
        weekly_hours=4,
    )
    subj_sci_5b = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area_sci.id,
        grade_id=grade5.id,
        name="Ciencias Naturales 5",
        weekly_hours=4,
    )
    subj_spa_3a = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area_spa.id,
        grade_id=grade3.id,
        name="Lengua Castellana 3",
        weekly_hours=4,
    )
    db_session.add_all([subj_math_3a, subj_sci_5b, subj_spa_3a])
    await db_session.flush()

    # Groups in Inst1
    group_3a = Group(
        academic_year_id=ay1.id,
        campus_id=campus1.id,
        grade_id=grade3.id,
        name="3-A",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    group_4a = Group(
        academic_year_id=ay1.id,
        campus_id=campus1.id,
        grade_id=grade4.id,
        name="4-A",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    group_5b = Group(
        academic_year_id=ay1.id,
        campus_id=campus1.id,
        grade_id=grade5.id,
        name="5-B",
        shift=ShiftEnum.TARDE,
        capacity_limit=35,
    )
    # Group in Inst2 (Cross Tenant)
    group_inst2 = Group(
        academic_year_id=ay2.id,
        campus_id=campus2.id,
        grade_id=grade3.id,
        name="3-A-Norte",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    db_session.add_all([group_3a, group_4a, group_5b, group_inst2])
    await db_session.flush()

    # Query already bootstrapped Roles
    role_rector_stmt = select(Role).where(Role.name == SystemRole.RECTOR.value)
    role_rector = (await db_session.execute(role_rector_stmt)).scalar_one()
    role_teacher_stmt = select(Role).where(Role.name == SystemRole.TEACHER.value)
    role_teacher = (await db_session.execute(role_teacher_stmt)).scalar_one()

    pwd_hash = password_hasher.hash("Colombia2026*!Secure")

    # 1. Rector User
    rector_user = User(
        institution_id=inst1.id,
        email="rector@central.edu.co",
        username="rector.central",
        hashed_password=pwd_hash,
        first_name="Guillermo",
        last_name="Rector",
        document_type=DocumentType.CC,
        document_number="10000001",
        is_active=True,
    )
    db_session.add(rector_user)
    await db_session.flush()
    db_session.add(
        UserRole(
            user_id=rector_user.id,
            role_id=role_rector.id,
            institution_id=inst1.id,
            is_active=True,
        )
    )

    # Helper to create Teacher
    async def create_teacher_user(email: str, username: str, doc: str, first: str, last: str) -> tuple[User, Teacher]:
        u = User(
            institution_id=inst1.id,
            email=email,
            username=username,
            hashed_password=pwd_hash,
            first_name=first,
            last_name=last,
            document_type=DocumentType.CC,
            document_number=doc,
            is_active=True,
        )
        db_session.add(u)
        await db_session.flush()
        db_session.add(
            UserRole(
                user_id=u.id,
                role_id=role_teacher.id,
                institution_id=inst1.id,
                is_active=True,
            )
        )
        t = Teacher(
            user_id=u.id,
            institution_id=inst1.id,
            contract_type=TeacherContractType.PROPIEDAD,
            specialty_area="Docencia",
        )
        db_session.add(t)
        await db_session.flush()
        return u, t

    # Teachers A, B, C, D, E, F
    u_ta, t_a = await create_teacher_user("teacher.a@central.edu.co", "teacher.a", "20000001", "Teacher", "A")
    u_tb, t_b = await create_teacher_user("teacher.b@central.edu.co", "teacher.b", "20000002", "Teacher", "B")
    u_tc, t_c = await create_teacher_user("teacher.c@central.edu.co", "teacher.c", "20000003", "Teacher", "C")
    u_td, t_d = await create_teacher_user("teacher.d@central.edu.co", "teacher.d", "20000004", "Teacher", "D")
    u_te, t_e = await create_teacher_user("teacher.e@central.edu.co", "teacher.e", "20000005", "Teacher", "E")
    u_tf, t_f = await create_teacher_user("teacher.f@central.edu.co", "teacher.f", "20000006", "Teacher", "F")

    # Set Teacher E as Group Director of 4-A
    group_4a.group_director_teacher_id = t_e.id
    await db_session.flush()

    # Academic Assignments
    # Teacher A -> Math in 3-A
    asg_ta = AcademicAssignment(
        teacher_id=t_a.id,
        subject_id=subj_math_3a.id,
        group_id=group_3a.id,
        academic_year_id=ay1.id,
        weekly_hours=4,
        is_active=True,
    )
    # Teacher B -> Science in 5-B
    asg_tb = AcademicAssignment(
        teacher_id=t_b.id,
        subject_id=subj_sci_5b.id,
        group_id=group_5b.id,
        academic_year_id=ay1.id,
        weekly_hours=4,
        is_active=True,
    )
    # Teacher D -> Spanish in 3-A (same group as Teacher A)
    asg_td = AcademicAssignment(
        teacher_id=t_d.id,
        subject_id=subj_spa_3a.id,
        group_id=group_3a.id,
        academic_year_id=ay1.id,
        weekly_hours=4,
        is_active=True,
    )
    # Teacher F -> Math in 3-A AND Science in 5-B (multi-group)
    # Note: we create unique subjects or inactive assignments if uniqueness per subject/group applies
    subj_art_3a = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area_spa.id,
        grade_id=grade3.id,
        name="Educación Artística 3",
        weekly_hours=2,
    )
    subj_ethics_5b = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area_spa.id,
        grade_id=grade5.id,
        name="Ética y Valores 5",
        weekly_hours=2,
    )
    db_session.add_all([subj_art_3a, subj_ethics_5b])
    await db_session.flush()

    asg_tf_1 = AcademicAssignment(
        teacher_id=t_f.id,
        subject_id=subj_art_3a.id,
        group_id=group_3a.id,
        academic_year_id=ay1.id,
        weekly_hours=2,
        is_active=True,
    )
    asg_tf_2 = AcademicAssignment(
        teacher_id=t_f.id,
        subject_id=subj_ethics_5b.id,
        group_id=group_5b.id,
        academic_year_id=ay1.id,
        weekly_hours=2,
        is_active=True,
    )
    db_session.add_all([asg_ta, asg_tb, asg_td, asg_tf_1, asg_tf_2])
    await db_session.flush()

    # Helper to create Student + Active Enrollment
    async def create_student_with_enrollment(
        email: str,
        username: str,
        doc: str,
        first: str,
        last: str,
        simat: str,
        inst: Institution,
        ay: AcademicYear,
        group: Group,
    ) -> tuple[User, Student, Enrollment]:
        su = User(
            institution_id=inst.id,
            email=email,
            username=username,
            hashed_password=pwd_hash,
            first_name=first,
            last_name=last,
            document_type=DocumentType.TI,
            document_number=doc,
            is_active=True,
        )
        db_session.add(su)
        await db_session.flush()
        st = Student(
            user_id=su.id,
            institution_id=inst.id,
            code_simat=simat,
            birth_date=date(2015, 3, 10),
            gender=StudentGender.M,
        )
        db_session.add(st)
        await db_session.flush()
        enr = Enrollment(
            student_id=st.id,
            group_id=group.id,
            academic_year_id=ay.id,
            enrollment_date=date(2026, 1, 20),
            status=EnrollmentStatus.ACTIVE,
        )
        db_session.add(enr)
        await db_session.flush()
        return su, st, enr

    # Student 1 in 3-A
    _, st_3a_1, enr_3a_1 = await create_student_with_enrollment(
        "st.3a1@central.edu.co", "st.3a1", "30000001", "Estudiante", "3A-Uno", "SIMAT-3A-01", inst1, ay1, group_3a
    )
    # Student 2 in 3-A
    _, st_3a_2, enr_3a_2 = await create_student_with_enrollment(
        "st.3a2@central.edu.co", "st.3a2", "30000002", "Estudiante", "3A-Dos", "SIMAT-3A-02", inst1, ay1, group_3a
    )
    # Student 3 in 5-B
    _, st_5b_1, enr_5b_1 = await create_student_with_enrollment(
        "st.5b1@central.edu.co", "st.5b1", "30000003", "Estudiante", "5B-Uno", "SIMAT-5B-01", inst1, ay1, group_5b
    )
    # Student 4 in 4-A (Director group for Teacher E)
    _, st_4a_1, enr_4a_1 = await create_student_with_enrollment(
        "st.4a1@central.edu.co", "st.4a1", "30000004", "Estudiante", "4A-Uno", "SIMAT-4A-01", inst1, ay1, group_4a
    )
    # Student 5 in Inst2 (Cross Tenant)
    _, st_inst2, enr_inst2 = await create_student_with_enrollment(
        "st.norte@norte.edu.co", "st.norte", "40000001", "Estudiante", "Norte", "SIMAT-NORTE-01", inst2, ay2, group_inst2
    )

    await db_session.commit()

    # JWT Tokens Helper
    async def create_jwt(user: User, roles: list[str]) -> str:
        return await token_service.create_access_token(
            subject=str(user.id),
            additional_claims={
                "roles": roles,
                "institution_id": str(user.institution_id) if user.institution_id else None,
            },
        )

    return {
        "inst1": inst1,
        "inst2": inst2,
        "ay1": ay1,
        "group_3a": group_3a,
        "group_4a": group_4a,
        "group_5b": group_5b,
        "group_inst2": group_inst2,
        "st_3a_1": st_3a_1,
        "st_3a_2": st_3a_2,
        "st_5b_1": st_5b_1,
        "st_4a_1": st_4a_1,
        "st_inst2": st_inst2,
        "enr_3a_1": enr_3a_1,
        "enr_3a_2": enr_3a_2,
        "enr_5b_1": enr_5b_1,
        "enr_4a_1": enr_4a_1,
        "enr_inst2": enr_inst2,
        "token_rector": await create_jwt(rector_user, [SystemRole.RECTOR.value]),
        "token_ta": await create_jwt(u_ta, [SystemRole.TEACHER.value]),
        "token_tb": await create_jwt(u_tb, [SystemRole.TEACHER.value]),
        "token_tc": await create_jwt(u_tc, [SystemRole.TEACHER.value]),
        "token_td": await create_jwt(u_td, [SystemRole.TEACHER.value]),
        "token_te": await create_jwt(u_te, [SystemRole.TEACHER.value]),
        "token_tf": await create_jwt(u_tf, [SystemRole.TEACHER.value]),
    }


@pytest.mark.asyncio
async def test_scope_01_teacher_a_assigned_to_grade_3a_sees_only_grade_3a_students(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-01: Teacher A assigned to Grade 3A -> /api/v1/students returns only 3A students."""
    headers = {"Authorization": f"Bearer {academic_scope_fixture['token_ta']}"}
    res = await client.get("/api/v1/students", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    student_ids = {s["id"] for s in data["items"]}

    assert data["total"] == 2
    assert str(academic_scope_fixture["st_3a_1"].id) in student_ids
    assert str(academic_scope_fixture["st_3a_2"].id) in student_ids
    assert str(academic_scope_fixture["st_5b_1"].id) not in student_ids
    assert str(academic_scope_fixture["st_4a_1"].id) not in student_ids


@pytest.mark.asyncio
async def test_scope_02_teacher_b_assigned_to_grade_5b_sees_only_grade_5b_students(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-02: Teacher B assigned to Grade 5B -> /api/v1/students returns only Grade 5B students."""
    headers = {"Authorization": f"Bearer {academic_scope_fixture['token_tb']}"}
    res = await client.get("/api/v1/students", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    student_ids = {s["id"] for s in data["items"]}

    assert data["total"] == 1
    assert str(academic_scope_fixture["st_5b_1"].id) in student_ids
    assert str(academic_scope_fixture["st_3a_1"].id) not in student_ids
    assert str(academic_scope_fixture["st_3a_2"].id) not in student_ids
    assert str(academic_scope_fixture["st_4a_1"].id) not in student_ids


@pytest.mark.asyncio
async def test_scope_03_new_teacher_with_no_assignments_sees_zero_students_and_groups(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-03: New teacher with no AcademicAssignment -> /api/v1/students and /api/v1/groups return 0 items."""
    headers = {"Authorization": f"Bearer {academic_scope_fixture['token_tc']}"}

    res_st = await client.get("/api/v1/students", headers=headers)
    assert res_st.status_code == 200, res_st.text
    assert res_st.json()["total"] == 0
    assert len(res_st.json()["items"]) == 0

    res_grp = await client.get("/api/v1/groups", headers=headers)
    assert res_grp.status_code == 200, res_grp.text
    assert res_grp.json()["total"] == 0
    assert len(res_grp.json()["items"]) == 0

    res_enr = await client.get("/api/v1/enrollments", headers=headers)
    assert res_enr.status_code == 200, res_enr.text
    assert res_enr.json()["total"] == 0


@pytest.mark.asyncio
async def test_scope_04_teacher_a_attempts_get_student_for_teacher_b_student_is_denied(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-04: Teacher A attempts GET /api/v1/students/{student_id_5b} -> denied (404/not found anti-leak)."""
    headers = {"Authorization": f"Bearer {academic_scope_fixture['token_ta']}"}
    st_5b_id = academic_scope_fixture["st_5b_1"].id

    res = await client.get(f"/api/v1/students/{st_5b_id}", headers=headers)
    # Must be rejected (404 Not Found to prevent data existence leaking)
    assert res.status_code in (404, 403), res.text

    # Teacher A requesting own student in 3A succeeds
    st_3a_id = academic_scope_fixture["st_3a_1"].id
    res_ok = await client.get(f"/api/v1/students/{st_3a_id}", headers=headers)
    assert res_ok.status_code == 200, res_ok.text
    assert res_ok.json()["id"] == str(st_3a_id)


@pytest.mark.asyncio
async def test_scope_05_rector_retains_full_institutional_visibility(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-05: Rector requests /api/v1/students -> retains full institutional visibility (all 4 inst1 students)."""
    headers = {"Authorization": f"Bearer {academic_scope_fixture['token_rector']}"}

    res = await client.get("/api/v1/students", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    student_ids = {s["id"] for s in data["items"]}

    assert data["total"] == 4
    assert str(academic_scope_fixture["st_3a_1"].id) in student_ids
    assert str(academic_scope_fixture["st_3a_2"].id) in student_ids
    assert str(academic_scope_fixture["st_5b_1"].id) in student_ids
    assert str(academic_scope_fixture["st_4a_1"].id) in student_ids
    # Does not see Inst2 student
    assert str(academic_scope_fixture["st_inst2"].id) not in student_ids


@pytest.mark.asyncio
async def test_scope_06_group_director_requests_students_of_their_group(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-06: Group director (Teacher E) requests students of 4A -> access allowed even without subject."""
    headers = {"Authorization": f"Bearer {academic_scope_fixture['token_te']}"}

    # /api/v1/students
    res = await client.get("/api/v1/students", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    student_ids = {s["id"] for s in data["items"]}

    assert data["total"] == 1
    assert str(academic_scope_fixture["st_4a_1"].id) in student_ids
    assert str(academic_scope_fixture["st_3a_1"].id) not in student_ids

    # /api/v1/groups
    res_grp = await client.get("/api/v1/groups", headers=headers)
    assert res_grp.status_code == 200, res_grp.text
    grp_ids = {g["id"] for g in res_grp.json()["items"]}
    assert str(academic_scope_fixture["group_4a"].id) in grp_ids
    assert str(academic_scope_fixture["group_3a"].id) not in grp_ids


@pytest.mark.asyncio
async def test_scope_07_teacher_assigned_to_multiple_groups_returns_union(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-07: Teacher F (assigned to 3A and 5B) -> returns exact union of students in 3A and 5B."""
    headers = {"Authorization": f"Bearer {academic_scope_fixture['token_tf']}"}

    res = await client.get("/api/v1/students", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    student_ids = {s["id"] for s in data["items"]}

    assert data["total"] == 3
    assert str(academic_scope_fixture["st_3a_1"].id) in student_ids
    assert str(academic_scope_fixture["st_3a_2"].id) in student_ids
    assert str(academic_scope_fixture["st_5b_1"].id) in student_ids
    assert str(academic_scope_fixture["st_4a_1"].id) not in student_ids


@pytest.mark.asyncio
async def test_scope_08_cross_tenant_access_is_denied(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-08: Cross-tenant access is denied regardless of role or ID."""
    # Inst1 Rector requesting Inst2 student
    headers_rector = {"Authorization": f"Bearer {academic_scope_fixture['token_rector']}"}
    st_inst2_id = academic_scope_fixture["st_inst2"].id

    res = await client.get(f"/api/v1/students/{st_inst2_id}", headers=headers_rector)
    assert res.status_code in (404, 403), res.text

    # Teacher A requesting Inst2 student
    headers_ta = {"Authorization": f"Bearer {academic_scope_fixture['token_ta']}"}
    res_t = await client.get(f"/api/v1/students/{st_inst2_id}", headers=headers_ta)
    assert res_t.status_code in (404, 403), res_t.text


@pytest.mark.asyncio
async def test_scope_09_two_teachers_in_same_group_both_see_group_students(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-09: Teacher A (Math) and Teacher D (Spanish) in 3A both see 3A students."""
    headers_ta = {"Authorization": f"Bearer {academic_scope_fixture['token_ta']}"}
    headers_td = {"Authorization": f"Bearer {academic_scope_fixture['token_td']}"}

    res_a = await client.get("/api/v1/students", headers=headers_ta)
    assert res_a.status_code == 200
    ids_a = {s["id"] for s in res_a.json()["items"]}

    res_d = await client.get("/api/v1/students", headers=headers_td)
    assert res_d.status_code == 200
    ids_d = {s["id"] for s in res_d.json()["items"]}

    assert ids_a == ids_d
    assert len(ids_a) == 2
    assert str(academic_scope_fixture["st_3a_1"].id) in ids_a
    assert str(academic_scope_fixture["st_3a_2"].id) in ids_a


@pytest.mark.asyncio
async def test_scope_10_teacher_cannot_access_unauthorized_groups_or_enrollments(
    client: AsyncClient,
    academic_scope_fixture: dict[str, Any],
) -> None:
    """TEST-SCOPE-10: Teacher A (assigned to 3A) cannot access group 5B or enrollment in 5B."""
    headers_ta = {"Authorization": f"Bearer {academic_scope_fixture['token_ta']}"}
    grp_5b_id = academic_scope_fixture["group_5b"].id
    enr_5b_id = academic_scope_fixture["enr_5b_1"].id

    # Group 5B detail denied
    res_grp = await client.get(f"/api/v1/groups/{grp_5b_id}", headers=headers_ta)
    assert res_grp.status_code in (404, 403), res_grp.text

    # Enrollment 5B detail denied
    res_enr = await client.get(f"/api/v1/enrollments/{enr_5b_id}", headers=headers_ta)
    assert res_enr.status_code in (404, 403), res_enr.text

    # Group 3A detail allowed
    grp_3a_id = academic_scope_fixture["group_3a"].id
    res_grp_ok = await client.get(f"/api/v1/groups/{grp_3a_id}", headers=headers_ta)
    assert res_grp_ok.status_code == 200, res_grp_ok.text

    # Enrollment 3A detail allowed
    enr_3a_id = academic_scope_fixture["enr_3a_1"].id
    res_enr_ok = await client.get(f"/api/v1/enrollments/{enr_3a_id}", headers=headers_ta)
    assert res_enr_ok.status_code == 200, res_enr_ok.text
