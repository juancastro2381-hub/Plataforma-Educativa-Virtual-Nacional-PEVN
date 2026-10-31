"""
PEVN Backend — Academic Calculation Domain Service (Phase 16E)

Authoritative, centralized calculation engine for:
1. Activity weighted grading and period consolidated scores according to institutional SIEE.
2. Pedagogical adjustment invariants preservation (DECISION-16-03).
3. Authoritative classroom and subject attendance / absence tracking from DailyAttendance.
4. Annual cumulative grade weighting and promotion status determination.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import CrossTenantMismatchError
from app.core.logging import get_logger
from app.models.academic_activity import (
    AcademicActivity,
    ActivityGrade,
    ActivitySubmissionStatus,
    AttendanceStatusEnum,
    DailyAttendance,
)
from app.models.academic_year import AcademicPeriod, AcademicYear, AcademicYearStatus
from app.models.evaluation import (
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    SieePolicy,
    StudentPromotion,
)
from app.services.siee_policy_service import SieePolicyService

_logger = get_logger(__name__)


@dataclass(frozen=True)
class AttendanceSummary:
    """Aggregated attendance breakdown."""

    total_absences: int
    unexcused_absences: int
    excused_absences: int
    late_count: int
    present_count: int


@dataclass(frozen=True)
class PeriodSubjectGradeCalculation:
    """Calculated period subject grade details."""

    calculated_score: Decimal
    final_score: Decimal
    adjustment_reason: str | None
    performance_level: PerformanceLevelEnum
    total_absences: int
    unexcused_absences: int
    excused_absences: int
    computed_score: Decimal
    is_locked: bool
    has_evaluation: bool = True
    is_pending: bool = False


class AcademicCalculationService:
    """
    Central authoritative service for academic calculations and attendance aggregation.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._siee_service = SieePolicyService(session=session)

    # =======================================================================
    # 1. Attendance & Absence Aggregation
    # =======================================================================

    async def calculate_period_attendance(
        self,
        *,
        institution_id: uuid.UUID,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        period: AcademicPeriod,
        subject_id: uuid.UUID | None = None,
        group_id: uuid.UUID | None = None,
    ) -> AttendanceSummary:
        """
        Aggregate attendance marks for a student within a specific academic period.

        Supports both homeroom group attendance (subject_id IS NULL) and subject-specific marks.
        A homeroom absence counts as an absence across all subjects in that group session.
        """
        # Fetch all periods for this academic year to establish the date window
        p_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.academic_year_id == academic_year_id)
            .order_by(AcademicPeriod.period_number.asc())
        )
        all_periods = list((await self._session.execute(p_stmt)).scalars().all())

        stmt = select(DailyAttendance).where(
            DailyAttendance.institution_id == institution_id,
            DailyAttendance.student_id == student_id,
            DailyAttendance.academic_year_id == academic_year_id,
        )

        if group_id is not None:
            stmt = stmt.where(DailyAttendance.group_id == group_id)

        if subject_id is not None:
            # Match records specific to this subject OR group-level homeroom attendance
            stmt = stmt.where(
                (DailyAttendance.subject_id == subject_id) | (DailyAttendance.subject_id.is_(None))
            )

        # Date window logic:
        # If this is the earliest period (period_number == 1), all attendance up to period.end_date counts
        if period.period_number == 1 or (all_periods and all_periods[0].id == period.id):
            if period.end_date:
                stmt = stmt.where(DailyAttendance.attendance_date <= period.end_date)
        else:
            if period.start_date:
                stmt = stmt.where(DailyAttendance.attendance_date >= period.start_date)
            if period.end_date:
                stmt = stmt.where(DailyAttendance.attendance_date <= period.end_date)

        records = list((await self._session.execute(stmt)).scalars().all())

        unexcused = sum(1 for r in records if r.status == AttendanceStatusEnum.ABSENT)
        excused = sum(1 for r in records if r.status == AttendanceStatusEnum.EXCUSED)
        lates = sum(1 for r in records if r.status == AttendanceStatusEnum.LATE)
        presents = sum(1 for r in records if r.status == AttendanceStatusEnum.PRESENT)

        return AttendanceSummary(
            total_absences=unexcused + excused,
            unexcused_absences=unexcused,
            excused_absences=excused,
            late_count=lates,
            present_count=presents,
        )

    async def calculate_annual_attendance(
        self,
        *,
        institution_id: uuid.UUID,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        subject_id: uuid.UUID | None = None,
        group_id: uuid.UUID | None = None,
    ) -> AttendanceSummary:
        """
        Aggregate attendance marks across the entire academic year for a student.
        """
        stmt = select(DailyAttendance).where(
            DailyAttendance.institution_id == institution_id,
            DailyAttendance.student_id == student_id,
            DailyAttendance.academic_year_id == academic_year_id,
        )

        if group_id is not None:
            stmt = stmt.where(DailyAttendance.group_id == group_id)

        if subject_id is not None:
            stmt = stmt.where(
                (DailyAttendance.subject_id == subject_id) | (DailyAttendance.subject_id.is_(None))
            )

        records = list((await self._session.execute(stmt)).scalars().all())

        unexcused = sum(1 for r in records if r.status == AttendanceStatusEnum.ABSENT)
        excused = sum(1 for r in records if r.status == AttendanceStatusEnum.EXCUSED)
        lates = sum(1 for r in records if r.status == AttendanceStatusEnum.LATE)
        presents = sum(1 for r in records if r.status == AttendanceStatusEnum.PRESENT)

        return AttendanceSummary(
            total_absences=unexcused + excused,
            unexcused_absences=unexcused,
            excused_absences=excused,
            late_count=lates,
            present_count=presents,
        )

    # =======================================================================
    # 2. Activity-Based Period Grade Calculation
    # =======================================================================

    async def calculate_subject_period_grade(
        self,
        *,
        institution_id: uuid.UUID,
        student_id: uuid.UUID,
        group_id: uuid.UUID,
        subject_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        period: AcademicPeriod,
        policy: SieePolicy,
        existing_grade: PeriodSubjectGrade | None = None,
    ) -> PeriodSubjectGradeCalculation:
        """
        Calculate authoritative period subject grade and attendance.

        Enforces:
        - Weighted sum of graded activities (ungraded activities excluded from denominator).
        - Preservation of teacher pedagogical override when adjustment_reason is present.
        - Dynamic recalculation when no manual override exists.
        - Immutability when period is closed or record is locked.
        - Live attendance metrics from DailyAttendance.
        """
        # If locked or closed, return existing frozen values with live attendance
        if period.is_closed or (existing_grade and existing_grade.is_locked):
            att = await self.calculate_period_attendance(
                institution_id=institution_id,
                student_id=student_id,
                academic_year_id=academic_year_id,
                period=period,
                subject_id=subject_id,
                group_id=group_id,
            )
            has_eval = existing_grade is not None
            return PeriodSubjectGradeCalculation(
                calculated_score=existing_grade.calculated_score if existing_grade else Decimal("0.00"),
                final_score=existing_grade.final_score if existing_grade else Decimal("0.00"),
                adjustment_reason=existing_grade.adjustment_reason if existing_grade else None,
                performance_level=existing_grade.performance_level if existing_grade else PerformanceLevelEnum.BASICO,
                total_absences=existing_grade.total_absences if existing_grade else att.total_absences,
                unexcused_absences=existing_grade.unexcused_absences if existing_grade else att.unexcused_absences,
                excused_absences=att.excused_absences,
                computed_score=existing_grade.calculated_score if existing_grade else Decimal("0.00"),
                is_locked=True,
                has_evaluation=has_eval,
                is_pending=not has_eval,
            )

        # 1. Fetch activities for this group, subject, and academic year
        act_stmt = (
            select(AcademicActivity)
            .where(
                AcademicActivity.institution_id == institution_id,
                AcademicActivity.group_id == group_id,
                AcademicActivity.subject_id == subject_id,
                AcademicActivity.academic_year_id == academic_year_id,
            )
            .order_by(AcademicActivity.created_at.asc())
        )
        activities = list((await self._session.execute(act_stmt)).scalars().all())

        # 2. Fetch student activity grades
        total_weight = Decimal("0.00")
        weighted_sum = Decimal("0.00")

        if activities:
            act_ids = [a.id for a in activities]
            sub_stmt = select(ActivityGrade).where(
                ActivityGrade.activity_id.in_(act_ids),
                ActivityGrade.student_id == student_id,
                ActivityGrade.status == ActivitySubmissionStatus.GRADED,
            )
            subs = {s.activity_id: s for s in (await self._session.execute(sub_stmt)).scalars().all()}

            for act in activities:
                sub = subs.get(act.id)
                if sub is not None and sub.score is not None:
                    act_weight = getattr(act, "weight_percentage", None)
                    w = (
                        Decimal(str(act_weight))
                        if act_weight is not None and Decimal(str(act_weight)) > Decimal("0.00")
                        else Decimal("1.00")
                    )
                    weighted_sum += Decimal(str(sub.score)) * w
                    total_weight += w

        # 3. Resolve pedagogical adjustment invariant (DECISION-16-03)
        if total_weight > Decimal("0.00"):
            has_evaluation = True
            is_pending = False
            computed_score = round(weighted_sum / total_weight, 2)
            if (
                existing_grade
                and existing_grade.adjustment_reason
                and str(existing_grade.adjustment_reason).strip()
                and existing_grade.final_score != existing_grade.calculated_score
            ):
                # Teacher has intentionally overridden the grade with a mandatory justification
                final_score = existing_grade.final_score
                calculated_score = computed_score
                adjustment_reason = existing_grade.adjustment_reason
            else:
                # Standard automated calculation: final score dynamically tracks mathematical score
                calculated_score = computed_score
                final_score = computed_score
                adjustment_reason = None
        else:
            # No evaluated activities in LMS: preserve existing teacher consolidated score if present
            if existing_grade:
                has_evaluation = True
                is_pending = False
                calculated_score = existing_grade.calculated_score
                final_score = existing_grade.final_score
                adjustment_reason = existing_grade.adjustment_reason
                computed_score = existing_grade.calculated_score
            else:
                has_evaluation = False
                is_pending = True
                computed_score = Decimal("0.00")
                calculated_score = Decimal("0.00")
                final_score = Decimal("0.00")
                adjustment_reason = None

        # Clamp final_score to SIEE bounds [0.00, policy.max_score]
        if final_score < Decimal("0.00"):
            final_score = Decimal("0.00")
        elif final_score > policy.max_score:
            final_score = policy.max_score

        performance_level = self._siee_service.map_score_to_performance_level(final_score, policy)

        # 4. Fetch live attendance marks
        att = await self.calculate_period_attendance(
            institution_id=institution_id,
            student_id=student_id,
            academic_year_id=academic_year_id,
            period=period,
            subject_id=subject_id,
            group_id=group_id,
        )

        return PeriodSubjectGradeCalculation(
            calculated_score=calculated_score,
            final_score=final_score,
            adjustment_reason=adjustment_reason,
            performance_level=performance_level,
            total_absences=att.total_absences,
            unexcused_absences=att.unexcused_absences,
            excused_absences=att.excused_absences,
            computed_score=computed_score,
            is_locked=False,
            has_evaluation=has_evaluation,
            is_pending=is_pending,
        )

    # =======================================================================
    # 3. Batch Calculation for Period Consolidation Sheet
    # =======================================================================

    async def batch_calculate_period_sheet(
        self,
        *,
        institution_id: uuid.UUID,
        period: AcademicPeriod,
        group_id: uuid.UUID,
        subject_id: uuid.UUID,
        policy: SieePolicy,
        enrollments: list[Any],
        existing_grades_map: dict[uuid.UUID, PeriodSubjectGrade],
    ) -> list[dict[str, Any]]:
        """
        Perform high-efficiency bulk calculation for all students in a period sheet.
        Pre-fetches all activities, submissions, and daily attendance in batch queries.
        """
        student_ids = [enr.student_id for enr in enrollments]

        # 1. Fetch activities
        act_stmt = (
            select(AcademicActivity)
            .where(
                AcademicActivity.institution_id == institution_id,
                AcademicActivity.group_id == group_id,
                AcademicActivity.subject_id == subject_id,
                AcademicActivity.academic_year_id == period.academic_year_id,
            )
            .order_by(AcademicActivity.created_at.asc())
        )
        activities = list((await self._session.execute(act_stmt)).scalars().all())

        # 2. Fetch submissions for all students
        submissions: dict[tuple[uuid.UUID, uuid.UUID], ActivityGrade] = {}
        if activities and student_ids:
            act_ids = [a.id for a in activities]
            sub_stmt = select(ActivityGrade).where(
                ActivityGrade.activity_id.in_(act_ids),
                ActivityGrade.student_id.in_(student_ids),
                ActivityGrade.status == ActivitySubmissionStatus.GRADED,
            )
            for sub in (await self._session.execute(sub_stmt)).scalars().all():
                submissions[(sub.activity_id, sub.student_id)] = sub

        # 3. Fetch period date window
        p_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.academic_year_id == period.academic_year_id)
            .order_by(AcademicPeriod.period_number.asc())
        )
        all_periods = list((await self._session.execute(p_stmt)).scalars().all())

        # 4. Fetch daily attendances in batch for all students
        att_stmt = select(DailyAttendance).where(
            DailyAttendance.institution_id == institution_id,
            DailyAttendance.student_id.in_(student_ids),
            DailyAttendance.academic_year_id == period.academic_year_id,
            (DailyAttendance.subject_id == subject_id) | (DailyAttendance.subject_id.is_(None)),
        )
        if period.period_number == 1 or (all_periods and all_periods[0].id == period.id):
            if period.end_date:
                att_stmt = att_stmt.where(DailyAttendance.attendance_date <= period.end_date)
        else:
            if period.start_date:
                att_stmt = att_stmt.where(DailyAttendance.attendance_date >= period.start_date)
            if period.end_date:
                att_stmt = att_stmt.where(DailyAttendance.attendance_date <= period.end_date)

        att_records = list((await self._session.execute(att_stmt)).scalars().all())

        # Group attendance by student_id
        att_map: dict[uuid.UUID, list[DailyAttendance]] = {sid: [] for sid in student_ids}
        for ar in att_records:
            if ar.student_id in att_map:
                att_map[ar.student_id].append(ar)

        # 5. Assemble calculated student rows
        student_rows = []

        for enr in enrollments:
            st = enr.student
            st_user = st.user
            existing_rec = existing_grades_map.get(st.id)

            # Compute weighted sum
            total_weight = Decimal("0.00")
            weighted_sum = Decimal("0.00")
            activity_grades_map = {}

            for act in activities:
                sub = submissions.get((act.id, st.id))
                score_val = sub.score if sub and sub.score is not None else None
                activity_grades_map[str(act.id)] = (
                    float(score_val) if score_val is not None else None
                )
                if score_val is not None:
                    act_weight = getattr(act, "weight_percentage", None)
                    w = (
                        Decimal(str(act_weight))
                        if act_weight is not None and Decimal(str(act_weight)) > Decimal("0.00")
                        else Decimal("1.00")
                    )
                    total_weight += w
                    weighted_sum += Decimal(str(score_val)) * w

            if total_weight > Decimal("0.00"):
                computed_score = round(weighted_sum / total_weight, 2)
            else:
                computed_score = Decimal("0.00")

            # Attendance metrics
            st_atts = att_map.get(st.id, [])
            unexcused = sum(1 for r in st_atts if r.status == AttendanceStatusEnum.ABSENT)
            excused = sum(1 for r in st_atts if r.status == AttendanceStatusEnum.EXCUSED)
            total_absences = unexcused + excused

            # Invariant check
            if period.is_closed or (existing_rec and existing_rec.is_locked):
                final_score = existing_rec.final_score if existing_rec else Decimal("0.00")
                calculated_score = existing_rec.calculated_score if existing_rec else Decimal("0.00")
                adjustment_reason = existing_rec.adjustment_reason if existing_rec else None
                performance_level = (
                    existing_rec.performance_level
                    if existing_rec
                    else self._siee_service.map_score_to_performance_level(final_score, policy)
                )
                is_locked = True
                total_absences = existing_rec.total_absences if existing_rec else total_absences
                unexcused = existing_rec.unexcused_absences if existing_rec else unexcused
            elif (
                existing_rec
                and existing_rec.adjustment_reason
                and str(existing_rec.adjustment_reason).strip()
                and existing_rec.final_score != existing_rec.calculated_score
            ):
                final_score = existing_rec.final_score
                calculated_score = computed_score
                adjustment_reason = existing_rec.adjustment_reason
                performance_level = self._siee_service.map_score_to_performance_level(final_score, policy)
                is_locked = False
            elif total_weight > Decimal("0.00"):
                calculated_score = computed_score
                final_score = computed_score
                adjustment_reason = None
                performance_level = self._siee_service.map_score_to_performance_level(final_score, policy)
                is_locked = False
            elif existing_rec:
                # No evaluated activities in LMS: keep existing saved period scores
                calculated_score = existing_rec.calculated_score
                final_score = existing_rec.final_score
                adjustment_reason = existing_rec.adjustment_reason
                performance_level = existing_rec.performance_level
                is_locked = False
            else:
                calculated_score = Decimal("0.00")
                final_score = Decimal("0.00")
                adjustment_reason = None
                performance_level = self._siee_service.map_score_to_performance_level(final_score, policy)
                is_locked = False

            recoveries_list = []
            if existing_rec:
                recoveries_list = [
                    {
                        "id": str(r.id),
                        "initial_score": float(r.initial_score),
                        "recovery_score": float(r.recovery_score),
                        "applied_cap": float(r.applied_cap),
                        "final_adjusted_score": float(r.final_adjusted_score),
                        "recovery_date": str(r.recovery_date),
                        "act_number": r.act_number,
                    }
                    for r in existing_rec.recovery_records
                ]

            student_rows.append({
                "student_id": str(st.id),
                "enrollment_id": str(enr.id),
                "simat_code": st.code_simat,
                "first_name": st_user.first_name if st_user else "",
                "last_name": st_user.last_name if st_user else "",
                "document_number": st_user.document_number if st_user else "",
                "calculated_score": float(calculated_score),
                "final_score": float(final_score),
                "adjustment_reason": adjustment_reason,
                "performance_level": performance_level.value,
                "total_absences": total_absences,
                "unexcused_absences": unexcused,
                "observations": existing_rec.observations if existing_rec else None,
                "is_locked": is_locked,
                "activity_grades": activity_grades_map,
                "recoveries": recoveries_list,
            })

        return student_rows
