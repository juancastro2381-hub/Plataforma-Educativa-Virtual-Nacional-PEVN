"""
PEVN Backend — Teacher Portal Domain Service

Authoritative business logic for the dedicated Teacher Portal:
- Server-side academic assignment validation (Single Source of Truth)
- Dashboard KPIs and workload metrics
- Assigned groups, subjects, and student roster discovery
- Academic activity creation and publication lifecycle
- Student grade recording, score validation, and feedback
- Daily student attendance logging
- Curricular lesson planning
- Multi-tenant boundary and anti-IDOR/BOLA security enforcement
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    GroupNotFoundError,
    TeacherNotFoundError,
)
from app.core.logging import get_logger
from app.models.academic_activity import (
    AcademicActivity,
    AcademicPlan,
    AcademicPlanStatus,
    ActivityGrade,
    ActivityStatus,
    ActivitySubmissionStatus,
    ActivityType,
    AttendanceStatusEnum,
    DailyAttendance,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicYear, AcademicYearStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.group import Group
from app.models.institution import Campus, Institution
from app.models.student import Student
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.teacher_portal import (
    AcademicActivityCreateRequest,
    AcademicActivityResponse,
    AcademicActivityUpdateRequest,
    AcademicPlanCreateRequest,
    AcademicPlanResponse,
    AcademicPlanUpdateRequest,
    ActivityGradeBatchUpdateRequest,
    ActivityGradeItemResponse,
    ActivityGradesListResponse,
    DailyAttendanceBatchRequest,
    DailyAttendanceListResponse,
    DailyAttendanceStudentItem,
    TeacherAssignmentItemResponse,
    TeacherAssignmentsListResponse,
    TeacherDashboardSummaryResponse,
    TeacherGroupItemResponse,
    TeacherGroupRosterResponse,
    TeacherGroupsListResponse,
    TeacherStudentRosterItem,
)

_logger = get_logger(__name__)


class TeacherPortalService:
    """
    Authoritative domain service for teacher-scoped academic operations.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    # =======================================================================
    # Profile & Assignment Security Checks
    # =======================================================================

    async def get_teacher_profile(
        self,
        user_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> Teacher:
        """
        Resolve the authenticated Teacher profile 1:1 linked to the current User and Institution.
        """
        stmt = (
            select(Teacher)
            .options(
                selectinload(Teacher.user),
                selectinload(Teacher.institution),
            )
            .where(
                Teacher.user_id == user_id,
                Teacher.institution_id == institution_id,
            )
        )
        teacher = (await self._session.execute(stmt)).scalar_one_or_none()
        if not teacher:
            raise TeacherNotFoundError(
                "No se encontró un perfil docente vinculado a su cuenta institucional."
            )
        return teacher

    async def _assert_active_assignment(
        self,
        teacher: Teacher,
        *,
        group_id: uuid.UUID,
        subject_id: uuid.UUID | None = None,
        academic_year_id: uuid.UUID | None = None,
    ) -> AcademicAssignment:
        """
        Strict server-side validation: verifies that the teacher has an active workload
        allocation for the specified group (and optionally subject/year).
        Prevents BOLA/IDOR vulnerabilities.
        """
        stmt = select(AcademicAssignment).where(
            AcademicAssignment.teacher_id == teacher.id,
            AcademicAssignment.group_id == group_id,
            AcademicAssignment.is_active == True,  # noqa: E712
        )
        if subject_id:
            stmt = stmt.where(AcademicAssignment.subject_id == subject_id)
        if academic_year_id:
            stmt = stmt.where(AcademicAssignment.academic_year_id == academic_year_id)

        assignment = (await self._session.execute(stmt)).scalar_one_or_none()
        if not assignment:
            raise AcademicDomainError(
                "Acceso denegado: El docente no tiene una asignación académica activa "
                "para el grupo y materia solicitados."
            )
        return assignment

    # =======================================================================
    # 1. Dashboard Summary
    # =======================================================================

    async def get_dashboard_summary(
        self,
        teacher: Teacher,
    ) -> TeacherDashboardSummaryResponse:
        """
        Fetch aggregated operational KPI metrics for the teacher's home workspace.
        """
        # Active Academic Year
        ay_stmt = (
            select(AcademicYear)
            .where(
                AcademicYear.institution_id == teacher.institution_id,
                AcademicYear.status == AcademicYearStatus.ACTIVE,
            )
            .order_by(AcademicYear.year.desc())
        )
        active_ay = (await self._session.execute(ay_stmt)).scalar_one_or_none()

        # Active Assignments
        asg_stmt = (
            select(AcademicAssignment)
            .where(
                AcademicAssignment.teacher_id == teacher.id,
                AcademicAssignment.is_active == True,  # noqa: E712
            )
        )
        assignments = (await self._session.execute(asg_stmt)).scalars().all()
        total_assignments = len(assignments)

        assigned_group_ids = list({a.group_id for a in assignments})
        assigned_subject_ids = list({a.subject_id for a in assignments})

        # Total Enrolled Students across teacher's groups
        total_students = 0
        if assigned_group_ids and active_ay:
            st_count_stmt = (
                select(func.count(func.distinct(Enrollment.student_id)))
                .where(
                    Enrollment.group_id.in_(assigned_group_ids),
                    Enrollment.academic_year_id == active_ay.id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
            total_students = (await self._session.execute(st_count_stmt)).scalar() or 0

        # Total Active Activities
        act_stmt = (
            select(func.count(AcademicActivity.id))
            .where(
                AcademicActivity.teacher_id == teacher.id,
                AcademicActivity.status == ActivityStatus.PUBLISHED,
            )
        )
        total_active_activities = (await self._session.execute(act_stmt)).scalar() or 0

        # Total Pending Grades
        pending_grades_stmt = (
            select(func.count(ActivityGrade.id))
            .join(AcademicActivity, ActivityGrade.activity_id == AcademicActivity.id)
            .where(
                AcademicActivity.teacher_id == teacher.id,
                ActivityGrade.status == ActivitySubmissionStatus.PENDING,
            )
        )
        total_pending_grades = (await self._session.execute(pending_grades_stmt)).scalar() or 0

        user_name = f"{teacher.user.first_name} {teacher.user.last_name}" if teacher.user else "Docente"
        inst_name = teacher.institution.name if teacher.institution else "Institución"

        return TeacherDashboardSummaryResponse(
            teacher_id=teacher.id,
            teacher_name=user_name,
            specialty_area=teacher.specialty_area,
            institution_id=teacher.institution_id,
            institution_name=inst_name,
            active_academic_year=active_ay.name if active_ay else None,
            total_active_assignments=total_assignments,
            total_assigned_groups=len(assigned_group_ids),
            total_assigned_subjects=len(assigned_subject_ids),
            total_active_activities=total_active_activities,
            total_pending_grades=total_pending_grades,
            total_enrolled_students=total_students,
        )

    # =======================================================================
    # 2. My Academic Load
    # =======================================================================

    async def list_teacher_assignments(
        self,
        teacher: Teacher,
        is_active: bool = True,
    ) -> TeacherAssignmentsListResponse:
        """
        List all academic assignments belonging to the authenticated teacher with resolved human-readable names.
        """
        stmt = (
            select(AcademicAssignment)
            .options(
                selectinload(AcademicAssignment.subject).selectinload(Subject.knowledge_area),
                selectinload(AcademicAssignment.group).selectinload(Group.campus),
                selectinload(AcademicAssignment.group).selectinload(Group.grade),
                selectinload(AcademicAssignment.academic_year),
            )
            .where(
                AcademicAssignment.teacher_id == teacher.id,
                AcademicAssignment.is_active == is_active,
            )
            .order_by(AcademicAssignment.created_at.desc())
        )
        records = (await self._session.execute(stmt)).scalars().all()

        items = [
            TeacherAssignmentItemResponse(
                id=a.id,
                teacher_id=a.teacher_id,
                subject_id=a.subject_id,
                subject_name=a.subject.name if a.subject else "Materia",
                knowledge_area_name=a.subject.knowledge_area.name if a.subject and a.subject.knowledge_area else None,
                group_id=a.group_id,
                group_name=a.group.name if a.group else "Grupo",
                grade_name=a.group.grade.name if a.group and a.group.grade else None,
                campus_name=a.group.campus.name if a.group and a.group.campus else None,
                shift=a.group.shift if a.group else None,
                academic_year_id=a.academic_year_id,
                academic_year_name=a.academic_year.name if a.academic_year else str(a.academic_year_id),
                weekly_hours=a.weekly_hours,
                is_active=a.is_active,
            )
            for a in records
        ]
        return TeacherAssignmentsListResponse(items=items, total=len(items))

    # =======================================================================
    # 3. My Groups & Student Rosters
    # =======================================================================

    async def list_teacher_groups(
        self,
        teacher: Teacher,
    ) -> TeacherGroupsListResponse:
        """
        List unique groups where the teacher has active assignments, enriched with enrolled student counts.
        """
        stmt = (
            select(AcademicAssignment)
            .options(
                selectinload(AcademicAssignment.group).selectinload(Group.campus),
                selectinload(AcademicAssignment.group).selectinload(Group.grade),
                selectinload(AcademicAssignment.academic_year),
                selectinload(AcademicAssignment.subject),
            )
            .where(
                AcademicAssignment.teacher_id == teacher.id,
                AcademicAssignment.is_active == True,  # noqa: E712
            )
        )
        assignments = (await self._session.execute(stmt)).scalars().all()

        # Group by Group ID
        groups_map: dict[uuid.UUID, dict] = {}
        for a in assignments:
            if not a.group:
                continue
            gid = a.group.id
            if gid not in groups_map:
                groups_map[gid] = {
                    "group": a.group,
                    "academic_year": a.academic_year,
                    "subjects": set(),
                }
            if a.subject:
                groups_map[gid]["subjects"].add(a.subject.name)

        items: list[TeacherGroupItemResponse] = []
        for gid, data in groups_map.items():
            grp: Group = data["group"]
            ay: AcademicYear = data["academic_year"]

            # Count active enrollments
            cnt_stmt = select(func.count(Enrollment.id)).where(
                Enrollment.group_id == grp.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            active_count = (await self._session.execute(cnt_stmt)).scalar() or 0

            items.append(
                TeacherGroupItemResponse(
                    group_id=grp.id,
                    group_name=grp.name,
                    grade_name=grp.grade.name if grp.grade else None,
                    campus_name=grp.campus.name if grp.campus else None,
                    shift=grp.shift,
                    academic_year_id=ay.id if ay else grp.academic_year_id,
                    academic_year_name=ay.name if ay else "Año Lectivo",
                    capacity_limit=grp.capacity_limit,
                    active_enrolled_count=active_count,
                    subjects_taught=sorted(list(data["subjects"])),
                )
            )

        items.sort(key=lambda x: x.group_name)
        return TeacherGroupsListResponse(items=items, total=len(items))

    async def get_group_roster(
        self,
        teacher: Teacher,
        group_id: uuid.UUID,
    ) -> TeacherGroupRosterResponse:
        """
        Get the student roster for an assigned group.
        Server-side validation: rejects request if teacher has no active assignment for this group.
        """
        await self._assert_active_assignment(teacher, group_id=group_id)

        grp_stmt = (
            select(Group)
            .options(
                selectinload(Group.campus),
                selectinload(Group.grade),
                selectinload(Group.academic_year),
            )
            .where(Group.id == group_id)
        )
        group = (await self._session.execute(grp_stmt)).scalar_one_or_none()
        if not group:
            raise GroupNotFoundError(f"Grupo {group_id} no encontrado.")

        # Enrolled Students
        enr_stmt = (
            select(Enrollment)
            .options(
                selectinload(Enrollment.student).selectinload(Student.user),
            )
            .where(
                Enrollment.group_id == group_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            .order_by(Enrollment.student_id)
        )
        enrollments = (await self._session.execute(enr_stmt)).scalars().all()

        students: list[TeacherStudentRosterItem] = []
        for enr in enrollments:
            st: Student = enr.student
            u: User | None = st.user if st else None
            fn = u.first_name if u else "Estudiante"
            ln = u.last_name if u else ""
            students.append(
                TeacherStudentRosterItem(
                    student_id=st.id,
                    enrollment_id=enr.id,
                    first_name=fn,
                    last_name=ln,
                    full_name=f"{fn} {ln}".strip(),
                    document_type=u.document_type.value if u and u.document_type else "TI",
                    document_number=u.document_number if u else "",
                    simat_code=st.code_simat,
                    enrollment_status=enr.status.value,
                    enrollment_date=enr.enrollment_date,
                )
            )

        students.sort(key=lambda s: (s.last_name, s.first_name))

        return TeacherGroupRosterResponse(
            group_id=group.id,
            group_name=group.name,
            academic_year_id=group.academic_year_id,
            academic_year_name=group.academic_year.name if group.academic_year else "Año Lectivo",
            campus_name=group.campus.name if group.campus else None,
            shift=group.shift.value if group.shift else None,
            total_students=len(students),
            students=students,
        )

    # =======================================================================
    # 4. Academic Activities
    # =======================================================================

    async def list_activities(
        self,
        teacher: Teacher,
        *,
        group_id: uuid.UUID | None = None,
        subject_id: uuid.UUID | None = None,
        status: ActivityStatus | None = None,
    ) -> list[AcademicActivity]:
        """
        List academic activities created by the teacher, optionally filtered.
        """
        stmt = (
            select(AcademicActivity)
            .options(
                selectinload(AcademicActivity.subject),
                selectinload(AcademicActivity.group),
                selectinload(AcademicActivity.academic_year),
                selectinload(AcademicActivity.teacher).selectinload(Teacher.user),
                selectinload(AcademicActivity.grades),
            )
            .where(
                AcademicActivity.teacher_id == teacher.id,
                AcademicActivity.institution_id == teacher.institution_id,
            )
        )
        if group_id:
            stmt = stmt.where(AcademicActivity.group_id == group_id)
        if subject_id:
            stmt = stmt.where(AcademicActivity.subject_id == subject_id)
        if status:
            stmt = stmt.where(AcademicActivity.status == status)

        stmt = stmt.order_by(AcademicActivity.created_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_activity(
        self,
        teacher: Teacher,
        activity_id: uuid.UUID,
    ) -> AcademicActivity:
        """
        Get activity details ensuring teacher ownership.
        """
        stmt = (
            select(AcademicActivity)
            .options(
                selectinload(AcademicActivity.subject),
                selectinload(AcademicActivity.group),
                selectinload(AcademicActivity.academic_year),
                selectinload(AcademicActivity.teacher).selectinload(Teacher.user),
                selectinload(AcademicActivity.grades),
            )
            .where(
                AcademicActivity.id == activity_id,
                AcademicActivity.teacher_id == teacher.id,
                AcademicActivity.institution_id == teacher.institution_id,
            )
        )
        activity = (await self._session.execute(stmt)).scalar_one_or_none()
        if not activity:
            raise AcademicDomainError("Actividad no encontrada o no pertenece al docente.")
        return activity

    async def create_activity(
        self,
        teacher: Teacher,
        data: AcademicActivityCreateRequest,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> AcademicActivity:
        """
        Create a new academic activity.
        Server-side validation: verifies that teacher has an ACTIVE assignment for (subject, group, year).
        """
        assignment = await self._assert_active_assignment(
            teacher,
            group_id=data.group_id,
            subject_id=data.subject_id,
            academic_year_id=data.academic_year_id,
        )

        activity = AcademicActivity(
            institution_id=teacher.institution_id,
            teacher_id=teacher.id,
            academic_assignment_id=assignment.id,
            subject_id=data.subject_id,
            group_id=data.group_id,
            academic_year_id=data.academic_year_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            activity_type=data.activity_type,
            status=ActivityStatus.DRAFT,
            due_date=data.due_date,
            max_score=data.max_score,
            instructions=data.instructions.strip() if data.instructions else None,
            resource_url=data.resource_url.strip() if data.resource_url else None,
        )
        self._session.add(activity)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACTIVITY_CREATED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(activity.id),
                target_type="AcademicActivity",
                institution_id=str(teacher.institution_id),
                metadata={
                    "title": activity.title,
                    "group_id": str(activity.group_id),
                    "subject_id": str(activity.subject_id),
                },
            )
        )
        return await self.get_activity(teacher, activity.id)

    async def update_activity(
        self,
        teacher: Teacher,
        activity_id: uuid.UUID,
        data: AcademicActivityUpdateRequest,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> AcademicActivity:
        """
        Update activity fields.
        """
        activity = await self.get_activity(teacher, activity_id)

        if data.title is not None:
            activity.title = data.title.strip()
        if data.description is not None:
            activity.description = data.description.strip() if data.description else None
        if data.activity_type is not None:
            activity.activity_type = data.activity_type
        if data.due_date is not None:
            activity.due_date = data.due_date
        if data.max_score is not None:
            activity.max_score = data.max_score
        if data.instructions is not None:
            activity.instructions = data.instructions.strip() if data.instructions else None
        if data.resource_url is not None:
            activity.resource_url = data.resource_url.strip() if data.resource_url else None

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACTIVITY_UPDATED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(activity.id),
                target_type="AcademicActivity",
                institution_id=str(teacher.institution_id),
                metadata={"title": activity.title},
            )
        )
        return await self.get_activity(teacher, activity.id)

    async def publish_activity(
        self,
        teacher: Teacher,
        activity_id: uuid.UUID,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> AcademicActivity:
        """
        Publish an activity and seed evaluation grade slots for all active students in the group.
        """
        activity = await self.get_activity(teacher, activity_id)
        activity.status = ActivityStatus.PUBLISHED
        activity.publication_date = datetime.now(UTC)

        # Seed ActivityGrade entries for all active students in group if not already present
        enr_stmt = select(Enrollment.student_id).where(
            Enrollment.group_id == activity.group_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        student_ids = (await self._session.execute(enr_stmt)).scalars().all()

        for sid in student_ids:
            grade_exists = (
                await self._session.execute(
                    select(ActivityGrade).where(
                        ActivityGrade.activity_id == activity.id,
                        ActivityGrade.student_id == sid,
                    )
                )
            ).scalar_one_or_none()
            if not grade_exists:
                self._session.add(
                    ActivityGrade(
                        activity_id=activity.id,
                        student_id=sid,
                        status=ActivitySubmissionStatus.PENDING,
                    )
                )

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACTIVITY_PUBLISHED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(activity.id),
                target_type="AcademicActivity",
                institution_id=str(teacher.institution_id),
                metadata={"title": activity.title, "seeded_students_count": len(student_ids)},
            )
        )
        return await self.get_activity(teacher, activity.id)

    async def close_activity(
        self,
        teacher: Teacher,
        activity_id: uuid.UUID,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> AcademicActivity:
        """
        Close an academic activity.
        """
        activity = await self.get_activity(teacher, activity_id)
        activity.status = ActivityStatus.CLOSED
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACTIVITY_CLOSED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(activity.id),
                target_type="AcademicActivity",
                institution_id=str(teacher.institution_id),
                metadata={"title": activity.title},
            )
        )
        return await self.get_activity(teacher, activity.id)

    async def delete_activity(
        self,
        teacher: Teacher,
        activity_id: uuid.UUID,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> None:
        """
        Delete an academic activity.
        """
        activity = await self.get_activity(teacher, activity_id)
        await self._session.delete(activity)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACTIVITY_DELETED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(activity_id),
                target_type="AcademicActivity",
                institution_id=str(teacher.institution_id),
                metadata={"title": activity.title},
            )
        )

    # =======================================================================
    # 5. Activity Grades & Evaluations
    # =======================================================================

    async def list_activity_grades(
        self,
        teacher: Teacher,
        activity_id: uuid.UUID,
    ) -> ActivityGradesListResponse:
        """
        List gradesheet for an activity. Ensures activity is owned by the teacher.
        """
        activity = await self.get_activity(teacher, activity_id)

        stmt = (
            select(ActivityGrade)
            .options(
                selectinload(ActivityGrade.student).selectinload(Student.user),
            )
            .where(ActivityGrade.activity_id == activity.id)
            .order_by(ActivityGrade.created_at)
        )
        records = (await self._session.execute(stmt)).scalars().all()

        items: list[ActivityGradeItemResponse] = []
        for g in records:
            st: Student = g.student
            u: User | None = st.user if st else None
            s_name = f"{u.first_name} {u.last_name}" if u else "Estudiante"
            s_doc = f"{u.document_type.value if u and u.document_type else 'TI'}: {u.document_number if u else ''}"
            items.append(
                ActivityGradeItemResponse(
                    id=g.id,
                    activity_id=g.activity_id,
                    student_id=g.student_id,
                    student_name=s_name,
                    student_document=s_doc,
                    score=g.score,
                    feedback=g.feedback,
                    status=g.status,
                    graded_at=g.graded_at,
                )
            )

        items.sort(key=lambda x: x.student_name)

        return ActivityGradesListResponse(
            activity_id=activity.id,
            activity_title=activity.title,
            group_name=activity.group.name if activity.group else "Grupo",
            subject_name=activity.subject.name if activity.subject else "Materia",
            max_score=activity.max_score,
            items=items,
            total=len(items),
        )

    async def batch_grade_activity(
        self,
        teacher: Teacher,
        activity_id: uuid.UUID,
        data: ActivityGradeBatchUpdateRequest,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> ActivityGradesListResponse:
        """
        Batch update grades and feedback for students in an activity.
        Enforces score limits (0 <= score <= max_score).
        """
        activity = await self.get_activity(teacher, activity_id)

        # Enrolled student IDs in this group
        enr_stmt = select(Enrollment.student_id).where(
            Enrollment.group_id == activity.group_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        enrolled_ids = set((await self._session.execute(enr_stmt)).scalars().all())

        now_utc = datetime.now(UTC)

        for entry in data.grades:
            if entry.student_id not in enrolled_ids:
                raise AcademicDomainError(
                    f"El estudiante {entry.student_id} no está matriculado activamente en el grupo de esta actividad."
                )

            if entry.score is not None:
                if entry.score < Decimal("0.00") or entry.score > activity.max_score:
                    raise AcademicDomainError(
                        f"La calificación {entry.score} excede el rango permitido (0.00 a {activity.max_score})."
                    )

            # Find or create grade record
            grade_stmt = select(ActivityGrade).where(
                ActivityGrade.activity_id == activity.id,
                ActivityGrade.student_id == entry.student_id,
            )
            grade = (await self._session.execute(grade_stmt)).scalar_one_or_none()

            if not grade:
                grade = ActivityGrade(
                    activity_id=activity.id,
                    student_id=entry.student_id,
                )
                self._session.add(grade)

            grade.score = entry.score
            grade.feedback = entry.feedback.strip() if entry.feedback else None
            grade.status = ActivitySubmissionStatus.GRADED if entry.score is not None else ActivitySubmissionStatus.PENDING
            grade.graded_by_teacher_id = teacher.id
            grade.graded_at = now_utc

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GRADE_UPDATED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(activity.id),
                target_type="ActivityGradeBatch",
                institution_id=str(teacher.institution_id),
                metadata={"updated_count": len(data.grades), "activity_title": activity.title},
            )
        )
        return await self.list_activity_grades(teacher, activity.id)

    # =======================================================================
    # 6. Daily Classroom Attendance
    # =======================================================================

    async def list_daily_attendance(
        self,
        teacher: Teacher,
        group_id: uuid.UUID,
        attendance_date: date,
        subject_id: uuid.UUID | None = None,
    ) -> DailyAttendanceListResponse:
        """
        List attendance sheet for a group and date.
        """
        await self._assert_active_assignment(teacher, group_id=group_id, subject_id=subject_id)

        grp_stmt = select(Group).where(Group.id == group_id)
        group = (await self._session.execute(grp_stmt)).scalar_one_or_none()
        if not group:
            raise GroupNotFoundError(f"Grupo {group_id} no encontrado.")

        sub_name: str | None = None
        if subject_id:
            s_stmt = select(Subject.name).where(Subject.id == subject_id)
            sub_name = (await self._session.execute(s_stmt)).scalar_one_or_none()

        # Enrolled Students
        enr_stmt = (
            select(Enrollment)
            .options(selectinload(Enrollment.student).selectinload(Student.user))
            .where(
                Enrollment.group_id == group_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        enrollments = (await self._session.execute(enr_stmt)).scalars().all()

        # Existing Attendance Records for this session
        att_stmt = select(DailyAttendance).where(
            DailyAttendance.group_id == group_id,
            DailyAttendance.attendance_date == attendance_date,
        )
        if subject_id:
            att_stmt = att_stmt.where(DailyAttendance.subject_id == subject_id)

        records = (await self._session.execute(att_stmt)).scalars().all()
        att_map = {r.student_id: r for r in records}

        items: list[DailyAttendanceStudentItem] = []
        for enr in enrollments:
            st: Student = enr.student
            u: User | None = st.user if st else None
            s_name = f"{u.first_name} {u.last_name}" if u else "Estudiante"
            s_doc = u.document_number if u else ""
            rec = att_map.get(st.id)

            items.append(
                DailyAttendanceStudentItem(
                    student_id=st.id,
                    student_name=s_name,
                    document_number=s_doc,
                    status=rec.status if rec else AttendanceStatusEnum.PRESENT,
                    remarks=rec.remarks if rec else None,
                )
            )

        items.sort(key=lambda x: x.student_name)

        return DailyAttendanceListResponse(
            group_id=group.id,
            group_name=group.name,
            subject_id=subject_id,
            subject_name=sub_name,
            attendance_date=attendance_date,
            total_students=len(items),
            items=items,
        )

    async def record_daily_attendance(
        self,
        teacher: Teacher,
        group_id: uuid.UUID,
        data: DailyAttendanceBatchRequest,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> DailyAttendanceListResponse:
        """
        Record or update daily student attendance sheet.
        """
        assignment = await self._assert_active_assignment(
            teacher,
            group_id=group_id,
            subject_id=data.subject_id,
        )

        for entry in data.records:
            # Query existing
            stmt = select(DailyAttendance).where(
                DailyAttendance.group_id == group_id,
                DailyAttendance.student_id == entry.student_id,
                DailyAttendance.attendance_date == data.attendance_date,
            )
            if data.subject_id:
                stmt = stmt.where(DailyAttendance.subject_id == data.subject_id)

            rec = (await self._session.execute(stmt)).scalar_one_or_none()
            if rec:
                rec.status = entry.status
                rec.remarks = entry.remarks.strip() if entry.remarks else None
                rec.teacher_id = teacher.id
            else:
                self._session.add(
                    DailyAttendance(
                        institution_id=teacher.institution_id,
                        group_id=group_id,
                        academic_year_id=assignment.academic_year_id,
                        subject_id=data.subject_id,
                        teacher_id=teacher.id,
                        student_id=entry.student_id,
                        attendance_date=data.attendance_date,
                        status=entry.status,
                        remarks=entry.remarks.strip() if entry.remarks else None,
                    )
                )

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ATTENDANCE_RECORDED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(group_id),
                target_type="DailyAttendanceBatch",
                institution_id=str(teacher.institution_id),
                metadata={
                    "date": str(data.attendance_date),
                    "records_count": len(data.records),
                },
            )
        )
        return await self.list_daily_attendance(
            teacher,
            group_id=group_id,
            attendance_date=data.attendance_date,
            subject_id=data.subject_id,
        )

    # =======================================================================
    # 7. Curricular Planning
    # =======================================================================

    async def list_academic_plans(
        self,
        teacher: Teacher,
        *,
        group_id: uuid.UUID | None = None,
        subject_id: uuid.UUID | None = None,
    ) -> list[AcademicPlan]:
        """
        List lesson plans created by the teacher.
        """
        stmt = (
            select(AcademicPlan)
            .options(
                selectinload(AcademicPlan.subject),
                selectinload(AcademicPlan.group),
                selectinload(AcademicPlan.academic_year),
                selectinload(AcademicPlan.teacher).selectinload(Teacher.user),
            )
            .where(
                AcademicPlan.teacher_id == teacher.id,
                AcademicPlan.institution_id == teacher.institution_id,
            )
        )
        if group_id:
            stmt = stmt.where(AcademicPlan.group_id == group_id)
        if subject_id:
            stmt = stmt.where(AcademicPlan.subject_id == subject_id)

        stmt = stmt.order_by(AcademicPlan.created_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_academic_plan(
        self,
        teacher: Teacher,
        data: AcademicPlanCreateRequest,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> AcademicPlan:
        """
        Create a new curricular unit lesson plan.
        """
        assignment = await self._assert_active_assignment(
            teacher,
            group_id=data.group_id,
            subject_id=data.subject_id,
            academic_year_id=data.academic_year_id,
        )

        plan = AcademicPlan(
            institution_id=teacher.institution_id,
            teacher_id=teacher.id,
            academic_assignment_id=assignment.id,
            subject_id=data.subject_id,
            group_id=data.group_id,
            academic_year_id=data.academic_year_id,
            unit_name=data.unit_name.strip(),
            competencies=data.competencies.strip() if data.competencies else None,
            learning_objectives=data.learning_objectives.strip() if data.learning_objectives else None,
            methodology=data.methodology.strip() if data.methodology else None,
            evaluation_criteria=data.evaluation_criteria.strip() if data.evaluation_criteria else None,
            resources=data.resources.strip() if data.resources else None,
            status=data.status,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        self._session.add(plan)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.PLAN_CREATED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(plan.id),
                target_type="AcademicPlan",
                institution_id=str(teacher.institution_id),
                metadata={"unit_name": plan.unit_name},
            )
        )

        # Load relationships
        return (
            await self._session.execute(
                select(AcademicPlan)
                .options(
                    selectinload(AcademicPlan.subject),
                    selectinload(AcademicPlan.group),
                    selectinload(AcademicPlan.academic_year),
                    selectinload(AcademicPlan.teacher).selectinload(Teacher.user),
                )
                .where(AcademicPlan.id == plan.id)
            )
        ).scalar_one()

    async def update_academic_plan(
        self,
        teacher: Teacher,
        plan_id: uuid.UUID,
        data: AcademicPlanUpdateRequest,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> AcademicPlan:
        """
        Update an existing lesson plan.
        """
        stmt = (
            select(AcademicPlan)
            .options(
                selectinload(AcademicPlan.subject),
                selectinload(AcademicPlan.group),
                selectinload(AcademicPlan.academic_year),
                selectinload(AcademicPlan.teacher).selectinload(Teacher.user),
            )
            .where(
                AcademicPlan.id == plan_id,
                AcademicPlan.teacher_id == teacher.id,
                AcademicPlan.institution_id == teacher.institution_id,
            )
        )
        plan = (await self._session.execute(stmt)).scalar_one_or_none()
        if not plan:
            raise AcademicDomainError("Planeación curricular no encontrada o no pertenece al docente.")

        if data.unit_name is not None:
            plan.unit_name = data.unit_name.strip()
        if data.competencies is not None:
            plan.competencies = data.competencies.strip() if data.competencies else None
        if data.learning_objectives is not None:
            plan.learning_objectives = data.learning_objectives.strip() if data.learning_objectives else None
        if data.methodology is not None:
            plan.methodology = data.methodology.strip() if data.methodology else None
        if data.evaluation_criteria is not None:
            plan.evaluation_criteria = data.evaluation_criteria.strip() if data.evaluation_criteria else None
        if data.resources is not None:
            plan.resources = data.resources.strip() if data.resources else None
        if data.status is not None:
            plan.status = data.status
        if data.start_date is not None:
            plan.start_date = data.start_date
        if data.end_date is not None:
            plan.end_date = data.end_date

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.PLAN_UPDATED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(plan.id),
                target_type="AcademicPlan",
                institution_id=str(teacher.institution_id),
                metadata={"unit_name": plan.unit_name},
            )
        )
        return (
            await self._session.execute(
                select(AcademicPlan)
                .options(
                    selectinload(AcademicPlan.subject),
                    selectinload(AcademicPlan.group),
                    selectinload(AcademicPlan.academic_year),
                    selectinload(AcademicPlan.teacher).selectinload(Teacher.user),
                )
                .where(AcademicPlan.id == plan.id)
            )
        ).scalar_one()

    async def delete_academic_plan(
        self,
        teacher: Teacher,
        plan_id: uuid.UUID,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> None:
        """
        Delete a lesson plan.
        """
        stmt = select(AcademicPlan).where(
            AcademicPlan.id == plan_id,
            AcademicPlan.teacher_id == teacher.id,
            AcademicPlan.institution_id == teacher.institution_id,
        )
        plan = (await self._session.execute(stmt)).scalar_one_or_none()
        if not plan:
            raise AcademicDomainError("Planeación curricular no encontrada o no pertenece al docente.")

        await self._session.delete(plan)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.PLAN_DELETED,
                actor_id=actor_id or str(teacher.user_id),
                actor_ip=actor_ip,
                target_id=str(plan_id),
                target_type="AcademicPlan",
                institution_id=str(teacher.institution_id),
                metadata={"unit_name": plan.unit_name},
            )
        )
