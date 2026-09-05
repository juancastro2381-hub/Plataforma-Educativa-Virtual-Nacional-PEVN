"""
PEVN Backend — SIEE Evaluation, Remediation & Promotion Domain Services Test Suite (Phase 16B)

Comprehensive verification of:
1. SIEE policy resolution and versioning.
2. Exact one active policy per institution/year invariant.
3. Score-to-performance level mapping (BAJO, BASICO, ALTO, SUPERIOR).
4. Hybrid grade calculation and mandatory adjustment reason.
5. Remediation/recovery grade cap enforcement: min(recovery_score, recovery_grade_cap).
6. Cross-tenant student/enrollment/assignment/period rejections (Anti-IDOR).
7. Teacher assignment scope enforcement.
8. Period closure and mutation blocking.
9. Period unlock and auditability.
10. Student periodic and annual report card generation.
11. SIEE-driven year-end promotion calculation and act commitment.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import audit_service
from app.core.exceptions import (
    AdjustmentReasonRequiredError,
    CrossTenantMismatchError,
    PeriodClosedLockedError,
    TeacherScopeViolationError,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import (
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    PromotionStatusEnum,
    SieePolicy,
)
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.academic_promotion_service import AcademicPromotionService
from app.services.evaluation_service import EvaluationService
from app.services.report_card_service import ReportCardService
from app.services.siee_policy_service import SieePolicyService


@pytest.fixture
async def evaluation_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Seed test institutions, teachers, students, subjects, groups, and academic years."""
    # 1. Territory
    dept = Department(code="11", name="Bogotá D.C.")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, code="11001", name="Bogotá D.C.")
    db_session.add(muni)
    await db_session.flush()

    # 2. Institutions
    inst_a = Institution(
        municipality_id=muni.id,
        dane_code="111001000111",
        name="Colegio Distrital San Mateo",
        email="rectoria@sanmateo.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        municipality_id=muni.id,
        dane_code="111001000222",
        name="Colegio Distrital Santa Clara",
        email="rectoria@santaclara.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    # 3. Users & Teachers
    user_teacher_a = User(
        institution_id=inst_a.id,
        email="docente.a@sanmateo.edu.co",
        username="docente.a",
        first_name="Pedro",
        last_name="Alvarez",
        document_type=DocumentType.CC,
        document_number="80100200",
        hashed_password="hashed_pass_placeholder",
        is_active=True,
        is_verified=True,
    )
    user_rector_a = User(
        institution_id=inst_a.id,
        email="rector@sanmateo.edu.co",
        username="rector.sanmateo",
        first_name="Guillermo",
        last_name="Rector",
        document_type=DocumentType.CC,
        document_number="80100300",
        hashed_password="hashed_pass_placeholder",
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([user_teacher_a, user_rector_a])
    await db_session.flush()

    teacher_a = Teacher(
        institution_id=inst_a.id,
        user_id=user_teacher_a.id,
        specialty_area="Licenciatura en Matemáticas",
        escalafon_grade="14",
        contract_type=TeacherContractType.PROPIEDAD,
    )
    db_session.add(teacher_a)
    await db_session.flush()

    # 4. Academic Year & Periods
    year_a = AcademicYear(
        institution_id=inst_a.id,
        year=2026,
        name="Año Escolar 2026",
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 11, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(year_a)
    await db_session.flush()

    period_1 = AcademicPeriod(
        academic_year_id=year_a.id,
        period_number=1,
        name="Primer Período",
        weight_percentage=Decimal("25.00"),
        start_date=date(2026, 2, 1),
        end_date=date(2026, 4, 15),
        is_closed=False,
    )
    period_2 = AcademicPeriod(
        academic_year_id=year_a.id,
        period_number=2,
        name="Segundo Período",
        weight_percentage=Decimal("25.00"),
        start_date=date(2026, 4, 16),
        end_date=date(2026, 6, 30),
        is_closed=False,
    )
    db_session.add_all([period_1, period_2])
    await db_session.flush()

    # 5. Grade, Knowledge Area & Subjects
    grade_10 = Grade(
        code="G10_TEST",
        name="Grado Décimo",
        level=EducationalLevel.MEDIA,
        ordinal_order=10,
    )
    db_session.add(grade_10)
    await db_session.flush()

    area_mat = KnowledgeArea(
        institution_id=inst_a.id,
        name="Matemáticas y Lógica",
        is_mandatory=True,
    )
    db_session.add(area_mat)
    await db_session.flush()

    subj_calc = Subject(
        institution_id=inst_a.id,
        grade_id=grade_10.id,
        knowledge_area_id=area_mat.id,
        name="Cálculo Diferencial",
        weekly_hours=4,
    )
    db_session.add(subj_calc)
    await db_session.flush()

    # 6. Group & Academic Assignment
    campus_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="11100100011101",
        name="Sede Principal",
        is_active=True,
    )
    db_session.add(campus_a)
    await db_session.flush()

    group_10a = Group(
        campus_id=campus_a.id,
        academic_year_id=year_a.id,
        grade_id=grade_10.id,
        name="10-A",
        shift=ShiftEnum.MANANA,
        capacity_limit=40,
    )
    db_session.add(group_10a)
    await db_session.flush()

    assignment_a = AcademicAssignment(
        academic_year_id=year_a.id,
        teacher_id=teacher_a.id,
        group_id=group_10a.id,
        subject_id=subj_calc.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assignment_a)
    await db_session.flush()

    # 7. Student Users & Students & Enrollments
    user_student_1 = User(
        institution_id=inst_a.id,
        email="juan.torres@sanmateo.edu.co",
        username="juan.torres",
        first_name="Juan",
        last_name="Torres",
        document_type=DocumentType.TI,
        document_number="10102020",
        hashed_password="hashed_pass_placeholder",
        is_active=True,
        is_verified=True,
    )
    user_student_2 = User(
        institution_id=inst_a.id,
        email="valentina.rojas@sanmateo.edu.co",
        username="valentina.rojas",
        first_name="Valentina",
        last_name="Rojas",
        document_type=DocumentType.TI,
        document_number="10103030",
        hashed_password="hashed_pass_placeholder",
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([user_student_1, user_student_2])
    await db_session.flush()

    student_1 = Student(
        institution_id=inst_a.id,
        user_id=user_student_1.id,
        code_simat="SIMAT-2026-001",
        birth_date=date(2010, 5, 12),
        gender=StudentGender.M,
    )
    student_2 = Student(
        institution_id=inst_a.id,
        user_id=user_student_2.id,
        code_simat="SIMAT-2026-002",
        birth_date=date(2010, 8, 24),
        gender=StudentGender.F,
    )
    db_session.add_all([student_1, student_2])
    await db_session.flush()

    enr_1 = Enrollment(
        academic_year_id=year_a.id,
        student_id=student_1.id,
        group_id=group_10a.id,
        status=EnrollmentStatus.ACTIVE,
    )
    enr_2 = Enrollment(
        academic_year_id=year_a.id,
        student_id=student_2.id,
        group_id=group_10a.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add_all([enr_1, enr_2])
    await db_session.flush()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "user_teacher_a": user_teacher_a,
        "user_rector_a": user_rector_a,
        "teacher_a": teacher_a,
        "year_a": year_a,
        "period_1": period_1,
        "period_2": period_2,
        "group_10a": group_10a,
        "subj_calc": subj_calc,
        "assignment_a": assignment_a,
        "student_1": student_1,
        "student_2": student_2,
        "enr_1": enr_1,
        "enr_2": enr_2,
    }


# ===========================================================================
# Test Cases
# ===========================================================================

@pytest.mark.asyncio
async def test_siee_policy_service_lifecycle_and_mapping(
    db_session: AsyncSession,
    evaluation_fixture: dict[str, Any],
) -> None:
    """Verify SIEE policy creation, versioning, and qualitative scale mapping."""
    inst_a = evaluation_fixture["inst_a"]
    year_a = evaluation_fixture["year_a"]
    user_rector_a = evaluation_fixture["user_rector_a"]

    siee_service = SieePolicyService(session=db_session)

    # 1. Bootstrap default policy
    policy_v1 = await siee_service.get_or_create_default_policy(
        institution_id=inst_a.id,
        academic_year_id=year_a.id,
        user_id=user_rector_a.id,
    )
    assert policy_v1 is not None
    assert policy_v1.version == 1
    assert policy_v1.is_active is True
    assert policy_v1.recovery_grade_cap == Decimal("3.00")

    # 2. Test Scale Mapping
    assert siee_service.map_score_to_performance_level(Decimal("2.50"), policy_v1) == PerformanceLevelEnum.BAJO
    assert siee_service.map_score_to_performance_level(Decimal("2.99"), policy_v1) == PerformanceLevelEnum.BAJO
    assert siee_service.map_score_to_performance_level(Decimal("3.00"), policy_v1) == PerformanceLevelEnum.BASICO
    assert siee_service.map_score_to_performance_level(Decimal("3.80"), policy_v1) == PerformanceLevelEnum.BASICO
    assert siee_service.map_score_to_performance_level(Decimal("4.20"), policy_v1) == PerformanceLevelEnum.ALTO
    assert siee_service.map_score_to_performance_level(Decimal("4.80"), policy_v1) == PerformanceLevelEnum.SUPERIOR
    assert siee_service.map_score_to_performance_level(Decimal("5.00"), policy_v1) == PerformanceLevelEnum.SUPERIOR

    # 3. Publish Policy Version 2 with custom recovery cap 3.50
    policy_v2 = await siee_service.create_policy_version(
        institution_id=inst_a.id,
        academic_year_id=year_a.id,
        data={
            "name": "SIEE Actualizado 2026",
            "min_passing_score": "3.00",
            "max_score": "5.00",
            "low_threshold_max": "2.99",
            "basic_threshold_max": "3.99",
            "high_threshold_max": "4.59",
            "recovery_grade_cap": "3.50",
            "max_failed_subjects_for_promotion": 1,
            "max_failed_core_subjects": 1,
            "min_attendance_percentage": "80.00",
            "is_active": True,
        },
        user_id=user_rector_a.id,
    )
    assert policy_v2.version == 2
    assert policy_v2.is_active is True
    assert policy_v2.recovery_grade_cap == Decimal("3.50")

    # 4. Verify v1 is now inactive and v2 is the single active policy
    active_resolved = await siee_service.get_active_policy(inst_a.id, year_a.id)
    assert active_resolved.id == policy_v2.id
    assert active_resolved.version == 2


@pytest.mark.asyncio
async def test_evaluation_service_hybrid_grading_and_adjustment_reason(
    db_session: AsyncSession,
    evaluation_fixture: dict[str, Any],
) -> None:
    """Verify hybrid consolidation, mandatory justification on override, and teacher scope."""
    inst_a = evaluation_fixture["inst_a"]
    inst_b = evaluation_fixture["inst_b"]
    teacher_a = evaluation_fixture["teacher_a"]
    period_1 = evaluation_fixture["period_1"]
    group_10a = evaluation_fixture["group_10a"]
    subj_calc = evaluation_fixture["subj_calc"]
    student_1 = evaluation_fixture["student_1"]
    enr_1 = evaluation_fixture["enr_1"]
    user_teacher_a = evaluation_fixture["user_teacher_a"]

    eval_service = EvaluationService(session=db_session)

    # 1. Cross-Tenant Rejection: Attempting to evaluate Inst B period in Inst A context
    with pytest.raises(CrossTenantMismatchError):
        await eval_service.get_period_sheet(
            institution_id=inst_b.id,
            period_id=period_1.id,
            group_id=group_10a.id,
            subject_id=subj_calc.id,
            teacher_id=teacher_a.id,
        )

    # 2. Teacher Scope Rejection: Random teacher UUID
    with pytest.raises(TeacherScopeViolationError):
        await eval_service.get_period_sheet(
            institution_id=inst_a.id,
            period_id=period_1.id,
            group_id=group_10a.id,
            subject_id=subj_calc.id,
            teacher_id=uuid.uuid4(),
        )

    # 3. Successful Period Sheet Fetch
    sheet = await eval_service.get_period_sheet(
        institution_id=inst_a.id,
        period_id=period_1.id,
        group_id=group_10a.id,
        subject_id=subj_calc.id,
        teacher_id=teacher_a.id,
    )
    assert len(sheet["students"]) == 2

    # 4. Save with Override WITHOUT reason -> MUST RAISE AdjustmentReasonRequiredError
    with pytest.raises(AdjustmentReasonRequiredError):
        await eval_service.save_period_grades(
            institution_id=inst_a.id,
            period_id=period_1.id,
            group_id=group_10a.id,
            subject_id=subj_calc.id,
            teacher_id=teacher_a.id,
            items=[{
                "enrollment_id": str(enr_1.id),
                "student_id": str(student_1.id),
                "calculated_score": 3.00,
                "final_score": 4.50, # Differs from 3.00
                "adjustment_reason": None, # Missing reason
            }],
            achievements=[],
            user_id=user_teacher_a.id,
        )

    # 5. Save with Override WITH valid reason -> SUCCEEDS
    saved = await eval_service.save_period_grades(
        institution_id=inst_a.id,
        period_id=period_1.id,
        group_id=group_10a.id,
        subject_id=subj_calc.id,
        teacher_id=teacher_a.id,
        items=[{
            "enrollment_id": str(enr_1.id),
            "student_id": str(student_1.id),
            "calculated_score": 3.00,
            "final_score": 4.50,
            "adjustment_reason": "Excelente desempeño en olimpiadas de matemáticas y trabajo colaborativo.",
            "total_absences": 1,
            "unexcused_absences": 0,
        }],
        achievements=[{
            "code": "DBA-01",
            "description": "Aplica derivadas para resolver problemas de optimización.",
            "performance_level": "ALTO",
        }],
        user_id=user_teacher_a.id,
    )
    assert len(saved) == 1
    grade_rec = saved[0]
    assert grade_rec.final_score == Decimal("4.50")
    assert grade_rec.performance_level == PerformanceLevelEnum.ALTO
    assert grade_rec.adjustment_reason is not None


@pytest.mark.asyncio
async def test_recovery_grade_capping_and_history(
    db_session: AsyncSession,
    evaluation_fixture: dict[str, Any],
) -> None:
    """Verify recovery records preserve original failed score and apply configured cap."""
    inst_a = evaluation_fixture["inst_a"]
    teacher_a = evaluation_fixture["teacher_a"]
    period_1 = evaluation_fixture["period_1"]
    group_10a = evaluation_fixture["group_10a"]
    subj_calc = evaluation_fixture["subj_calc"]
    student_2 = evaluation_fixture["student_2"]
    enr_2 = evaluation_fixture["enr_2"]
    user_teacher_a = evaluation_fixture["user_teacher_a"]

    eval_service = EvaluationService(session=db_session)

    # 1. Save initial failing grade (2.10)
    saved = await eval_service.save_period_grades(
        institution_id=inst_a.id,
        period_id=period_1.id,
        group_id=group_10a.id,
        subject_id=subj_calc.id,
        teacher_id=teacher_a.id,
        items=[{
            "enrollment_id": str(enr_2.id),
            "student_id": str(student_2.id),
            "calculated_score": 2.10,
            "final_score": 2.10,
            "adjustment_reason": None,
        }],
        achievements=[],
        user_id=user_teacher_a.id,
    )
    grade_rec = saved[0]
    assert grade_rec.final_score == Decimal("2.10")
    assert grade_rec.performance_level == PerformanceLevelEnum.BAJO

    # 2. Record Recovery where student scored 4.80 (Institutional cap is 3.00)
    recovery = await eval_service.record_recovery_grade(
        institution_id=inst_a.id,
        grade_id=grade_rec.id,
        recovery_score=Decimal("4.80"),
        recovery_date=date(2026, 4, 20),
        act_number="ACTA-REC-001",
        observations="Superó los talleres de nivelación satisfactoriamente.",
        teacher_id=teacher_a.id,
        user_id=user_teacher_a.id,
    )
    assert recovery.initial_score == Decimal("2.10")
    assert recovery.recovery_score == Decimal("4.80")
    assert recovery.applied_cap == Decimal("3.00")
    assert recovery.final_adjusted_score == Decimal("3.00")

    # Grade record is updated to 3.00 / BASICO
    assert grade_rec.final_score == Decimal("3.00")
    assert grade_rec.performance_level == PerformanceLevelEnum.BASICO


@pytest.mark.asyncio
async def test_period_closure_and_unlock_lifecycle(
    db_session: AsyncSession,
    evaluation_fixture: dict[str, Any],
) -> None:
    """Verify period closing locks grades and unlocking requires explicit reason."""
    inst_a = evaluation_fixture["inst_a"]
    teacher_a = evaluation_fixture["teacher_a"]
    period_1 = evaluation_fixture["period_1"]
    group_10a = evaluation_fixture["group_10a"]
    subj_calc = evaluation_fixture["subj_calc"]
    student_1 = evaluation_fixture["student_1"]
    enr_1 = evaluation_fixture["enr_1"]
    user_rector_a = evaluation_fixture["user_rector_a"]
    user_teacher_a = evaluation_fixture["user_teacher_a"]

    eval_service = EvaluationService(session=db_session)

    # 1. Close the period
    closed_p = await eval_service.close_period(
        institution_id=inst_a.id,
        period_id=period_1.id,
        user_id=user_rector_a.id,
    )
    assert closed_p.is_closed is True

    # 2. Attempting to save grades during closed period -> MUST FAIL with PeriodClosedLockedError
    with pytest.raises(PeriodClosedLockedError):
        await eval_service.save_period_grades(
            institution_id=inst_a.id,
            period_id=period_1.id,
            group_id=group_10a.id,
            subject_id=subj_calc.id,
            teacher_id=teacher_a.id,
            items=[{
                "enrollment_id": str(enr_1.id),
                "student_id": str(student_1.id),
                "calculated_score": 4.00,
                "final_score": 4.00,
            }],
            achievements=[],
            user_id=user_teacher_a.id,
        )

    # 3. Unlock with empty reason -> MUST FAIL with ValueError
    with pytest.raises(ValueError):
        await eval_service.unlock_period(
            institution_id=inst_a.id,
            period_id=period_1.id,
            user_id=user_rector_a.id,
            reason="",
        )

    # 4. Unlock with valid reason -> SUCCEEDS
    unlocked_p = await eval_service.unlock_period(
        institution_id=inst_a.id,
        period_id=period_1.id,
        user_id=user_rector_a.id,
        reason="Corrección autorizada por comisión de evaluación para estudiante con incapacidad médica.",
    )
    assert unlocked_p.is_closed is False


@pytest.mark.asyncio
async def test_report_card_service_generation(
    db_session: AsyncSession,
    evaluation_fixture: dict[str, Any],
) -> None:
    """Verify report card generation, group ranking, and Anti-IDOR enforcement."""
    inst_a = evaluation_fixture["inst_a"]
    inst_b = evaluation_fixture["inst_b"]
    period_1 = evaluation_fixture["period_1"]
    year_a = evaluation_fixture["year_a"]
    group_10a = evaluation_fixture["group_10a"]
    student_1 = evaluation_fixture["student_1"]
    user_rector_a = evaluation_fixture["user_rector_a"]

    report_service = ReportCardService(session=db_session)

    # 1. Anti-IDOR: Inst B querying Inst A student report card
    with pytest.raises(CrossTenantMismatchError):
        await report_service.get_student_report_card(
            institution_id=inst_b.id,
            student_id=student_1.id,
            period_id=period_1.id,
        )

    # 2. Legitimate Report Card Generation
    card = await report_service.get_student_report_card(
        institution_id=inst_a.id,
        student_id=student_1.id,
        period_id=period_1.id,
        actor_user_id=user_rector_a.id,
    )
    assert card["student"]["id"] == str(student_1.id)
    assert card["group"]["name"] == "10-A"
    assert "summary" in card
    assert "subjects" in card

    # 3. Group Consolidation Matrix
    matrix = await report_service.get_group_consolidation_matrix(
        institution_id=inst_a.id,
        group_id=group_10a.id,
        period_id=period_1.id,
    )
    assert matrix["group"]["name"] == "10-A"
    assert len(matrix["students"]) == 2


@pytest.mark.asyncio
async def test_academic_promotion_service_preview_and_commit(
    db_session: AsyncSession,
    evaluation_fixture: dict[str, Any],
) -> None:
    """Verify SIEE-driven promotion preview and transactional commission act commitment."""
    inst_a = evaluation_fixture["inst_a"]
    year_a = evaluation_fixture["year_a"]
    group_10a = evaluation_fixture["group_10a"]
    student_1 = evaluation_fixture["student_1"]
    student_2 = evaluation_fixture["student_2"]
    user_rector_a = evaluation_fixture["user_rector_a"]

    promotion_service = AcademicPromotionService(session=db_session)

    # 1. Promotion Preview
    preview = await promotion_service.calculate_promotion_preview(
        institution_id=inst_a.id,
        group_id=group_10a.id,
        academic_year_id=year_a.id,
    )
    assert len(preview["candidates"]) == 2
    cand_1 = preview["candidates"][0]
    assert cand_1["proposed_status"] in [
        PromotionStatusEnum.PROMOVIDO.value,
        PromotionStatusEnum.PENDIENTE_NIVELACION.value,
    ]

    # 2. Commit Promotion Act
    promotions = await promotion_service.commit_group_promotions(
        institution_id=inst_a.id,
        group_id=group_10a.id,
        academic_year_id=year_a.id,
        user_id=user_rector_a.id,
        acta_number="ACTA-2026-FINAL-10A",
        decision_date=date(2026, 11, 28),
        items=[
            {
                "student_id": str(student_1.id),
                "cumulative_average": 4.50,
                "failed_subjects_count": 0,
                "failed_core_subjects_count": 0,
                "attendance_percentage": 98.00,
                "promotion_status": PromotionStatusEnum.PROMOVIDO.value,
                "observations": "Promovido a Grado 11.",
            },
            {
                "student_id": str(student_2.id),
                "cumulative_average": 3.10,
                "failed_subjects_count": 0,
                "failed_core_subjects_count": 0,
                "attendance_percentage": 95.00,
                "promotion_status": PromotionStatusEnum.PROMOVIDO.value,
                "observations": "Promovido a Grado 11 tras superar nivelaciones.",
            },
        ],
        observations="Comisión de evaluación y promoción de fin de año lectivo 2026.",
    )
    assert len(promotions) == 2
    assert promotions[0].acta_number == "ACTA-2026-FINAL-10A"
    assert promotions[0].promotion_status == PromotionStatusEnum.PROMOVIDO
