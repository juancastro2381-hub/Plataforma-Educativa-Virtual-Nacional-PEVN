"""
PEVN Backend — Teacher Portal REST API Integration Tests (Phase 13D.5)

Comprehensive integration and security tests for the dedicated Teacher Portal:
  - Teacher Dashboard KPIs and institutional identity
  - Teacher Academic Workload querying (Mi Carga)
  - Teacher Groups & Classroom student roster discovery
  - Server-side academic assignment validation (Single Source of Truth / anti-IDOR)
  - Academic activity creation, publication, and automatic grading slot seeding
  - Student gradesheet batch evaluation and score range validation
  - Daily classroom attendance recording and retrieval
  - Curricular lesson planning lifecycle
  - Multi-tenant boundary enforcement
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_async_session
from app.main import create_application
from app.models.academic_activity import (
    AcademicActivity,
    AcademicPlan,
    AcademicPlanStatus,
    ActivityGrade,
    ActivityStatus,
    ActivityType,
    DailyAttendance,
)
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.communication import (
    CommunicationCategory,
    CommunicationPriority,
    InstitutionalCommunication,
    PublishingStatus,
    TargetScopeType,
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
async def teacher_portal_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Fixture setting up institutional hierarchy, teacher, students, assignments, and tokens."""
    dept = Department(code="76", name="Valle del Cauca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="76001", name="Cali")
    db_session.add(mun)
    await db_session.flush()

    # Institutions
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
    campus2 = Campus(
        institution_id=inst2.id,
        dane_sede_code="17600100002-01",
        name="Sede Principal San Luis",
        is_active=True,
    )
    db_session.add_all([campus1, campus2])
    await db_session.flush()

    # Academic Year
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

    # Grade & Subject
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
    subject_chemistry = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area.id,
        grade_id=grade10.id,
        name="Química General",
        weekly_hours=3,
    )
    db_session.add_all([subject_physics, subject_chemistry])
    await db_session.flush()

    # Group 10-A
    group10a = Group(
        academic_year_id=ay1.id,
        campus_id=campus1.id,
        grade_id=grade10.id,
        name="10-A",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    # Group 10-B (for unassigned checks)
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

    # Teacher User & Profile
    pwd_hash = password_hasher.hash("ColombiaSegura2026*!")
    teacher_user = User(
        institution_id=inst1.id,
        email="carlos.mendoza@librada.edu.co",
        username="carlos.mendoza",
        hashed_password=pwd_hash,
        first_name="Carlos",
        last_name="Mendoza",
        document_type=DocumentType.CC,
        document_number="79123456",
        is_active=True,
    )
    db_session.add(teacher_user)
    await db_session.flush()

    teacher_profile = Teacher(
        user_id=teacher_user.id,
        institution_id=inst1.id,
        contract_type=TeacherContractType.PROPIEDAD,
        specialty_area="Física",
    )
    db_session.add(teacher_profile)
    await db_session.flush()

    # Student 1 (Ana Garcia)
    st_user1 = User(
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
    db_session.add(st_user1)
    await db_session.flush()

    student1 = Student(
        user_id=st_user1.id,
        institution_id=inst1.id,
        code_simat="SIM-10203040",
        birth_date=date(2010, 5, 12),
        gender=StudentGender.F,
    )
    db_session.add(student1)
    await db_session.flush()

    # Enrollment for Student 1 in Group 10-A
    enrollment1 = Enrollment(
        student_id=student1.id,
        academic_year_id=ay1.id,
        group_id=group10a.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=date(2026, 1, 20),
    )
    db_session.add(enrollment1)
    await db_session.flush()

    # Academic Assignment: Teacher Mendoza teaches Física in Group 10-A
    assignment1 = AcademicAssignment(
        teacher_id=teacher_profile.id,
        group_id=group10a.id,
        subject_id=subject_physics.id,
        academic_year_id=ay1.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assignment1)
    await db_session.flush()

    # Assign TEACHER role and permissions to Teacher User
    teacher_role_stmt = select(Role).where(Role.name == SystemRole.TEACHER.value)
    teacher_role = (await db_session.execute(teacher_role_stmt)).scalar_one()

    all_teacher_perms = [
        ("academic_years", "read"),
        ("academic_periods", "read"),
        ("grades", "read"),
        ("grades", "write"),
        ("subjects", "read"),
        ("groups", "read"),
        ("teachers", "read"),
        ("students", "read"),
        ("enrollments", "read"),
        ("academic_assignments", "read"),
        ("activities", "read"),
        ("activities", "create"),
        ("activities", "update"),
        ("activities", "publish"),
        ("activities", "close"),
        ("activities", "delete"),
        ("attendance", "read"),
        ("attendance", "write"),
        ("planning", "read"),
        ("planning", "create"),
        ("planning", "update"),
        ("planning", "delete"),
        ("communications", "read"),
        ("news", "read"),
    ]

    for res, act in all_teacher_perms:
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
                    RolePermission.role_id == teacher_role.id,
                    RolePermission.permission_id == p.id,
                )
            )
        ).scalar_one_or_none()
        if not rp_exists:
            db_session.add(RolePermission(role_id=teacher_role.id, permission_id=p.id))

    db_session.add(
        UserRole(
            user_id=teacher_user.id,
            role_id=teacher_role.id,
            institution_id=inst1.id,
            is_active=True,
        )
    )
    await db_session.flush()
    await db_session.commit()

    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={
            "roles": [SystemRole.TEACHER.value],
            "institution_id": str(inst1.id),
        },
    )

    return {
        "inst1": inst1,
        "inst2": inst2,
        "ay1": ay1,
        "grade10": grade10,
        "subject_physics": subject_physics,
        "subject_chemistry": subject_chemistry,
        "group10a": group10a,
        "group10b": group10b,
        "teacher_user": teacher_user,
        "teacher_profile": teacher_profile,
        "student1": student1,
        "enrollment1": enrollment1,
        "assignment1": assignment1,
        "teacher_token": teacher_token,
    }


def make_isolated_client(db_session: AsyncSession) -> AsyncClient:
    """
    Creates an HTTP test client that enforces real session isolation.
    Each HTTP request receives a dedicated AsyncSession which is closed upon request exit,
    mirroring the exact behavior of get_async_session in production runtime.
    """
    engine = db_session.bind
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    test_app = create_application()

    async def _fresh_session_generator() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    test_app.dependency_overrides[get_async_session] = _fresh_session_generator
    return AsyncClient(
        transport=ASGITransport(app=test_app),  # type: ignore[arg-type]
        base_url="http://testserver",
        headers={"Host": "localhost"},
    )


@pytest.mark.asyncio
async def test_teacher_dashboard_kpis_and_identity(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify teacher home dashboard KPIs, assignments count, active academic year, and student count."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    res = await client.get("/api/v1/teacher/dashboard", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["teacher_name"] == "Carlos Mendoza"
    assert data["specialty_area"] == "Física"
    assert data["institution_name"] == "Colegio Santa Librada"
    assert data["active_academic_year"] == "Año Escolar 2026"
    assert data["total_active_assignments"] == 1
    assert data["total_assigned_groups"] == 1
    assert data["total_assigned_subjects"] == 1
    assert data["total_enrolled_students"] == 1
    assert data["total_active_activities"] == 0


@pytest.mark.asyncio
async def test_teacher_my_academic_load_query(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify teacher can query active workload with human-readable resolved subject/group names."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    res = await client.get("/api/v1/teacher/assignments", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["total"] == 1
    item = data["items"][0]
    assert item["subject_name"] == "Física Clásica"
    assert item["group_name"] == "10-A"
    assert item["grade_name"] == "Décimo Grado"
    assert item["weekly_hours"] == 4
    assert item["is_active"] is True


@pytest.mark.asyncio
async def test_teacher_my_groups_and_roster(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify teacher can query assigned groups and official student roster."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    # 1. Groups list
    grp_res = await client.get("/api/v1/teacher/groups", headers=headers)
    assert grp_res.status_code == 200, grp_res.text
    groups = grp_res.json()
    assert groups["total"] == 1
    assert groups["items"][0]["group_name"] == "10-A"
    assert groups["items"][0]["active_enrolled_count"] == 1
    assert "Física Clásica" in groups["items"][0]["subjects_taught"]

    # 2. Roster for 10-A
    group_id = str(teacher_portal_fixture["group10a"].id)
    roster_res = await client.get(f"/api/v1/teacher/groups/{group_id}/roster", headers=headers)
    assert roster_res.status_code == 200, roster_res.text
    roster = roster_res.json()

    assert roster["group_name"] == "10-A"
    assert roster["total_students"] == 1
    st = roster["students"][0]
    assert st["full_name"] == "Ana García"
    assert st["document_type"] == "TI"
    assert st["document_number"] == "1020304050"
    assert st["simat_code"] == "SIM-10203040"
    assert st["enrollment_status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_teacher_roster_anti_idor_enforcement(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify server rejects roster access for a group where the teacher has no active assignment."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    unassigned_group_id = str(teacher_portal_fixture["group10b"].id)
    res = await client.get(f"/api/v1/teacher/groups/{unassigned_group_id}/roster", headers=headers)
    assert res.status_code in [400, 403, 404]
    assert "Acceso denegado" in res.text or "no tiene una asignación" in res.text


@pytest.mark.asyncio
async def test_teacher_activities_lifecycle(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify creating, querying, publishing, closing, and deleting an academic activity."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)

    # 1. Create Activity (DRAFT)
    create_payload = {
        "subject_id": subject_id,
        "group_id": group_id,
        "academic_year_id": academic_year_id,
        "title": "Taller 1: Cinemática y Movimiento Uniforme",
        "description": "Ejercicios prácticos del capítulo 2",
        "activity_type": "WORKSHOP",
        "due_date": "2026-03-15T23:59:00Z",
        "max_score": 5.0,
        "instructions": "Entregar en grupos de dos estudiantes.",
        "resource_url": "https://santander.edu.co/guias/cinematica.pdf",
    }
    create_res = await client.post("/api/v1/teacher/activities", headers=headers, json=create_payload)
    assert create_res.status_code == 201, create_res.text
    act_data = create_res.json()
    activity_id = act_data["id"]

    assert act_data["title"] == "Taller 1: Cinemática y Movimiento Uniforme"
    assert act_data["status"] == "DRAFT"
    assert act_data["subject_name"] == "Física Clásica"
    assert act_data["group_name"] == "10-A"

    # 2. Query activity
    get_res = await client.get(f"/api/v1/teacher/activities/{activity_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == create_payload["title"]

    # 3. Publish activity (should seed grade slots for active enrolled students)
    pub_res = await client.post(f"/api/v1/teacher/activities/{activity_id}/publish", headers=headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "PUBLISHED"

    # 4. Close activity
    close_res = await client.post(f"/api/v1/teacher/activities/{activity_id}/close", headers=headers)
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"

    # 5. Delete activity
    del_res = await client.delete(f"/api/v1/teacher/activities/{activity_id}", headers=headers)
    assert del_res.status_code == 204

    # 6. Verify deleted
    verify_del = await client.get(f"/api/v1/teacher/activities/{activity_id}", headers=headers)
    assert verify_del.status_code in [400, 404]


@pytest.mark.asyncio
async def test_teacher_activity_creation_rejects_unassigned_group_or_subject(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify backend enforces assignment validation when creating an activity."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    # Group 10-B is not assigned to Teacher Mendoza
    invalid_payload = {
        "subject_id": str(teacher_portal_fixture["subject_physics"].id),
        "group_id": str(teacher_portal_fixture["group10b"].id),
        "academic_year_id": str(teacher_portal_fixture["ay1"].id),
        "title": "Actividad Ilegal",
        "activity_type": "TASK",
        "max_score": 5.0,
    }
    res = await client.post("/api/v1/teacher/activities", headers=headers, json=invalid_payload)
    assert res.status_code in [400, 403, 404]
    assert "Acceso denegado" in res.text or "no tiene una asignación" in res.text


@pytest.mark.asyncio
async def test_teacher_batch_grading_and_score_bounds(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify student gradesheet evaluation and range checks (0.00 to max_score)."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    # 1. Create and publish activity
    create_res = await client.post(
        "/api/v1/teacher/activities",
        headers=headers,
        json={
            "subject_id": str(teacher_portal_fixture["subject_physics"].id),
            "group_id": str(teacher_portal_fixture["group10a"].id),
            "academic_year_id": str(teacher_portal_fixture["ay1"].id),
            "title": "Examen Parcial 1",
            "activity_type": "EXAM",
            "max_score": 5.0,
        },
    )
    activity_id = create_res.json()["id"]
    await client.post(f"/api/v1/teacher/activities/{activity_id}/publish", headers=headers)

    # 2. Query gradesheet
    grades_res = await client.get(f"/api/v1/teacher/activities/{activity_id}/grades", headers=headers)
    assert grades_res.status_code == 200
    gradesheet = grades_res.json()
    assert gradesheet["total"] == 1
    assert gradesheet["items"][0]["student_name"] == "Ana García"
    assert gradesheet["items"][0]["status"] == "PENDING"

    # 3. Batch grading valid score
    student_id = str(teacher_portal_fixture["student1"].id)
    update_res = await client.put(
        f"/api/v1/teacher/activities/{activity_id}/grades",
        headers=headers,
        json={
            "grades": [
                {
                    "student_id": student_id,
                    "score": 4.8,
                    "feedback": "Excelente comprensión de las leyes de Newton.",
                }
            ]
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert float(updated["items"][0]["score"]) == 4.8
    assert updated["items"][0]["status"] == "GRADED"
    assert updated["items"][0]["feedback"] == "Excelente comprensión de las leyes de Newton."

    # 4. Out of range score (> 5.0) rejected
    invalid_grade_res = await client.put(
        f"/api/v1/teacher/activities/{activity_id}/grades",
        headers=headers,
        json={
            "grades": [
                {
                    "student_id": student_id,
                    "score": 7.5,
                }
            ]
        },
    )
    assert invalid_grade_res.status_code in [400, 422]


@pytest.mark.asyncio
async def test_teacher_daily_attendance_logging(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify daily attendance recording and retrieval per group and session date."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    student_id = str(teacher_portal_fixture["student1"].id)

    # 1. Query initial attendance (defaults to PRESENT)
    today_str = date.today().isoformat()
    init_res = await client.get(
        f"/api/v1/teacher/groups/{group_id}/attendance",
        headers=headers,
        params={"attendance_date": today_str, "subject_id": subject_id},
    )
    assert init_res.status_code == 200
    init_sheet = init_res.json()
    assert init_sheet["total_students"] == 1
    assert init_sheet["items"][0]["status"] == "PRESENT"

    # 2. Record attendance (mark as EXCUSED with remarks)
    post_res = await client.post(
        f"/api/v1/teacher/groups/{group_id}/attendance",
        headers=headers,
        json={
            "subject_id": subject_id,
            "attendance_date": today_str,
            "records": [
                {
                    "student_id": student_id,
                    "status": "EXCUSED",
                    "remarks": "Cita médica comprobada en secretaría.",
                }
            ],
        },
    )
    assert post_res.status_code == 200
    saved_sheet = post_res.json()
    assert saved_sheet["items"][0]["status"] == "EXCUSED"
    assert saved_sheet["items"][0]["remarks"] == "Cita médica comprobada en secretaría."


@pytest.mark.asyncio
async def test_teacher_curricular_planning_lifecycle(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify creating, listing, updating, and deleting curricular lesson units."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)

    # 1. Create Plan
    create_res = await client.post(
        "/api/v1/teacher/planning",
        headers=headers,
        json={
            "subject_id": subject_id,
            "group_id": group_id,
            "academic_year_id": academic_year_id,
            "unit_name": "Unidad 1: Cinemática Vectorial",
            "competencies": "Modelación matemática y experimentación.",
            "learning_objectives": "El estudiante calcula vectores de desplazamiento y velocidad.",
            "methodology": "Aprendizaje Basado en Proyectos (ABP)",
            "evaluation_criteria": "Rúbrica de laboratorio y quiz diagnóstico.",
            "resources": "Software GeoGebra y guías del MEN.",
            "status": "IN_PROGRESS",
            "start_date": "2026-02-01",
            "end_date": "2026-03-30",
        },
    )
    assert create_res.status_code == 201, create_res.text
    plan_data = create_res.json()
    plan_id = plan_data["id"]

    assert plan_data["unit_name"] == "Unidad 1: Cinemática Vectorial"
    assert plan_data["subject_name"] == "Física Clásica"
    assert plan_data["status"] == "IN_PROGRESS"

    # 2. List plans
    list_res = await client.get("/api/v1/teacher/planning", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # 3. Update Plan
    update_res = await client.patch(
        f"/api/v1/teacher/planning/{plan_id}",
        headers=headers,
        json={"status": "COMPLETED", "unit_name": "Unidad 1: Cinemática Vectorial (Finalizada)"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "COMPLETED"
    assert update_res.json()["unit_name"] == "Unidad 1: Cinemática Vectorial (Finalizada)"

    # 4. Delete Plan
    del_res = await client.delete(f"/api/v1/teacher/planning/{plan_id}", headers=headers)
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_teacher_communications_feed_and_tenant_isolation(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """
    Test B2-H02 regression: Verify GET /api/v1/teacher/communications
    executed by an authenticated teacher returns HTTP 200, valid structure,
    proper audience matching, unread counts, and strict tenant isolation.
    """
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}
    inst1 = teacher_portal_fixture["inst1"]
    inst2 = teacher_portal_fixture["inst2"]
    teacher_user = teacher_portal_fixture["teacher_user"]

    # 1. Seed communications in DB
    # Comm 1: Target SOLO_DOCENTES in Institution 1 (Must be visible)
    comm_teachers = InstitutionalCommunication(
        institution_id=inst1.id,
        author_user_id=teacher_user.id,
        title="Circular Docente: Evaluación Trimestral",
        summary="Lineamientos pedagógicos para el cierre trimestral",
        content="Contenido oficial de la circular docente.",
        category=CommunicationCategory.CIRCULAR_OFICIAL,
        priority=CommunicationPriority.ALTA,
        target_scope=TargetScopeType.SOLO_DOCENTES,
        requires_acknowledgment=True,
        status=PublishingStatus.PUBLICADO,
        published_at=datetime.now(UTC),
    )
    # Comm 2: Target SOLO_ESTUDIANTES in Institution 1 (Must NOT be visible to teacher)
    comm_students = InstitutionalCommunication(
        institution_id=inst1.id,
        author_user_id=teacher_user.id,
        title="Aviso Exclusivo Estudiantes",
        summary="Aviso para estudiantes",
        content="Contenido solo para estudiantes.",
        category=CommunicationCategory.CIRCULAR_OFICIAL,
        priority=CommunicationPriority.MEDIA,
        target_scope=TargetScopeType.SOLO_ESTUDIANTES,
        requires_acknowledgment=False,
        status=PublishingStatus.PUBLICADO,
        published_at=datetime.now(UTC),
    )
    # Comm 3: Institution 2 (Cross-tenant boundary - Must NOT be visible to teacher)
    comm_cross_tenant = InstitutionalCommunication(
        institution_id=inst2.id,
        author_user_id=teacher_user.id,
        title="Circular Colegio San Luis",
        summary="Comunicado de otra institución",
        content="Información institucional de San Luis.",
        category=CommunicationCategory.CIRCULAR_OFICIAL,
        priority=CommunicationPriority.ALTA,
        target_scope=TargetScopeType.TODOS_INSTITUCION,
        requires_acknowledgment=False,
        status=PublishingStatus.PUBLICADO,
        published_at=datetime.now(UTC),
    )
    db_session.add_all([comm_teachers, comm_students, comm_cross_tenant])
    await db_session.commit()
    comm_teachers_id = comm_teachers.id
    comm_cross_tenant_id = comm_cross_tenant.id

    # 2. Execute GET /api/v1/teacher/communications
    res = await client.get("/api/v1/teacher/communications", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    # 3. Validate response structure and pagination/aggregations
    assert "items" in data
    assert "total" in data
    assert "unread_count" in data
    assert data["total"] == 1
    assert data["unread_count"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["id"] == str(comm_teachers_id)
    assert item["title"] == "Circular Docente: Evaluación Trimestral"
    assert item["priority"] == "ALTA"
    assert item["requires_acknowledgment"] is True
    assert item["is_read"] is False
    assert item["is_acknowledged"] is False

    # 4. Detail endpoint & automatic read recording
    detail_res = await client.get(
        f"/api/v1/teacher/communications/{comm_teachers_id}",
        headers=headers,
    )
    assert detail_res.status_code == 200, detail_res.text
    detail_data = detail_res.json()
    assert detail_data["id"] == str(comm_teachers_id)
    assert detail_data["is_read"] is True

    # List feed now reflects unread_count == 0 and is_read == True
    db_session.expire_all()
    list_after_read = await client.get("/api/v1/teacher/communications", headers=headers)
    assert list_after_read.status_code == 200
    assert list_after_read.json()["unread_count"] == 0
    assert list_after_read.json()["items"][0]["is_read"] is True

    # 5. Cross-tenant non-disclosure (Anti-IDOR)
    cross_res = await client.get(
        f"/api/v1/teacher/communications/{comm_cross_tenant_id}",
        headers=headers,
    )
    assert cross_res.status_code == 404


@pytest.mark.asyncio
async def test_teacher_activity_draft_update_and_persistence(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify B3 requirement: Updating an activity in DRAFT status persists changes and preserves DRAFT."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)

    # 1. Create activity (starts in DRAFT)
    create_payload = {
        "subject_id": subject_id,
        "group_id": group_id,
        "academic_year_id": academic_year_id,
        "title": "Taller Borrador Inicial: Leyes de Newton",
        "description": "Descripción inicial",
        "activity_type": "TASK",
        "due_date": "2026-04-01T23:59:00Z",
        "max_score": 5.0,
        "instructions": "Instrucciones iniciales",
        "resource_url": "https://ejemplo.edu.co/guia1.pdf",
    }
    create_res = await client.post("/api/v1/teacher/activities", headers=headers, json=create_payload)
    assert create_res.status_code == 201, create_res.text
    act_id = create_res.json()["id"]
    assert create_res.json()["status"] == "DRAFT"

    # 2. Update activity via PATCH (modify title, description, max_score, instructions)
    update_payload = {
        "title": "Taller Borrador Editado: Leyes de Newton y Dinámica",
        "description": "Descripción pedagógica actualizada por el docente",
        "activity_type": "WORKSHOP",
        "due_date": "2026-04-10T23:59:00Z",
        "max_score": 4.8,
        "instructions": "Nuevas instrucciones paso a paso",
        "resource_url": "https://ejemplo.edu.co/guia-actualizada.pdf",
    }
    patch_res = await client.patch(f"/api/v1/teacher/activities/{act_id}", headers=headers, json=update_payload)
    assert patch_res.status_code == 200, patch_res.text
    patch_data = patch_res.json()

    assert patch_data["id"] == act_id
    assert patch_data["title"] == update_payload["title"]
    assert patch_data["description"] == update_payload["description"]
    assert patch_data["activity_type"] == "WORKSHOP"
    assert float(patch_data["max_score"]) == 4.8
    assert patch_data["instructions"] == update_payload["instructions"]
    assert patch_data["resource_url"] == update_payload["resource_url"]

    # CRITICAL: Status must remain DRAFT (must NOT publish)
    assert patch_data["status"] == "DRAFT"
    assert patch_data["publication_date"] is None

    # 3. Reload via GET to confirm database persistence
    get_res = await client.get(f"/api/v1/teacher/activities/{act_id}", headers=headers)
    assert get_res.status_code == 200
    persisted = get_res.json()
    assert persisted["title"] == update_payload["title"]
    assert persisted["description"] == update_payload["description"]
    assert persisted["status"] == "DRAFT"
    assert float(persisted["max_score"]) == 4.8

    # 4. Anti-IDOR: Non-existent or unauthorized activity update returns 400/403/404
    fake_id = str(uuid.uuid4())
    fake_patch = await client.patch(f"/api/v1/teacher/activities/{fake_id}", headers=headers, json=update_payload)
    assert fake_patch.status_code in [400, 403, 404]


@pytest.mark.asyncio
async def test_teacher_planning_update_and_persistence(
    client: AsyncClient,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify B3 requirement: Updating an academic curricular plan persists changes and respects ownership."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}

    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)

    # 1. Create a lesson plan
    create_payload = {
        "subject_id": subject_id,
        "group_id": group_id,
        "academic_year_id": academic_year_id,
        "unit_name": "Unidad 1: Introducción a la Mecánica",
        "competencies": "Competencias básicas de física",
        "learning_objectives": "Objetivos iniciales",
        "methodology": "Clase magistral",
        "evaluation_criteria": "Quiz corto",
        "resources": "Libro guía",
        "status": "DRAFT",
        "start_date": "2026-02-01",
        "end_date": "2026-02-28",
    }
    create_res = await client.post("/api/v1/teacher/planning", headers=headers, json=create_payload)
    assert create_res.status_code == 201, create_res.text
    plan_id = create_res.json()["id"]

    # 2. Update lesson plan via PATCH
    update_payload = {
        "unit_name": "Unidad 1: Cinemática y Movimiento en Una Dimensión",
        "competencies": "Competencias actualizadas MEN: Razonamiento cuantitativo y formulación de hipótesis",
        "learning_objectives": "El estudiante resuelve ecuaciones de MRU y MRUA con precisión",
        "methodology": "Aprendizaje Activo y Laboratorios Virtuales",
        "evaluation_criteria": "Rúbrica formativa continua y sustentación",
        "resources": "Simulador PhET y guía experimental",
        "status": "IN_PROGRESS",
        "start_date": "2026-02-05",
        "end_date": "2026-03-15",
    }
    patch_res = await client.patch(f"/api/v1/teacher/planning/{plan_id}", headers=headers, json=update_payload)
    assert patch_res.status_code == 200, patch_res.text
    patch_data = patch_res.json()

    assert patch_data["id"] == plan_id
    assert patch_data["unit_name"] == update_payload["unit_name"]
    assert patch_data["competencies"] == update_payload["competencies"]
    assert patch_data["learning_objectives"] == update_payload["learning_objectives"]
    assert patch_data["methodology"] == update_payload["methodology"]
    assert patch_data["status"] == "IN_PROGRESS"
    assert patch_data["start_date"] == "2026-02-05"
    assert patch_data["end_date"] == "2026-03-15"

    # 3. Reload list via GET to confirm database persistence
    list_res = await client.get("/api/v1/teacher/planning", headers=headers, params={"group_id": group_id})
    assert list_res.status_code == 200
    plans = list_res.json()["items"]
    target_plan = next((p for p in plans if p["id"] == plan_id), None)
    assert target_plan is not None
    assert target_plan["unit_name"] == update_payload["unit_name"]
    assert target_plan["methodology"] == update_payload["methodology"]
    assert target_plan["status"] == "IN_PROGRESS"

    # 4. Anti-IDOR: Non-existent plan returns 400/403/404
    fake_plan_id = str(uuid.uuid4())
    fake_res = await client.patch(f"/api/v1/teacher/planning/{fake_plan_id}", headers=headers, json=update_payload)
    assert fake_res.status_code in [400, 403, 404]


# ===========================================================================
# 9. Real Transactional Persistence Tests with Independent HTTP Sessions (B3-H01)
# ===========================================================================

@pytest.mark.asyncio
async def test_teacher_activity_draft_persistence_independent_sessions(
    db_session: AsyncSession,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify B3-H01 requirement: POST creates DRAFT in Session A, commits, and Session B finds it."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}
    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)

    create_payload = {
        "subject_id": subject_id,
        "group_id": group_id,
        "academic_year_id": academic_year_id,
        "title": "Actividad Real con Sesiones Independientes",
        "description": "Verificación estricta de commit entre sesiones HTTP",
        "activity_type": "TASK",
        "due_date": "2026-05-01T23:59:00Z",
        "max_score": 5.0,
        "instructions": "Prueba de aislamiento transaccional real.",
    }

    async with make_isolated_client(db_session) as iso_client:
        # Request 1 (Session A): POST create activity
        post_res = await iso_client.post("/api/v1/teacher/activities", headers=headers, json=create_payload)
        assert post_res.status_code == 201, post_res.text
        act_id = post_res.json()["id"]
        assert post_res.json()["status"] == "DRAFT"

        # Request 2 (Session B - fresh session after Session A closed): GET list
        list_res = await iso_client.get("/api/v1/teacher/activities", headers=headers)
        assert list_res.status_code == 200, list_res.text
        items = list_res.json()["items"]
        found = next((a for a in items if a["id"] == act_id), None)
        assert found is not None, "FALLA CRÍTICA: La actividad no persistió en la base de datos entre sesiones independientes!"
        assert found["status"] == "DRAFT"
        assert found["title"] == create_payload["title"]

    # Request 3: Direct physical database query through brand new independent session
    engine = db_session.bind
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as verify_session:
        stmt = select(AcademicActivity).where(AcademicActivity.id == uuid.UUID(act_id))
        db_act = (await verify_session.execute(stmt)).scalar_one_or_none()
        assert db_act is not None
        assert db_act.title == create_payload["title"]
        assert db_act.status == ActivityStatus.DRAFT


@pytest.mark.asyncio
async def test_teacher_activity_draft_update_persistence_independent_sessions(
    db_session: AsyncSession,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify B3-H01 requirement: PATCH updates DRAFT in Session A, commits, and Session B reads updated values."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}
    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)

    async with make_isolated_client(db_session) as iso_client:
        # Step 1: Create DRAFT in Session 1
        create_payload = {
            "subject_id": subject_id,
            "group_id": group_id,
            "academic_year_id": academic_year_id,
            "title": "Actividad Original",
            "activity_type": "TASK",
            "max_score": 5.0,
        }
        create_res = await iso_client.post("/api/v1/teacher/activities", headers=headers, json=create_payload)
        assert create_res.status_code == 201
        act_id = create_res.json()["id"]

        # Step 2: Update DRAFT in Session 2
        update_payload = {
            "title": "Actividad con Título Modificado y Persistido",
            "max_score": 4.5,
            "instructions": "Instrucciones actualizadas en sesión independiente.",
        }
        patch_res = await iso_client.patch(f"/api/v1/teacher/activities/{act_id}", headers=headers, json=update_payload)
        assert patch_res.status_code == 200

        # Step 3: Read in Session 3
        get_res = await iso_client.get(f"/api/v1/teacher/activities/{act_id}", headers=headers)
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["title"] == update_payload["title"]
        assert float(data["max_score"]) == 4.5
        assert data["instructions"] == update_payload["instructions"]
        assert data["status"] == "DRAFT"


@pytest.mark.asyncio
async def test_teacher_activity_publish_and_close_persistence_independent_sessions(
    db_session: AsyncSession,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify B3-H01 requirement: publish and close operations persist atomically across independent sessions."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}
    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)

    async with make_isolated_client(db_session) as iso_client:
        # 1. Create
        create_res = await iso_client.post(
            "/api/v1/teacher/activities",
            headers=headers,
            json={
                "subject_id": subject_id,
                "group_id": group_id,
                "academic_year_id": academic_year_id,
                "title": "Actividad para Publicación",
                "activity_type": "EXAM",
                "max_score": 5.0,
            },
        )
        assert create_res.status_code == 201
        act_id = create_res.json()["id"]

        # 2. Publish in Session 2
        pub_res = await iso_client.post(f"/api/v1/teacher/activities/{act_id}/publish", headers=headers)
        assert pub_res.status_code == 200
        assert pub_res.json()["status"] == "PUBLISHED"

        # 3. Read in Session 3: Verify PUBLISHED and grade slots exist in fresh session
        get_res = await iso_client.get(f"/api/v1/teacher/activities/{act_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "PUBLISHED"

        # Check gradesheet in Session 4: grade slots were seeded and committed
        grades_res = await iso_client.get(f"/api/v1/teacher/activities/{act_id}/grades", headers=headers)
        assert grades_res.status_code == 200
        assert len(grades_res.json()["items"]) == 1
        assert grades_res.json()["items"][0]["student_name"] == "Ana García"

        # 4. Close in Session 5
        close_res = await iso_client.post(f"/api/v1/teacher/activities/{act_id}/close", headers=headers)
        assert close_res.status_code == 200
        assert close_res.json()["status"] == "CLOSED"

        # 5. Read in Session 6: verify CLOSED
        get_res2 = await iso_client.get(f"/api/v1/teacher/activities/{act_id}", headers=headers)
        assert get_res2.status_code == 200
        assert get_res2.json()["status"] == "CLOSED"


@pytest.mark.asyncio
async def test_teacher_batch_grading_persistence_independent_sessions(
    db_session: AsyncSession,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify B3-H01 requirement: batch grades update persists across independent HTTP sessions."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}
    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)
    student_id = str(teacher_portal_fixture["student1"].id)

    async with make_isolated_client(db_session) as iso_client:
        # Create & publish
        c_res = await iso_client.post(
            "/api/v1/teacher/activities",
            headers=headers,
            json={
                "subject_id": subject_id,
                "group_id": group_id,
                "academic_year_id": academic_year_id,
                "title": "Actividad Evaluada",
                "activity_type": "TASK",
                "max_score": 5.0,
            },
        )
        act_id = c_res.json()["id"]
        await iso_client.post(f"/api/v1/teacher/activities/{act_id}/publish", headers=headers)

        # Batch update grades in Session A
        grade_payload = {
            "grades": [
                {
                    "student_id": student_id,
                    "score": 4.8,
                    "feedback": "Excelente trabajo experimental",
                }
            ]
        }
        put_res = await iso_client.put(f"/api/v1/teacher/activities/{act_id}/grades", headers=headers, json=grade_payload)
        assert put_res.status_code == 200

        # Verify in fresh Session B
        read_res = await iso_client.get(f"/api/v1/teacher/activities/{act_id}/grades", headers=headers)
        assert read_res.status_code == 200
        st_grade = read_res.json()["items"][0]
        assert float(st_grade["score"]) == 4.8
        assert st_grade["feedback"] == "Excelente trabajo experimental"


@pytest.mark.asyncio
async def test_teacher_attendance_persistence_independent_sessions(
    db_session: AsyncSession,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify B3-H01 requirement: attendance logging persists across independent HTTP sessions."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}
    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    student_id = str(teacher_portal_fixture["student1"].id)

    async with make_isolated_client(db_session) as iso_client:
        # Record attendance in Session A
        att_payload = {
            "subject_id": subject_id,
            "attendance_date": "2026-03-09",
            "records": [
                {
                    "student_id": student_id,
                    "status": "EXCUSED",
                    "remarks": "Cita médica comprobada en secretaría.",
                }
            ],
        }
        post_res = await iso_client.post(f"/api/v1/teacher/groups/{group_id}/attendance", headers=headers, json=att_payload)
        assert post_res.status_code == 200

        # Query in fresh Session B
        get_res = await iso_client.get(
            f"/api/v1/teacher/groups/{group_id}/attendance",
            headers=headers,
            params={"attendance_date": "2026-03-09", "subject_id": subject_id},
        )
        assert get_res.status_code == 200
        items = get_res.json()["items"]
        assert len(items) == 1
        assert items[0]["status"] == "EXCUSED"
        assert items[0]["remarks"] == "Cita médica comprobada en secretaría."


@pytest.mark.asyncio
async def test_teacher_planning_lifecycle_persistence_independent_sessions(
    db_session: AsyncSession,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify B3-H01 requirement: Curricular planning lifecycle persists across independent HTTP sessions."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}
    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)

    async with make_isolated_client(db_session) as iso_client:
        # 1. Create plan in Session A
        plan_payload = {
            "subject_id": subject_id,
            "group_id": group_id,
            "academic_year_id": academic_year_id,
            "unit_name": "Unidad de Termodinámica",
            "competencies": "Termodinámica y calorimetría",
            "status": "DRAFT",
        }
        create_res = await iso_client.post("/api/v1/teacher/planning", headers=headers, json=plan_payload)
        assert create_res.status_code == 201
        plan_id = create_res.json()["id"]

        # 2. Query in Session B
        list_res = await iso_client.get("/api/v1/teacher/planning", headers=headers, params={"group_id": group_id})
        assert list_res.status_code == 200
        plans = list_res.json()["items"]
        assert any(p["id"] == plan_id for p in plans)

        # 3. Update in Session C
        patch_res = await iso_client.patch(
            f"/api/v1/teacher/planning/{plan_id}",
            headers=headers,
            json={"unit_name": "Unidad de Termodinámica y Máquinas Térmicas", "status": "APPROVED"},
        )
        assert patch_res.status_code == 200

        # 4. Verify in Session D
        list_res2 = await iso_client.get("/api/v1/teacher/planning", headers=headers, params={"group_id": group_id})
        assert list_res2.status_code == 200
        target = next(p for p in list_res2.json()["items"] if p["id"] == plan_id)
        assert target["unit_name"] == "Unidad de Termodinámica y Máquinas Térmicas"
        assert target["status"] == "APPROVED"

        # 5. Delete in Session E
        del_res = await iso_client.delete(f"/api/v1/teacher/planning/{plan_id}", headers=headers)
        assert del_res.status_code == 204

        # 6. Verify gone in Session F
        list_res3 = await iso_client.get("/api/v1/teacher/planning", headers=headers, params={"group_id": group_id})
        assert list_res3.status_code == 200
        assert not any(p["id"] == plan_id for p in list_res3.json()["items"])


@pytest.mark.asyncio
async def test_teacher_atomicity_and_rollback_on_error_independent_sessions(
    db_session: AsyncSession,
    teacher_portal_fixture: dict[str, Any],
) -> None:
    """Verify requirement 9: A failed compound operation triggers rollback and NO partial state persists."""
    headers = {"Authorization": f"Bearer {teacher_portal_fixture['teacher_token']}"}
    group_id = str(teacher_portal_fixture["group10a"].id)
    subject_id = str(teacher_portal_fixture["subject_physics"].id)
    academic_year_id = str(teacher_portal_fixture["ay1"].id)
    student_id = str(teacher_portal_fixture["student1"].id)

    async with make_isolated_client(db_session) as iso_client:
        # Create & publish
        c_res = await iso_client.post(
            "/api/v1/teacher/activities",
            headers=headers,
            json={
                "subject_id": subject_id,
                "group_id": group_id,
                "academic_year_id": academic_year_id,
                "title": "Actividad para Test de Atomicidad",
                "activity_type": "TASK",
                "max_score": 5.0,
            },
        )
        act_id = c_res.json()["id"]
        await iso_client.post(f"/api/v1/teacher/activities/{act_id}/publish", headers=headers)

        # Attempt to batch grade with an invalid score exceeding max_score (99.0 > 5.0)
        invalid_payload = {
            "grades": [
                {
                    "student_id": student_id,
                    "score": 99.0,  # Invalid: max_score is 5.0
                    "feedback": "Puntaje fuera de rango",
                }
            ]
        }
        bad_put = await iso_client.put(f"/api/v1/teacher/activities/{act_id}/grades", headers=headers, json=invalid_payload)
        assert bad_put.status_code in [400, 422], f"Expected validation failure, got: {bad_put.status_code}"

        # In a completely fresh independent session, verify score was NOT partially updated
        check_res = await iso_client.get(f"/api/v1/teacher/activities/{act_id}/grades", headers=headers)
        assert check_res.status_code == 200
        st_grade = check_res.json()["items"][0]
        # Score must remain None or unassigned, not 99.0
        assert st_grade["score"] is None, f"Atomic rollback violated! Partial score persisted: {st_grade['score']}"



