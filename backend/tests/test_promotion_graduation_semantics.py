"""
PEVN Backend -- Phase 16B Semantic Hardening Tests: Promotion vs. Graduation (DECISION-16-04)

Verifies that the domain service correctly distinguishes:
  - PROMOVIDO (annual grade advancement)  -> Enrollment stays ACTIVE
  - GRADUADO  (school cycle completion)   -> Enrollment becomes GRADUATED
  - NO_PROMOVIDO (retention)              -> Enrollment stays ACTIVE
  - PENDIENTE_NIVELACION (pending)        -> Enrollment stays ACTIVE

Test Coverage:
  TEST A: Grade 6 -> Grade 7 promotion: PROMOVIDO, Enrollment stays ACTIVE
  TEST B: Grade 10 -> Grade 11 promotion: PROMOVIDO, Enrollment stays ACTIVE
  TEST C: Grade 11 graduation eligible: GRADUADO, Enrollment becomes GRADUATED
  TEST D: Failed student: NO_PROMOVIDO, Enrollment stays ACTIVE
  TEST E: Pending student: PENDIENTE_NIVELACION, Enrollment stays ACTIVE
  TEST F: Mixed group commit: per-student discrimination validated
  TEST G: Phase 1-15 regression sentinel -- enum values and structure unchanged
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import PromotionStatusEnum
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.student import Student, StudentGender
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.academic_promotion_service import AcademicPromotionService


# ===========================================================================
# Shared Fixture
# ===========================================================================

@pytest.fixture
async def promo_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """
    Seed the minimal entities for promotion/graduation semantics tests.
    Creates three grade groups:
      - group_6a:  Grade 6 (SECUNDARIA, ordinal_order=6)  -> non-final
      - group_10a: Grade 10 (MEDIA, ordinal_order=10)     -> non-final
      - group_11a: Grade 11 (MEDIA, ordinal_order=11)     -> final graduating grade
    """
    dept = Department(code="76", name="Valle del Cauca")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, code="76001", name="Cali")
    db_session.add(muni)
    await db_session.flush()

    inst = Institution(
        municipality_id=muni.id,
        dane_code="176001001001",
        name="IE Tecnico Industrial Antonio Jose Camacho",
        email="rectoria@camacho.edu.co",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code="17600100100101",
        name="Sede Principal AJC",
        is_active=True,
    )
    db_session.add(campus)
    await db_session.flush()

    user_rector = User(
        institution_id=inst.id,
        email="rector@camacho.edu.co",
        username="rector.camacho",
        first_name="Hernando",
        last_name="Camacho",
        document_type=DocumentType.CC,
        document_number="19123456",
        hashed_password="hashed_pass",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user_rector)
    await db_session.flush()

    year = AcademicYear(
        institution_id=inst.id,
        year=2026,
        name="Ano Escolar 2026 AJC",
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 11, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(year)
    await db_session.flush()

    grade_6 = Grade(
        code="G06_PROMO_TEST",
        name="Grado Sexto",
        level=EducationalLevel.SECUNDARIA,
        ordinal_order=6,
    )
    grade_10 = Grade(
        code="G10_PROMO_TEST",
        name="Grado Decimo",
        level=EducationalLevel.MEDIA,
        ordinal_order=10,
    )
    grade_11 = Grade(
        code="G11_PROMO_TEST",
        name="Grado Once",
        level=EducationalLevel.MEDIA,
        ordinal_order=11,
    )
    db_session.add_all([grade_6, grade_10, grade_11])
    await db_session.flush()

    group_6a = Group(
        campus_id=campus.id,
        academic_year_id=year.id,
        grade_id=grade_6.id,
        name="6-A AJC",
        shift=ShiftEnum.MANANA,
        capacity_limit=40,
    )
    group_10a = Group(
        campus_id=campus.id,
        academic_year_id=year.id,
        grade_id=grade_10.id,
        name="10-A AJC",
        shift=ShiftEnum.MANANA,
        capacity_limit=40,
    )
    group_11a = Group(
        campus_id=campus.id,
        academic_year_id=year.id,
        grade_id=grade_11.id,
        name="11-A AJC",
        shift=ShiftEnum.MANANA,
        capacity_limit=40,
    )
    db_session.add_all([group_6a, group_10a, group_11a])
    await db_session.flush()

    async def make_student_enrollment(
        n: int,
        group: Group,
        doc_suffix: str,
    ) -> tuple[Student, Enrollment]:
        u = User(
            institution_id=inst.id,
            email=f"student{n}.{doc_suffix}@camacho.edu.co",
            username=f"student{n}.{doc_suffix}",
            first_name=f"Estudiante{n}",
            last_name="Camacho",
            document_type=DocumentType.TI,
            document_number=f"TI{n}{doc_suffix}",
            hashed_password="hashed_pass",
            is_active=True,
            is_verified=True,
        )
        db_session.add(u)
        await db_session.flush()

        st = Student(
            institution_id=inst.id,
            user_id=u.id,
            code_simat=f"SIMAT-{n}-{doc_suffix}",
            birth_date=date(2008, 1, (n % 28) + 1),
            gender=StudentGender.M,
        )
        db_session.add(st)
        await db_session.flush()

        enr = Enrollment(
            academic_year_id=year.id,
            student_id=st.id,
            group_id=group.id,
            status=EnrollmentStatus.ACTIVE,
        )
        db_session.add(enr)
        await db_session.flush()
        return st, enr

    st_6_promoted, enr_6_promoted = await make_student_enrollment(1, group_6a, "g6p")
    st_10_promoted, enr_10_promoted = await make_student_enrollment(2, group_10a, "g10p")
    st_11_grad, enr_11_grad = await make_student_enrollment(3, group_11a, "g11g")
    st_11_fail, enr_11_fail = await make_student_enrollment(4, group_11a, "g11f")
    st_11_pend, enr_11_pend = await make_student_enrollment(5, group_11a, "g11np")

    return {
        "inst": inst,
        "year": year,
        "user_rector": user_rector,
        "group_6a": group_6a,
        "grade_6": grade_6,
        "st_6_promoted": st_6_promoted,
        "enr_6_promoted": enr_6_promoted,
        "group_10a": group_10a,
        "grade_10": grade_10,
        "st_10_promoted": st_10_promoted,
        "enr_10_promoted": enr_10_promoted,
        "group_11a": group_11a,
        "grade_11": grade_11,
        "st_11_grad": st_11_grad,
        "enr_11_grad": enr_11_grad,
        "st_11_fail": st_11_fail,
        "enr_11_fail": enr_11_fail,
        "st_11_pend": st_11_pend,
        "enr_11_pend": enr_11_pend,
    }


# ===========================================================================
# TEST A: Grade 6 -> Grade 7 Promotion
# ===========================================================================

@pytest.mark.asyncio
async def test_a_grade6_promoted_enrollment_stays_active(
    db_session: AsyncSession,
    promo_fixture: dict[str, Any],
) -> None:
    """
    TEST A -- PROMOVIDO (Grade 6 student): Enrollment.status must remain ACTIVE.
    A student promoted from Grade 6 to Grade 7 is NOT a school graduate.
    """
    inst = promo_fixture["inst"]
    year = promo_fixture["year"]
    group_6a = promo_fixture["group_6a"]
    st = promo_fixture["st_6_promoted"]
    enr = promo_fixture["enr_6_promoted"]
    rector = promo_fixture["user_rector"]

    assert enr.status == EnrollmentStatus.ACTIVE

    service = AcademicPromotionService(session=db_session)
    promotions = await service.commit_group_promotions(
        institution_id=inst.id,
        group_id=group_6a.id,
        academic_year_id=year.id,
        acta_number="ACTA-2026-6A-001",
        decision_date=date(2026, 11, 28),
        user_id=rector.id,
        items=[{
            "student_id": str(st.id),
            "cumulative_average": 4.20,
            "failed_subjects_count": 0,
            "failed_core_subjects_count": 0,
            "attendance_percentage": 95.00,
            "promotion_status": PromotionStatusEnum.PROMOVIDO.value,
            "observations": "Promovido a Grado 7.",
        }],
    )

    assert len(promotions) == 1
    assert promotions[0].promotion_status == PromotionStatusEnum.PROMOVIDO

    await db_session.refresh(enr)
    assert enr.status == EnrollmentStatus.ACTIVE, (
        f"SEMANTIC VIOLATION: Grade 6 PROMOVIDO must have ACTIVE enrollment, got {enr.status!r}"
    )
    assert enr.status != EnrollmentStatus.GRADUATED


# ===========================================================================
# TEST B: Grade 10 -> Grade 11 Promotion
# ===========================================================================

@pytest.mark.asyncio
async def test_b_grade10_promoted_enrollment_stays_active(
    db_session: AsyncSession,
    promo_fixture: dict[str, Any],
) -> None:
    """
    TEST B -- PROMOVIDO (Grade 10 student): Enrollment.status must remain ACTIVE.
    Grade 10 is not the final school grade. A promoted Grade 10 student
    moves to Grade 11 and is NOT a graduate.
    """
    inst = promo_fixture["inst"]
    year = promo_fixture["year"]
    group_10a = promo_fixture["group_10a"]
    st = promo_fixture["st_10_promoted"]
    enr = promo_fixture["enr_10_promoted"]
    rector = promo_fixture["user_rector"]

    assert enr.status == EnrollmentStatus.ACTIVE

    service = AcademicPromotionService(session=db_session)
    promotions = await service.commit_group_promotions(
        institution_id=inst.id,
        group_id=group_10a.id,
        academic_year_id=year.id,
        acta_number="ACTA-2026-10A-001",
        decision_date=date(2026, 11, 28),
        user_id=rector.id,
        items=[{
            "student_id": str(st.id),
            "cumulative_average": 3.80,
            "failed_subjects_count": 0,
            "failed_core_subjects_count": 0,
            "attendance_percentage": 90.00,
            "promotion_status": PromotionStatusEnum.PROMOVIDO.value,
            "observations": "Promovido a Grado 11.",
        }],
    )

    assert len(promotions) == 1
    assert promotions[0].promotion_status == PromotionStatusEnum.PROMOVIDO

    await db_session.refresh(enr)
    assert enr.status == EnrollmentStatus.ACTIVE, (
        f"SEMANTIC VIOLATION: Grade 10 PROMOVIDO must have ACTIVE enrollment, got {enr.status!r}"
    )
    assert enr.status != EnrollmentStatus.GRADUATED


# ===========================================================================
# TEST C: Grade 11 -- Graduation Eligible
# ===========================================================================

@pytest.mark.asyncio
async def test_c_grade11_graduado_enrollment_becomes_graduated(
    db_session: AsyncSession,
    promo_fixture: dict[str, Any],
) -> None:
    """
    TEST C -- GRADUADO (Grade 11 student): Enrollment.status becomes GRADUATED.
    Grade 11 is the final Colombian school grade. A student who passes all
    SIEE criteria in Grade 11 receives GRADUADO. ONLY this status transitions
    the enrollment to GRADUATED.
    """
    inst = promo_fixture["inst"]
    year = promo_fixture["year"]
    group_11a = promo_fixture["group_11a"]
    st = promo_fixture["st_11_grad"]
    enr = promo_fixture["enr_11_grad"]
    rector = promo_fixture["user_rector"]

    assert enr.status == EnrollmentStatus.ACTIVE

    service = AcademicPromotionService(session=db_session)
    promotions = await service.commit_group_promotions(
        institution_id=inst.id,
        group_id=group_11a.id,
        academic_year_id=year.id,
        acta_number="ACTA-2026-11A-GRAD-001",
        decision_date=date(2026, 11, 28),
        user_id=rector.id,
        items=[{
            "student_id": str(st.id),
            "cumulative_average": 4.65,
            "failed_subjects_count": 0,
            "failed_core_subjects_count": 0,
            "attendance_percentage": 97.00,
            "promotion_status": PromotionStatusEnum.GRADUADO.value,
            "observations": "Graduado Bachiller Tecnico Industrial 2026.",
        }],
    )

    assert len(promotions) == 1
    assert promotions[0].promotion_status == PromotionStatusEnum.GRADUADO

    await db_session.refresh(enr)
    assert enr.status == EnrollmentStatus.GRADUATED, (
        f"SEMANTIC VIOLATION: GRADUADO must set GRADUATED enrollment, got {enr.status!r}"
    )


# ===========================================================================
# TEST D: Failed Student -- NO_PROMOVIDO
# ===========================================================================

@pytest.mark.asyncio
async def test_d_no_promovido_enrollment_stays_active(
    db_session: AsyncSession,
    promo_fixture: dict[str, Any],
) -> None:
    """
    TEST D -- NO_PROMOVIDO: Enrollment.status must remain ACTIVE.
    A failed student repeats the grade. Must NOT receive GRADUATED status.
    """
    inst = promo_fixture["inst"]
    year = promo_fixture["year"]
    group_11a = promo_fixture["group_11a"]
    st = promo_fixture["st_11_fail"]
    enr = promo_fixture["enr_11_fail"]
    rector = promo_fixture["user_rector"]

    assert enr.status == EnrollmentStatus.ACTIVE

    service = AcademicPromotionService(session=db_session)
    promotions = await service.commit_group_promotions(
        institution_id=inst.id,
        group_id=group_11a.id,
        academic_year_id=year.id,
        acta_number="ACTA-2026-11A-FAIL-001",
        decision_date=date(2026, 11, 28),
        user_id=rector.id,
        items=[{
            "student_id": str(st.id),
            "cumulative_average": 2.40,
            "failed_subjects_count": 4,
            "failed_core_subjects_count": 2,
            "attendance_percentage": 60.00,
            "promotion_status": PromotionStatusEnum.NO_PROMOVIDO.value,
            "observations": "Reprobado por inasistencia y areas no superadas.",
        }],
    )

    assert len(promotions) == 1
    assert promotions[0].promotion_status == PromotionStatusEnum.NO_PROMOVIDO

    await db_session.refresh(enr)
    assert enr.status == EnrollmentStatus.ACTIVE, (
        f"SEMANTIC VIOLATION: NO_PROMOVIDO must have ACTIVE enrollment, got {enr.status!r}"
    )
    assert enr.status != EnrollmentStatus.GRADUATED


# ===========================================================================
# TEST E: Pending Remediation -- PENDIENTE_NIVELACION
# ===========================================================================

@pytest.mark.asyncio
async def test_e_pendiente_nivelacion_enrollment_stays_active(
    db_session: AsyncSession,
    promo_fixture: dict[str, Any],
) -> None:
    """
    TEST E -- PENDIENTE_NIVELACION: Enrollment.status must remain ACTIVE.
    A student pending remediation has not earned promotion or graduation.
    Must NOT receive GRADUATED status.
    """
    inst = promo_fixture["inst"]
    year = promo_fixture["year"]
    group_11a = promo_fixture["group_11a"]
    st = promo_fixture["st_11_pend"]
    enr = promo_fixture["enr_11_pend"]
    rector = promo_fixture["user_rector"]

    assert enr.status == EnrollmentStatus.ACTIVE

    service = AcademicPromotionService(session=db_session)
    promotions = await service.commit_group_promotions(
        institution_id=inst.id,
        group_id=group_11a.id,
        academic_year_id=year.id,
        acta_number="ACTA-2026-11A-NIV-001",
        decision_date=date(2026, 11, 28),
        user_id=rector.id,
        items=[{
            "student_id": str(st.id),
            "cumulative_average": 3.15,
            "failed_subjects_count": 1,
            "failed_core_subjects_count": 0,
            "attendance_percentage": 88.00,
            "promotion_status": PromotionStatusEnum.PENDIENTE_NIVELACION.value,
            "observations": "Pendiente de nivelacion en Matematicas - Comision Enero 2027.",
        }],
    )

    assert len(promotions) == 1
    assert promotions[0].promotion_status == PromotionStatusEnum.PENDIENTE_NIVELACION

    await db_session.refresh(enr)
    assert enr.status == EnrollmentStatus.ACTIVE, (
        f"SEMANTIC VIOLATION: PENDIENTE_NIVELACION must have ACTIVE enrollment, got {enr.status!r}"
    )
    assert enr.status != EnrollmentStatus.GRADUATED


# ===========================================================================
# TEST F: Regression -- Mixed group commit, per-student discrimination
# ===========================================================================

@pytest.mark.asyncio
async def test_f_mixed_group_commit_per_student_discrimination(
    db_session: AsyncSession,
    promo_fixture: dict[str, Any],
) -> None:
    """
    TEST F -- REGRESSION: In a single group commit with students of
    GRADUADO, NO_PROMOVIDO, and PENDIENTE_NIVELACION statuses:
    - Only GRADUADO student gets GRADUATED enrollment.
    - Others remain ACTIVE.
    """
    inst = promo_fixture["inst"]
    year = promo_fixture["year"]
    group_11a = promo_fixture["group_11a"]
    st_grad = promo_fixture["st_11_grad"]
    enr_grad = promo_fixture["enr_11_grad"]
    st_fail = promo_fixture["st_11_fail"]
    enr_fail = promo_fixture["enr_11_fail"]
    st_pend = promo_fixture["st_11_pend"]
    enr_pend = promo_fixture["enr_11_pend"]
    rector = promo_fixture["user_rector"]

    service = AcademicPromotionService(session=db_session)
    promotions = await service.commit_group_promotions(
        institution_id=inst.id,
        group_id=group_11a.id,
        academic_year_id=year.id,
        acta_number="ACTA-2026-11A-MIXED-001",
        decision_date=date(2026, 11, 28),
        user_id=rector.id,
        items=[
            {
                "student_id": str(st_grad.id),
                "cumulative_average": 4.50,
                "failed_subjects_count": 0,
                "failed_core_subjects_count": 0,
                "attendance_percentage": 96.00,
                "promotion_status": PromotionStatusEnum.GRADUADO.value,
            },
            {
                "student_id": str(st_fail.id),
                "cumulative_average": 2.10,
                "failed_subjects_count": 5,
                "failed_core_subjects_count": 2,
                "attendance_percentage": 55.00,
                "promotion_status": PromotionStatusEnum.NO_PROMOVIDO.value,
            },
            {
                "student_id": str(st_pend.id),
                "cumulative_average": 3.20,
                "failed_subjects_count": 1,
                "failed_core_subjects_count": 0,
                "attendance_percentage": 82.00,
                "promotion_status": PromotionStatusEnum.PENDIENTE_NIVELACION.value,
            },
        ],
    )

    assert len(promotions) == 3

    await db_session.refresh(enr_grad)
    await db_session.refresh(enr_fail)
    await db_session.refresh(enr_pend)

    # Only GRADUADO -> GRADUATED
    assert enr_grad.status == EnrollmentStatus.GRADUATED, (
        f"SEMANTIC VIOLATION: GRADUADO must yield GRADUATED enrollment, got {enr_grad.status!r}"
    )
    # NO_PROMOVIDO -> ACTIVE
    assert enr_fail.status == EnrollmentStatus.ACTIVE, (
        f"SEMANTIC VIOLATION: NO_PROMOVIDO must stay ACTIVE, got {enr_fail.status!r}"
    )
    # PENDIENTE_NIVELACION -> ACTIVE
    assert enr_pend.status == EnrollmentStatus.ACTIVE, (
        f"SEMANTIC VIOLATION: PENDIENTE_NIVELACION must stay ACTIVE, got {enr_pend.status!r}"
    )


# ===========================================================================
# TEST G: Phase 1-15 Regression Sentinel -- Enum integrity
# ===========================================================================

@pytest.mark.asyncio
async def test_g_phase1_15_regression_enum_integrity(
    db_session: AsyncSession,
) -> None:
    """
    TEST G -- REGRESSION SENTINEL: Verifies that PromotionStatusEnum and
    EnrollmentStatus retain exactly the expected values from Phases 1-15,
    and that PROMOVIDO != GRADUADO at the value level.
    """
    # PromotionStatusEnum: must have exactly these four values
    promo_values = {e.value for e in PromotionStatusEnum}
    assert promo_values == {
        "PROMOVIDO",
        "NO_PROMOVIDO",
        "GRADUADO",
        "PENDIENTE_NIVELACION",
    }, f"PromotionStatusEnum unexpected values: {promo_values}"

    # PROMOVIDO and GRADUADO are semantically and value-distinct
    assert PromotionStatusEnum.PROMOVIDO != PromotionStatusEnum.GRADUADO
    assert PromotionStatusEnum.PROMOVIDO.value == "PROMOVIDO"
    assert PromotionStatusEnum.GRADUADO.value == "GRADUADO"

    # EnrollmentStatus: must have exactly these five values
    enr_values = {e.value for e in EnrollmentStatus}
    assert enr_values == {
        "PRE_ENROLLED",
        "ACTIVE",
        "WITHDRAWN",
        "TRANSFERRED",
        "GRADUATED",
    }, f"EnrollmentStatus unexpected values: {enr_values}"

    # ACTIVE and GRADUATED are distinct
    assert EnrollmentStatus.ACTIVE != EnrollmentStatus.GRADUATED
    assert EnrollmentStatus.ACTIVE.value == "ACTIVE"
    assert EnrollmentStatus.GRADUATED.value == "GRADUATED"

    # Domain invariant: PROMOVIDO value != GRADUATED value
    assert PromotionStatusEnum.PROMOVIDO.value != EnrollmentStatus.GRADUATED.value
