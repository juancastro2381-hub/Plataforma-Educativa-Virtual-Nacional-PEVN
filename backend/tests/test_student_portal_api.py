"""
PEVN Backend — Student Portal API Integration Tests (Phase 14A)

Comprehensive security, tenant isolation, and functional tests for the Student Portal:
- Student Profile & Academic Context retrieval
- Student Dashboard aggregation & KPI metrics
- Enrolled Subjects listing
- Activities & Homework discovery with status calculation (PENDING, OVERDUE, GRADED)
- Activity Detail access & Anti-IDOR enforcement (cross-group 404)
- Grades retrieval & multi-student grade isolation
- Daily Attendance & Statistics
- Virtual Classrooms & Lecture Recordings access
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
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.models.virtual_classroom import (
    MeetingRecording,
    VirtualClassroom,
    VirtualClassroomStatus,
)


@pytest.fixture
async def student_portal_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Sets up institutional hierarchy, 2 groups, 2 students, assignments, activities, and tokens."""
    dept = Department(code="76", name="Valle del Cauca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="76001", name="Cali")
    db_session.add(mun)
    await db_session.flush()

    inst1 = Institution(
        municipality_id=mun.id,
        dane_code="17600100001",
        name="Colegio Santa Librada",
        email="rectoria@librada.edu.co",
        is_active=True,
    )
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
    db_session.add(campus1)
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

    grade10 = Grade(
        code="10",
        name="Décimo Grado",
        level=EducationalLevel.MEDIA,
        ordinal_order=10,
    )
    db_session.add(grade10)
    await db_session.flush()

    area = KnowledgeArea(
        institution_id=inst1.id,
        name="Ciencias Naturales",
        is_mandatory=True,
    )
    db_session.add(area)
    await db_session.flush()

    subject_physics = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area.id,
        grade_id=grade10.id,
        name="Física Clásica",
        weekly_hours=4,
    )
    db_session.add(subject_physics)
    await db_session.flush()

    # Group 10-A and Group 10-B
    group10a = Group(
        academic_year_id=ay1.id,
        campus_id=campus1.id,
        grade_id=grade10.id,
        name="10-A",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    group10b = Group(
        academic_year_id=ay1.id,
        campus_id=campus1.id,
        grade_id=grade10.id,
        name="10-B",
        shift=ShiftEnum.TARDE,
        capacity_limit=35,
    )
    db_session.add_all([group10a, group10b])
    await db_session.flush()

    # Teacher
    pwd_hash = password_hasher.hash("ColombiaSegura2026*!")
    teacher_user = User(
        institution_id=inst1.id,
        email="profesor.fisica@librada.edu.co",
        username="profe_fisica",
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

    # Assignment for Group 10-A
    assignment1 = AcademicAssignment(
        teacher_id=teacher.id,
        group_id=group10a.id,
        subject_id=subject_physics.id,
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
    db_session.add(st1_user)
    await db_session.flush()

    student1 = Student(
        user_id=st1_user.id,
        institution_id=inst1.id,
        code_simat="SIM-10203040",
        birth_date=date(2010, 5, 12),
        gender=StudentGender.F,
    )
    db_session.add(student1)
    await db_session.flush()

    enrollment1 = Enrollment(
        student_id=student1.id,
        academic_year_id=ay1.id,
        group_id=group10a.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=date(2026, 1, 20),
    )
    db_session.add(enrollment1)
    await db_session.flush()

    # Student 2 in 10-B (Pedro Gomez)
    st2_user = User(
        institution_id=inst1.id,
        email="pedro.gomez@librada.edu.co",
        username="pedro.gomez",
        hashed_password=pwd_hash,
        first_name="Pedro",
        last_name="Gómez",
        document_type=DocumentType.TI,
        document_number="1030405060",
        is_active=True,
    )
    db_session.add(st2_user)
    await db_session.flush()

    student2 = Student(
        user_id=st2_user.id,
        institution_id=inst1.id,
        code_simat="SIM-10304050",
        birth_date=date(2010, 8, 22),
        gender=StudentGender.M,
    )
    db_session.add(student2)
    await db_session.flush()

    enrollment2 = Enrollment(
        student_id=student2.id,
        academic_year_id=ay1.id,
        group_id=group10b.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=date(2026, 1, 20),
    )
    db_session.add(enrollment2)
    await db_session.flush()

    # Activities for Group 10-A
    now = datetime.now(UTC)
    act1 = AcademicActivity(
        institution_id=inst1.id,
        teacher_id=teacher.id,
        academic_assignment_id=assignment1.id,
        subject_id=subject_physics.id,
        group_id=group10a.id,
        academic_year_id=ay1.id,
        title="Taller de Leyes de Newton",
        description="Resolver ejercicios 1 al 10",
        activity_type=ActivityType.WORKSHOP,
        status=ActivityStatus.PUBLISHED,
        publication_date=now - timedelta(days=2),
        due_date=now + timedelta(days=5),
        max_score=Decimal("5.00"),
        instructions="Entregar en PDF",
    )
    act2 = AcademicActivity(
        institution_id=inst1.id,
        teacher_id=teacher.id,
        academic_assignment_id=assignment1.id,
        subject_id=subject_physics.id,
        group_id=group10a.id,
        academic_year_id=ay1.id,
        title="Quiz Cinemática",
        description="Evaluación corta",
        activity_type=ActivityType.QUIZ,
        status=ActivityStatus.PUBLISHED,
        publication_date=now - timedelta(days=7),
        due_date=now - timedelta(days=1),
        max_score=Decimal("5.00"),
    )
    # Activity for Group 10-B (Unauthorized for Student 1)
    act_10b = AcademicActivity(
        institution_id=inst1.id,
        teacher_id=teacher.id,
        subject_id=subject_physics.id,
        group_id=group10b.id,
        academic_year_id=ay1.id,
        title="Actividad Exclusiva 10-B",
        activity_type=ActivityType.TASK,
        status=ActivityStatus.PUBLISHED,
        publication_date=now,
        due_date=now + timedelta(days=3),
        max_score=Decimal("5.00"),
    )
    db_session.add_all([act1, act2, act_10b])
    await db_session.flush()

    # Grade for Student 1 on Act 2
    grade_act2 = ActivityGrade(
        activity_id=act2.id,
        student_id=student1.id,
        score=Decimal("4.50"),
        feedback="Excelente trabajo en vectores",
        status=ActivitySubmissionStatus.GRADED,
        graded_by_teacher_id=teacher.id,
        graded_at=now,
    )
    db_session.add(grade_act2)
    await db_session.flush()

    # Attendance for Student 1
    att1 = DailyAttendance(
        institution_id=inst1.id,
        group_id=group10a.id,
        academic_year_id=ay1.id,
        subject_id=subject_physics.id,
        teacher_id=teacher.id,
        student_id=student1.id,
        attendance_date=date(2026, 2, 10),
        status=AttendanceStatusEnum.PRESENT,
    )
    att2 = DailyAttendance(
        institution_id=inst1.id,
        group_id=group10a.id,
        academic_year_id=ay1.id,
        subject_id=subject_physics.id,
        teacher_id=teacher.id,
        student_id=student1.id,
        attendance_date=date(2026, 2, 11),
        status=AttendanceStatusEnum.LATE,
        remarks="Llegada 10 minutos tarde",
    )
    db_session.add_all([att1, att2])
    await db_session.flush()

    # Virtual Classroom for 10-A
    vc1 = VirtualClassroom(
        institution_id=inst1.id,
        academic_assignment_id=assignment1.id,
        host_user_id=teacher_user.id,
        title="Clase de Física en Vivo - Dinámica",
        description="Explicación de fuerzas de rozamiento",
        status=VirtualClassroomStatus.RUNNING,
        scheduled_start_time=now - timedelta(minutes=15),
        scheduled_end_time=now + timedelta(minutes=45),
        bbb_meeting_id="pevn-librada-fisica-10a",
        moderator_password_hash="modpass123",
        attendee_password_hash="attpass123",
    )
    db_session.add(vc1)
    await db_session.flush()

    # Recording for vc1
    rec1 = MeetingRecording(
        virtual_classroom_id=vc1.id,
        institution_id=inst1.id,
        bbb_record_id="rec-dinamica-001",
        duration_seconds=2700,
        file_size_bytes=104857600,
        playback_url="https://media.pevn.gov.co/recordings/dinamica1.mp4",
        is_published=True,
    )
    db_session.add(rec1)
    await db_session.flush()

    # Setup RBAC for Student role
    role_stmt = select(Role).where(Role.name == SystemRole.STUDENT.value)
    student_role = (await db_session.execute(role_stmt)).scalar_one()

    all_student_perms = [
        ("students", "read"),
        ("subjects", "read"),
        ("activities", "read"),
        ("grades", "read"),
        ("attendance", "read"),
        ("virtual_classrooms", "read"),
        ("recordings", "read"),
        ("academic_years", "read"),
    ]
    for res, act in all_student_perms:
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
                    RolePermission.role_id == student_role.id,
                    RolePermission.permission_id == p.id,
                )
            )
        ).scalar_one_or_none()
        if not rp_exists:
            db_session.add(RolePermission(role_id=student_role.id, permission_id=p.id))
            await db_session.flush()

    # Link UserRole for Student 1
    db_session.add(
        UserRole(
            user_id=st1_user.id,
            role_id=student_role.id,
            institution_id=inst1.id,
            is_active=True,
        )
    )
    # Link UserRole for Student 2
    db_session.add(
        UserRole(
            user_id=st2_user.id,
            role_id=student_role.id,
            institution_id=inst1.id,
            is_active=True,
        )
    )
    await db_session.commit()

    # Generate access tokens
    token_st1 = await token_service.create_access_token(
        subject=str(st1_user.id),
        additional_claims={
            "roles": [SystemRole.STUDENT.value],
            "institution_id": str(inst1.id),
        },
    )
    token_st2 = await token_service.create_access_token(
        subject=str(st2_user.id),
        additional_claims={
            "roles": [SystemRole.STUDENT.value],
            "institution_id": str(inst1.id),
        },
    )

    return {
        "institution": inst1,
        "student1": student1,
        "student2": student2,
        "token_st1": token_st1,
        "token_st2": token_st2,
        "activity1": act1,
        "activity2": act2,
        "activity_10b": act_10b,
        "virtual_classroom": vc1,
        "recording": rec1,
    }


@pytest.mark.asyncio
async def test_student_get_profile(
    client: AsyncClient,
    student_portal_fixture: dict[str, Any],
) -> None:
    """Validate student can access their own enriched academic profile."""
    token = student_portal_fixture["token_st1"]
    resp = await client.get(
        "/api/v1/student/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Ana García"
    assert data["code_simat"] == "SIM-10203040"
    assert data["group_name"] == "10-A"
    assert data["grade_name"] == "Décimo Grado"
    assert data["institution_name"] == "Colegio Santa Librada"


@pytest.mark.asyncio
async def test_student_get_dashboard(
    client: AsyncClient,
    student_portal_fixture: dict[str, Any],
) -> None:
    """Validate student dashboard returns consolidated metrics, activities, and virtual classes."""
    token = student_portal_fixture["token_st1"]
    resp = await client.get(
        "/api/v1/student/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_subjects"] >= 1
    assert data["pending_activities_count"] == 1  # act1 is due in 5 days
    assert data["graded_activities_count"] == 1   # act2 has score
    assert len(data["upcoming_virtual_classrooms"]) == 1
    assert data["attendance_summary"]["total_sessions"] == 2
    assert data["attendance_summary"]["present_count"] == 1
    assert data["attendance_summary"]["late_count"] == 1


@pytest.mark.asyncio
async def test_student_list_subjects(
    client: AsyncClient,
    student_portal_fixture: dict[str, Any],
) -> None:
    """Validate student receives subjects with teacher information."""
    token = student_portal_fixture["token_st1"]
    resp = await client.get(
        "/api/v1/student/subjects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    phys = next(s for s in data["items"] if s["name"] == "Física Clásica")
    assert phys["weekly_hours"] == 4
    assert phys["teacher_name"] == "Ernesto Torres"


@pytest.mark.asyncio
async def test_student_list_activities_and_status(
    client: AsyncClient,
    student_portal_fixture: dict[str, Any],
) -> None:
    """Validate activities list dynamically computes submission statuses."""
    token = student_portal_fixture["token_st1"]
    resp = await client.get(
        "/api/v1/student/activities",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2  # act1 and act2 for 10-A, not act_10b

    act1_item = next(a for a in data["items"] if a["title"] == "Taller de Leyes de Newton")
    assert act1_item["submission_status"] == "PENDING"
    assert act1_item["instructions"] == "Entregar en PDF"

    act2_item = next(a for a in data["items"] if a["title"] == "Quiz Cinemática")
    assert act2_item["submission_status"] == "GRADED"
    assert float(act2_item["score"]) == 4.50


@pytest.mark.asyncio
async def test_student_activity_detail_and_anti_idor(
    client: AsyncClient,
    student_portal_fixture: dict[str, Any],
) -> None:
    """Validate activity detail returns instructions and blocks unauthorized cross-group access (404)."""
    token = student_portal_fixture["token_st1"]
    act1 = student_portal_fixture["activity1"]
    act_10b = student_portal_fixture["activity_10b"]

    # Authorized activity
    resp = await client.get(
        f"/api/v1/student/activities/{act1.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Taller de Leyes de Newton"

    # Unauthorized activity from Group 10-B
    resp_unauth = await client.get(
        f"/api/v1/student/activities/{act_10b.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_unauth.status_code == 404


@pytest.mark.asyncio
async def test_student_grades_isolation(
    client: AsyncClient,
    student_portal_fixture: dict[str, Any],
) -> None:
    """Validate student can only view their own grades."""
    token_st1 = student_portal_fixture["token_st1"]
    token_st2 = student_portal_fixture["token_st2"]

    # Student 1 has 1 grade
    resp1 = await client.get(
        "/api/v1/student/grades",
        headers={"Authorization": f"Bearer {token_st1}"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["total"] == 1
    assert float(resp1.json()["average_score"]) == 4.50

    # Student 2 has 0 grades
    resp2 = await client.get(
        "/api/v1/student/grades",
        headers={"Authorization": f"Bearer {token_st2}"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0


@pytest.mark.asyncio
async def test_student_attendance_history(
    client: AsyncClient,
    student_portal_fixture: dict[str, Any],
) -> None:
    """Validate student attendance history and percentage."""
    token = student_portal_fixture["token_st1"]
    resp = await client.get(
        "/api/v1/student/attendance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["summary"]["attendance_rate"] == 100.0  # (1 present + 1 late) / 2


@pytest.mark.asyncio
async def test_student_virtual_classrooms_and_recordings(
    client: AsyncClient,
    student_portal_fixture: dict[str, Any],
) -> None:
    """Validate student can discover virtual classrooms and stream authorized recordings."""
    token = student_portal_fixture["token_st1"]
    vc1 = student_portal_fixture["virtual_classroom"]

    # List classrooms
    resp = await client.get(
        "/api/v1/student/virtual-classrooms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["can_join"] is True

    # Get single classroom
    resp_vc = await client.get(
        f"/api/v1/student/virtual-classrooms/{vc1.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_vc.status_code == 200
    assert resp_vc.json()["room_name"] == "pevn-librada-fisica-10a"

    # List recordings
    resp_rec = await client.get(
        f"/api/v1/student/virtual-classrooms/{vc1.id}/recordings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_rec.status_code == 200
    assert resp_rec.json()["total"] == 1
    assert resp_rec.json()["items"][0]["playback_url"] == "https://media.pevn.gov.co/recordings/dinamica1.mp4"
