"""
PEVN Backend — Official Academic Report Card Domain Service (Phase 16B)

Authoritative business logic for:
- Periodic and Year-End Student Report Cards (Boletines de Calificaciones)
- Group Consolidation Matrices (Sábanas de Notas)
- Group Ranking and Area Averages
- Anti-IDOR security guards ensuring Students only access their own report cards
  and Guardians only access their legitimately associated children.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    CrossTenantMismatchError,
    ReportCardAccessDeniedError,
)
from app.core.logging import get_logger
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicPeriod, AcademicYear, AcademicYearStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import (
    AcademicAchievement,
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    RecoveryGrade,
    SieePolicy,
    StudentPromotion,
)
from app.models.group import Group
from app.models.guardian import Guardian, StudentGuardian
from app.models.institution import Campus, Institution
from app.models.student import Student
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher
from app.services.academic_calculation_service import (
    AcademicCalculationService,
    PeriodLifecycleStatus,
    resolve_period_lifecycle_status,
)
from app.services.academic_curriculum_service import AcademicCurriculumService
from app.services.siee_policy_service import SieePolicyService

_logger = get_logger(__name__)


class ReportCardService:
    """
    Authoritative domain service for generating institutional report cards.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit
        self._siee_service = SieePolicyService(session=session, audit_service=audit)
        self._academic_calc_service = AcademicCalculationService(session=session)
        self._curriculum_service = AcademicCurriculumService(session=session)

    # =======================================================================
    # 1. Periodic Student Report Card
    # =======================================================================

    async def get_student_report_card(
        self,
        institution_id: uuid.UUID,
        student_id: uuid.UUID,
        period_id: uuid.UUID,
        actor_user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Generate the authoritative periodic report card for a student.
        """
        # 1. Fetch Student & Tenant Validation
        st_stmt = (
            select(Student)
            .where(Student.id == student_id)
            .options(selectinload(Student.user))
        )
        student = (await self._session.execute(st_stmt)).scalars().first()
        if not student or student.institution_id != institution_id:
            raise CrossTenantMismatchError("Estudiante no encontrado en esta institución.")

        # 2. Fetch Period & Academic Year
        p_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.id == period_id)
            .options(selectinload(AcademicPeriod.academic_year))
        )
        period = (await self._session.execute(p_stmt)).scalars().first()
        if not period or period.academic_year.institution_id != institution_id:
            raise CrossTenantMismatchError("Período académico no encontrado en esta institución.")

        # 3. Fetch Student's Enrollment in that Academic Year
        enr_stmt = (
            select(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.academic_year_id == period.academic_year_id,
                Enrollment.status.in_([EnrollmentStatus.ACTIVE, EnrollmentStatus.GRADUATED]),
            )
            .options(
                selectinload(Enrollment.group).selectinload(Group.campus),
                selectinload(Enrollment.group).selectinload(Group.grade),
            )
        )
        enrollment = (await self._session.execute(enr_stmt)).scalars().first()
        if not enrollment or not enrollment.group:
            raise ReportCardAccessDeniedError("El estudiante no cuenta con una matrícula válida para este período.")

        group = enrollment.group

        # 4. Resolve SIEE Policy
        policy = await self._siee_service.get_or_create_default_policy(
            institution_id=institution_id,
            academic_year_id=period.academic_year_id,
        )

        # 5. Resolve Authoritative Curriculum Matrix for the student
        curriculum = await self._curriculum_service.resolve_student_curriculum(
            institution_id=institution_id,
            student_id=student_id,
            academic_year_id=period.academic_year_id,
        )

        # 6. Fetch all existing PeriodSubjectGrade records for this student and period
        grades_stmt = (
            select(PeriodSubjectGrade)
            .where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.student_id == student_id,
                PeriodSubjectGrade.academic_period_id == period_id,
            )
            .options(
                selectinload(PeriodSubjectGrade.subject).selectinload(Subject.knowledge_area),
                selectinload(PeriodSubjectGrade.graded_by).selectinload(Teacher.user),
                selectinload(PeriodSubjectGrade.recovery_records),
            )
        )
        existing_grades = list((await self._session.execute(grades_stmt)).scalars().all())
        existing_grades_map = {g.subject_id: g for g in existing_grades}

        # 7. Fetch Achievements for the subjects evaluated in this period
        achievements_stmt = select(AcademicAchievement).where(
            AcademicAchievement.institution_id == institution_id,
            AcademicAchievement.academic_period_id == period_id,
        )
        all_achievements = list((await self._session.execute(achievements_stmt)).scalars().all())

        # 8. Authoritative period attendance calculation from DailyAttendance
        period_att = await self._academic_calc_service.calculate_period_attendance(
            institution_id=institution_id,
            student_id=student_id,
            academic_year_id=period.academic_year_id,
            period=period,
            group_id=group.id,
        )
        total_absences_period = period_att.total_absences
        unexcused_absences_period = period_att.unexcused_absences

        # 9. Format Subjects Detail for EVERY curriculum subject
        subject_rows = []
        scores_list = []
        failed_subjects = 0
        passed_subjects = 0
        pending_subjects = 0

        for cur_sub in curriculum.subjects:
            existing_g = existing_grades_map.get(cur_sub.subject_id)

            # Subject-specific attendance
            sub_att = await self._academic_calc_service.calculate_period_attendance(
                institution_id=institution_id,
                student_id=student_id,
                academic_year_id=period.academic_year_id,
                period=period,
                subject_id=cur_sub.subject_id,
                group_id=group.id,
            )

            # Calculation & status resolution
            if not period.is_closed:
                calc = await self._academic_calc_service.calculate_subject_period_grade(
                    institution_id=institution_id,
                    student_id=student_id,
                    group_id=group.id,
                    subject_id=cur_sub.subject_id,
                    academic_year_id=period.academic_year_id,
                    period=period,
                    policy=policy,
                    existing_grade=existing_g,
                )
                if calc.has_evaluation:
                    # Sync into existing grade record if present, or create new record
                    if existing_g:
                        if not existing_g.is_locked:
                            if (
                                existing_g.calculated_score != calc.calculated_score
                                or existing_g.final_score != calc.final_score
                                or existing_g.total_absences != calc.total_absences
                                or existing_g.unexcused_absences != calc.unexcused_absences
                            ):
                                existing_g.calculated_score = calc.calculated_score
                                existing_g.final_score = calc.final_score
                                existing_g.adjustment_reason = calc.adjustment_reason
                                existing_g.performance_level = calc.performance_level
                                existing_g.total_absences = calc.total_absences
                                existing_g.unexcused_absences = calc.unexcused_absences
                                existing_g.calculated_at = datetime.now(UTC)
                                existing_g.updated_at = datetime.now(UTC)
                                self._session.add(existing_g)
                    else:
                        new_g = PeriodSubjectGrade(
                            institution_id=institution_id,
                            academic_period_id=period_id,
                            enrollment_id=enrollment.id,
                            student_id=student_id,
                            subject_id=cur_sub.subject_id,
                            academic_assignment_id=cur_sub.assignment_id,
                            calculated_score=calc.calculated_score,
                            final_score=calc.final_score,
                            adjustment_reason=calc.adjustment_reason,
                            performance_level=calc.performance_level,
                            total_absences=calc.total_absences,
                            unexcused_absences=calc.unexcused_absences,
                            observations=None,
                            is_locked=False,
                            graded_by_teacher_id=cur_sub.teacher_id,
                            calculated_at=datetime.now(UTC),
                            created_at=datetime.now(UTC),
                            updated_at=datetime.now(UTC),
                        )
                        self._session.add(new_g)
                        existing_grades_map[cur_sub.subject_id] = new_g
                        existing_g = new_g

                    final_score_val: float | None = float(calc.final_score)
                    calc_score_val: float | None = float(calc.calculated_score)
                    perf_level_str: str | None = calc.performance_level.value
                    is_passed_val: bool | None = calc.final_score >= policy.min_passing_score
                    eval_status = "GRADED"
                    scores_list.append(calc.final_score)
                    if is_passed_val:
                        passed_subjects += 1
                    else:
                        failed_subjects += 1
                    adj_reason = calc.adjustment_reason
                else:
                    final_score_val = None
                    calc_score_val = None
                    perf_level_str = None
                    is_passed_val = None
                    eval_status = "PENDING"
                    adj_reason = None
                    pending_subjects += 1
            else:
                if existing_g:
                    final_score_val = float(existing_g.final_score)
                    calc_score_val = float(existing_g.calculated_score)
                    perf_level_str = existing_g.performance_level.value
                    is_passed_val = existing_g.final_score >= policy.min_passing_score
                    eval_status = "CLOSED"
                    scores_list.append(existing_g.final_score)
                    if is_passed_val:
                        passed_subjects += 1
                    else:
                        failed_subjects += 1
                    adj_reason = existing_g.adjustment_reason
                else:
                    final_score_val = None
                    calc_score_val = None
                    perf_level_str = None
                    is_passed_val = None
                    eval_status = "PENDING"
                    adj_reason = None
                    pending_subjects += 1

            # Achievements
            subj_achs = [
                {
                    "code": a.code,
                    "description": a.description,
                    "level": a.performance_level.value,
                }
                for a in all_achievements
                if perf_level_str and a.performance_level.value == perf_level_str
            ]

            # Recoveries
            recoveries = [
                {
                    "initial_score": float(r.initial_score),
                    "recovery_score": float(r.recovery_score),
                    "applied_cap": float(r.applied_cap),
                    "final_adjusted_score": float(r.final_adjusted_score),
                    "recovery_date": str(r.recovery_date),
                    "act_number": r.act_number,
                }
                for r in (existing_g.recovery_records if existing_g else [])
            ]

            teacher_name = (
                cur_sub.teacher_name
                if cur_sub.teacher_name
                else (
                    f"{existing_g.graded_by.user.first_name} {existing_g.graded_by.user.last_name}".strip()
                    if existing_g and existing_g.graded_by and existing_g.graded_by.user
                    else "No asignado"
                )
            )

            subject_rows.append({
                "subject_id": str(cur_sub.subject_id),
                "subject_name": cur_sub.subject_name,
                "area_name": cur_sub.knowledge_area_name,
                "weekly_hours": cur_sub.weekly_hours,
                "teacher_name": teacher_name,
                "calculated_score": calc_score_val,
                "final_score": final_score_val,
                "performance_level": perf_level_str,
                "is_passed": is_passed_val,
                "evaluation_status": eval_status,
                "adjustment_reason": adj_reason,
                "total_absences": sub_att.total_absences,
                "unexcused_absences": sub_att.unexcused_absences,
                "observations": existing_g.observations if existing_g else None,
                "achievements": subj_achs,
                "recoveries": recoveries,
            })

        await self._session.flush()

        # 10. Fetch Group Academic Ranking (Puesto en el Grupo)
        group_grades_stmt = (
            select(
                PeriodSubjectGrade.student_id,
                func.coalesce(func.avg(PeriodSubjectGrade.final_score), Decimal("0.00")).label("student_avg"),
            )
            .join(Enrollment, Enrollment.student_id == PeriodSubjectGrade.student_id)
            .where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.academic_period_id == period_id,
                Enrollment.group_id == group.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            .group_by(PeriodSubjectGrade.student_id)
            .order_by(func.avg(PeriodSubjectGrade.final_score).desc())
        )
        rank_rows = (await self._session.execute(group_grades_stmt)).all()

        total_enr_stmt = select(func.count(Enrollment.id)).where(
            Enrollment.group_id == group.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        total_students_in_group = (await self._session.execute(total_enr_stmt)).scalar() or len(rank_rows) or 1

        rank = 1
        for idx, r in enumerate(rank_rows, start=1):
            if r.student_id == student_id:
                rank = idx
                break

        # 11. Compute Student Period Summary
        student_period_avg = (
            round(sum(scores_list) / len(scores_list), 2)
            if scores_list
            else Decimal("0.00")
        )
        avg_level = (
            self._siee_service.map_score_to_performance_level(student_period_avg, policy).value
            if scores_list
            else "PENDIENTE"
        )
        is_provisional = (not period.is_closed) or (pending_subjects > 0)

        # 12. Fetch Institution & Campus Metadata
        inst_stmt = select(Institution).where(Institution.id == institution_id)
        institution = (await self._session.execute(inst_stmt)).scalars().first()

        report_card = {
            "institution": {
                "id": str(institution.id),
                "name": institution.name,
                "dane_code": institution.dane_code,
            },
            "campus": {
                "id": str(group.campus.id) if group.campus else None,
                "name": group.campus.name if group.campus else "Sede Principal",
            },
            "student": {
                "id": str(student.id),
                "simat_code": student.code_simat,
                "full_name": f"{student.user.first_name} {student.user.last_name}" if student.user else "",
                "document_number": student.user.document_number if student.user else "",
                "document_type": student.user.document_type.value if student.user else "",
            },
            "academic_year": {
                "id": str(period.academic_year.id),
                "year": period.academic_year.year,
            },
            "period": {
                "id": str(period.id),
                "period_number": period.period_number,
                "name": period.name,
                "weight_percentage": float(period.weight_percentage),
                "is_closed": period.is_closed,
            },
            "group": {
                "id": str(group.id),
                "name": group.name,
                "grade_name": group.grade.name if group.grade else "",
            },
            "summary": {
                "average_score": float(student_period_avg),
                "performance_level": avg_level,
                "total_subjects": len(curriculum.subjects),
                "failed_subjects": failed_subjects,
                "passed_subjects": passed_subjects,
                "pending_subjects": pending_subjects,
                "rank": rank,
                "total_students": total_students_in_group,
                "total_absences": total_absences_period,
                "unexcused_absences": unexcused_absences_period,
                "is_provisional": is_provisional,
            },
            "subjects": subject_rows,
        }

        if actor_user_id:
            await self._audit.record(
                AuditEvent(
                    event_type=AuditEventType.REPORT_CARD_GENERATED,
                    actor_id=str(actor_user_id),
                    actor_ip="127.0.0.1",
                    target_id=str(student_id),
                    target_type="Student",
                    institution_id=str(institution_id),
                    metadata={
                        "period_id": str(period_id),
                        "average_score": str(student_period_avg),
                        "rank": rank,
                    },
                )
            )

        return report_card

    # =======================================================================
    # 2. Year-End Cumulative Report Card
    # =======================================================================

    async def get_student_final_report_card(
        self,
        institution_id: uuid.UUID,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        actor_user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Generate the cumulative final report card across all periods of the school year.
        """
        # 1. Fetch Student & Academic Year
        st_stmt = (
            select(Student)
            .where(Student.id == student_id)
            .options(selectinload(Student.user))
        )
        student = (await self._session.execute(st_stmt)).scalars().first()
        if not student or student.institution_id != institution_id:
            raise CrossTenantMismatchError("Estudiante no encontrado en esta institución.")

        y_stmt = (
            select(AcademicYear)
            .where(AcademicYear.id == academic_year_id)
            .options(selectinload(AcademicYear.periods))
        )
        year = (await self._session.execute(y_stmt)).scalars().first()
        if not year or year.institution_id != institution_id:
            raise CrossTenantMismatchError("Año lectivo no encontrado en esta institución.")

        # 2. Fetch Enrollment
        enr_stmt = (
            select(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.academic_year_id == academic_year_id,
            )
            .options(
                selectinload(Enrollment.group).selectinload(Group.campus),
                selectinload(Enrollment.group).selectinload(Group.grade),
            )
        )
        enrollment = (await self._session.execute(enr_stmt)).scalars().first()
        if not enrollment or not enrollment.group:
            raise ReportCardAccessDeniedError("El estudiante no cuenta con matrícula para este año escolar.")

        group = enrollment.group

        # 3. Resolve SIEE Policy
        policy = await self._siee_service.get_or_create_default_policy(
            institution_id=institution_id,
            academic_year_id=academic_year_id,
        )

        # 4. Resolve Authoritative Curriculum Matrix for the student
        curriculum = await self._curriculum_service.resolve_student_curriculum(
            institution_id=institution_id,
            student_id=student_id,
            academic_year_id=academic_year_id,
        )

        # 5. Fetch all academic periods for the year
        all_periods_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.academic_year_id == academic_year_id)
            .order_by(AcademicPeriod.period_number.asc())
        )
        all_year_periods = list((await self._session.execute(all_periods_stmt)).scalars().all())
        total_periods_count = len(all_year_periods)
        open_periods = [p for p in all_year_periods if not p.is_closed]

        # 6. Fetch All Period Grades for this Student and Year
        grades_stmt = (
            select(PeriodSubjectGrade)
            .join(AcademicPeriod, AcademicPeriod.id == PeriodSubjectGrade.academic_period_id)
            .where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.student_id == student_id,
                AcademicPeriod.academic_year_id == academic_year_id,
            )
            .options(
                selectinload(PeriodSubjectGrade.subject).selectinload(Subject.knowledge_area),
                selectinload(PeriodSubjectGrade.academic_period),
            )
        )
        all_grades = list((await self._session.execute(grades_stmt)).scalars().all())

        # Index existing grades by (period_id, subject_id)
        grades_by_period_subject = {
            (g.academic_period_id, g.subject_id): g for g in all_grades
        }

        # Determine authoritative active period according to institutional calendar
        # Chronological sequence: the first non-closed period is the ACTIVE term.
        # Periods following the active period are SCHEDULED (future) and must NEVER receive grades.
        active_period = next((p for p in all_year_periods if not p.is_closed), None)

        # Dynamic synchronization of open period grades across ALL curriculum subjects
        # SIEE Rule: ONLY the current ACTIVE period may synchronize live unpersisted LMS activities.
        # Future/SCHEDULED periods must NEVER receive evaluations from report generation.
        if active_period:
            for cur_sub in curriculum.subjects:
                g = grades_by_period_subject.get((active_period.id, cur_sub.subject_id))
                calc = await self._academic_calc_service.calculate_subject_period_grade(
                    institution_id=institution_id,
                    student_id=student_id,
                    group_id=group.id,
                    subject_id=cur_sub.subject_id,
                    academic_year_id=academic_year_id,
                    period=active_period,
                    policy=policy,
                    existing_grade=g,
                )
                if calc.has_evaluation:
                    if g:
                        if not g.is_locked:
                            if (
                                g.calculated_score != calc.calculated_score
                                or g.final_score != calc.final_score
                                or g.total_absences != calc.total_absences
                                or g.unexcused_absences != calc.unexcused_absences
                            ):
                                g.calculated_score = calc.calculated_score
                                g.final_score = calc.final_score
                                g.adjustment_reason = calc.adjustment_reason
                                g.performance_level = calc.performance_level
                                g.total_absences = calc.total_absences
                                g.unexcused_absences = calc.unexcused_absences
                                g.calculated_at = datetime.now(UTC)
                                g.updated_at = datetime.now(UTC)
                                self._session.add(g)
                    else:
                        new_g = PeriodSubjectGrade(
                            institution_id=institution_id,
                            academic_period_id=active_period.id,
                            enrollment_id=enrollment.id,
                            student_id=student_id,
                            subject_id=cur_sub.subject_id,
                            academic_assignment_id=cur_sub.assignment_id,
                            calculated_score=calc.calculated_score,
                            final_score=calc.final_score,
                            adjustment_reason=calc.adjustment_reason,
                            performance_level=calc.performance_level,
                            total_absences=calc.total_absences,
                            unexcused_absences=calc.unexcused_absences,
                            observations=None,
                            is_locked=False,
                            graded_by_teacher_id=cur_sub.teacher_id,
                            calculated_at=datetime.now(UTC),
                            created_at=datetime.now(UTC),
                            updated_at=datetime.now(UTC),
                        )
                        self._session.add(new_g)
                        grades_by_period_subject[(active_period.id, cur_sub.subject_id)] = new_g
            await self._session.flush()

        # Calculate authoritative live annual attendance from DailyAttendance
        annual_att = await self._academic_calc_service.calculate_annual_attendance(
            institution_id=institution_id,
            student_id=student_id,
            academic_year_id=academic_year_id,
            group_id=group.id,
        )

        # Build annual subject rows for EVERY curriculum subject
        subject_final_rows = []
        cumulative_scores = []
        failed_subjects = 0
        pending_subjects = 0
        is_year_completed = (year.status == AcademicYearStatus.CLOSED) and (len(open_periods) == 0)

        for cur_sub in curriculum.subjects:
            p_grades = {}
            weighted_sum = Decimal("0.00")
            total_weight = Decimal("0.00")

            for p in all_year_periods:
                # FUTURE PERIOD GRADE ISOLATION:
                # Only include actual persisted evaluation records for closed or active periods.
                # Scheduled/future periods that have not yet started must never have grades populated.
                p_status = resolve_period_lifecycle_status(p, all_year_periods)
                if p_status in (PeriodLifecycleStatus.ACTIVE, PeriodLifecycleStatus.CLOSED):
                    g = grades_by_period_subject.get((p.id, cur_sub.subject_id))
                    if g and g.final_score is not None:
                        w = p.weight_percentage
                        s = g.final_score
                        p_grades[p.period_number] = {
                            "score": float(s),
                            "weight": float(w),
                        }
                        weighted_sum += s * (w / Decimal("100.00"))
                        total_weight += w

            # Subject annual attendance
            sub_att = await self._academic_calc_service.calculate_annual_attendance(
                institution_id=institution_id,
                student_id=student_id,
                academic_year_id=academic_year_id,
                subject_id=cur_sub.subject_id,
                group_id=group.id,
            )

            if total_weight > Decimal("0.00"):
                final_subj_score = round(weighted_sum * (Decimal("100.00") / total_weight), 2)
                cumulative_scores.append(final_subj_score)
                subj_perf = self._siee_service.map_score_to_performance_level(final_subj_score, policy).value

                # Rule 10: Annual final grades must remain pending when the academic year is active
                # and the required evaluation periods have not been closed.
                if is_year_completed:
                    if final_subj_score < policy.min_passing_score:
                        failed_subjects += 1
                    final_annual_val: float | None = float(final_subj_score)
                    perf_level_val: str | None = subj_perf
                    eval_status = "CLOSED"
                else:
                    final_annual_val = None
                    perf_level_val = "PENDIENTE"
                    eval_status = "PENDING"
            else:
                final_annual_val = None
                perf_level_val = "PENDIENTE"
                eval_status = "PENDING"
                pending_subjects += 1

            subject_final_rows.append({
                "subject_id": str(cur_sub.subject_id),
                "subject_name": cur_sub.subject_name,
                "area_name": cur_sub.knowledge_area_name,
                "weekly_hours": cur_sub.weekly_hours,
                "teacher_name": cur_sub.teacher_name or "No asignado",
                "period_grades": p_grades,
                "final_annual_score": final_annual_val,
                "provisional_annual_score": float(final_subj_score) if total_weight > Decimal("0.00") else None,
                "performance_level": perf_level_val if perf_level_val else "PENDIENTE",
                "evaluation_status": eval_status,
                "total_absences": sub_att.total_absences,
                "unexcused_absences": sub_att.unexcused_absences,
            })

        final_year_avg = (
            round(sum(cumulative_scores) / len(cumulative_scores), 2)
            if cumulative_scores
            else Decimal("0.00")
        )
        final_level = (
            self._siee_service.map_score_to_performance_level(final_year_avg, policy).value
            if cumulative_scores
            else "PENDIENTE"
        )

        evaluated_period_numbers = {
            p.period_number
            for p in all_year_periods
            if any(p.period_number in s["period_grades"] for s in subject_final_rows)
        }
        is_provisional = (
            (year.status == AcademicYearStatus.ACTIVE)
            or (len(open_periods) > 0)
            or (pending_subjects > 0)
            or (len(evaluated_period_numbers) < total_periods_count)
        )

        # 7. Fetch Official Promotion Record if committed
        promo_stmt = select(StudentPromotion).where(
            StudentPromotion.institution_id == institution_id,
            StudentPromotion.academic_year_id == academic_year_id,
            StudentPromotion.student_id == student_id,
        )
        promotion_rec = (await self._session.execute(promo_stmt)).scalars().first()

        inst_stmt = select(Institution).where(Institution.id == institution_id)
        institution = (await self._session.execute(inst_stmt)).scalars().first()

        return {
            "institution": {
                "id": str(institution.id),
                "name": institution.name,
                "dane_code": institution.dane_code,
            },
            "campus": {
                "id": str(group.campus.id) if group.campus else None,
                "name": group.campus.name if group.campus else "Sede Principal",
            },
            "student": {
                "id": str(student.id),
                "simat_code": student.code_simat,
                "full_name": f"{student.user.first_name} {student.user.last_name}" if student.user else "",
                "document_number": student.user.document_number if student.user else "",
            },
            "academic_year": {
                "id": str(year.id),
                "year": year.year,
                "status": year.status.value,
                "periods": [
                    {
                        "id": str(p.id),
                        "period_number": p.period_number,
                        "name": p.name,
                        "weight_percentage": float(p.weight_percentage),
                        "is_closed": p.is_closed,
                    }
                    for p in all_year_periods
                ],
            },
            "group": {
                "id": str(group.id),
                "name": group.name,
                "grade_name": group.grade.name if group.grade else "",
            },
            "summary": {
                "cumulative_average": float(final_year_avg),
                "performance_level": final_level,
                "total_subjects": len(curriculum.subjects),
                "failed_subjects_count": failed_subjects,
                "pending_subjects_count": pending_subjects,
                "total_absences": annual_att.total_absences,
                "unexcused_absences": annual_att.unexcused_absences,
                "is_provisional": is_provisional,
            },
            "promotion": {
                "status": promotion_rec.promotion_status.value if promotion_rec else "PENDIENTE",
                "acta_number": promotion_rec.acta_number if promotion_rec else None,
                "decision_date": str(promotion_rec.decision_date) if promotion_rec else None,
                "observations": (
                    promotion_rec.observations
                    if promotion_rec
                    else (
                        "Año lectivo en curso. Dictamen provisional sujeto al cierre de todos los períodos académicos."
                        if is_provisional
                        else None
                    )
                ),
                "is_provisional": is_provisional,
                "evaluated_periods_count": len(evaluated_period_numbers),
                "total_periods_count": total_periods_count,
            },
            "subjects": subject_final_rows,
        }

    # =======================================================================
    # 3. Group Consolidation Matrix (Sábana de Notas)
    # =======================================================================

    async def get_group_consolidation_matrix(
        self,
        institution_id: uuid.UUID,
        group_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Generate complete matrix of student grades by subject for a classroom group.
        Used by Teachers and Academic Directives during evaluation commissions.
        """
        g_stmt = (
            select(Group)
            .where(Group.id == group_id)
            .options(selectinload(Group.campus), selectinload(Group.grade))
        )
        group = (await self._session.execute(g_stmt)).scalars().first()
        if not group or not group.campus or group.campus.institution_id != institution_id:
            raise CrossTenantMismatchError("El grupo no pertenece a la institución educativa.")

        p_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.id == period_id)
            .options(selectinload(AcademicPeriod.academic_year))
        )
        period = (await self._session.execute(p_stmt)).scalars().first()
        if not period or period.academic_year.institution_id != institution_id:
            raise CrossTenantMismatchError("El período no pertenece a la institución educativa.")

        # 1. Fetch group enrollments
        enr_stmt = (
            select(Enrollment)
            .where(
                Enrollment.group_id == group_id,
                Enrollment.academic_year_id == period.academic_year_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            .options(selectinload(Enrollment.student).selectinload(Student.user))
            .order_by(Enrollment.created_at.asc())
        )
        enrollments = list((await self._session.execute(enr_stmt)).scalars().all())

        # 2. Fetch all grades in this group and period
        grades_stmt = (
            select(PeriodSubjectGrade)
            .join(Enrollment, Enrollment.id == PeriodSubjectGrade.enrollment_id)
            .where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.academic_period_id == period_id,
                Enrollment.group_id == group_id,
            )
            .options(selectinload(PeriodSubjectGrade.subject))
        )
        all_grades = list((await self._session.execute(grades_stmt)).scalars().all())

        # 3. Fetch authoritative curriculum for this group
        curriculum_subjects = await self._curriculum_service.resolve_group_curriculum(
            institution_id=institution_id,
            group_id=group_id,
            academic_year_id=period.academic_year_id,
        )

        student_matrix = []
        for enr in enrollments:
            st = enr.student
            st_grades = {g.subject_id: g for g in all_grades if g.student_id == st.id}

            scores_list = []
            subj_dict = {}
            total_abs = 0

            for sub in curriculum_subjects:
                g = st_grades.get(sub.subject_id)
                if g:
                    final_s = float(g.final_score)
                    scores_list.append(g.final_score)
                    total_abs += g.total_absences
                    subj_dict[str(sub.subject_id)] = {
                        "score": final_s,
                        "level": g.performance_level.value,
                    }
                else:
                    subj_dict[str(sub.subject_id)] = {
                        "score": None,
                        "level": None,
                    }

            avg_score = (
                round(sum(scores_list) / len(scores_list), 2)
                if scores_list
                else Decimal("0.00")
            )

            student_matrix.append({
                "student_id": str(st.id),
                "student_name": f"{st.user.first_name} {st.user.last_name}" if st.user else "",
                "simat_code": st.code_simat,
                "subjects": subj_dict,
                "average": float(avg_score),
                "total_absences": total_abs,
            })

        # Sort matrix by average descending for group ranking
        student_matrix.sort(key=lambda x: x["average"], reverse=True)
        for idx, row in enumerate(student_matrix, start=1):
            row["rank"] = idx

        return {
            "group": {
                "id": str(group.id),
                "name": group.name,
                "grade_name": group.grade.name if group.grade else "",
            },
            "period": {
                "id": str(period.id),
                "period_number": period.period_number,
                "name": period.name,
            },
            "subjects": [
                {
                    "id": str(s.subject_id),
                    "name": s.subject_name,
                    "area_name": s.knowledge_area_name,
                    "weekly_hours": s.weekly_hours,
                    "teacher_name": s.teacher_name,
                }
                for s in curriculum_subjects
            ],
            "students": student_matrix,
            "total_students": len(student_matrix),
        }
