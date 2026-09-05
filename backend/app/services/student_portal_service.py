"""
PEVN Backend — Student Portal Domain Service

Authoritative application service providing strictly-isolated, anti-IDOR,
self-service academic data for authenticated students:
- Identity and profile derivation from authenticated user context
- Consolidated dashboard metrics and alerts
- Enrolled curriculum subjects and assigned teachers
- Academic activities, homework, tasks and submissions
- Evaluated grades and qualitative teacher remarks
- Daily classroom attendance and absence metrics
- Virtual classroom sessions and recordings
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import IAuditService
from app.audit.service import audit_service
from app.core.exceptions import StudentNotFoundError
from app.core.logging import get_logger
from app.exceptions.errors import NotFoundError
from app.models.academic_activity import (
    AcademicActivity,
    ActivityGrade,
    ActivityStatus,
    ActivitySubmissionStatus,
    DailyAttendance,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.group import Group
from app.models.institution import Campus, Institution
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User
from app.models.virtual_classroom import MeetingRecording, VirtualClassroom
from app.schemas.student_portal import (
    StudentActivitiesListResponse,
    StudentActivityItemResponse,
    StudentAttendanceItemResponse,
    StudentAttendanceListResponse,
    StudentAttendanceSummary,
    StudentDashboardResponse,
    StudentGradeItemResponse,
    StudentGradesListResponse,
    StudentProfileResponse,
    StudentRecordingItemResponse,
    StudentRecordingsListResponse,
    StudentSubjectItemResponse,
    StudentSubjectsListResponse,
    StudentVirtualClassroomItemResponse,
    StudentVirtualClassroomsListResponse,
)

_logger = get_logger(__name__)


class StudentPortalService:
    """
    Application service managing Student Portal operations.
    Enforces that student identity is ALWAYS resolved from the authenticated user token.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def get_student_by_user_id(
        self,
        user_id: uuid.UUID,
        institution_id: uuid.UUID | None = None,
    ) -> Student:
        """
        Derive authenticated student domain entity strictly from current_user.id.
        Anti-IDOR: Never accepts a client-supplied student_id for self-operations.
        """
        stmt = (
            select(Student)
            .where(Student.user_id == user_id)
            .options(
                selectinload(Student.user),
                selectinload(Student.institution),
            )
        )
        if institution_id is not None:
            stmt = stmt.where(Student.institution_id == institution_id)

        student = (await self._session.execute(stmt)).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError("Perfil de estudiante no encontrado para el usuario actual.")
        return student

    async def get_active_enrollment(
        self,
        student_id: uuid.UUID,
    ) -> Enrollment | None:
        """Retrieve the current active group enrollment for the student."""
        stmt = (
            select(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            .options(
                selectinload(Enrollment.group).selectinload(Group.grade),
                selectinload(Enrollment.group).selectinload(Group.campus),
                selectinload(Enrollment.academic_year),
            )
            .order_by(Enrollment.created_at.desc())
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_profile(
        self,
        student: Student,
    ) -> StudentProfileResponse:
        """Construct the enriched student profile."""
        enrollment = await self.get_active_enrollment(student.id)

        group_name = enrollment.group.name if enrollment and enrollment.group else None
        group_id = enrollment.group.id if enrollment and enrollment.group else None
        grade_name = enrollment.group.grade.name if enrollment and enrollment.group and enrollment.group.grade else None
        campus_name = enrollment.group.campus.name if enrollment and enrollment.group and enrollment.group.campus else None
        academic_year_id = enrollment.academic_year.id if enrollment and enrollment.academic_year else None
        academic_year_name = enrollment.academic_year.name if enrollment and enrollment.academic_year else None
        enrollment_status = enrollment.status.value if enrollment else None

        return StudentProfileResponse(
            student_id=student.id,
            user_id=student.user_id,
            first_name=student.user.first_name,
            last_name=student.user.last_name,
            full_name=student.user.full_name,
            email=student.user.email,
            document_type=student.user.document_type,
            document_number=student.user.document_number,
            code_simat=student.code_simat,
            birth_date=student.birth_date,
            institution_id=student.institution_id,
            institution_name=student.institution.name,
            campus_name=campus_name,
            grade_name=grade_name,
            group_id=group_id,
            group_name=group_name,
            academic_year_id=academic_year_id,
            academic_year_name=academic_year_name,
            enrollment_status=enrollment_status,
        )

    async def list_subjects(
        self,
        student: Student,
    ) -> StudentSubjectsListResponse:
        """List all curriculum subjects for the student's active group."""
        enrollment = await self.get_active_enrollment(student.id)
        if not enrollment or not enrollment.group:
            return StudentSubjectsListResponse(items=[], total=0)

        group_id = enrollment.group.id
        grade_id = enrollment.group.grade_id

        # 1. Fetch active academic assignments for this group
        assignments_stmt = (
            select(AcademicAssignment)
            .where(
                AcademicAssignment.group_id == group_id,
                AcademicAssignment.is_active.is_(True),
            )
            .options(
                selectinload(AcademicAssignment.subject).selectinload(Subject.knowledge_area),
                selectinload(AcademicAssignment.teacher).selectinload(Teacher.user),
            )
        )
        assignments = (await self._session.execute(assignments_stmt)).scalars().all()

        items: list[StudentSubjectItemResponse] = []
        covered_subject_ids: set[uuid.UUID] = set()

        for assign in assignments:
            subj = assign.subject
            covered_subject_ids.add(subj.id)
            teacher_name = assign.teacher.user.full_name if assign.teacher and assign.teacher.user else None
            teacher_email = assign.teacher.user.email if assign.teacher and assign.teacher.user else None

            items.append(
                StudentSubjectItemResponse(
                    subject_id=subj.id,
                    name=subj.name,
                    weekly_hours=assign.weekly_hours,
                    knowledge_area_name=subj.knowledge_area.name if subj.knowledge_area else None,
                    teacher_id=assign.teacher_id,
                    teacher_name=teacher_name,
                    teacher_email=teacher_email,
                )
            )

        # 2. Add any statutory subjects for the grade not yet formally assigned to a teacher
        subjects_stmt = (
            select(Subject)
            .where(
                Subject.institution_id == student.institution_id,
                Subject.grade_id == grade_id,
                Subject.id.not_in(covered_subject_ids) if covered_subject_ids else True,
            )
            .options(selectinload(Subject.knowledge_area))
            .order_by(Subject.name.asc())
        )
        unassigned_subjects = (await self._session.execute(subjects_stmt)).scalars().all()
        for subj in unassigned_subjects:
            items.append(
                StudentSubjectItemResponse(
                    subject_id=subj.id,
                    name=subj.name,
                    weekly_hours=subj.weekly_hours,
                    knowledge_area_name=subj.knowledge_area.name if subj.knowledge_area else None,
                    teacher_id=None,
                    teacher_name=None,
                    teacher_email=None,
                )
            )

        return StudentSubjectsListResponse(items=items, total=len(items))

    async def list_activities(
        self,
        student: Student,
        *,
        subject_id: uuid.UUID | None = None,
        submission_status: str | None = None,
    ) -> StudentActivitiesListResponse:
        """
        List academic activities published for the student's active group.
        Dynamically computes student submission state (PENDING, OVERDUE, SUBMITTED, GRADED).
        """
        enrollment = await self.get_active_enrollment(student.id)
        if not enrollment or not enrollment.group:
            return StudentActivitiesListResponse(items=[], total=0)

        now = datetime.now(UTC)

        stmt = (
            select(AcademicActivity, ActivityGrade)
            .outerjoin(
                ActivityGrade,
                (ActivityGrade.activity_id == AcademicActivity.id)
                & (ActivityGrade.student_id == student.id),
            )
            .join(Subject, AcademicActivity.subject_id == Subject.id)
            .join(Teacher, AcademicActivity.teacher_id == Teacher.id)
            .join(User, Teacher.user_id == User.id)
            .where(
                AcademicActivity.group_id == enrollment.group_id,
                AcademicActivity.status == ActivityStatus.PUBLISHED,
            )
            .options(
                selectinload(AcademicActivity.subject),
                selectinload(AcademicActivity.teacher).selectinload(Teacher.user),
            )
            .order_by(AcademicActivity.due_date.asc().nulls_last())
        )

        if subject_id is not None:
            stmt = stmt.where(AcademicActivity.subject_id == subject_id)

        rows = (await self._session.execute(stmt)).all()

        items: list[StudentActivityItemResponse] = []
        for activity, grade in rows:
            # Derive student submission status
            computed_status = "PENDING"
            if grade:
                if grade.status == ActivitySubmissionStatus.GRADED:
                    computed_status = "GRADED"
                elif grade.status == ActivitySubmissionStatus.SUBMITTED:
                    computed_status = "SUBMITTED"
            
            if computed_status == "PENDING" and activity.due_date and activity.due_date < now:
                computed_status = "OVERDUE"

            # Filter if requested
            if submission_status and computed_status != submission_status.upper():
                continue

            teacher_name = activity.teacher.user.full_name if activity.teacher and activity.teacher.user else None

            items.append(
                StudentActivityItemResponse(
                    id=activity.id,
                    title=activity.title,
                    description=activity.description,
                    activity_type=activity.activity_type,
                    status=activity.status,
                    submission_status=computed_status,
                    publication_date=activity.publication_date,
                    due_date=activity.due_date,
                    max_score=activity.max_score,
                    score=grade.score if grade else None,
                    feedback=grade.feedback if grade else None,
                    graded_at=grade.graded_at if grade else None,
                    subject_id=activity.subject_id,
                    subject_name=activity.subject.name,
                    teacher_name=teacher_name,
                    instructions=activity.instructions,
                    resource_url=activity.resource_url,
                )
            )

        return StudentActivitiesListResponse(items=items, total=len(items))

    async def get_activity_detail(
        self,
        student: Student,
        activity_id: uuid.UUID,
    ) -> StudentActivityItemResponse:
        """Retrieve detailed view of an authorized academic activity."""
        enrollment = await self.get_active_enrollment(student.id)
        if not enrollment or not enrollment.group:
            raise NotFoundError("Actividad académica no encontrada o no autorizada.")

        stmt = (
            select(AcademicActivity, ActivityGrade)
            .outerjoin(
                ActivityGrade,
                (ActivityGrade.activity_id == AcademicActivity.id)
                & (ActivityGrade.student_id == student.id),
            )
            .join(Subject, AcademicActivity.subject_id == Subject.id)
            .join(Teacher, AcademicActivity.teacher_id == Teacher.id)
            .join(User, Teacher.user_id == User.id)
            .where(
                AcademicActivity.id == activity_id,
                AcademicActivity.group_id == enrollment.group_id,
                AcademicActivity.status == ActivityStatus.PUBLISHED,
            )
            .options(
                selectinload(AcademicActivity.subject),
                selectinload(AcademicActivity.teacher).selectinload(Teacher.user),
            )
        )
        row = (await self._session.execute(stmt)).first()
        if not row:
            raise NotFoundError("Actividad académica no encontrada o no autorizada.")

        activity, grade = row
        now = datetime.now(UTC)

        computed_status = "PENDING"
        if grade:
            if grade.status == ActivitySubmissionStatus.GRADED:
                computed_status = "GRADED"
            elif grade.status == ActivitySubmissionStatus.SUBMITTED:
                computed_status = "SUBMITTED"

        if computed_status == "PENDING" and activity.due_date and activity.due_date < now:
            computed_status = "OVERDUE"

        teacher_name = activity.teacher.user.full_name if activity.teacher and activity.teacher.user else None

        return StudentActivityItemResponse(
            id=activity.id,
            title=activity.title,
            description=activity.description,
            activity_type=activity.activity_type,
            status=activity.status,
            submission_status=computed_status,
            publication_date=activity.publication_date,
            due_date=activity.due_date,
            max_score=activity.max_score,
            score=grade.score if grade else None,
            feedback=grade.feedback if grade else None,
            graded_at=grade.graded_at if grade else None,
            subject_id=activity.subject_id,
            subject_name=activity.subject.name,
            teacher_name=teacher_name,
            instructions=activity.instructions,
            resource_url=activity.resource_url,
        )

    async def list_grades(
        self,
        student: Student,
        *,
        subject_id: uuid.UUID | None = None,
    ) -> StudentGradesListResponse:
        """List all evaluated grades for the student."""
        stmt = (
            select(ActivityGrade)
            .join(AcademicActivity, ActivityGrade.activity_id == AcademicActivity.id)
            .join(Subject, AcademicActivity.subject_id == Subject.id)
            .outerjoin(Teacher, ActivityGrade.graded_by_teacher_id == Teacher.id)
            .outerjoin(User, Teacher.user_id == User.id)
            .where(
                ActivityGrade.student_id == student.id,
                ActivityGrade.status == ActivitySubmissionStatus.GRADED,
            )
            .options(
                selectinload(ActivityGrade.activity).selectinload(AcademicActivity.subject),
                selectinload(ActivityGrade.graded_by).selectinload(Teacher.user),
            )
            .order_by(ActivityGrade.graded_at.desc().nulls_last())
        )

        if subject_id is not None:
            stmt = stmt.where(AcademicActivity.subject_id == subject_id)

        grades = (await self._session.execute(stmt)).scalars().all()

        items: list[StudentGradeItemResponse] = []
        total_scores = Decimal("0.00")
        score_count = 0

        for g in grades:
            activity = g.activity
            teacher_name = g.graded_by.user.full_name if g.graded_by and g.graded_by.user else None
            if g.score is not None:
                total_scores += g.score
                score_count += 1

            items.append(
                StudentGradeItemResponse(
                    grade_id=g.id,
                    activity_id=activity.id,
                    activity_title=activity.title,
                    activity_type=activity.activity_type,
                    subject_id=activity.subject_id,
                    subject_name=activity.subject.name,
                    score=g.score,
                    max_score=activity.max_score,
                    feedback=g.feedback,
                    status=g.status,
                    graded_at=g.graded_at,
                    teacher_name=teacher_name,
                )
            )

        avg = round(total_scores / Decimal(score_count), 2) if score_count > 0 else None
        return StudentGradesListResponse(items=items, total=len(items), average_score=avg)

    async def list_attendance(
        self,
        student: Student,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> StudentAttendanceListResponse:
        """List daily classroom attendance marks with breakdown metrics."""
        stmt = (
            select(DailyAttendance)
            .outerjoin(Subject, DailyAttendance.subject_id == Subject.id)
            .outerjoin(Teacher, DailyAttendance.teacher_id == Teacher.id)
            .outerjoin(User, Teacher.user_id == User.id)
            .where(DailyAttendance.student_id == student.id)
            .options(
                selectinload(DailyAttendance.subject),
                selectinload(DailyAttendance.teacher).selectinload(Teacher.user),
            )
            .order_by(DailyAttendance.attendance_date.desc())
        )

        if start_date:
            stmt = stmt.where(DailyAttendance.attendance_date >= start_date)
        if end_date:
            stmt = stmt.where(DailyAttendance.attendance_date <= end_date)

        records = (await self._session.execute(stmt)).scalars().all()

        items: list[StudentAttendanceItemResponse] = []
        present = absent = excused = late = 0

        for r in records:
            if r.status == "PRESENT":
                present += 1
            elif r.status == "ABSENT":
                absent += 1
            elif r.status == "EXCUSED":
                excused += 1
            elif r.status == "LATE":
                late += 1

            items.append(
                StudentAttendanceItemResponse(
                    id=r.id,
                    attendance_date=r.attendance_date,
                    status=r.status,
                    remarks=r.remarks,
                    subject_name=r.subject.name if r.subject else None,
                    teacher_name=r.teacher.user.full_name if r.teacher and r.teacher.user else None,
                )
            )

        total_sessions = len(records)
        rate = round(((present + late) / total_sessions) * 100, 1) if total_sessions > 0 else 100.0

        summary = StudentAttendanceSummary(
            total_sessions=total_sessions,
            present_count=present,
            absent_count=absent,
            excused_count=excused,
            late_count=late,
            attendance_rate=rate,
        )

        return StudentAttendanceListResponse(items=items, total=len(items), summary=summary)

    async def list_virtual_classrooms(
        self,
        student: Student,
    ) -> StudentVirtualClassroomsListResponse:
        """List virtual classroom sessions available to the student's active group."""
        enrollment = await self.get_active_enrollment(student.id)
        if not enrollment or not enrollment.group:
            return StudentVirtualClassroomsListResponse(items=[], total=0)

        stmt = (
            select(VirtualClassroom)
            .join(AcademicAssignment, VirtualClassroom.academic_assignment_id == AcademicAssignment.id)
            .join(Subject, AcademicAssignment.subject_id == Subject.id)
            .join(Teacher, AcademicAssignment.teacher_id == Teacher.id)
            .join(User, Teacher.user_id == User.id)
            .where(
                AcademicAssignment.group_id == enrollment.group_id,
                VirtualClassroom.status.in_(["SCHEDULED", "RUNNING", "ENDED"]),
            )
            .options(
                selectinload(VirtualClassroom.academic_assignment).selectinload(AcademicAssignment.subject),
                selectinload(VirtualClassroom.academic_assignment).selectinload(AcademicAssignment.teacher).selectinload(Teacher.user),
                selectinload(VirtualClassroom.recordings),
            )
            .order_by(VirtualClassroom.scheduled_start_time.desc().nulls_last())
        )

        classrooms = (await self._session.execute(stmt)).scalars().all()

        items: list[StudentVirtualClassroomItemResponse] = []
        for vc in classrooms:
            assign = vc.academic_assignment
            subj_name = assign.subject.name if assign and assign.subject else None
            teacher_name = assign.teacher.user.full_name if assign and assign.teacher and assign.teacher.user else None
            has_recs = len(vc.recordings) > 0 if vc.recordings else False

            items.append(
                StudentVirtualClassroomItemResponse(
                    id=vc.id,
                    title=vc.title,
                    description=vc.description,
                    status=vc.status,
                    scheduled_start_time=vc.scheduled_start_time,
                    scheduled_end_time=vc.scheduled_end_time,
                    subject_name=subj_name,
                    teacher_name=teacher_name,
                    can_join=(vc.status == "RUNNING" or vc.status == "SCHEDULED"),
                    room_name=vc.bbb_meeting_id,
                    has_recordings=has_recs,
                )
            )

        return StudentVirtualClassroomsListResponse(items=items, total=len(items))

    async def get_virtual_classroom(
        self,
        student: Student,
        classroom_id: uuid.UUID,
    ) -> StudentVirtualClassroomItemResponse:
        """Retrieve authorized virtual classroom details for attendee join."""
        enrollment = await self.get_active_enrollment(student.id)
        if not enrollment or not enrollment.group:
            raise NotFoundError("Aula virtual no encontrada o no autorizada.")

        stmt = (
            select(VirtualClassroom)
            .join(AcademicAssignment, VirtualClassroom.academic_assignment_id == AcademicAssignment.id)
            .where(
                VirtualClassroom.id == classroom_id,
                AcademicAssignment.group_id == enrollment.group_id,
            )
            .options(
                selectinload(VirtualClassroom.academic_assignment).selectinload(AcademicAssignment.subject),
                selectinload(VirtualClassroom.academic_assignment).selectinload(AcademicAssignment.teacher).selectinload(Teacher.user),
                selectinload(VirtualClassroom.recordings),
            )
        )
        vc = (await self._session.execute(stmt)).scalar_one_or_none()
        if not vc:
            raise NotFoundError("Aula virtual no encontrada o no autorizada.")

        assign = vc.academic_assignment
        subj_name = assign.subject.name if assign and assign.subject else None
        teacher_name = assign.teacher.user.full_name if assign and assign.teacher and assign.teacher.user else None
        has_recs = len(vc.recordings) > 0 if vc.recordings else False

        return StudentVirtualClassroomItemResponse(
            id=vc.id,
            title=vc.title,
            description=vc.description,
            status=vc.status,
            scheduled_start_time=vc.scheduled_start_time,
            scheduled_end_time=vc.scheduled_end_time,
            subject_name=subj_name,
            teacher_name=teacher_name,
            can_join=(vc.status == "RUNNING" or vc.status == "SCHEDULED"),
            room_name=vc.bbb_meeting_id,
            has_recordings=has_recs,
        )

    async def list_recordings(
        self,
        student: Student,
        classroom_id: uuid.UUID,
    ) -> StudentRecordingsListResponse:
        """List lecture recordings for an authorized virtual class."""
        # Ensure student is authorized for this classroom
        await self.get_virtual_classroom(student, classroom_id)

        stmt = (
            select(MeetingRecording)
            .where(
                MeetingRecording.virtual_classroom_id == classroom_id,
                MeetingRecording.is_published.is_(True),
            )
            .order_by(MeetingRecording.created_at.desc())
        )
        recs = (await self._session.execute(stmt)).scalars().all()

        items = [
            StudentRecordingItemResponse(
                id=r.id,
                virtual_classroom_id=r.virtual_classroom_id,
                title=f"Grabación de Sesión {r.bbb_record_id[:8]}",
                duration_seconds=r.duration_seconds,
                file_size_bytes=r.file_size_bytes,
                playback_url=r.playback_url,
                created_at=r.created_at,
            )
            for r in recs
        ]
        return StudentRecordingsListResponse(items=items, total=len(items))

    async def get_dashboard(
        self,
        student: Student,
    ) -> StudentDashboardResponse:
        """Compile the consolidated dashboard for the authenticated student."""
        profile = await self.get_profile(student)
        subjects = await self.list_subjects(student)
        activities = await self.list_activities(student)
        grades = await self.list_grades(student)
        attendance = await self.list_attendance(student)
        classrooms = await self.list_virtual_classrooms(student)

        pending_count = sum(1 for a in activities.items if a.submission_status == "PENDING")
        overdue_count = sum(1 for a in activities.items if a.submission_status == "OVERDUE")
        graded_count = sum(1 for a in activities.items if a.submission_status == "GRADED")

        # Upcoming 5 activities and classrooms
        upcoming_act = [a for a in activities.items if a.submission_status in ("PENDING", "OVERDUE")][:5]
        upcoming_vc = [vc for vc in classrooms.items if vc.status in ("SCHEDULED", "RUNNING")][:5]
        recent_gr = grades.items[:5]

        return StudentDashboardResponse(
            profile=profile,
            total_subjects=subjects.total,
            pending_activities_count=pending_count,
            overdue_activities_count=overdue_count,
            graded_activities_count=graded_count,
            attendance_summary=attendance.summary,
            upcoming_virtual_classrooms=upcoming_vc,
            upcoming_activities=upcoming_act,
            recent_grades=recent_gr,
        )
