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
from decimal import Decimal
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
    AcademicPeriod,
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
