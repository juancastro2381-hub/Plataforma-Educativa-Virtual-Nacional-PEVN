"""
PEVN Backend — Evaluation & Grade Consolidation Domain Service (SIEE-Compliant)

Implements core SIEE evaluation workflows:
- Consolidation of hybrid period grades (deterministic activities calculation + audited teacher adjustment)
- Enforcing mandatory adjustment_reason whenever final_score != calculated_score
- Recording remediation / recovery grades with configurable institutional caps (DECISION-16-01)
- Period closing and reopening with full audit logging and grade row locking
- Strict multi-tenant boundaries and teacher assignment scope enforcement
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service as _default_audit_service
from app.core.exceptions import (
    AdjustmentReasonRequiredError,
    CrossTenantMismatchError,
    PeriodClosedLockedError,
    TeacherScopeViolationError,
)
from app.models.academic_activity import AcademicActivity, ActivityGrade
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicPeriod, AcademicYear
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import (
    AcademicAchievement,
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    RecoveryGrade,
    SieePolicy,
)
from app.models.group import Group
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.services.siee_policy_service import SieePolicyService


class EvaluationService:
    """
    Authoritative domain service for SIEE evaluations, hybrid consolidations,
    remediations, and period lock states across multi-tenant educational institutions.
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
    # 1. Period Sheet Consolidation (Sábana de Calificaciones del Período)
    # =======================================================================

    async def get_period_sheet(
        self,
        institution_id: uuid.UUID,
        period_id: uuid.UUID,
        group_id: uuid.UUID,
        subject_id: uuid.UUID,
        teacher_id: uuid.UUID | None = None,
        is_directive: bool = False,
    ) -> dict[str, Any]:
        """
        Fetch the complete evaluation consolidation sheet for a group, subject, and period.
        Validates strict tenant boundaries and teacher academic assignment scope.
        """
        # 1. Validate AcademicPeriod & Year
        period_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.id == period_id)
            .options(selectinload(AcademicPeriod.academic_year))
        )
        period = (await self._session.execute(period_stmt)).scalars().first()
        if not period or period.academic_year.institution_id != institution_id:
            raise CrossTenantMismatchError(
                "El período académico no pertenece a la institución educativa."
            )

        # 2. Validate Group & Subject
        group_stmt = (
            select(Group)
            .where(Group.id == group_id)
            .options(selectinload(Group.campus), selectinload(Group.grade))
        )
        group = (await self._session.execute(group_stmt)).scalars().first()
        if not group or not group.campus or group.campus.institution_id != institution_id:
            raise CrossTenantMismatchError(
                "El grupo no pertenece a la institución educativa."
            )

        subj_stmt = select(Subject).where(Subject.id == subject_id)
        subject = (await self._session.execute(subj_stmt)).scalars().first()
        if not subject or subject.institution_id != institution_id:
            raise CrossTenantMismatchError(
                "La asignatura no pertenece a la institución educativa."
            )

        # 3. Resolve AcademicAssignment
        assignment_stmt = select(AcademicAssignment).where(
            AcademicAssignment.academic_year_id == period.academic_year_id,
            AcademicAssignment.group_id == group_id,
            AcademicAssignment.subject_id == subject_id,
            AcademicAssignment.is_active.is_(True),
        )
        assignment = (await self._session.execute(assignment_stmt)).scalars().first()

        # 4. Enforce Teacher Scope
        if not is_directive:
            if not teacher_id or not assignment or assignment.teacher_id != teacher_id:
                raise TeacherScopeViolationError(
                    "El docente no tiene asignación académica activa para calificar este grupo y asignatura."
                )

        # 5. Resolve active SIEE policy
        policy = await self._siee_service.get_or_create_default_policy(
            institution_id=institution_id,
            academic_year_id=period.academic_year_id,
        )

        # 6. Fetch Active Enrollments
        enrollment_stmt = (
            select(Enrollment)
            .where(
                Enrollment.academic_year_id == period.academic_year_id,
                Enrollment.group_id == group_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            .options(selectinload(Enrollment.student).selectinload(Student.user))
            .order_by(Enrollment.created_at.asc())
        )
        enrollments = list((await self._session.execute(enrollment_stmt)).scalars().all())

        # 7. Fetch Existing Consolidated Period Grades
        grade_stmt = (
            select(PeriodSubjectGrade)
            .where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.academic_period_id == period_id,
                PeriodSubjectGrade.subject_id == subject_id,
            )
            .options(selectinload(PeriodSubjectGrade.recovery_records))
        )
        existing_grades = {
            g.student_id: g
            for g in (await self._session.execute(grade_stmt)).scalars().all()
        }

        # 8. Fetch Activities for this Period & Subject
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

        # 9. Fetch Activity Grades
        submissions: dict[tuple[uuid.UUID, uuid.UUID], ActivityGrade] = {}
        if activities:
            act_ids = [a.id for a in activities]
            sub_stmt = select(ActivityGrade).where(
                ActivityGrade.activity_id.in_(act_ids)
            )
            for sub in (await self._session.execute(sub_stmt)).scalars().all():
                submissions[(sub.activity_id, sub.student_id)] = sub

        # 10. Fetch Achievements / Descriptors
        ach_stmt = select(AcademicAchievement).where(
            AcademicAchievement.institution_id == institution_id,
            AcademicAchievement.academic_period_id == period_id,
            AcademicAchievement.academic_assignment_id == assignment.id if assignment else False,
        )
        achievements = list((await self._session.execute(ach_stmt)).scalars().all())

        # 11. Assemble Student Rows
        student_rows = []
        for enr in enrollments:
            st = enr.student
            st_user = st.user
            existing_rec = existing_grades.get(st.id)

            # Compute automatic weighted average from activities
            activity_grades_map = {}
            total_weight = Decimal("0.00")
            weighted_sum = Decimal("0.00")

            for act in activities:
                sub = submissions.get((act.id, st.id))
                score_val = sub.score if sub and sub.score is not None else None
                activity_grades_map[str(act.id)] = (
                    float(score_val) if score_val is not None else None
                )
                if score_val is not None and act.weight_percentage:
                    w = act.weight_percentage
                    total_weight += w
                    weighted_sum += score_val * (w / Decimal("100.00"))

            if total_weight > Decimal("0.00"):
                computed_score = round(
                    weighted_sum * (Decimal("100.00") / total_weight), 2
                )
            else:
                computed_score = Decimal("0.00")

            if existing_rec:
                final_score = existing_rec.final_score
                calculated_score = existing_rec.calculated_score
                adjustment_reason = existing_rec.adjustment_reason
                performance_level = existing_rec.performance_level
                total_absences = existing_rec.total_absences
                unexcused_absences = existing_rec.unexcused_absences
                observations = existing_rec.observations
                is_locked = existing_rec.is_locked
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
            else:
                final_score = computed_score
                calculated_score = computed_score
                adjustment_reason = None
                performance_level = self._siee_service.map_score_to_performance_level(
                    final_score, policy
                )
                total_absences = 0
                unexcused_absences = 0
                observations = None
                is_locked = period.is_closed
                recoveries_list = []

            student_rows.append({
                "student_id": str(st.id),
                "enrollment_id": str(enr.id),
                "simat_code": st.code_simat,
                "first_name": st_user.first_name if st_user else "",
                "last_name": st_user.last_name if st_user else "",
                "document_number": st_user.document_number if st_user else "",
                "activity_grades": activity_grades_map,
                "calculated_score": float(calculated_score),
                "final_score": float(final_score),
                "adjustment_reason": adjustment_reason,
                "performance_level": performance_level.value,
                "total_absences": total_absences,
                "unexcused_absences": unexcused_absences,
                "observations": observations,
                "is_locked": is_locked or period.is_closed,
                "recoveries": recoveries_list,
            })

        return {
            "period": {
                "id": str(period.id),
                "name": period.name,
                "period_number": period.period_number,
                "weight_percentage": float(period.weight_percentage),
                "is_closed": period.is_closed,
            },
            "group": {
                "id": str(group.id),
                "name": group.name,
                "grade_name": group.grade.name if group.grade else "",
            },
            "subject": {
                "id": str(subject.id),
                "name": subject.name,
                "weekly_hours": subject.weekly_hours,
            },
            "policy": {
                "id": str(policy.id),
                "min_passing_score": float(policy.min_passing_score),
                "max_score": float(policy.max_score),
                "recovery_grade_cap": float(policy.recovery_grade_cap),
                "low_threshold_max": float(policy.low_threshold_max),
                "basic_threshold_max": float(policy.basic_threshold_max),
                "high_threshold_max": float(policy.high_threshold_max),
            },
            "activities": [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "weight_percentage": float(a.weight_percentage) if a.weight_percentage else 0.0,
                    "max_score": float(a.max_score),
                    "due_date": str(a.due_date) if a.due_date else None,
                }
                for a in activities
            ],
            "achievements": [
                {
                    "id": str(ach.id),
                    "code": ach.code,
                    "description": ach.description,
                    "performance_level": ach.performance_level.value,
                }
                for ach in achievements
            ],
            "students": student_rows,
        }

    # =======================================================================
    # 2. Save Consolidated Period Grades (DECISION-16-03 Hybrid Invariant)
    # =======================================================================

    async def save_period_grades(
        self,
        institution_id: uuid.UUID,
        period_id: uuid.UUID,
        group_id: uuid.UUID,
        subject_id: uuid.UUID,
        teacher_id: uuid.UUID | None,
        items: list[dict[str, Any]],
        achievements: list[dict[str, Any]] | None,
        user_id: uuid.UUID,
        is_directive: bool = False,
    ) -> list[PeriodSubjectGrade]:
        """
        Save period consolidated grades.
        Enforces:
          - SIEE scale mapping
          - Mandatory adjustment_reason if final_score != calculated_score
          - Immutable block if period is closed (AcademicPeriod.is_closed = True)
          - Full audit logging
        """
        # 1. Validate Period & Status
        period_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.id == period_id)
            .options(selectinload(AcademicPeriod.academic_year))
        )
        period = (await self._session.execute(period_stmt)).scalars().first()
        if not period or period.academic_year.institution_id != institution_id:
            raise CrossTenantMismatchError(
                "El período académico no pertenece a la institución educativa."
            )

        if period.is_closed:
            raise PeriodClosedLockedError(
                "No se pueden guardar calificaciones: el período académico se encuentra cerrado y sellado."
            )

        # 2. Validate Group & Subject
        group_stmt = (
            select(Group)
            .where(Group.id == group_id)
            .options(selectinload(Group.campus))
        )
        group = (await self._session.execute(group_stmt)).scalars().first()
        if not group or not group.campus or group.campus.institution_id != institution_id:
            raise CrossTenantMismatchError("El grupo no pertenece a la institución educativa.")

        subj_stmt = select(Subject).where(Subject.id == subject_id)
        subject = (await self._session.execute(subj_stmt)).scalars().first()
        if not subject or subject.institution_id != institution_id:
            raise CrossTenantMismatchError("La asignatura no pertenece a la institución educativa.")

        # 3. Validate Teacher Scope
        assignment_stmt = select(AcademicAssignment).where(
            AcademicAssignment.academic_year_id == period.academic_year_id,
            AcademicAssignment.group_id == group_id,
            AcademicAssignment.subject_id == subject_id,
            AcademicAssignment.is_active.is_(True),
        )
        assignment = (await self._session.execute(assignment_stmt)).scalars().first()

        if not is_directive:
            if not teacher_id or not assignment or assignment.teacher_id != teacher_id:
                raise TeacherScopeViolationError(
                    "El docente no tiene asignación académica activa para calificar este grupo y asignatura."
                )

        # 4. Resolve SIEE policy
        policy = await self._siee_service.get_or_create_default_policy(
            institution_id=institution_id,
            academic_year_id=period.academic_year_id,
        )

        saved_grades = []
        for item in items:
            student_id = uuid.UUID(str(item["student_id"]))
            enrollment_id = uuid.UUID(str(item["enrollment_id"]))

            # Validate enrollment tenant & student ownership
            enr_stmt = (
                select(Enrollment)
                .where(Enrollment.id == enrollment_id)
                .options(selectinload(Enrollment.student))
            )
            enrollment = (await self._session.execute(enr_stmt)).scalars().first()
            if (
                not enrollment
                or not enrollment.student
                or enrollment.student.institution_id != institution_id
                or enrollment.student_id != student_id
                or enrollment.group_id != group_id
            ):
                raise CrossTenantMismatchError(
                    f"Matrícula inválida o no coincidente para el estudiante {student_id}."
                )

            calculated_score = Decimal(str(item.get("calculated_score", "0.00")))
            final_score = Decimal(str(item.get("final_score", calculated_score)))
            adjustment_reason = item.get("adjustment_reason")
            observations = item.get("observations")
            total_absences = int(item.get("total_absences", 0))
            unexcused_absences = int(item.get("unexcused_absences", 0))

            # Enforce inclusive score bounds [0.00, 5.00]
            if final_score < Decimal("0.00"):
                final_score = Decimal("0.00")
            elif final_score > policy.max_score:
                final_score = policy.max_score

            # Invariant: If final_score != calculated_score, adjustment_reason is mandatory
            if round(final_score, 2) != round(calculated_score, 2):
                if not adjustment_reason or not str(adjustment_reason).strip():
                    raise AdjustmentReasonRequiredError(
                        f"Se requiere justificación para el estudiante {student_id} porque la nota definitiva ({final_score}) difiere de la calculada ({calculated_score})."
                    )

            performance_level = self._siee_service.map_score_to_performance_level(
                final_score,
                policy,
            )

            # Query existing record
            grade_stmt = select(PeriodSubjectGrade).where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.academic_period_id == period_id,
                PeriodSubjectGrade.student_id == student_id,
                PeriodSubjectGrade.subject_id == subject_id,
            )
            grade_record = (await self._session.execute(grade_stmt)).scalars().first()

            if grade_record:
                if grade_record.is_locked:
                    raise PeriodClosedLockedError("El registro de calificación individual está bloqueado.")

                # Audit modification if score changed
                if grade_record.final_score != final_score:
                    await self._audit.record(
                        AuditEvent(
                            event_type=AuditEventType.PERIOD_GRADE_ADJUSTED,
                            actor_id=str(user_id) if user_id else None,
                            actor_ip="127.0.0.1",
                            target_id=str(grade_record.id),
                            target_type="PeriodSubjectGrade",
                            institution_id=str(institution_id),
                            metadata={
                                "student_id": str(student_id),
                                "subject_id": str(subject_id),
                                "previous_final_score": str(grade_record.final_score),
                                "new_final_score": str(final_score),
                                "adjustment_reason": adjustment_reason,
                            },
                        )
                    )

                grade_record.calculated_score = calculated_score
                grade_record.final_score = final_score
                grade_record.adjustment_reason = adjustment_reason
                grade_record.performance_level = performance_level
                grade_record.total_absences = total_absences
                grade_record.unexcused_absences = unexcused_absences
                grade_record.observations = observations
                grade_record.graded_by_teacher_id = teacher_id
                grade_record.updated_at = datetime.now(UTC)
            else:
                grade_record = PeriodSubjectGrade(
                    institution_id=institution_id,
                    academic_period_id=period_id,
                    enrollment_id=enrollment_id,
                    student_id=student_id,
                    subject_id=subject_id,
                    academic_assignment_id=assignment.id if assignment else None,
                    calculated_score=calculated_score,
                    final_score=final_score,
                    adjustment_reason=adjustment_reason,
                    performance_level=performance_level,
                    total_absences=total_absences,
                    unexcused_absences=unexcused_absences,
                    observations=observations,
                    is_locked=False,
                    graded_by_teacher_id=teacher_id,
                )
                self._session.add(grade_record)

            saved_grades.append(grade_record)

        # 5. Save Achievements if provided
        if achievements and assignment:
            del_stmt = select(AcademicAchievement).where(
                AcademicAchievement.institution_id == institution_id,
                AcademicAchievement.academic_period_id == period_id,
                AcademicAchievement.academic_assignment_id == assignment.id,
            )
            for old_ach in (await self._session.execute(del_stmt)).scalars().all():
                await self._session.delete(old_ach)

            for ach_item in achievements:
                ach_level = PerformanceLevelEnum(ach_item.get("performance_level", "BASICO"))
                ach = AcademicAchievement(
                    institution_id=institution_id,
                    academic_assignment_id=assignment.id,
                    academic_period_id=period_id,
                    code=ach_item.get("code"),
                    description=ach_item["description"],
                    performance_level=ach_level,
                )
                self._session.add(ach)

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.PERIOD_GRADES_CONSOLIDATED,
                actor_id=str(user_id) if user_id else None,
                actor_ip="127.0.0.1",
                target_id=str(period_id),
                target_type="AcademicPeriod",
                institution_id=str(institution_id),
                metadata={
                    "group_id": str(group_id),
                    "subject_id": str(subject_id),
                    "student_count": len(saved_grades),
                },
            )
        )

        return saved_grades

    # =======================================================================
    # 3. Remediation & Recovery Grades (Nivelaciones)
    # =======================================================================

    async def record_recovery_grade(
        self,
        institution_id: uuid.UUID,
        grade_id: uuid.UUID,
        recovery_score: Decimal | float | int,
        recovery_date: date,
        act_number: str | None,
        observations: str | None,
        teacher_id: uuid.UUID,
        user_id: uuid.UUID,
        is_directive: bool = False,
    ) -> RecoveryGrade:
        """
        Record a remedial / recovery grade.
        Enforces:
          - Preserving initial failing grade inmutable
          - Applying configured SIEE recovery cap: min(recovery_score, recovery_grade_cap)
          - Updating period grade final score with the adjusted recovery
          - Full audit logging
        """
        # 1. Fetch Period Grade
        grade_stmt = (
            select(PeriodSubjectGrade)
            .where(PeriodSubjectGrade.id == grade_id)
            .options(selectinload(PeriodSubjectGrade.academic_period))
        )
        grade = (await self._session.execute(grade_stmt)).scalars().first()
        if not grade or grade.institution_id != institution_id:
            raise CrossTenantMismatchError("La calificación de período no pertenece a la institución.")

        # 2. Enforce Teacher Scope
        if not is_directive:
            teacher_stmt = select(Teacher).where(Teacher.id == teacher_id)
            teacher = (await self._session.execute(teacher_stmt)).scalars().first()
            if not teacher or teacher.institution_id != institution_id:
                raise CrossTenantMismatchError("Docente no válido para esta institución.")

            # Validate assignment
            assignment_stmt = select(AcademicAssignment).where(
                AcademicAssignment.academic_year_id == grade.academic_period.academic_year_id,
                AcademicAssignment.subject_id == grade.subject_id,
                AcademicAssignment.teacher_id == teacher_id,
                AcademicAssignment.is_active.is_(True),
            )
            assignment = (await self._session.execute(assignment_stmt)).scalars().first()
            if not assignment:
                raise TeacherScopeViolationError("El docente no tiene asignación para asentar esta recuperación.")

        # 3. Resolve SIEE Policy & Recovery Cap
        policy = await self._siee_service.get_or_create_default_policy(
            institution_id=institution_id,
            academic_year_id=grade.academic_period.academic_year_id,
        )

        initial_score = grade.final_score
        recovery_score_dec = Decimal(str(recovery_score))
        applied_cap = policy.recovery_grade_cap
        final_adjusted_score = min(recovery_score_dec, applied_cap)

        # 4. Create Recovery Record
        recovery = RecoveryGrade(
            period_subject_grade_id=grade.id,
            initial_score=initial_score,
            recovery_score=recovery_score_dec,
            applied_cap=applied_cap,
            final_adjusted_score=final_adjusted_score,
            teacher_id=teacher_id,
            act_number=act_number,
            recovery_date=recovery_date,
            observations=observations,
        )
        self._session.add(recovery)

        # 5. Update Grade Record with Adjusted Score & New Performance Level
        grade.final_score = final_adjusted_score
        grade.performance_level = self._siee_service.map_score_to_performance_level(
            final_adjusted_score,
            policy,
        )
        grade.updated_at = datetime.now(UTC)

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RECOVERY_GRADE_RECORDED,
                actor_id=str(user_id) if user_id else None,
                actor_ip="127.0.0.1",
                target_id=str(recovery.id),
                target_type="RecoveryGrade",
                institution_id=str(institution_id),
                metadata={
                    "period_subject_grade_id": str(grade.id),
                    "initial_score": str(initial_score),
                    "recovery_score": str(recovery_score_dec),
                    "applied_cap": str(applied_cap),
                    "final_adjusted_score": str(final_adjusted_score),
                    "act_number": act_number,
                },
            )
        )

        return recovery

    # =======================================================================
    # 4. Period Closure & Reopening Workflows
    # =======================================================================

    async def close_period(
        self,
        institution_id: uuid.UUID,
        period_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> AcademicPeriod:
        """
        Officially close an academic period and seal all grades immutably.
        """
        period_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.id == period_id)
            .options(selectinload(AcademicPeriod.academic_year))
        )
        period = (await self._session.execute(period_stmt)).scalars().first()
        if not period or period.academic_year.institution_id != institution_id:
            raise CrossTenantMismatchError("El período no pertenece a la institución educativa.")

        if period.is_closed:
            return period

        # 1. Mark period as closed
        period.is_closed = True

        # 2. Lock all consolidated grade rows in this period
        lock_stmt = (
            update(PeriodSubjectGrade)
            .where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.academic_period_id == period_id,
            )
            .values(is_locked=True, updated_at=datetime.now(UTC))
        )
        await self._session.execute(lock_stmt)
        await self._session.flush()

        # 3. Audit Closure
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.PERIOD_CLOSED,
                actor_id=str(user_id) if user_id else None,
                actor_ip="127.0.0.1",
                target_id=str(period.id),
                target_type="AcademicPeriod",
                institution_id=str(institution_id),
                metadata={
                    "period_number": period.period_number,
                    "name": period.name,
                    "academic_year_id": str(period.academic_year_id),
                },
            )
        )

        return period

    async def unlock_period(
        self,
        institution_id: uuid.UUID,
        period_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str,
    ) -> AcademicPeriod:
        """
        Reopen an officially closed academic period with audited administrative authorization.
        """
        if not reason or not reason.strip():
            raise ValueError("Se requiere una justificación formal para reabrir un período cerrado.")

        period_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.id == period_id)
            .options(selectinload(AcademicPeriod.academic_year))
        )
        period = (await self._session.execute(period_stmt)).scalars().first()
        if not period or period.academic_year.institution_id != institution_id:
            raise CrossTenantMismatchError("El período no pertenece a la institución educativa.")

        # 1. Mark period as open
        period.is_closed = False

        # 2. Unlock grade rows
        unlock_stmt = (
            update(PeriodSubjectGrade)
            .where(
                PeriodSubjectGrade.institution_id == institution_id,
                PeriodSubjectGrade.academic_period_id == period_id,
            )
            .values(is_locked=False, updated_at=datetime.now(UTC))
        )
        await self._session.execute(unlock_stmt)
        await self._session.flush()

        # 3. Audit Unlock
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.PERIOD_UNLOCKED,
                actor_id=str(user_id) if user_id else None,
                actor_ip="127.0.0.1",
                target_id=str(period.id),
                target_type="AcademicPeriod",
                institution_id=str(institution_id),
                metadata={
                    "period_number": period.period_number,
                    "reason": reason,
                    "academic_year_id": str(period.academic_year_id),
                },
            )
        )

        return period
