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
from app.models.academic_year import AcademicPeriod, AcademicYear
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

        # 5. Fetch all PeriodSubjectGrade records for this student and period
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
        grades = list((await self._session.execute(grades_stmt)).scalars().all())

        # 6. Fetch Group Academic Ranking (Puesto en el Grupo)
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

        rank = 1
        total_students_in_group = len(rank_rows)
        for idx, r in enumerate(rank_rows, start=1):
            if r.student_id == student_id:
                rank = idx
                break

        # 7. Fetch Achievements for the subjects evaluated
        subj_ids = [g.subject_id for g in grades]
        achievements_stmt = select(AcademicAchievement).where(
            AcademicAchievement.institution_id == institution_id,
            AcademicAchievement.academic_period_id == period_id,
        )
        all_achievements = list((await self._session.execute(achievements_stmt)).scalars().all())

        # 8. Compute Student Period Summary
        scores_list = [g.final_score for g in grades]
        student_period_avg = (
            round(sum(scores_list) / len(scores_list), 2)
            if scores_list
            else Decimal("0.00")
        )
        avg_level = self._siee_service.map_score_to_performance_level(student_period_avg, policy)

        failed_subjects = sum(1 for g in grades if g.final_score < policy.min_passing_score)
        total_absences_period = sum(g.total_absences for g in grades)
        unexcused_absences_period = sum(g.unexcused_absences for g in grades)

        # 9. Format Subjects Detail
        subject_rows = []
        for g in grades:
            # Find matching achievements
            subj_achs = [
                {
                    "code": a.code,
                    "description": a.description,
                    "level": a.performance_level.value,
                }
                for a in all_achievements
                if a.performance_level == g.performance_level
            ]

            teacher_name = (
                f"{g.graded_by.user.first_name} {g.graded_by.user.last_name}"
                if g.graded_by and g.graded_by.user
                else "No asignado"
            )

            recoveries = [
                {
                    "initial_score": float(r.initial_score),
                    "recovery_score": float(r.recovery_score),
                    "applied_cap": float(r.applied_cap),
                    "final_adjusted_score": float(r.final_adjusted_score),
                    "recovery_date": str(r.recovery_date),
                    "act_number": r.act_number,
                }
                for r in g.recovery_records
            ]

            subject_rows.append({
                "subject_id": str(g.subject_id),
                "subject_name": g.subject.name,
                "area_name": g.subject.knowledge_area.name if g.subject.knowledge_area else "General",
                "weekly_hours": g.subject.weekly_hours,
                "teacher_name": teacher_name,
                "calculated_score": float(g.calculated_score),
                "final_score": float(g.final_score),
                "performance_level": g.performance_level.value,
                "is_passed": g.final_score >= policy.min_passing_score,
                "adjustment_reason": g.adjustment_reason,
                "total_absences": g.total_absences,
                "unexcused_absences": g.unexcused_absences,
                "observations": g.observations,
                "achievements": subj_achs,
                "recoveries": recoveries,
            })

        # 10. Fetch Institution & Campus Metadata
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
                "performance_level": avg_level.value,
                "total_subjects": len(grades),
                "failed_subjects": failed_subjects,
                "passed_subjects": len(grades) - failed_subjects,
                "rank": rank,
                "total_students": total_students_in_group,
                "total_absences": total_absences_period,
                "unexcused_absences": unexcused_absences_period,
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

        # 4. Fetch All Period Grades for this Student and Year
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

        # Group grades by subject
        subject_period_map: dict[uuid.UUID, dict[str, Any]] = {}
        for g in all_grades:
            sub_id = g.subject_id
            if sub_id not in subject_period_map:
                subject_period_map[sub_id] = {
                    "subject_id": str(sub_id),
                    "subject_name": g.subject.name,
                    "area_name": g.subject.knowledge_area.name if g.subject.knowledge_area else "General",
                    "period_grades": {},
                    "total_absences": 0,
                    "unexcused_absences": 0,
                }
            p_num = g.academic_period.period_number
            weight = g.academic_period.weight_percentage
            subject_period_map[sub_id]["period_grades"][p_num] = {
                "score": float(g.final_score),
                "weight": float(weight),
            }
            subject_period_map[sub_id]["total_absences"] += g.total_absences
            subject_period_map[sub_id]["unexcused_absences"] += g.unexcused_absences

        # Calculate final cumulative score per subject
        subject_final_rows = []
        cumulative_scores = []
        failed_subjects = 0

        for sub_id, data in subject_period_map.items():
            p_grades = data["period_grades"]
            weighted_sum = Decimal("0.00")
            total_weight = Decimal("0.00")

            for p_num, p_val in p_grades.items():
                w = Decimal(str(p_val["weight"]))
                s = Decimal(str(p_val["score"]))
                weighted_sum += s * (w / Decimal("100.00"))
                total_weight += w

            # Normalize if sum of weights is less than 100%
            if total_weight > Decimal("0.00"):
                final_subj_score = round(weighted_sum * (Decimal("100.00") / total_weight), 2)
            else:
                final_subj_score = Decimal("0.00")

            cumulative_scores.append(final_subj_score)
            if final_subj_score < policy.min_passing_score:
                failed_subjects += 1

            subj_perf = self._siee_service.map_score_to_performance_level(final_subj_score, policy)

            subject_final_rows.append({
                "subject_id": data["subject_id"],
                "subject_name": data["subject_name"],
                "area_name": data["area_name"],
                "period_grades": p_grades,
                "final_annual_score": float(final_subj_score),
                "performance_level": subj_perf.value,
                "total_absences": data["total_absences"],
                "unexcused_absences": data["unexcused_absences"],
            })

        final_year_avg = (
            round(sum(cumulative_scores) / len(cumulative_scores), 2)
            if cumulative_scores
            else Decimal("0.00")
        )
        final_level = self._siee_service.map_score_to_performance_level(final_year_avg, policy)

        # 5. Fetch Official Promotion Record if committed
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
            },
            "group": {
                "id": str(group.id),
                "name": group.name,
                "grade_name": group.grade.name if group.grade else "",
            },
            "summary": {
                "cumulative_average": float(final_year_avg),
                "performance_level": final_level.value,
                "failed_subjects_count": failed_subjects,
            },
            "promotion": {
                "status": promotion_rec.promotion_status.value if promotion_rec else "PENDIENTE",
                "acta_number": promotion_rec.acta_number if promotion_rec else None,
                "decision_date": str(promotion_rec.decision_date) if promotion_rec else None,
                "observations": promotion_rec.observations if promotion_rec else None,
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

        # 3. Fetch subjects taught in this group
        subjects_stmt = (
            select(Subject)
            .join(AcademicAssignment, AcademicAssignment.subject_id == Subject.id)
            .where(
                Subject.institution_id == institution_id,
                AcademicAssignment.group_id == group_id,
                AcademicAssignment.academic_year_id == period.academic_year_id,
                AcademicAssignment.is_active.is_(True),
            )
            .distinct()
        )
        subjects = list((await self._session.execute(subjects_stmt)).scalars().all())

        student_matrix = []
        for enr in enrollments:
            st = enr.student
            st_grades = {g.subject_id: g for g in all_grades if g.student_id == st.id}

            scores_list = []
            subj_dict = {}
            total_abs = 0

            for sub in subjects:
                g = st_grades.get(sub.id)
                if g:
                    final_s = float(g.final_score)
                    scores_list.append(g.final_score)
                    total_abs += g.total_absences
                    subj_dict[str(sub.id)] = {
                        "score": final_s,
                        "level": g.performance_level.value,
                    }
                else:
                    subj_dict[str(sub.id)] = {
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
                    "id": str(s.id),
                    "name": s.name,
                }
                for s in subjects
            ],
            "students": student_matrix,
            "total_students": len(student_matrix),
        }
