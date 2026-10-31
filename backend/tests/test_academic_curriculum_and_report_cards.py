"""
PEVN Backend — Academic Curriculum Resolution & Complete Subject Reports Tests (Phase 16E)

Authoritative test suite covering:
1. Curriculum matrix resolution merging statutory grade subjects and active teacher assignments.
2. Alignment between Student Portal, Periodic Report Card, and Final Year-End Report Card.
3. Proper handling of pending subjects (never penalized as 0.00, marked PENDING).
4. Academic promotion preview against complete group curriculum matrix.
5. Multi-tenant isolation and anti-IDOR security.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CrossTenantMismatchError, ReportCardAccessDeniedError
from app.models.academic_activity import (
    AcademicActivity,
    ActivityDeliveryType,
    ActivityGrade,
    ActivitySubmissionStatus,
    ActivityType,
    AttendanceStatusEnum,
    DailyAttendance,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicPeriod, AcademicYear, AcademicYearStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import (
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    PromotionStatusEnum,
    SieePolicy,
)
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group
from app.models.institution import Campus, Institution
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.academic_curriculum_service import AcademicCurriculumService
from app.services.academic_promotion_service import AcademicPromotionService
from app.services.report_card_service import ReportCardService
from app.services.siee_policy_service import SieePolicyService
from app.services.student_portal_service import StudentPortalService


@pytest.fixture
async def curriculum_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Build multi-tenant fixture with statutory subjects and assignments."""
    dept = Department(name="Antioquia", code="05")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, name="Medellin", code="05001")
    db_session.add(muni)
    await db_session.flush()

    uid_sfx = uuid.uuid4().hex[:6]
    inst = Institution(
        municipality_id=muni.id,
        name=f"Colegio Nacional San Martin {uid_sfx}",
        dane_code=f"105{uid_sfx}",
        email=f"sanmartin_{uid_sfx}@pevn.edu.co",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code=f"105{uid_sfx}01",
        name="Sede Central",
        is_active=True,
    )
    db_session.add(campus)
    await db_session.flush()

    # Academic Year & Periods
    ay = AcademicYear(
        institution_id=inst.id,
        year=2027,
        name="Año Lectivo 2027",
        start_date=date(2027, 1, 15),
        end_date=date(2027, 11, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    await db_session.flush()

    p1 = AcademicPeriod(
        academic_year_id=ay.id,
        period_number=1,
        name="Primer Periodo",
        weight_percentage=Decimal("33.33"),
        start_date=date(2027, 1, 15),
        end_date=date(2027, 4, 30),
        is_closed=False,
    )
    p2 = AcademicPeriod(
        academic_year_id=ay.id,
        period_number=2,
        name="Segundo Periodo",
        weight_percentage=Decimal("33.33"),
        start_date=date(2027, 5, 1),
        end_date=date(2027, 8, 15),
        is_closed=False,
    )
    p3 = AcademicPeriod(
        academic_year_id=ay.id,
        period_number=3,
        name="Tercer Periodo",
        weight_percentage=Decimal("33.34"),
        start_date=date(2027, 8, 16),
        end_date=date(2027, 11, 30),
        is_closed=False,
    )
    db_session.add_all([p1, p2, p3])
    await db_session.flush()

    # SIEE Policy via authoritative service
    siee_service = SieePolicyService(session=db_session)
    siee = await siee_service.get_or_create_default_policy(
        institution_id=inst.id,
        academic_year_id=ay.id,
    )

    # Grade & Group
    grade = Grade(
        name="Quinto",
        code=f"G05_{uid_sfx}",
        level=EducationalLevel.PRIMARIA,
        ordinal_order=5,
    )
    db_session.add(grade)
    await db_session.flush()

    group = Group(
        campus_id=campus.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="501",
        shift="MANANA",
    )
    db_session.add(group)
    await db_session.flush()

    # Knowledge Areas & Subjects (4 subjects: 2 assigned to teachers, 2 statutory unassigned)
    area_math = KnowledgeArea(institution_id=inst.id, name="Matemáticas", is_mandatory=True)
    area_sci = KnowledgeArea(institution_id=inst.id, name="Ciencias Naturales", is_mandatory=True)
    area_art = KnowledgeArea(institution_id=inst.id, name="Educación Artística", is_mandatory=False)
    area_soc = KnowledgeArea(institution_id=inst.id, name="Ciencias Sociales", is_mandatory=True)
    db_session.add_all([area_math, area_sci, area_art, area_soc])
    await db_session.flush()

    sub_math = Subject(
        institution_id=inst.id,
        grade_id=grade.id,
        knowledge_area_id=area_math.id,
        name="Matemáticas - Quinto",
        weekly_hours=4,
    )
    sub_sci = Subject(
        institution_id=inst.id,
        grade_id=grade.id,
        knowledge_area_id=area_sci.id,
        name="Ciencias Naturales - Quinto",
        weekly_hours=3,
    )
    sub_art = Subject(
        institution_id=inst.id,
        grade_id=grade.id,
        knowledge_area_id=area_art.id,
        name="Educación Artística - Quinto",
        weekly_hours=2,
    )
    sub_soc = Subject(
        institution_id=inst.id,
        grade_id=grade.id,
        knowledge_area_id=area_soc.id,
        name="Ciencias Sociales - Quinto",
        weekly_hours=3,
    )
    db_session.add_all([sub_math, sub_sci, sub_art, sub_soc])
    await db_session.flush()

    # Teachers & Assignments
    u_teach = User(
        email=f"docente_{uid_sfx}@pevn.edu.co",
        username=f"teach_{uid_sfx}",
        hashed_password="hashed_pass_test",
        first_name="Carlos",
        last_name="Mendoza",
        document_type=DocumentType.CC,
        document_number=f"71{uid_sfx[:6]}",
        institution_id=inst.id,
        is_active=True,
    )
    db_session.add(u_teach)
    await db_session.flush()

    teacher = Teacher(
        user_id=u_teach.id,
        institution_id=inst.id,
    )
    db_session.add(teacher)
    await db_session.flush()

    assign_math = AcademicAssignment(
        teacher_id=teacher.id,
        group_id=group.id,
        subject_id=sub_math.id,
        academic_year_id=ay.id,
        weekly_hours=4,
        is_active=True,
    )
    assign_sci = AcademicAssignment(
        teacher_id=teacher.id,
        group_id=group.id,
        subject_id=sub_sci.id,
        academic_year_id=ay.id,
        weekly_hours=3,
        is_active=True,
    )
    db_session.add_all([assign_math, assign_sci])
    await db_session.flush()

    # Student & Enrollment
    u_student = User(
        email=f"estudiante_{uid_sfx}@pevn.edu.co",
        username=f"student_{uid_sfx}",
        hashed_password="hashed_pass_test",
        first_name="Valeria",
        last_name="Ramirez",
        document_type=DocumentType.TI,
        document_number=f"102{uid_sfx[:6]}",
        institution_id=inst.id,
        is_active=True,
    )
    db_session.add(u_student)
    await db_session.flush()

    student = Student(
        user_id=u_student.id,
        institution_id=inst.id,
        code_simat=f"SIMAT-{uid_sfx}",
        gender=StudentGender.F,
        birth_date=date(2015, 6, 10),
    )
    db_session.add(student)
    await db_session.flush()

    enrollment = Enrollment(
        student_id=student.id,
        group_id=group.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enrollment)
    await db_session.flush()

    return {
        "institution": inst,
        "campus": campus,
        "academic_year": ay,
        "periods": [p1, p2, p3],
        "siee": siee,
        "grade": grade,
        "group": group,
        "subjects": {
            "math": sub_math,
            "sci": sub_sci,
            "art": sub_art,
            "soc": sub_soc,
        },
        "teacher": teacher,
        "student": student,
        "enrollment": enrollment,
    }


@pytest.mark.anyio
async def test_curriculum_service_resolution_statutory_and_assignments(
    db_session: AsyncSession,
    curriculum_fixture: dict[str, Any],
) -> None:
    """
    Verify that AcademicCurriculumService resolves all statutory and assigned subjects
    in authoritative canonical order.
    """
    f = curriculum_fixture
    service = AcademicCurriculumService(session=db_session)

    matrix = await service.resolve_student_curriculum(
        institution_id=f["institution"].id,
        student_id=f["student"].id,
        academic_year_id=f["academic_year"].id,
    )

    assert matrix.student_id == f["student"].id
    assert matrix.group_id == f["group"].id
    assert matrix.grade_id == f["grade"].id
    assert len(matrix.subjects) == 4

    # Check math: assigned to Carlos Mendoza
    math_item = next((s for s in matrix.subjects if s.subject_id == f["subjects"]["math"].id), None)
    assert math_item is not None
    assert math_item.teacher_id == f["teacher"].id
    assert math_item.teacher_name == "Carlos Mendoza"
    assert math_item.weekly_hours == 4
    assert math_item.is_mandatory is True

    # Check art: statutory but not assigned
    art_item = next((s for s in matrix.subjects if s.subject_id == f["subjects"]["art"].id), None)
    assert art_item is not None
    assert art_item.teacher_id is None
    assert art_item.teacher_name is None
    assert art_item.weekly_hours == 2
    assert art_item.is_mandatory is False


@pytest.mark.anyio
async def test_student_portal_and_report_cards_curriculum_alignment(
    db_session: AsyncSession,
    curriculum_fixture: dict[str, Any],
) -> None:
    """
    Verify that StudentPortalService, Periodic Report Card, and Final Report Card
    exhibit 100% curriculum matrix consistency across all 4 subjects.
    """
    f = curriculum_fixture
    student = f["student"]
    inst = f["institution"]
    ay = f["academic_year"]
    p1 = f["periods"][0]

    # Create grade only for Math (4.20) in Period 1
    grade_math = PeriodSubjectGrade(
        institution_id=inst.id,
        academic_period_id=p1.id,
        enrollment_id=f["enrollment"].id,
        student_id=student.id,
        subject_id=f["subjects"]["math"].id,
        calculated_score=Decimal("4.20"),
        final_score=Decimal("4.20"),
        performance_level=PerformanceLevelEnum.ALTO,
        total_absences=0,
        unexcused_absences=0,
    )
    db_session.add(grade_math)
    await db_session.flush()

    # 1. Student Portal check
    portal_service = StudentPortalService(session=db_session)
    portal_subjects = await portal_service.list_subjects(student=student)
    assert portal_subjects.total == 4
    portal_subj_ids = {s.subject_id for s in portal_subjects.items}
    assert portal_subj_ids == {s.id for s in f["subjects"].values()}

    # 2. Official Period Report Card check
    rc_service = ReportCardService(session=db_session)
    p_card = await rc_service.get_student_report_card(
        institution_id=inst.id,
        student_id=student.id,
        period_id=p1.id,
    )
    assert len(p_card["subjects"]) == 4
    assert p_card["summary"]["total_subjects"] == 4
    assert p_card["summary"]["passed_subjects"] == 1
    assert p_card["summary"]["failed_subjects"] == 0
    assert p_card["summary"]["pending_subjects"] == 3
    # Promedio must only average the evaluated subject (4.20), not divided by 4!
    assert p_card["summary"]["average_score"] == 4.20
    assert p_card["summary"]["performance_level"] == "ALTO"
    assert p_card["summary"]["is_provisional"] is True

    # 3. Official Year-End Report Card check
    f_card = await rc_service.get_student_final_report_card(
        institution_id=inst.id,
        student_id=student.id,
        academic_year_id=ay.id,
    )
    assert len(f_card["subjects"]) == 4
    assert f_card["summary"]["total_subjects"] == 4
    assert f_card["summary"]["cumulative_average"] == 4.20
    assert f_card["summary"]["pending_subjects_count"] == 3
    assert f_card["summary"]["is_provisional"] is True
    assert f_card["promotion"]["is_provisional"] is True


@pytest.mark.anyio
async def test_pending_subjects_not_penalized_in_average(
    db_session: AsyncSession,
    curriculum_fixture: dict[str, Any],
) -> None:
    """
    Ensure that un-evaluated (pending) subjects do not evaluate as 0.00
    and do not penalize the student's academic standing.
    """
    f = curriculum_fixture
    student = f["student"]
    inst = f["institution"]
    p1 = f["periods"][0]

    # Two subjects evaluated: Math (4.00) and Sciences (3.60)
    g1 = PeriodSubjectGrade(
        institution_id=inst.id,
        academic_period_id=p1.id,
        enrollment_id=f["enrollment"].id,
        student_id=student.id,
        subject_id=f["subjects"]["math"].id,
        calculated_score=Decimal("4.00"),
        final_score=Decimal("4.00"),
        performance_level=PerformanceLevelEnum.ALTO,
        total_absences=0,
        unexcused_absences=0,
    )
    g2 = PeriodSubjectGrade(
        institution_id=inst.id,
        academic_period_id=p1.id,
        enrollment_id=f["enrollment"].id,
        student_id=student.id,
        subject_id=f["subjects"]["sci"].id,
        calculated_score=Decimal("3.60"),
        final_score=Decimal("3.60"),
        performance_level=PerformanceLevelEnum.BASICO,
        total_absences=0,
        unexcused_absences=0,
    )
    db_session.add_all([g1, g2])
    await db_session.flush()

    rc_service = ReportCardService(session=db_session)
    p_card = await rc_service.get_student_report_card(
        institution_id=inst.id,
        student_id=student.id,
        period_id=p1.id,
    )

    # Average of 4.00 and 3.60 is (4.00 + 3.60)/2 = 3.80
    assert p_card["summary"]["average_score"] == 3.80
    assert p_card["summary"]["passed_subjects"] == 2
    assert p_card["summary"]["failed_subjects"] == 0
    assert p_card["summary"]["pending_subjects"] == 2

    # Check that pending subjects have None score
    pending_art = next((s for s in p_card["subjects"] if s["subject_id"] == str(f["subjects"]["art"].id)), None)
    assert pending_art is not None
    assert pending_art["final_score"] is None
    assert pending_art["evaluation_status"] == "PENDING"
    assert pending_art["performance_level"] is None


@pytest.mark.anyio
async def test_promotion_preview_with_curriculum_matrix(
    db_session: AsyncSession,
    curriculum_fixture: dict[str, Any],
) -> None:
    """
    Verify that AcademicPromotionService calculates preview against all curriculum subjects,
    accurately detecting in-progress status when subjects remain pending.
    """
    f = curriculum_fixture
    inst = f["institution"]
    ay = f["academic_year"]
    group = f["group"]
    p1 = f["periods"][0]

    # Evaluate one subject in Period 1
    g = PeriodSubjectGrade(
        institution_id=inst.id,
        academic_period_id=p1.id,
        enrollment_id=f["enrollment"].id,
        student_id=f["student"].id,
        subject_id=f["subjects"]["math"].id,
        calculated_score=Decimal("3.80"),
        final_score=Decimal("3.80"),
        performance_level=PerformanceLevelEnum.BASICO,
        total_absences=0,
        unexcused_absences=0,
    )
    db_session.add(g)
    await db_session.flush()

    promo_service = AcademicPromotionService(session=db_session)
    preview = await promo_service.calculate_promotion_preview(
        institution_id=inst.id,
        group_id=group.id,
        academic_year_id=ay.id,
    )

    assert preview["total_candidates"] == 1
    cand = preview["candidates"][0]
    assert cand["student_id"] == str(f["student"].id)
    assert cand["total_curriculum_subjects"] == 4
    assert cand["evaluated_subjects_count"] == 1
    assert cand["pending_subjects_count"] == 3
    assert cand["is_provisional"] is True
    assert "Dictamen provisional" in cand["decision_reason"]


@pytest.mark.anyio
async def test_report_cards_multi_tenant_and_anti_idor(
    db_session: AsyncSession,
    curriculum_fixture: dict[str, Any],
) -> None:
    """
    Verify cross-tenant and anti-IDOR protections in report cards and curriculum service.
    """
    f = curriculum_fixture
    alien_inst_id = uuid.uuid4()

    rc_service = ReportCardService(session=db_session)

    # Cross-tenant student access denied
    with pytest.raises(CrossTenantMismatchError):
        await rc_service.get_student_report_card(
            institution_id=alien_inst_id,
            student_id=f["student"].id,
            period_id=f["periods"][0].id,
        )

    # Cross-tenant curriculum resolution denied
    curriculum_service = AcademicCurriculumService(session=db_session)
    with pytest.raises(CrossTenantMismatchError):
        await curriculum_service.resolve_student_curriculum(
            institution_id=alien_inst_id,
            student_id=f["student"].id,
            academic_year_id=f["academic_year"].id,
        )
