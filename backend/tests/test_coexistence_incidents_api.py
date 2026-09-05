"""
PEVN Backend — School Coexistence & Student Incidents Integration & Anti-IDOR Tests (Phase 15)

Tests:
1. Ley 1620 situation recording (Tipo I, II, III, Positiva).
2. Teacher academic scope enforcement (DECISION-15-04: teachers can only record/view for assigned students).
3. Student Observador visibility (DECISION-15-01: student sees own records only if is_visible_to_student = True).
4. Guardian Observador family isolation (guardians can ONLY see linked children via StudentGuardian, cross-child 404 Anti-IDOR).
5. Chronological follow-up notes and formal closure resolution.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
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
from app.models.coexistence_incident import (
    CoexistenceSituationType,
    IncidentStatus,
    StudentIncident,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.guardian import Guardian, GuardianRelationshipType, StudentGuardian
from app.models.institution import Campus, Institution
from app.models.role import Role, UserRole
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def incident_test_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Sets up institution, groups, assigned teacher, unassigned teacher, 2 students, guardian, and tokens."""
    dept = Department(code="25", name="Cundinamarca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="25001", name="Chia")
    db_session.add(mun)
    await db_session.flush()

    inst = Institution(
        dane_code="555555555555",
        name="Colegio Mayor de Chia",
        email="rector.chia@pevn.edu.co",
        municipality_id=mun.id,
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(institution_id=inst.id, dane_sede_code="55555555555501", name="Sede Campestre", is_active=True)
    db_session.add(campus)
    await db_session.flush()

    res9 = await db_session.execute(select(Grade).where(Grade.code == "G09"))
    grade_9 = res9.scalar_one_or_none()
    if not grade_9:
        grade_9 = Grade(code="G09", name="Grado Noveno", level=EducationalLevel.SECUNDARIA, ordinal_order=9)
        db_session.add(grade_9)
        await db_session.flush()

    res11 = await db_session.execute(select(Grade).where(Grade.code == "G11"))
    grade_11 = res11.scalar_one_or_none()
    if not grade_11:
        grade_11 = Grade(code="G11", name="Grado Once", level=EducationalLevel.MEDIA, ordinal_order=11)
        db_session.add(grade_11)
        await db_session.flush()

    year_2026 = AcademicYear(
        institution_id=inst.id,
        name="Año 2026",
        year=2026,
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        start_date=datetime(2026, 1, 20).date(),
        end_date=datetime(2026, 11, 30).date(),
    )
    db_session.add(year_2026)
    await db_session.flush()

    group_9a = Group(
        academic_year_id=year_2026.id,
        campus_id=campus.id,
        grade_id=grade_9.id,
        name="9-A",
        shift=ShiftEnum.MANANA,
    )
    group_11a = Group(
        academic_year_id=year_2026.id,
        campus_id=campus.id,
        grade_id=grade_11.id,
        name="11-A",
        shift=ShiftEnum.MANANA,
    )
    db_session.add_all([group_9a, group_11a])
    await db_session.flush()

    area = KnowledgeArea(institution_id=inst.id, name="Humanidades", is_mandatory=True)
    db_session.add(area)
    await db_session.flush()

    subject_esp = Subject(
        institution_id=inst.id,
        knowledge_area_id=area.id,
        grade_id=grade_9.id,
        name="Lengua Castellana",
        weekly_hours=4,
    )
    db_session.add(subject_esp)
    await db_session.flush()

    # Retrieve bootstrapped roles
    roles_res = await db_session.execute(select(Role))
    roles_map = {r.name: r for r in roles_res.scalars().all()}

    # Users
    rector_user = User(
        email="rector.chia@pevn.edu.co",
        username="rector_chia",
        hashed_password=password_hasher.hash("RectorPass123!"),
        document_type=DocumentType.CC,
        document_number="30001",
        first_name="Ernesto",
        last_name="Rector",
        institution_id=inst.id,
        is_active=True,
    )
    teacher_assigned_user = User(
        email="docente.assigned@pevn.edu.co",
        username="docente_assigned",
        hashed_password=password_hasher.hash("TeacherPass123!"),
        document_type=DocumentType.CC,
        document_number="30002",
        first_name="Profesor",
        last_name="Asignado",
        institution_id=inst.id,
        is_active=True,
    )
    teacher_unassigned_user = User(
        email="docente.unassigned@pevn.edu.co",
        username="docente_unassigned",
        hashed_password=password_hasher.hash("TeacherPass123!"),
        document_type=DocumentType.CC,
        document_number="30003",
        first_name="Profesor",
        last_name="NoAsignado",
        institution_id=inst.id,
        is_active=True,
    )
    student1_user = User(
        email="estudiante.andres@pevn.edu.co",
        username="andres_student",
        hashed_password=password_hasher.hash("StudentPass123!"),
        document_type=DocumentType.TI,
        document_number="30004",
        first_name="Andres",
        last_name="Perez",
        institution_id=inst.id,
        is_active=True,
    )
    student2_user = User(
        email="estudiante.felipe@pevn.edu.co",
        username="felipe_student",
        hashed_password=password_hasher.hash("StudentPass123!"),
        document_type=DocumentType.TI,
        document_number="30005",
        first_name="Felipe",
        last_name="Mora",
        institution_id=inst.id,
        is_active=True,
    )
    guardian_user = User(
        email="acudiente.perez@pevn.edu.co",
        username="perez_guardian",
        hashed_password=password_hasher.hash("GuardianPass123!"),
        document_type=DocumentType.CC,
        document_number="30006",
        first_name="Martha",
        last_name="Perez",
        institution_id=inst.id,
        is_active=True,
    )
    db_session.add_all([
        rector_user,
        teacher_assigned_user,
        teacher_unassigned_user,
        student1_user,
        student2_user,
        guardian_user,
    ])
    await db_session.flush()

    db_session.add(UserRole(user_id=rector_user.id, role_id=roles_map["rector"].id))
    db_session.add(UserRole(user_id=teacher_assigned_user.id, role_id=roles_map["teacher"].id))
    db_session.add(UserRole(user_id=teacher_unassigned_user.id, role_id=roles_map["teacher"].id))
    db_session.add(UserRole(user_id=student1_user.id, role_id=roles_map["student"].id))
    db_session.add(UserRole(user_id=student2_user.id, role_id=roles_map["student"].id))
    db_session.add(UserRole(user_id=guardian_user.id, role_id=roles_map["guardian"].id))
    await db_session.flush()

    # Profiles
    teacher_assigned = Teacher(
        institution_id=inst.id,
        user_id=teacher_assigned_user.id,
        contract_type=TeacherContractType.PROPIEDAD,
        specialty_area="Lengua Castellana",
    )
    student1 = Student(
        institution_id=inst.id,
        user_id=student1_user.id,
        code_simat="SIMAT-3001",
        birth_date=datetime(2010, 2, 14).date(),
        gender=StudentGender.M,
    )
    student2 = Student(
        institution_id=inst.id,
        user_id=student2_user.id,
        code_simat="SIMAT-3002",
        birth_date=datetime(2008, 6, 20).date(),
        gender=StudentGender.M,
    )
    guardian = Guardian(
        institution_id=inst.id,
        user_id=guardian_user.id,
        first_name="Martha",
        last_name="Perez",
        document_type=DocumentType.CC,
        document_number="30006",
        phone="3007654321",
        relationship_type=GuardianRelationshipType.MADRE,
    )
    db_session.add_all([teacher_assigned, student1, student2, guardian])
    await db_session.flush()

    # Enrollments: Student 1 in 9-A, Student 2 in 11-A
    enr1 = Enrollment(
        student_id=student1.id,
        academic_year_id=year_2026.id,
        group_id=group_9a.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=datetime(2026, 1, 20).date(),
    )
    enr2 = Enrollment(
        student_id=student2.id,
        academic_year_id=year_2026.id,
        group_id=group_11a.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=datetime(2026, 1, 20).date(),
    )
    # Teacher assignment: Teacher Assigned teaches 9-A only
    asg = AcademicAssignment(
        academic_year_id=year_2026.id,
        teacher_id=teacher_assigned.id,
        subject_id=subject_esp.id,
        group_id=group_9a.id,
        weekly_hours=4,
    )
    # Guardian links to Student 1 only
    link1 = StudentGuardian(
        student_id=student1.id,
        guardian_id=guardian.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
    )
    db_session.add_all([enr1, enr2, asg, link1])
    await db_session.commit()

    rector_token = await token_service.create_access_token(
        subject=str(rector_user.id),
        additional_claims={"email": rector_user.email, "roles": ["rector"], "institution_id": str(inst.id)},
    )
    teacher_assigned_token = await token_service.create_access_token(
        subject=str(teacher_assigned_user.id),
        additional_claims={"email": teacher_assigned_user.email, "roles": ["teacher"], "institution_id": str(inst.id)},
    )
    teacher_unassigned_token = await token_service.create_access_token(
        subject=str(teacher_unassigned_user.id),
        additional_claims={"email": teacher_unassigned_user.email, "roles": ["teacher"], "institution_id": str(inst.id)},
    )
    student1_token = await token_service.create_access_token(
        subject=str(student1_user.id),
        additional_claims={"email": student1_user.email, "roles": ["student"], "institution_id": str(inst.id)},
    )
    guardian_token = await token_service.create_access_token(
        subject=str(guardian_user.id),
        additional_claims={"email": guardian_user.email, "roles": ["guardian"], "institution_id": str(inst.id)},
    )

    return {
        "inst_id": inst.id,
        "student1_id": student1.id,
        "student2_id": student2.id,
        "rector_token": rector_token,
        "teacher_assigned_token": teacher_assigned_token,
        "teacher_unassigned_token": teacher_unassigned_token,
        "student1_token": student1_token,
        "guardian_token": guardian_token,
    }


@pytest.mark.asyncio
async def test_teacher_scope_and_incident_recording(
    client: AsyncClient,
    incident_test_fixture: dict[str, Any],
) -> None:
    """Test DECISION-15-04: Teacher scope enforcement for student coexistence recording."""
    student1_id = str(incident_test_fixture["student1_id"])
    student2_id = str(incident_test_fixture["student2_id"])
    teacher_assigned_token = incident_test_fixture["teacher_assigned_token"]
    teacher_unassigned_token = incident_test_fixture["teacher_unassigned_token"]

    payload_student1 = {
        "student_id": student1_id,
        "situation_type": "TIPO_I",
        "description": "El estudiante interrumpio la clase de espanol de forma reiterada.",
        "pedagogical_measures": "Acuerdo pedagogico en el aula y lectura reflexiva.",
        "commitments": "Compromiso de prestar atencion y respetar la palabra.",
        "is_visible_to_guardian": True,
        "is_visible_to_student": True,
    }

    # 1. Assigned teacher records incident for student 1 (in 9-A) -> Allowed
    res_ok = await client.post(
        "/api/v1/incidents",
        json=payload_student1,
        headers={"Authorization": f"Bearer {teacher_assigned_token}"},
    )
    assert res_ok.status_code == 201
    incident_id = res_ok.json()["id"]
    assert res_ok.json()["situation_type"] == "TIPO_I"

    # 2. Assigned teacher attempts recording for student 2 (in 11-A, not assigned) -> Denied (404)
    payload_student2 = {
        "student_id": student2_id,
        "situation_type": "TIPO_I",
        "description": "Incidente fuera de su grado.",
        "pedagogical_measures": "Medida.",
    }
    res_denied = await client.post(
        "/api/v1/incidents",
        json=payload_student2,
        headers={"Authorization": f"Bearer {teacher_assigned_token}"},
    )
    assert res_denied.status_code == 404

    # 3. Unassigned teacher attempts recording for student 1 -> Denied (404)
    res_unassigned = await client.post(
        "/api/v1/incidents",
        json=payload_student1,
        headers={"Authorization": f"Bearer {teacher_unassigned_token}"},
    )
    assert res_unassigned.status_code == 404


@pytest.mark.asyncio
async def test_student_and_guardian_observador_visibility(
    client: AsyncClient,
    incident_test_fixture: dict[str, Any],
) -> None:
    """Test DECISION-15-01: Student visibility and Guardian strict Anti-IDOR family isolation."""
    student1_id = str(incident_test_fixture["student1_id"])
    student2_id = str(incident_test_fixture["student2_id"])
    rector_token = incident_test_fixture["rector_token"]
    student1_token = incident_test_fixture["student1_token"]
    guardian_token = incident_test_fixture["guardian_token"]

    # Rector creates a confidential/hidden incident for Student 1
    res_hidden = await client.post(
        "/api/v1/incidents",
        json={
            "student_id": student1_id,
            "situation_type": "TIPO_II",
            "description": "Investigacion preliminar de convivencia.",
            "pedagogical_measures": "Seguimiento con comite.",
            "is_visible_to_student": False,  # Hidden from student
            "is_visible_to_guardian": True,  # Visible to guardian
        },
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    hidden_id = res_hidden.json()["id"]

    # Rector creates an open positive observation for Student 1
    res_open = await client.post(
        "/api/v1/incidents",
        json={
            "student_id": student1_id,
            "situation_type": "OBSERVACION_POSITIVA",
            "description": "Felicitacion por liderazgo en convivencia.",
            "pedagogical_measures": "Mencion de honor en izada de bandera.",
            "is_visible_to_student": True,
            "is_visible_to_guardian": True,
        },
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    open_id = res_open.json()["id"]

    # 1. Student 1 queries own Observador -> Hidden incident must NOT be returned, open must be present
    student_res = await client.get(
        "/api/v1/student/incidents",
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert student_res.status_code == 200
    student_incident_ids = [i["id"] for i in student_res.json()["items"]]
    assert open_id in student_incident_ids
    assert hidden_id not in student_incident_ids

    # 2. Guardian queries Student 1 (linked child) -> Both returned because is_visible_to_guardian = True
    guardian_child1_res = await client.get(
        f"/api/v1/guardian/students/{student1_id}/incidents",
        headers={"Authorization": f"Bearer {guardian_token}"},
    )
    assert guardian_child1_res.status_code == 200
    guardian_child1_ids = [i["id"] for i in guardian_child1_res.json()["items"]]
    assert open_id in guardian_child1_ids
    assert hidden_id in guardian_child1_ids

    # 3. Guardian queries Student 2 (unlinked student) -> Must return 404 Anti-IDOR
    guardian_child2_res = await client.get(
        f"/api/v1/guardian/students/{student2_id}/incidents",
        headers={"Authorization": f"Bearer {guardian_token}"},
    )
    assert guardian_child2_res.status_code == 404


@pytest.mark.asyncio
async def test_incident_follow_up_and_closure(
    client: AsyncClient,
    incident_test_fixture: dict[str, Any],
) -> None:
    """Test adding follow-up notes and formally closing a coexistence incident."""
    student1_id = str(incident_test_fixture["student1_id"])
    rector_token = incident_test_fixture["rector_token"]

    # 1. Create incident
    res = await client.post(
        "/api/v1/incidents",
        json={
            "student_id": student1_id,
            "situation_type": "TIPO_I",
            "description": "Llegada tarde reiterada.",
            "pedagogical_measures": "Compromiso de puntualidad.",
        },
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    incident_id = res.json()["id"]
    assert res.json()["status"] == "ABIERTO"

    # 2. Add follow-up note
    followup_res = await client.post(
        f"/api/v1/incidents/{incident_id}/follow-ups",
        json={
            "notes": "Entrevista con el acudiente y revision de cumplimiento.",
        },
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    assert followup_res.status_code == 201
    assert followup_res.json()["notes"] == "Entrevista con el acudiente y revision de cumplimiento."

    # 3. Close incident
    close_res = await client.post(
        f"/api/v1/incidents/{incident_id}/close",
        json={
            "resolution_notes": "El estudiante cumplio a cabalidad con los compromisos.",
        },
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CERRADO"
    assert close_res.json()["closed_at"] is not None
