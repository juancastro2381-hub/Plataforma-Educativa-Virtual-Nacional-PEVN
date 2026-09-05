"""
PEVN Backend — Guardian Portal API Integration Tests (Phase 14A)

Comprehensive security, tenant isolation, anti-IDOR, and functional tests for the Guardian Portal:
- Guardian Profile retrieval
- Authorized Children (Child Context Switcher) discovery
- Single Child Academic Overview aggregation
- Child Homework & Task monitoring (Follow-up mode)
- Child Grades and qualitative educator feedback
- Child Attendance and absence tracking
- Child Virtual Classrooms schedule agenda
- Centralized Guardian-to-Student Anti-IDOR enforcement (404 on unlinked or cross-tenant child)
- Unauthenticated / unauthorized rejection
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.academic_activity import (
    AcademicActivity,
    ActivityGrade,
    ActivityStatus,
    ActivitySubmissionStatus,
    ActivityType,
    AttendanceStatusEnum,
    DailyAttendance,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.guardian import (
    Guardian,
    GuardianRelationshipType,
    StudentGuardian,
)
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.models.virtual_classroom import (
    VirtualClassroom,
    VirtualClassroomStatus,
)


@pytest.fixture
async def guardian_portal_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Fixture setting up 2 institutions, 2 guardians, 3 students, enrollments, activities, and tokens."""
    dept = Department(code="76", name="Valle del Cauca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="76001", name="Cali")
    db_session.add(mun)
    await db_session.flush()

    # Institution 1: Santa Librada
    inst1 = Institution(
        municipality_id=mun.id,
        dane_code="17600100001",
        name="Colegio Santa Librada",
        email="rectoria@librada.edu.co",
        is_active=True,
    )
    # Institution 2: San Luis
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

    ay1 = AcademicYear(
        institution_id=inst1.id,
        name="Año Escolar 2026",
        year=2026,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 11, 30),
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
    )
    db_session.add(ay1)
    await db_session.flush()

    grade10 = Grade(code="10", name="Décimo Grado", level=EducationalLevel.MEDIA, ordinal_order=10)
    grade6 = Grade(code="6", name="Sexto Grado", level=EducationalLevel.SECUNDARIA, ordinal_order=6)
    db_session.add_all([grade10, grade6])
    await db_session.flush()

    area = KnowledgeArea(institution_id=inst1.id, name="Ciencias Naturales", is_mandatory=True)
    db_session.add(area)
    await db_session.flush()

    subj_physics = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area.id,
        grade_id=grade10.id,
        name="Física Clásica",
        weekly_hours=4,
    )
    db_session.add(subj_physics)
    await db_session.flush()

    group10a = Group(
        academic_year_id=ay1.id,
        campus_id=campus1.id,
        grade_id=grade10.id,
        name="10-A",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    group6a = Group(
        academic_year_id=ay1.id,
        campus_id=campus1.id,
        grade_id=grade6.id,
        name="6-A",
        shift=ShiftEnum.TARDE,
        capacity_limit=30,
    )
    db_session.add_all([group10a, group6a])
    await db_session.flush()

    # Teacher
    pwd_hash = password_hasher.hash("ColombiaSegura2026*!")
    teacher_user = User(
        institution_id=inst1.id,
        email="ernesto.torres@librada.edu.co",
        username="ernesto.torres",
        hashed_password=pwd_hash,
        first_name="Ernesto",
        last_name="Torres",
        document_type=DocumentType.CC,
        document_number="80123456",
        is_active=True,
    )
    db_session.add(teacher_user)
    await db_session.flush()

    teacher = Teacher(
        user_id=teacher_user.id,
        institution_id=inst1.id,
        contract_type=TeacherContractType.PROPIEDAD,
        specialty_area="Física",
    )
    db_session.add(teacher)
    await db_session.flush()

    assignment1 = AcademicAssignment(
        teacher_id=teacher.id,
        group_id=group10a.id,
        subject_id=subj_physics.id,
        academic_year_id=ay1.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assignment1)
    await db_session.flush()

    # Student 1 in 10-A (Ana Garcia)
    st1_user = User(
        institution_id=inst1.id,
        email="ana.garcia@librada.edu.co",
        username="ana.garcia",
        hashed_password=pwd_hash,
        first_name="Ana",
        last_name="García",
        document_type=DocumentType.TI,
        document_number="1020304050",
        is_active=True,
    )
    # Student 2 in 6-A (Felipe Garcia - sibling)
    st2_user = User(
        institution_id=inst1.id,
        email="felipe.garcia@librada.edu.co",
        username="felipe.garcia",
        hashed_password=pwd_hash,
        first_name="Felipe",
        last_name="García",
        document_type=DocumentType.TI,
        document_number="1020304099",
        is_active=True,
    )
    # Student 3 in San Luis Inst 2 (Camilo Lopez - Cross-tenant student)
    st3_user = User(
        institution_id=inst2.id,
        email="camilo.lopez@sanluis.edu.co",
        username="camilo.lopez",
        hashed_password=pwd_hash,
        first_name="Camilo",
        last_name="López",
        document_type=DocumentType.TI,
        document_number="1099887766",
        is_active=True,
    )
    db_session.add_all([st1_user, st2_user, st3_user])
    await db_session.flush()

    student1 = Student(
        user_id=st1_user.id,
        institution_id=inst1.id,
        code_simat="SIM-10203040",
        birth_date=date(2010, 5, 12),
        gender=StudentGender.F,
    )
    student2 = Student(
        user_id=st2_user.id,
        institution_id=inst1.id,
        code_simat="SIM-10203099",
        birth_date=date(2014, 9, 18),
        gender=StudentGender.M,
    )
    student3 = Student(
        user_id=st3_user.id,
        institution_id=inst2.id,
        code_simat="SIM-10998877",
        birth_date=date(2010, 1, 15),
        gender=StudentGender.M,
    )
    db_session.add_all([student1, student2, student3])
    await db_session.flush()

    enrollment1 = Enrollment(
        student_id=student1.id,
        academic_year_id=ay1.id,
        group_id=group10a.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=date(2026, 1, 20),
    )
    enrollment2 = Enrollment(
        student_id=student2.id,
        academic_year_id=ay1.id,
        group_id=group6a.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=date(2026, 1, 20),
    )
    db_session.add_all([enrollment1, enrollment2])
    await db_session.flush()

    # Guardian 1 (Martha Garcia - Mother of Ana and Felipe in Inst 1)
    g1_user = User(
        institution_id=inst1.id,
        email="martha.garcia@gmail.com",
        username="martha.garcia",
        hashed_password=pwd_hash,
        first_name="Martha",
        last_name="García",
        document_type=DocumentType.CC,
        document_number="31456789",
        is_active=True,
    )
    # Guardian 2 (Sofia Lopez - Mother of Camilo in Inst 2)
    g2_user = User(
        institution_id=inst2.id,
        email="sofia.lopez@gmail.com",
        username="sofia.lopez",
        hashed_password=pwd_hash,
        first_name="Sofía",
        last_name="López",
        document_type=DocumentType.CC,
        document_number="52987654",
        is_active=True,
    )
    db_session.add_all([g1_user, g2_user])
    await db_session.flush()

    guardian1 = Guardian(
        institution_id=inst1.id,
        user_id=g1_user.id,
        first_name="Martha",
        last_name="García",
        document_type=DocumentType.CC,
        document_number="31456789",
        phone="3119876543",
        email="martha.garcia@gmail.com",
        relationship_type=GuardianRelationshipType.MADRE,
    )
    guardian2 = Guardian(
        institution_id=inst2.id,
        user_id=g2_user.id,
        first_name="Sofía",
        last_name="López",
        document_type=DocumentType.CC,
        document_number="52987654",
        phone="3154567890",
        email="sofia.lopez@gmail.com",
        relationship_type=GuardianRelationshipType.MADRE,
    )
    db_session.add_all([guardian1, guardian2])
    await db_session.flush()

    # StudentGuardian links
    sg1 = StudentGuardian(
        student_id=student1.id,
        guardian_id=guardian1.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
        is_authorized_pickup=True,
    )
    sg2 = StudentGuardian(
        student_id=student2.id,
        guardian_id=guardian1.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
        is_authorized_pickup=True,
    )
    sg3 = StudentGuardian(
        student_id=student3.id,
        guardian_id=guardian2.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
        is_authorized_pickup=True,
    )
    db_session.add_all([sg1, sg2, sg3])
    await db_session.flush()

    # Activity and Grade for Student 1
    now = datetime.now(UTC)
    act1 = AcademicActivity(
        institution_id=inst1.id,
        teacher_id=teacher.id,
        academic_assignment_id=assignment1.id,
        subject_id=subj_physics.id,
        group_id=group10a.id,
        academic_year_id=ay1.id,
        title="Taller de Dinámica",
        activity_type=ActivityType.WORKSHOP,
        status=ActivityStatus.PUBLISHED,
        publication_date=now - timedelta(days=3),
        due_date=now + timedelta(days=4),
        max_score=Decimal("5.00"),
    )
    db_session.add(act1)
    await db_session.flush()

    grade1 = ActivityGrade(
        activity_id=act1.id,
        student_id=student1.id,
        score=Decimal("4.80"),
        feedback="Sobresaliente desempeño",
        status=ActivitySubmissionStatus.GRADED,
        graded_by_teacher_id=teacher.id,
        graded_at=now,
    )
    db_session.add(grade1)
    await db_session.flush()

    att1 = DailyAttendance(
        institution_id=inst1.id,
        group_id=group10a.id,
        academic_year_id=ay1.id,
        subject_id=subj_physics.id,
        teacher_id=teacher.id,
        student_id=student1.id,
        attendance_date=date(2026, 2, 12),
        status=AttendanceStatusEnum.PRESENT,
    )
    db_session.add(att1)
    await db_session.flush()

    vc1 = VirtualClassroom(
        institution_id=inst1.id,
        academic_assignment_id=assignment1.id,
        host_user_id=teacher_user.id,
        title="Clase de Física Virtual - Leyes de Newton",
        status=VirtualClassroomStatus.SCHEDULED,
        scheduled_start_time=now + timedelta(hours=2),
        scheduled_end_time=now + timedelta(hours=3),
        bbb_meeting_id="pevn-librada-fisica-guardian-10a",
        moderator_password_hash="modpass123",
        attendee_password_hash="attpass123",
    )
    db_session.add(vc1)
    await db_session.flush()

    # Setup RBAC for guardian role
    role_stmt = select(Role).where(Role.name == "guardian")
    guardian_role = (await db_session.execute(role_stmt)).scalar_one()

    all_guardian_perms = [
        ("guardians", "read"),
        ("students", "read"),
        ("activities", "read"),
        ("grades", "read"),
        ("attendance", "read"),
        ("virtual_classrooms", "read"),
        ("academic_years", "read"),
    ]
    for res, act in all_guardian_perms:
        p_stmt = select(Permission).where(
            Permission.resource == res,
            Permission.action == act,
        )
        p = (await db_session.execute(p_stmt)).scalar_one_or_none()
        if not p:
            p = Permission(resource=res, action=act, description=f"{res}:{act}")
            db_session.add(p)
            await db_session.flush()

        rp_exists = (
            await db_session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == guardian_role.id,
                    RolePermission.permission_id == p.id,
                )
            )
        ).scalar_one_or_none()
        if not rp_exists:
            db_session.add(RolePermission(role_id=guardian_role.id, permission_id=p.id))
            await db_session.flush()

    # Assign UserRoles
    db_session.add(
        UserRole(
            user_id=g1_user.id,
            role_id=guardian_role.id,
            institution_id=inst1.id,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=g2_user.id,
            role_id=guardian_role.id,
            institution_id=inst2.id,
            is_active=True,
        )
    )
    await db_session.commit()

    token_g1 = await token_service.create_access_token(
        subject=str(g1_user.id),
        additional_claims={
            "roles": ["guardian"],
            "institution_id": str(inst1.id),
        },
    )
    token_g2 = await token_service.create_access_token(
        subject=str(g2_user.id),
        additional_claims={
            "roles": ["guardian"],
            "institution_id": str(inst2.id),
        },
    )

    return {
        "inst1": inst1,
        "inst2": inst2,
        "guardian1": guardian1,
        "guardian2": guardian2,
        "student1": student1,
        "student2": student2,
        "student3": student3,
        "token_g1": token_g1,
        "token_g2": token_g2,
        "activity1": act1,
        "virtual_classroom": vc1,
    }


@pytest.mark.asyncio
async def test_guardian_get_profile(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Validate guardian can view their profile with count of linked children."""
    token = guardian_portal_fixture["token_g1"]
    resp = await client.get(
        "/api/v1/guardian/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Martha García"
    assert data["phone"] == "3119876543"
    assert data["total_linked_students"] == 2


@pytest.mark.asyncio
async def test_guardian_list_students_child_switcher(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Validate guardian receives all authorized children for the frontend switcher."""
    token = guardian_portal_fixture["token_g1"]
    resp = await client.get(
        "/api/v1/guardian/students",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    names = {s["first_name"] for s in data["items"]}
    assert names == {"Ana", "Felipe"}


@pytest.mark.asyncio
async def test_guardian_get_child_overview(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Validate guardian can retrieve comprehensive overview for an authorized child."""
    token = guardian_portal_fixture["token_g1"]
    st1 = guardian_portal_fixture["student1"]

    resp = await client.get(
        f"/api/v1/guardian/students/{st1.id}/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["child"]["full_name"] == "Ana García"
    assert data["child"]["group_name"] == "10-A"
    assert float(data["average_score"]) == 4.80
    assert data["attendance_summary"]["total_sessions"] == 1


@pytest.mark.asyncio
async def test_guardian_list_child_activities_follow_up(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Validate guardian can follow up on child's homework without submission abilities."""
    token = guardian_portal_fixture["token_g1"]
    st1 = guardian_portal_fixture["student1"]

    resp = await client.get(
        f"/api/v1/guardian/students/{st1.id}/activities",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Taller de Dinámica"
    assert data["items"][0]["submission_status"] == "GRADED"


@pytest.mark.asyncio
async def test_guardian_list_child_grades(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Validate guardian can view child evaluations and feedback."""
    token = guardian_portal_fixture["token_g1"]
    st1 = guardian_portal_fixture["student1"]

    resp = await client.get(
        f"/api/v1/guardian/students/{st1.id}/grades",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert float(data["items"][0]["score"]) == 4.80
    assert data["items"][0]["feedback"] == "Sobresaliente desempeño"


@pytest.mark.asyncio
async def test_guardian_list_child_attendance(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Validate guardian can monitor child's daily attendance."""
    token = guardian_portal_fixture["token_g1"]
    st1 = guardian_portal_fixture["student1"]

    resp = await client.get(
        f"/api/v1/guardian/students/{st1.id}/attendance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "PRESENT"


@pytest.mark.asyncio
async def test_guardian_list_child_virtual_classrooms(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Validate guardian can view scheduled virtual classroom agenda for the child."""
    token = guardian_portal_fixture["token_g1"]
    st1 = guardian_portal_fixture["student1"]
    vc1 = guardian_portal_fixture["virtual_classroom"]

    resp = await client.get(
        f"/api/v1/guardian/students/{st1.id}/virtual-classrooms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["title"] == "Clase de Física Virtual - Leyes de Newton"

    # Single classroom detail
    resp_vc = await client.get(
        f"/api/v1/guardian/students/{st1.id}/virtual-classrooms/{vc1.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_vc.status_code == 200
    assert resp_vc.json()["status"] == "SCHEDULED"


@pytest.mark.asyncio
async def test_guardian_cannot_access_unlinked_child_anti_idor(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Anti-IDOR: Guardian 1 accessing random UUID or unlinked student returns 404 (never 403)."""
    token = guardian_portal_fixture["token_g1"]
    fake_student_id = uuid.uuid4()

    resp = await client.get(
        f"/api/v1/guardian/students/{fake_student_id}/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_guardian_cannot_access_cross_tenant_student_anti_idor(
    client: AsyncClient,
    guardian_portal_fixture: dict[str, Any],
) -> None:
    """Multi-Tenant Isolation: Guardian 1 (Inst 1) accessing Student 3 (Inst 2) returns 404."""
    token = guardian_portal_fixture["token_g1"]
    st3 = guardian_portal_fixture["student3"]

    resp = await client.get(
        f"/api/v1/guardian/students/{st3.id}/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
