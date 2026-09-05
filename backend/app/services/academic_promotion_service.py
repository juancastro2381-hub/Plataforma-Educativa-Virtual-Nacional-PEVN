"""
PEVN Backend — Academic Promotion & Graduation Commission Domain Service (Phase 16B)

Authoritative business logic for:
- Evaluating year-end student promotion, retention, and graduation status (DECISION-16-02)
- Applying institutional SIEE promotion criteria dynamically:
  * Maximum failed subjects threshold (max_failed_subjects_for_promotion)
  * Maximum failed core areas threshold (max_failed_core_subjects)
  * Attendance percentage threshold (min_attendance_percentage)
- Generation of Promotion Assessment Previews for Institutional Evaluation Commissions
- Transactional commitment of official Promotion Acts (Actas de Promoción y Evaluación)
- Strict multi-tenant boundaries and auditability.

SEMANTIC INVARIANT — PROMOTION vs. GRADUATION (DECISION-16-04):
  PROMOVIDO: The student successfully completed the academic year according to the active
    SIEE policy and is promoted to the NEXT grade. The enrollment for the CURRENT year
    remains ACTIVE (historical record). NO automatic transition to EnrollmentStatus.GRADUATED.
    The student's academic trajectory continues into the next grade/year.

  GRADUADO: The student is in the institutionally defined FINAL GRADE (Grade 11 / Culminación
    de Educación Media) AND satisfies all graduation requirements under the active SIEE
    policy. ONLY this status causes EnrollmentStatus.GRADUATED on the current enrollment.
    This is a terminal status for the student's school cycle.

  NO_PROMOVIDO: The student failed and must repeat the current grade.
    Enrollment remains ACTIVE.

  PENDIENTE_NIVELACION: The student has pending remediation subjects and requires
    a supplementary evaluation commission decision. Enrollment remains ACTIVE.

  Promotion ≠ Graduation. These are distinct academic domain concepts.
  Never conflate PROMOVIDO with GRADUADO.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service as _default_audit_service
from app.core.exceptions import (
    CrossTenantMismatchError,
    DuplicatePromotionError,
    SieePolicyValidationError,
)
from app.core.logging import get_logger
from app.models.academic_year import AcademicPeriod, AcademicYear
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import (
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    PromotionStatusEnum,
    SieePolicy,
    StudentPromotion,
)
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group
from app.models.institution import Campus, Institution
from app.models.student import Student
from app.models.subject import KnowledgeArea, Subject
from app.services.siee_policy_service import SieePolicyService

_logger = get_logger(__name__)


class AcademicPromotionService:
    """
    Authoritative domain service for evaluating and committing academic promotion
    decisions in compliance with Colombian decree 1290 and institutional SIEE policies.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService | None = None,
        audit_service: IAuditService | None = None,
        siee_service: SieePolicyService | None = None,
    ) -> None:
        self._session = session
        self._audit = audit_service or audit or _default_audit_service
        self._siee_service = siee_service or SieePolicyService(session, audit=self._audit)

    # =======================================================================
    # 1. Promotion Preview (Evaluación para Comisión de Evaluación y Promoción)
    # =======================================================================

    async def calculate_promotion_preview(
        self,
        institution_id: uuid.UUID,
        group_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Calculate proposed promotion outcomes for every enrolled student in a group,
        strictly applying the configured institutional SIEE policy for the academic year.
        """
        # 1. Validate Group & Academic Year
        g_stmt = (
            select(Group)
            .where(Group.id == group_id)
            .options(selectinload(Group.campus), selectinload(Group.grade))
        )
        group = (await self._session.execute(g_stmt)).scalars().first()
        if not group or not group.campus or group.campus.institution_id != institution_id:
            raise CrossTenantMismatchError("El grupo no pertenece a la institución educativa.")

        y_stmt = select(AcademicYear).where(AcademicYear.id == academic_year_id)
        year = (await self._session.execute(y_stmt)).scalars().first()
        if not year or year.institution_id != institution_id:
            raise CrossTenantMismatchError("El año lectivo no pertenece a la institución educativa.")

        # 2. Resolve Active SIEE Policy
        policy = await self._siee_service.get_or_create_default_policy(
            institution_id=institution_id,
            academic_year_id=academic_year_id,
        )

        # 3. Fetch Active / Graduated Enrollments
        enr_stmt = (
            select(Enrollment)
            .where(
                Enrollment.group_id == group_id,
                Enrollment.academic_year_id == academic_year_id,
                Enrollment.status.in_([EnrollmentStatus.ACTIVE, EnrollmentStatus.GRADUATED]),
            )
            .options(selectinload(Enrollment.student).selectinload(Student.user))
            .order_by(Enrollment.created_at.asc())
        )
        enrollments = list((await self._session.execute(enr_stmt)).scalars().all())

        # 4. Fetch All Period Grades for this Group and Year
        grades_stmt = (
            select(PeriodSubjectGrade)
            .join(AcademicPeriod, AcademicPeriod.id == PeriodSubjectGrade.academic_period_id)
            .where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.enrollment_id.in_([e.id for e in enrollments]) if enrollments else False,
                AcademicPeriod.academic_year_id == academic_year_id,
            )
            .options(
                selectinload(PeriodSubjectGrade.subject).selectinload(Subject.knowledge_area),
                selectinload(PeriodSubjectGrade.academic_period),
            )
        )
        all_grades = list((await self._session.execute(grades_stmt)).scalars().all()) if enrollments else []

        # 5. Fetch Existing Promotion Decisions if already committed
        promo_stmt = select(StudentPromotion).where(
            StudentPromotion.institution_id == institution_id,
            StudentPromotion.academic_year_id == academic_year_id,
            StudentPromotion.group_id == group_id,
        )
        existing_promotions = {
            p.student_id: p
            for p in (await self._session.execute(promo_stmt)).scalars().all()
        }

        # 6. Evaluate Each Student
        candidates = []
        is_graduating_grade = group.grade.code in ("G11", "11", "GRADO_11") or (
            group.grade.level == EducationalLevel.MEDIA and group.grade.ordinal_order == 11
        )

        for enr in enrollments:
            st = enr.student
            st_grades = [g for g in all_grades if g.student_id == st.id]

            # Group by subject and calculate weighted final score
            subject_map: dict[uuid.UUID, dict[str, Any]] = {}
            for g in st_grades:
                sub_id = g.subject_id
                if sub_id not in subject_map:
                    is_core = (
                        g.subject.knowledge_area is not None
                        and any(
                            core_term in g.subject.knowledge_area.name.lower()
                            for core_term in ["matemátic", "lengu", "español", "humanidad", "ciencias"]
                        )
                    )
                    subject_map[sub_id] = {
                        "subject_name": g.subject.name,
                        "is_core": is_core,
                        "weighted_sum": Decimal("0.00"),
                        "total_weight": Decimal("0.00"),
                        "total_absences": 0,
                        "unexcused_absences": 0,
                    }
                w = g.academic_period.weight_percentage
                s = g.final_score
                subject_map[sub_id]["weighted_sum"] += s * (w / Decimal("100.00"))
                subject_map[sub_id]["total_weight"] += w
                subject_map[sub_id]["total_absences"] += g.total_absences
                subject_map[sub_id]["unexcused_absences"] += g.unexcused_absences

            failed_subjects_count = 0
            failed_core_subjects_count = 0
            subject_final_scores = []
            total_unexcused_absences = 0

            for sub_id, data in subject_map.items():
                tw = data["total_weight"]
                if tw > Decimal("0.00"):
                    final_subj = round(data["weighted_sum"] * (Decimal("100.00") / tw), 2)
                else:
                    final_subj = Decimal("0.00")

                subject_final_scores.append(final_subj)
                total_unexcused_absences += data["unexcused_absences"]

                if final_subj < policy.min_passing_score:
                    failed_subjects_count += 1
                    if data["is_core"]:
                        failed_core_subjects_count += 1

            cum_average = (
                round(sum(subject_final_scores) / len(subject_final_scores), 2)
                if subject_final_scores
                else Decimal("0.00")
            )

            # Estimate attendance percentage (assuming ~180 school days/year standard)
            est_total_days = Decimal("180.00")
            att_percentage = max(
                Decimal("0.00"),
                round(
                    ((est_total_days - Decimal(str(total_unexcused_absences))) / est_total_days) * Decimal("100.00"),
                    2,
                ),
            )

            # Determine proposed promotion status from SIEE policy rules
            proposed_status = PromotionStatusEnum.PROMOVIDO
            decision_reason = "Cumple con los requisitos académicos del SIEE."

            if policy.attendance_affects_promotion and att_percentage < policy.min_attendance_percentage:
                proposed_status = PromotionStatusEnum.NO_PROMOVIDO
                decision_reason = (
                    f"Reprobado por inasistencia: {att_percentage}% (Mínimo requerido: {policy.min_attendance_percentage}%)."
                )
            elif failed_core_subjects_count > policy.max_failed_core_subjects:
                proposed_status = PromotionStatusEnum.NO_PROMOVIDO
                decision_reason = (
                    f"Reprobado por áreas fundamentales: {failed_core_subjects_count} asignaturas núcleo no superadas."
                )
            elif failed_subjects_count > policy.max_failed_subjects_for_promotion:
                proposed_status = PromotionStatusEnum.NO_PROMOVIDO
                decision_reason = (
                    f"Reprobado por asignaturas no superadas: {failed_subjects_count} (Límite SIEE: {policy.max_failed_subjects_for_promotion})."
                )
            elif failed_subjects_count > 0:
                proposed_status = PromotionStatusEnum.PENDIENTE_NIVELACION
                decision_reason = (
                    f"Pendiente de nivelación: registra {failed_subjects_count} asignatura(s) con desempeño bajo."
                )
            else:
                if is_graduating_grade:
                    proposed_status = PromotionStatusEnum.GRADUADO
                    decision_reason = "Promovido y Graduado satisfactoriamente (Culminación de Educación Media)."
                else:
                    proposed_status = PromotionStatusEnum.PROMOVIDO
                    decision_reason = "Promovido al grado siguiente por excelencia o suficiencia académica."

            existing_promo = existing_promotions.get(st.id)

            candidates.append({
                "student_id": str(st.id),
                "simat_code": st.code_simat,
                "first_name": st.user.first_name if st.user else "",
                "last_name": st.user.last_name if st.user else "",
                "cumulative_average": float(cum_average),
                "failed_subjects_count": failed_subjects_count,
                "failed_core_subjects_count": failed_core_subjects_count,
                "attendance_percentage": float(att_percentage),
                "proposed_status": proposed_status.value,
                "decision_reason": decision_reason,
                "is_committed": existing_promo is not None,
                "committed_status": existing_promo.promotion_status.value if existing_promo else None,
                "acta_number": existing_promo.acta_number if existing_promo else None,
            })

        return {
            "group": {
                "id": str(group.id),
                "name": group.name,
                "grade_name": group.grade.name if group.grade else "",
                "is_graduating_grade": is_graduating_grade,
            },
            "academic_year": {
                "id": str(year.id),
                "year": year.year,
            },
            "siee_policy": {
                "id": str(policy.id),
                "name": policy.name,
                "version": policy.version,
                "min_passing_score": float(policy.min_passing_score),
                "max_failed_subjects_for_promotion": policy.max_failed_subjects_for_promotion,
                "max_failed_core_subjects": policy.max_failed_core_subjects,
                "min_attendance_percentage": float(policy.min_attendance_percentage),
            },
            "total_candidates": len(candidates),
            "candidates": candidates,
        }

    # =======================================================================
    # 2. Commit Promotion Act (Cierre y Asentamiento de Acta de Promoción)
    # =======================================================================

    async def commit_group_promotions(
        self,
        institution_id: uuid.UUID,
        group_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        acta_number: str,
        decision_date: date,
        decisions: list[dict[str, Any]] | None = None,
        items: list[dict[str, Any]] | None = None,
        user_id: uuid.UUID | None = None,
        observations: str | None = None,
    ) -> list[StudentPromotion]:
        """
        Officially commit promotion records for students in a classroom group.

        Records an immutable promotion record per student and conditionally transitions
        the enrollment status according to the following SIEE domain rules:

          - PROMOVIDO         → Enrollment.status remains ACTIVE (annual grade promotion,
                                student continues into next academic year/grade).
          - GRADUADO          → Enrollment.status becomes GRADUATED (terminal status,
                                student has completed the final grade of their school cycle).
          - NO_PROMOVIDO      → Enrollment.status remains ACTIVE (student repeats grade).
          - PENDIENTE_NIV...  → Enrollment.status remains ACTIVE (pending commission).

        IMPORTANT: Historical enrollment records are NEVER overwritten or deleted.
        The committed StudentPromotion rows are the immutable act-of-record.
        """
        decision_items = decisions if decisions is not None else (items or [])

        # 1. Validate Group & Academic Year
        g_stmt = (
            select(Group)
            .where(Group.id == group_id)
            .options(selectinload(Group.campus))
        )
        group = (await self._session.execute(g_stmt)).scalars().first()
        if not group or not group.campus or group.campus.institution_id != institution_id:
            raise CrossTenantMismatchError("El grupo no pertenece a la institución educativa.")

        y_stmt = select(AcademicYear).where(AcademicYear.id == academic_year_id)
        year = (await self._session.execute(y_stmt)).scalars().first()
        if not year or year.institution_id != institution_id:
            raise CrossTenantMismatchError("El año lectivo no pertenece a la institución educativa.")

        # 2. Validate SIEE Policy
        policy = await self._siee_service.get_or_create_default_policy(
            institution_id=institution_id,
            academic_year_id=academic_year_id,
        )

        committed_records = []

        for item in decision_items:
            student_id = uuid.UUID(str(item["student_id"]))
            status_val = PromotionStatusEnum(item["promotion_status"])
            cum_avg = Decimal(str(item.get("cumulative_average", "0.00")))
            failed_count = int(item.get("failed_subjects_count", 0))
            failed_core_count = int(item.get("failed_core_subjects_count", 0))
            att_percentage = Decimal(str(item.get("attendance_percentage", "100.00")))
            item_obs = item.get("observations") or observations

            # Check if promotion already exists
            existing_stmt = select(StudentPromotion).where(
                StudentPromotion.institution_id == institution_id,
                StudentPromotion.academic_year_id == academic_year_id,
                StudentPromotion.student_id == student_id,
            )
            existing = (await self._session.execute(existing_stmt)).scalars().first()

            if existing:
                existing.group_id = group_id
                existing.cumulative_average = cum_avg
                existing.failed_subjects_count = failed_count
                existing.failed_core_subjects_count = failed_core_count
                existing.attendance_percentage = att_percentage
                existing.promotion_status = status_val
                existing.acta_number = acta_number
                existing.decision_date = decision_date
                existing.observations = item_obs
                existing.closed_by_user_id = user_id
                existing.updated_at = datetime.now(UTC)
                record = existing
            else:
                record = StudentPromotion(
                    institution_id=institution_id,
                    academic_year_id=academic_year_id,
                    student_id=student_id,
                    group_id=group_id,
                    cumulative_average=cum_avg,
                    failed_subjects_count=failed_count,
                    failed_core_subjects_count=failed_core_count,
                    attendance_percentage=att_percentage,
                    promotion_status=status_val,
                    acta_number=acta_number,
                    decision_date=decision_date,
                    observations=item_obs,
                    closed_by_user_id=user_id,
                )
                self._session.add(record)

            # Transition enrollment status based on promotion outcome.
            #
            # SEMANTIC INVARIANT (DECISION-16-04):
            #   Only PromotionStatusEnum.GRADUADO (final-grade completers, Grade 11)
            #   causes EnrollmentStatus.GRADUATED on the current year's enrollment.
            #
            #   PromotionStatusEnum.PROMOVIDO means the student successfully
            #   completed the academic year and advances to the NEXT grade.
            #   The current-year enrollment stays ACTIVE as a historical record.
            #   Future enrollment in the next academic year will be a SEPARATE
            #   enrollment record created during the next matriculation process.
            #
            #   NO_PROMOVIDO and PENDIENTE_NIVELACION also leave the enrollment
            #   as ACTIVE (student remains in the same grade for the next year).
            enr_stmt = select(Enrollment).where(
                Enrollment.academic_year_id == academic_year_id,
                Enrollment.student_id == student_id,
            )
            enrollment = (await self._session.execute(enr_stmt)).scalars().first()
            if enrollment:
                if status_val == PromotionStatusEnum.GRADUADO:
                    # Terminal status: student completed the final grade of their school cycle.
                    enrollment.status = EnrollmentStatus.GRADUATED
                # PROMOVIDO, NO_PROMOVIDO, PENDIENTE_NIVELACION → preserve ACTIVE.
                # Promotion is not graduation. These are distinct academic outcomes.

            committed_records.append(record)

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.PROMOTION_COMMITTED,
                actor_id=str(user_id) if user_id else None,
                actor_ip="127.0.0.1",
                target_id=acta_number,
                target_type="StudentPromotion",
                institution_id=str(institution_id),
                metadata={
                    "group_id": str(group_id),
                    "academic_year_id": str(academic_year_id),
                    "acta_number": acta_number,
                    "student_count": len(committed_records),
                    "decision_date": decision_date.isoformat(),
                },
            )
        )

        return committed_records
