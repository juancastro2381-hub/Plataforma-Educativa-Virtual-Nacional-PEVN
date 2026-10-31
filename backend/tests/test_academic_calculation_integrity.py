"""
PEVN Backend — Academic Calculation & Data Integrity Tests (Phase 16E)

Authoritative test suite covering:
1. Activity weighted grading and period consolidated scores.
2. Ungraded/missing activity handling (not defaulting to 0).
3. Pedagogical adjustments preservation vs dynamic tracking (DECISION-16-03).
4. Authoritative classroom and subject attendance / absence tracking from DailyAttendance.
5. Periodic and Year-End report card consistency.
6. Multi-tenant isolation and security enforcement.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_activity import (
    AcademicActivity,
    ActivityGrade,
    ActivitySubmissionStatus,
    ActivityType,
    AttendanceStatusEnum,
    DailyAttendance,
    ActivityDeliveryType,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicPeriod, AcademicYear, AcademicYearStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import (
    PerformanceLevelEnum,
    PeriodSubjectGrade,
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
from app.services.academic_calculation_service import AcademicCalculationService
from app.services.evaluation_service import EvaluationService
from app.services.report_card_service import ReportCardService
from app.services.siee_policy_service import SieePolicyService


@pytest.fixture
async def academic_calc_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Build isolated multi-tenant fixture for academic calculation tests."""
    dept = Department(name="Tolima", code="73")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, name="Ibague", code="73001")
    db_session.add(muni)
    await db_session.flush()

    uid_sfx = uuid.uuid4().hex[:6]
    inst = Institution(
        municipality_id=muni.id,
        name=f"Institución Modelo SIEE {uid_sfx}",
        dane_code=f"173{uid_sfx}",
        email=f"modelo_{uid_sfx}@siee.edu.co",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code=f"173{uid_sfx}01",
        name="Sede Principal",
        is_active=True,
    )
    db_session.add(campus)
    await db_session.flush()

    year = AcademicYear(
        institution_id=inst.id,
        year=2027,
        name="Año Lectivo 2027",
        status=AcademicYearStatus.ACTIVE,
        start_date=date(2027, 2, 1),
        end_date=date(2027, 11, 30),
    )
    db_session.add(year)
    await db_session.flush()

    p1 = AcademicPeriod(
        academic_year_id=year.id,
        period_number=1,
        name="Primer Periodo",
        weight_percentage=Decimal("33.33"),
        start_date=date(2027, 2, 1),
        end_date=date(2027, 5, 12),
        is_closed=False,
    )
    p2 = AcademicPeriod(
        academic_year_id=year.id,
        period_number=2,
        name="Segundo Periodo",
        weight_percentage=Decimal("33.33"),
        start_date=date(2027, 5, 13),
        end_date=date(2027, 8, 21),
        is_closed=False,
    )
    p3 = AcademicPeriod(
        academic_year_id=year.id,
        period_number=3,
        name="Tercer Periodo",
        weight_percentage=Decimal("33.34"),
        start_date=date(2027, 8, 22),
        end_date=date(2027, 11, 30),
        is_closed=False,
    )
    db_session.add_all([p1, p2, p3])
    await db_session.flush()

    grade_1 = Grade(code=f"G01_{uid_sfx}", name="Primero", level=EducationalLevel.PRIMARIA, ordinal_order=1)
    db_session.add(grade_1)
    await db_session.flush()

    group_101 = Group(
        campus_id=campus.id,
        academic_year_id=year.id,
        grade_id=grade_1.id,
        name="101",
        shift="MANANA",
    )
    db_session.add(group_101)
    await db_session.flush()

    area = KnowledgeArea(institution_id=inst.id, name=f"Ciencias Naturales {uid_sfx}", is_mandatory=True)
    db_session.add(area)
    await db_session.flush()

    subj = Subject(
        institution_id=inst.id,
        knowledge_area_id=area.id,
        grade_id=grade_1.id,
        name="Ciencias Naturales - Primero",
        weekly_hours=4,
    )
    db_session.add(subj)
    await db_session.flush()

    u_teacher = User(
        email=f"docente_{uid_sfx}@pevn.edu.co",
        username=f"doc_{uid_sfx}",
        hashed_password="hashed_pass_test",
        first_name="Profesor",
        last_name="Ciencias",
        document_type=DocumentType.CC,
        document_number=f"79{uid_sfx}",
        institution_id=inst.id,
    )
    u_student = User(
        email=f"danna_{uid_sfx}@pevn.edu.co",
        username=f"danna_{uid_sfx}",
        hashed_password="hashed_pass_test",
        first_name="Danna",
        last_name="Gonzalez",
        document_type=DocumentType.TI,
        document_number=f"10{uid_sfx}",
        institution_id=inst.id,
    )
    db_session.add_all([u_teacher, u_student])
    await db_session.flush()

    teacher = Teacher(institution_id=inst.id, user_id=u_teacher.id)
    student = Student(
        institution_id=inst.id,
        user_id=u_student.id,
        code_simat=f"SIMAT-2026-{uid_sfx}",
        birth_date=date(2018, 5, 10),
        gender=StudentGender.F,
    )
    db_session.add_all([teacher, student])
    await db_session.flush()

    enr = Enrollment(
        student_id=student.id,
        academic_year_id=year.id,
        group_id=group_101.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enr)
    await db_session.flush()

    assignment = AcademicAssignment(
        teacher_id=teacher.id,
        group_id=group_101.id,
        subject_id=subj.id,
        academic_year_id=year.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assignment)
    await db_session.flush()

    siee = SieePolicyService(session=db_session)
    policy = await siee.get_or_create_default_policy(
        institution_id=inst.id,
        academic_year_id=year.id,
    )

    return {
        "institution": inst,
        "campus": campus,
        "academic_year": year,
        "period_1": p1,
        "period_2": p2,
        "period_3": p3,
        "group": group_101,
        "subject": subj,
        "teacher": teacher,
        "student": student,
        "enrollment": enr,
        "assignment": assignment,
        "policy": policy,
        "user_teacher": u_teacher,
        "user_student": u_student,
    }


@pytest.mark.asyncio
async def test_activity_grade_aggregation_and_missing_grades(
    db_session: AsyncSession,
    academic_calc_fixture: dict[str, Any],
) -> None:
    """
    Verify activity weighted grading and that missing activities are not counted as 0.0.
    """
    f = academic_calc_fixture
    calc_svc = AcademicCalculationService(session=db_session)

    # 1. Create 3 activities:
    # Act 1: 3.10 (weight 1.0)
    # Act 2: 2.50 (weight 1.0)
    # Act 3: 4.50 (weight 1.0)
    # Act 4: Ungraded activity (should NOT pull average down)
    act1 = AcademicActivity(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        title="Actividad 1 ciencias",
        activity_type=ActivityType.WORKSHOP,
        status="PUBLISHED",
        delivery_type=ActivityDeliveryType.TEXT,
        max_score=Decimal("5.00"),
    )
    act2 = AcademicActivity(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        title="Taller #2 Ecuaciones",
        activity_type=ActivityType.WORKSHOP,
        status="PUBLISHED",
        delivery_type=ActivityDeliveryType.TEXT,
        max_score=Decimal("5.00"),
    )
    act3 = AcademicActivity(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        title="Taller 1 - Investigación",
        activity_type=ActivityType.WORKSHOP,
        status="PUBLISHED",
        delivery_type=ActivityDeliveryType.TEXT,
        max_score=Decimal("5.00"),
    )
    act_ungraded = AcademicActivity(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        title="Actividad Futura Sin Calificar",
        activity_type=ActivityType.TASK,
        status="PUBLISHED",
        delivery_type=ActivityDeliveryType.TEXT,
        max_score=Decimal("5.00"),
    )
    db_session.add_all([act1, act2, act3, act_ungraded])
    await db_session.flush()

    g1 = ActivityGrade(
        activity_id=act1.id,
        student_id=f["student"].id,
        score=Decimal("3.10"),
        status=ActivitySubmissionStatus.GRADED,
    )
    g2 = ActivityGrade(
        activity_id=act2.id,
        student_id=f["student"].id,
        score=Decimal("2.50"),
        status=ActivitySubmissionStatus.GRADED,
    )
    g3 = ActivityGrade(
        activity_id=act3.id,
        student_id=f["student"].id,
        score=Decimal("4.50"),
        status=ActivitySubmissionStatus.GRADED,
    )
    db_session.add_all([g1, g2, g3])
    await db_session.flush()

    res = await calc_svc.calculate_subject_period_grade(
        institution_id=f["institution"].id,
        student_id=f["student"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        period=f["period_1"],
        policy=f["policy"],
    )

    # (3.10 + 2.50 + 4.50) / 3 = 10.10 / 3 = 3.37
    # Note: act_ungraded must NOT cause division by 4 or be treated as 0.00
    assert res.calculated_score == Decimal("3.37")
    assert res.final_score == Decimal("3.37")
    assert res.performance_level == PerformanceLevelEnum.BASICO


@pytest.mark.asyncio
async def test_pedagogical_adjustments_and_locking(
    db_session: AsyncSession,
    academic_calc_fixture: dict[str, Any],
) -> None:
    """
    Verify that pedagogical adjustment overrides with mandatory reasons are preserved,
    while records without overrides track true mathematical calculations dynamically.
    """
    f = academic_calc_fixture
    calc_svc = AcademicCalculationService(session=db_session)

    act1 = AcademicActivity(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        title="Actividad Evaluación",
        activity_type=ActivityType.EXAM,
        status="PUBLISHED",
        delivery_type=ActivityDeliveryType.TEXT,
        max_score=Decimal("5.00"),
    )
    db_session.add(act1)
    await db_session.flush()

    db_session.add(
        ActivityGrade(
            activity_id=act1.id,
            student_id=f["student"].id,
            score=Decimal("2.80"),
            status=ActivitySubmissionStatus.GRADED,
        )
    )
    await db_session.flush()

    # Case A: Saved period grade with explicit teacher override
    existing_with_override = PeriodSubjectGrade(
        institution_id=f["institution"].id,
        academic_period_id=f["period_1"].id,
        enrollment_id=f["enrollment"].id,
        student_id=f["student"].id,
        subject_id=f["subject"].id,
        calculated_score=Decimal("2.80"),
        final_score=Decimal("3.50"),
        adjustment_reason="Superación demostrada en sustentación oral.",
        performance_level=PerformanceLevelEnum.BASICO,
    )
    db_session.add(existing_with_override)
    await db_session.flush()

    res_a = await calc_svc.calculate_subject_period_grade(
        institution_id=f["institution"].id,
        student_id=f["student"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        period=f["period_1"],
        policy=f["policy"],
        existing_grade=existing_with_override,
    )
    # Teacher adjustment must be preserved
    assert res_a.final_score == Decimal("3.50")
    assert res_a.adjustment_reason == "Superación demostrada en sustentación oral."
    assert res_a.calculated_score == Decimal("2.80")

    # Case B: Period record without override (tracking calculation)
    existing_no_override = PeriodSubjectGrade(
        institution_id=f["institution"].id,
        academic_period_id=f["period_2"].id,
        enrollment_id=f["enrollment"].id,
        student_id=f["student"].id,
        subject_id=f["subject"].id,
        calculated_score=Decimal("4.50"),
        final_score=Decimal("4.50"),
        adjustment_reason=None,
        performance_level=PerformanceLevelEnum.ALTO,
    )
    db_session.add(existing_no_override)
    await db_session.flush()

    # When recalculating where activities produce 2.80, it must update to 2.80
    res_b = await calc_svc.calculate_subject_period_grade(
        institution_id=f["institution"].id,
        student_id=f["student"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        period=f["period_2"],
        policy=f["policy"],
        existing_grade=existing_no_override,
    )
    assert res_b.final_score == Decimal("2.80")
    assert res_b.calculated_score == Decimal("2.80")
    assert res_b.adjustment_reason is None


@pytest.mark.asyncio
async def test_live_attendance_aggregation(
    db_session: AsyncSession,
    academic_calc_fixture: dict[str, Any],
) -> None:
    """
    Verify attendance marks classification (ABSENT vs EXCUSED vs LATE) and period scoping.
    """
    f = academic_calc_fixture
    calc_svc = AcademicCalculationService(session=db_session)

    # 1. Period 1 marks:
    # 2027-02-10: ABSENT (unexcused)
    # 2027-02-15: EXCUSED (excused)
    # 2027-02-20: LATE (tardy, not an absence)
    # 2027-02-25: PRESENT
    att1 = DailyAttendance(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        student_id=f["student"].id,
        attendance_date=date(2027, 2, 10),
        status=AttendanceStatusEnum.ABSENT,
    )
    att2 = DailyAttendance(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        student_id=f["student"].id,
        attendance_date=date(2027, 2, 15),
        status=AttendanceStatusEnum.EXCUSED,
        remarks="Excusa médica validada",
    )
    att3 = DailyAttendance(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        student_id=f["student"].id,
        attendance_date=date(2027, 2, 20),
        status=AttendanceStatusEnum.LATE,
    )
    att4 = DailyAttendance(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        student_id=f["student"].id,
        attendance_date=date(2027, 2, 25),
        status=AttendanceStatusEnum.PRESENT,
    )

    # 2. Period 2 mark:
    # 2027-06-10: ABSENT
    att5 = DailyAttendance(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        student_id=f["student"].id,
        attendance_date=date(2027, 6, 10),
        status=AttendanceStatusEnum.ABSENT,
    )
    db_session.add_all([att1, att2, att3, att4, att5])
    await db_session.flush()

    # Test Period 1 Attendance
    p1_summary = await calc_svc.calculate_period_attendance(
        institution_id=f["institution"].id,
        student_id=f["student"].id,
        academic_year_id=f["academic_year"].id,
        period=f["period_1"],
        group_id=f["group"].id,
    )
    assert p1_summary.unexcused_absences == 1
    assert p1_summary.excused_absences == 1
    assert p1_summary.total_absences == 2
    assert p1_summary.late_count == 1
    assert p1_summary.present_count == 1

    # Test Annual Attendance (all periods combined)
    annual_summary = await calc_svc.calculate_annual_attendance(
        institution_id=f["institution"].id,
        student_id=f["student"].id,
        academic_year_id=f["academic_year"].id,
        group_id=f["group"].id,
    )
    assert annual_summary.unexcused_absences == 2  # 1 in P1 + 1 in P2
    assert annual_summary.excused_absences == 1
    assert annual_summary.total_absences == 3


@pytest.mark.asyncio
async def test_report_cards_consistency_and_provisional_status(
    db_session: AsyncSession,
    academic_calc_fixture: dict[str, Any],
) -> None:
    """
    Verify report card generation reflects live activities, live absences,
    and flags provisional in-progress status for active academic years.
    """
    f = academic_calc_fixture
    rc_svc = ReportCardService(session=db_session)

    # Add 3 graded activities replicating the Danna Gonzalez scenario
    act1 = AcademicActivity(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        title="Actividad 1 ciencias",
        activity_type=ActivityType.WORKSHOP,
        status="PUBLISHED",
        delivery_type=ActivityDeliveryType.TEXT,
        max_score=Decimal("5.00"),
    )
    act2 = AcademicActivity(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        title="Taller #2 Ecuaciones",
        activity_type=ActivityType.WORKSHOP,
        status="PUBLISHED",
        delivery_type=ActivityDeliveryType.TEXT,
        max_score=Decimal("5.00"),
    )
    act3 = AcademicActivity(
        institution_id=f["institution"].id,
        group_id=f["group"].id,
        subject_id=f["subject"].id,
        academic_year_id=f["academic_year"].id,
        teacher_id=f["teacher"].id,
        title="Taller 1 - Investigación",
        activity_type=ActivityType.WORKSHOP,
        status="PUBLISHED",
        delivery_type=ActivityDeliveryType.TEXT,
        max_score=Decimal("5.00"),
    )
    db_session.add_all([act1, act2, act3])
    await db_session.flush()

    db_session.add_all([
        ActivityGrade(activity_id=act1.id, student_id=f["student"].id, score=Decimal("3.10"), status=ActivitySubmissionStatus.GRADED),
        ActivityGrade(activity_id=act2.id, student_id=f["student"].id, score=Decimal("2.50"), status=ActivitySubmissionStatus.GRADED),
        ActivityGrade(activity_id=act3.id, student_id=f["student"].id, score=Decimal("4.50"), status=ActivitySubmissionStatus.GRADED),
    ])
    # Add an unexcused absence
    db_session.add(
        DailyAttendance(
            institution_id=f["institution"].id,
            group_id=f["group"].id,
            academic_year_id=f["academic_year"].id,
            teacher_id=f["teacher"].id,
            student_id=f["student"].id,
            attendance_date=date(2027, 2, 10),
            status=AttendanceStatusEnum.ABSENT,
        )
    )
    # Stale period grade record
    db_session.add(
        PeriodSubjectGrade(
            institution_id=f["institution"].id,
            academic_period_id=f["period_1"].id,
            enrollment_id=f["enrollment"].id,
            student_id=f["student"].id,
            subject_id=f["subject"].id,
            calculated_score=Decimal("4.50"),
            final_score=Decimal("4.50"),
            total_absences=0,
            unexcused_absences=0,
        )
    )
    await db_session.flush()

    # 1. Periodic Report Card
    p_card = await rc_svc.get_student_report_card(
        institution_id=f["institution"].id,
        student_id=f["student"].id,
        period_id=f["period_1"].id,
    )
    assert p_card["summary"]["average_score"] == 3.37
    assert p_card["summary"]["performance_level"] == "BASICO"
    assert p_card["summary"]["total_absences"] == 1
    assert p_card["summary"]["unexcused_absences"] == 1
    assert p_card["subjects"][0]["final_score"] == 3.37
    assert p_card["subjects"][0]["total_absences"] == 1

    # 2. Year-End Report Card
    y_card = await rc_svc.get_student_final_report_card(
        institution_id=f["institution"].id,
        student_id=f["student"].id,
        academic_year_id=f["academic_year"].id,
    )
    assert y_card["summary"]["cumulative_average"] == 3.37
    assert y_card["summary"]["performance_level"] == "BASICO"
    assert y_card["summary"]["total_absences"] == 1
    assert y_card["summary"]["is_provisional"] is True
    assert y_card["promotion"]["status"] == "PENDIENTE"
    assert y_card["promotion"]["is_provisional"] is True
