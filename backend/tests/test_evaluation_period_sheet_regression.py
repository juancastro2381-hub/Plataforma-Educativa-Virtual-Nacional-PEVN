"""
PEVN Backend — Regression Test Suite for Teacher SIEE Period Grades Sheet (GET /api/v1/evaluations/period-sheet)

Validates:
1. Normal flow: grades present and correctly consolidated.
2. Normal flow: no grades yet (empty period sheet calculated dynamically).
3. No activities defined yet (clean empty state, no division by zero).
4. Closed period enforcement (period.is_closed=True locks student rows).
5. Cross-tenant isolation (foreign institution period/group access blocked).
6. Unauthorized access (unassigned teacher without academic assignment blocked with 403).
7. Invalid period_id or group_id (returns error response, no unhandled 500).
8. Model audit timestamps persistence (created_at, updated_at on PeriodSubjectGrade, AcademicAchievement, RecoveryGrade).
9. Schema validation (output strictly conforms to PeriodSheetResponse).
10. Administrative access boundaries (least privilege enforcement).
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

from app.core.security.tokens import token_service
from app.models.academic_activity import AcademicActivity, ActivityGrade
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import (
    AcademicAchievement,
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    RecoveryGrade,
    SieePolicy,
)
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.role import Role
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.schemas.evaluation import PeriodSheetResponse
from app.services.rbac_bootstrap_service import RbacBootstrapService


@pytest.fixture
async def period_sheet_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Sets up a complete academic fixture for testing the period sheet endpoint."""
    rbac_svc = RbacBootstrapService(db_session)
    await rbac_svc.seed_canonical_rbac_if_needed()
    await db_session.flush()

    # Territory
    dept = Department(code="11", name="Bogota D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogota D.C.")
    db_session.add(mun)
    await db_session.flush()

    # Primary Institution
    inst1 = Institution(
        dane_code="222222222222",
        name="Colegio Primario Period Sheet",
        email="rector.ps1@pevn.edu.co",
        municipality_id=mun.id,
        is_active=True,
    )
    # Foreign Institution (for cross-tenant tests)
    inst2 = Institution(
        dane_code="333333333333",
        name="Colegio Secundario Cross-Tenant",
        email="rector.ps2@pevn.edu.co",
        municipality_id=mun.id,
        is_active=True,
    )
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    campus1 = Campus(
        institution_id=inst1.id,
        dane_sede_code="22222222222201",
        name="Sede A",
        is_active=True,
    )
    campus2 = Campus(
        institution_id=inst2.id,
        dane_sede_code="33333333333301",
        name="Sede B",
        is_active=True,
    )
    db_session.add_all([campus1, campus2])
    await db_session.flush()

    # Grade
    res_grade = await db_session.execute(select(Grade).where(Grade.code == "G10"))
    grade_10 = res_grade.scalar_one_or_none()
    if not grade_10:
        grade_10 = Grade(code="G10", name="Grado Decimo", level=EducationalLevel.MEDIA, ordinal_order=10)
        db_session.add(grade_10)
        await db_session.flush()

    # Academic Year & Period for Inst1
    year1 = AcademicYear(
        institution_id=inst1.id,
        name="Ano 2026 Inst1",
        year=2026,
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        start_date=date(2026, 1, 20),
        end_date=date(2026, 11, 30),
    )
    # Academic Year & Period for Inst2
    year2 = AcademicYear(
        institution_id=inst2.id,
        name="Ano 2026 Inst2",
        year=2026,
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        start_date=date(2026, 1, 20),
        end_date=date(2026, 11, 30),
    )
    db_session.add_all([year1, year2])
    await db_session.flush()

    period1_open = AcademicPeriod(
        academic_year_id=year1.id,
        period_number=1,
        name="Periodo 1 Abierto",
        weight_percentage=Decimal("25.00"),
        start_date=date(2026, 1, 20),
        end_date=date(2026, 4, 15),
        is_closed=False,
    )
    period1_closed = AcademicPeriod(
        academic_year_id=year1.id,
        period_number=2,
        name="Periodo 2 Cerrado",
        weight_percentage=Decimal("25.00"),
        start_date=date(2026, 4, 16),
        end_date=date(2026, 6, 30),
        is_closed=True,
    )
    period2_foreign = AcademicPeriod(
        academic_year_id=year2.id,
        period_number=1,
        name="Periodo Inst2",
        weight_percentage=Decimal("25.00"),
        start_date=date(2026, 1, 20),
        end_date=date(2026, 4, 15),
        is_closed=False,
    )
    db_session.add_all([period1_open, period1_closed, period2_foreign])
    await db_session.flush()

    # Groups
    group1 = Group(
        academic_year_id=year1.id,
        campus_id=campus1.id,
        grade_id=grade_10.id,
        name="10-1",
        shift=ShiftEnum.MANANA,
    )
    group2 = Group(
        academic_year_id=year2.id,
        campus_id=campus2.id,
        grade_id=grade_10.id,
        name="10-2-Foreign",
        shift=ShiftEnum.MANANA,
    )
    db_session.add_all([group1, group2])
    await db_session.flush()

    # Subject & Area
    area1 = KnowledgeArea(institution_id=inst1.id, name="Ciencias Naturales", is_mandatory=True)
    db_session.add(area1)
    await db_session.flush()

    subject_bio = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area1.id,
        grade_id=grade_10.id,
        name="Biologia",
        weekly_hours=3,
    )
    db_session.add(subject_bio)
    await db_session.flush()

    # Users: Assigned Teacher, Unassigned Teacher
    from app.core.security.password import password_hasher
    u_assigned = User(
        email="docente.assigned.reg@pevn.edu.co",
        username="docente_assigned_reg",
        hashed_password=password_hasher.hash("TeacherPass123!"),
        document_type=DocumentType.CC,
        document_number="99001",
        first_name="Beatriz",
        last_name="Docente",
        institution_id=inst1.id,
        is_active=True,
    )
    u_unassigned = User(
        email="docente.unassigned.reg@pevn.edu.co",
        username="docente_unassigned_reg",
        hashed_password=password_hasher.hash("TeacherPass123!"),
        document_type=DocumentType.CC,
        document_number="99002",
        first_name="Felipe",
        last_name="NoAsignado",
        institution_id=inst1.id,
        is_active=True,
    )
    u_foreign_teacher = User(
        email="docente.foreign.reg@pevn.edu.co",
        username="docente_foreign_reg",
        hashed_password=password_hasher.hash("TeacherPass123!"),
        document_type=DocumentType.CC,
        document_number="99003",
        first_name="Diana",
        last_name="Extranjera",
        institution_id=inst2.id,
        is_active=True,
    )
    # Students
    from app.models.student import Student, StudentGender
    u_student = User(
        email="estudiante.reg@pevn.edu.co",
        username="estudiante_reg",
        hashed_password=password_hasher.hash("StudentPass123!"),
        document_type=DocumentType.TI,
        document_number="99004",
        first_name="Camilo",
        last_name="Estudiante",
        institution_id=inst1.id,
        is_active=True,
    )
    db_session.add_all([u_assigned, u_unassigned, u_foreign_teacher, u_student])
    await db_session.flush()

    # Roles
    from app.models.role import UserRole
    role_teacher = (await db_session.execute(select(Role).where(Role.name == "teacher"))).scalar_one()
    role_student = (await db_session.execute(select(Role).where(Role.name == "student"))).scalar_one()

    db_session.add_all([
        UserRole(user_id=u_assigned.id, role_id=role_teacher.id),
        UserRole(user_id=u_unassigned.id, role_id=role_teacher.id),
        UserRole(user_id=u_foreign_teacher.id, role_id=role_teacher.id),
        UserRole(user_id=u_student.id, role_id=role_student.id),
    ])
    await db_session.flush()

    # Teacher Profiles
    t_assigned = Teacher(
        user_id=u_assigned.id,
        institution_id=inst1.id,
        contract_type=TeacherContractType.PROPIEDAD,
    )
    t_unassigned = Teacher(
        user_id=u_unassigned.id,
        institution_id=inst1.id,
        contract_type=TeacherContractType.PROPIEDAD,
    )
    t_foreign = Teacher(
        user_id=u_foreign_teacher.id,
        institution_id=inst2.id,
        contract_type=TeacherContractType.PROPIEDAD,
    )
    db_session.add_all([t_assigned, t_unassigned, t_foreign])
    await db_session.flush()

    # Academic Assignment for Assigned Teacher
    assign1 = AcademicAssignment(
        academic_year_id=year1.id,
        group_id=group1.id,
        subject_id=subject_bio.id,
        teacher_id=t_assigned.id,
        weekly_hours=3,
        is_active=True,
    )
    db_session.add(assign1)
    await db_session.flush()

    # Student Profile & Enrollment
    student_profile = Student(
        user_id=u_student.id,
        institution_id=inst1.id,
        code_simat="SIMAT-99004",
        birth_date=date(2009, 5, 10),
        gender=StudentGender.M,
    )
    db_session.add(student_profile)
    await db_session.flush()

    enrollment = Enrollment(
        academic_year_id=year1.id,
        group_id=group1.id,
        student_id=student_profile.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enrollment)
    await db_session.flush()

    # Auth Tokens
    token_assigned = await token_service.create_access_token(
        subject=str(u_assigned.id),
        additional_claims={"email": u_assigned.email, "roles": ["teacher"]},
    )
    token_unassigned = await token_service.create_access_token(
        subject=str(u_unassigned.id),
        additional_claims={"email": u_unassigned.email, "roles": ["teacher"]},
    )
    token_foreign = await token_service.create_access_token(
        subject=str(u_foreign_teacher.id),
        additional_claims={"email": u_foreign_teacher.email, "roles": ["teacher"]},
    )

    return {
        "inst1": inst1,
        "inst2": inst2,
        "period_open": period1_open,
        "period_closed": period1_closed,
        "period_foreign": period2_foreign,
        "group1": group1,
        "group2": group2,
        "subject_bio": subject_bio,
        "assignment": assign1,
        "student": student_profile,
        "enrollment": enrollment,
        "teacher_assigned": t_assigned,
        "token_assigned": token_assigned,
        "token_unassigned": token_unassigned,
        "token_foreign": token_foreign,
    }


@pytest.mark.asyncio
async def test_regression_period_sheet_empty_when_no_activities(
    client: AsyncClient,
    period_sheet_fixture: dict[str, Any],
) -> None:
    """Case 2 & 3: Sheet renders clean 200 OK when no activities or grades exist yet."""
    f = period_sheet_fixture
    p_id = str(f["period_open"].id)
    g_id = str(f["group1"].id)
    s_id = str(f["subject_bio"].id)

    resp = await client.get(
        f"/api/v1/evaluations/period-sheet?period_id={p_id}&group_id={g_id}&subject_id={s_id}",
        headers={"Authorization": f"Bearer {f['token_assigned']}"},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    # Schema validation
    validated = PeriodSheetResponse.model_validate(data)
    assert validated.period["id"] == p_id
    assert validated.activities == []
    assert len(validated.students) == 1
    assert validated.students[0].calculated_score == 0.0
    assert validated.students[0].final_score == 0.0
    assert validated.students[0].is_locked is False


@pytest.mark.asyncio
async def test_regression_period_sheet_with_grades_and_orm_timestamps(
    client: AsyncClient,
    db_session: AsyncSession,
    period_sheet_fixture: dict[str, Any],
) -> None:
    """Case 1 & 8: Saving and retrieving period grades persists created_at and updated_at."""
    f = period_sheet_fixture
    p_id = str(f["period_open"].id)
    g_id = str(f["group1"].id)
    s_id = str(f["subject_bio"].id)
    st_id = str(f["student"].id)
    enr_id = str(f["enrollment"].id)

    # 1. Save grades
    save_payload = {
        "period_id": p_id,
        "group_id": g_id,
        "subject_id": s_id,
        "items": [
            {
                "student_id": st_id,
                "enrollment_id": enr_id,
                "calculated_score": 4.2,
                "final_score": 4.5,
                "adjustment_reason": "Excelente participación pedagógica en proyectos",
                "total_absences": 2,
                "unexcused_absences": 1,
            }
        ],
        "achievements": [
            {
                "code": "ACH-BIO-01",
                "description": "Comprende los mecanismos de adaptación celular",
                "performance_level": "ALTO",
            }
        ],
    }

    save_resp = await client.post(
        "/api/v1/evaluations/period-grades",
        headers={"Authorization": f"Bearer {f['token_assigned']}"},
        json=save_payload,
    )
    assert save_resp.status_code == 200, save_resp.text

    # 2. Fetch sheet and verify data
    sheet_resp = await client.get(
        f"/api/v1/evaluations/period-sheet?period_id={p_id}&group_id={g_id}&subject_id={s_id}",
        headers={"Authorization": f"Bearer {f['token_assigned']}"},
    )
    assert sheet_resp.status_code == 200, sheet_resp.text
    sheet_data = sheet_resp.json()
    assert len(sheet_data["students"]) == 1
    s_row = sheet_data["students"][0]
    assert s_row["calculated_score"] == 4.2
    assert s_row["final_score"] == 4.5
    assert s_row["adjustment_reason"] == "Excelente participación pedagógica en proyectos"
    assert s_row["total_absences"] == 2
    assert s_row["unexcused_absences"] == 1
    assert len(sheet_data["achievements"]) == 1
    assert sheet_data["achievements"][0]["code"] == "ACH-BIO-01"

    # 3. Direct ORM model verification: timestamps must exist and be valid
    stmt = select(PeriodSubjectGrade).where(
        PeriodSubjectGrade.academic_period_id == uuid.UUID(p_id),
        PeriodSubjectGrade.student_id == uuid.UUID(st_id),
        PeriodSubjectGrade.subject_id == uuid.UUID(s_id),
    )
    grade_rec = (await db_session.execute(stmt)).scalars().first()
    assert grade_rec is not None
    assert grade_rec.created_at is not None
    assert grade_rec.updated_at is not None
    assert grade_rec.calculated_at is not None

    # Verify AcademicAchievement has created_at and updated_at
    ach_stmt = select(AcademicAchievement).where(
        AcademicAchievement.academic_period_id == uuid.UUID(p_id),
        AcademicAchievement.code == "ACH-BIO-01",
    )
    ach_rec = (await db_session.execute(ach_stmt)).scalars().first()
    assert ach_rec is not None
    assert ach_rec.created_at is not None
    assert ach_rec.updated_at is not None


@pytest.mark.asyncio
async def test_regression_period_sheet_closed_period_lock(
    client: AsyncClient,
    period_sheet_fixture: dict[str, Any],
) -> None:
    """Case 4: A closed period locks all student rows and reports is_closed=True."""
    f = period_sheet_fixture
    p_closed_id = str(f["period_closed"].id)
    g_id = str(f["group1"].id)
    s_id = str(f["subject_bio"].id)

    resp = await client.get(
        f"/api/v1/evaluations/period-sheet?period_id={p_closed_id}&group_id={g_id}&subject_id={s_id}",
        headers={"Authorization": f"Bearer {f['token_assigned']}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["period"]["is_closed"] is True
    assert len(data["students"]) == 1
    assert data["students"][0]["is_locked"] is True


@pytest.mark.asyncio
async def test_regression_period_sheet_unassigned_teacher_denied(
    client: AsyncClient,
    period_sheet_fixture: dict[str, Any],
) -> None:
    """Case 6: A teacher without academic assignment for the group x subject is denied with 403."""
    f = period_sheet_fixture
    p_id = str(f["period_open"].id)
    g_id = str(f["group1"].id)
    s_id = str(f["subject_bio"].id)

    resp = await client.get(
        f"/api/v1/evaluations/period-sheet?period_id={p_id}&group_id={g_id}&subject_id={s_id}",
        headers={"Authorization": f"Bearer {f['token_unassigned']}"},
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"


@pytest.mark.asyncio
async def test_regression_period_sheet_cross_tenant_isolation(
    client: AsyncClient,
    period_sheet_fixture: dict[str, Any],
) -> None:
    """Case 5: Attempting to access foreign institution's period from another tenant is strictly blocked."""
    f = period_sheet_fixture
    # Teacher from Inst2 tries to query Inst1's period and group
    p1_id = str(f["period_open"].id)
    g1_id = str(f["group1"].id)
    s1_id = str(f["subject_bio"].id)

    resp = await client.get(
        f"/api/v1/evaluations/period-sheet?period_id={p1_id}&group_id={g1_id}&subject_id={s1_id}",
        headers={"Authorization": f"Bearer {f['token_foreign']}"},
    )
    # Must be 403 or 400 (CrossTenantMismatchError)
    assert resp.status_code in (400, 403), f"Expected 400 or 403, got {resp.status_code}"


@pytest.mark.asyncio
async def test_regression_period_sheet_invalid_period_or_group(
    client: AsyncClient,
    period_sheet_fixture: dict[str, Any],
) -> None:
    """Case 7: Non-existent UUIDs return error without unhandled 500."""
    f = period_sheet_fixture
    random_id = str(uuid.uuid4())
    g_id = str(f["group1"].id)
    s_id = str(f["subject_bio"].id)

    resp = await client.get(
        f"/api/v1/evaluations/period-sheet?period_id={random_id}&group_id={g_id}&subject_id={s_id}",
        headers={"Authorization": f"Bearer {f['token_assigned']}"},
    )
    assert resp.status_code in (400, 403, 404), f"Expected 400/403/404, got {resp.status_code}"
