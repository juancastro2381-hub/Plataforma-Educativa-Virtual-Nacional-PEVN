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

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import AcademicDomainError, StudentNotFoundError
from app.core.logging import get_logger
from app.core.storage.service import get_storage_service
from app.exceptions.errors import NotFoundError
from app.models.academic_activity import (
    AcademicActivity,
    ActivityDeliveryType,
    ActivityGrade,
    ActivityResource,
    ActivityStatus,
    ActivitySubmissionStatus,
    DailyAttendance,
    StudentSubmission,
    SubmissionAttachment,
    SubmissionStatus,
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
    StudentActivityResourceItem,
    StudentActivityResourceListResponse,
    StudentAttendanceItemResponse,
    StudentAttendanceListResponse,
    StudentAttendanceSummary,
    StudentDashboardResponse,
    StudentGradeItemResponse,
    StudentGradesListResponse,
    StudentProfileResponse,
    StudentRecordingItemResponse,
    StudentRecordingsListResponse,
    StudentSubmissionAttemptResponse,
    StudentSubmissionDetailResponse,
    StudentSubmissionDraftUpdateRequest,
    StudentSubjectItemResponse,
    StudentSubjectsListResponse,
    StudentVirtualClassroomItemResponse,
    StudentVirtualClassroomsListResponse,
    SubmissionAttachmentItemResponse,
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
                selectinload(AcademicActivity.resources),
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

            res_items = [
                StudentActivityResourceItem(
                    id=r.id,
                    resource_type=r.resource_type.value,
                    title=r.title,
                    url=r.url,
                    original_filename=r.original_filename,
                    file_size_bytes=r.file_size_bytes,
                    mime_type=r.mime_type,
                    created_at=r.created_at,
                )
                for r in (activity.resources or [])
            ]

            items.append(
                StudentActivityItemResponse(
                    id=activity.id,
                    title=activity.title,
                    description=activity.description,
                    activity_type=activity.activity_type,
                    status=activity.status,
                    delivery_type=activity.delivery_type,
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
                    resources=res_items,
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
                selectinload(AcademicActivity.resources),
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

        res_stmt = (
            select(ActivityResource)
            .where(
                ActivityResource.activity_id == activity.id,
                ActivityResource.institution_id == student.institution_id,
            )
            .order_by(ActivityResource.created_at.asc())
        )
        resources_list = list((await self._session.execute(res_stmt)).scalars().all())

        res_items = [
            StudentActivityResourceItem(
                id=r.id,
                resource_type=r.resource_type.value,
                title=r.title,
                url=r.url,
                original_filename=r.original_filename,
                file_size_bytes=r.file_size_bytes,
                mime_type=r.mime_type,
                created_at=r.created_at,
            )
            for r in resources_list
        ]

        return StudentActivityItemResponse(
            id=activity.id,
            title=activity.title,
            description=activity.description,
            activity_type=activity.activity_type,
            status=activity.status,
            delivery_type=activity.delivery_type,
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
            resources=res_items,
        )

    async def list_activity_resources(
        self,
        student: Student,
        activity_id: uuid.UUID,
    ) -> list[ActivityResource]:
        """List materials for a published activity in the student's active group."""
        enrollment = await self.get_active_enrollment(student.id)
        if not enrollment or not enrollment.group:
            raise NotFoundError("Actividad académica no encontrada o no autorizada.")

        act_stmt = select(AcademicActivity).where(
            AcademicActivity.id == activity_id,
            AcademicActivity.group_id == enrollment.group_id,
            AcademicActivity.status == ActivityStatus.PUBLISHED,
        )
        activity = (await self._session.execute(act_stmt)).scalar_one_or_none()
        if not activity:
            raise NotFoundError("Actividad académica no encontrada o no autorizada.")

        res_stmt = (
            select(ActivityResource)
            .where(
                ActivityResource.activity_id == activity.id,
                ActivityResource.institution_id == student.institution_id,
            )
            .order_by(ActivityResource.created_at.asc())
        )
        return list((await self._session.execute(res_stmt)).scalars().all())

    async def get_resource_for_download(
        self,
        student: Student,
        activity_id: uuid.UUID,
        resource_id: uuid.UUID,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> tuple[ActivityResource, str]:
        """Validate student group authorization and retrieve physical file path for download streaming."""
        enrollment = await self.get_active_enrollment(student.id)
        if not enrollment or not enrollment.group:
            raise NotFoundError("Actividad académica no encontrada o no autorizada.")

        act_stmt = select(AcademicActivity).where(
            AcademicActivity.id == activity_id,
            AcademicActivity.group_id == enrollment.group_id,
            AcademicActivity.status == ActivityStatus.PUBLISHED,
        )
        activity = (await self._session.execute(act_stmt)).scalar_one_or_none()
        if not activity:
            raise NotFoundError("Actividad académica no encontrada o no autorizada.")

        res_stmt = select(ActivityResource).where(
            ActivityResource.id == resource_id,
            ActivityResource.activity_id == activity.id,
            ActivityResource.institution_id == student.institution_id,
        )
        resource = (await self._session.execute(res_stmt)).scalar_one_or_none()
        if not resource or resource.resource_type.value != "FILE" or not resource.file_path:
            raise NotFoundError("Archivo de recurso no encontrado o no disponible para descarga.")

        storage = get_storage_service()
        physical_path = storage.get_physical_path(resource.file_path)

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RESOURCE_DOWNLOADED,
                actor_id=actor_id or str(student.user_id),
                actor_ip=actor_ip,
                target_id=str(resource_id),
                target_type="ActivityResource",
                institution_id=str(student.institution_id),
                metadata={"title": resource.title, "activity_id": str(activity.id)},
            ),
            session=self._session,
        )
        return resource, physical_path

    # =======================================================================
    # Student Submissions & Deliveries (Phase B3-H13)
    # =======================================================================

    async def _get_authorized_activity(
        self,
        student: Student,
        activity_id: uuid.UUID,
    ) -> AcademicActivity:
        """Helper to ensure student is enrolled in the activity's group and tenant."""
        enrollment = await self.get_active_enrollment(student.id)
        if not enrollment or not enrollment.group:
            raise NotFoundError("Actividad académica no encontrada o no autorizada.")

        stmt = (
            select(AcademicActivity)
            .where(
                AcademicActivity.id == activity_id,
                AcademicActivity.group_id == enrollment.group_id,
                AcademicActivity.institution_id == student.institution_id,
            )
        )
        activity = (await self._session.execute(stmt)).scalar_one_or_none()
        if not activity:
            raise NotFoundError("Actividad académica no encontrada o no autorizada.")
        return activity

    async def get_submission_detail(
        self,
        student: Student,
        activity_id: uuid.UUID,
    ) -> StudentSubmissionDetailResponse:
        """
        Retrieve student's submission status, active attempt draft, and historical attempts.
        If no attempt exists and activity is PUBLISHED, creates Attempt 1 in DRAFT state.
        If latest attempt was RETURNED and activity is PUBLISHED, creates next Attempt in DRAFT state.
        """
        activity = await self._get_authorized_activity(student, activity_id)

        # Fetch all attempts for (activity_id, student.id)
        # populate_existing=True ensures relationships (e.g. attachments) are refreshed
        # from the database even if the parent object is already in the identity map.
        sub_stmt = (
            select(StudentSubmission)
            .options(
                selectinload(StudentSubmission.attachments),
            )
            .where(
                StudentSubmission.activity_id == activity_id,
                StudentSubmission.student_id == student.id,
                StudentSubmission.institution_id == student.institution_id,
            )
            .order_by(StudentSubmission.attempt_number.asc())
            .execution_options(populate_existing=True)
        )
        attempts = list((await self._session.execute(sub_stmt)).scalars().all())

        latest_attempt = attempts[-1] if attempts else None

        # Auto-create draft attempt if needed
        now_utc = datetime.now(UTC)
        if activity.status == ActivityStatus.PUBLISHED:
            if not attempts:
                new_draft = StudentSubmission(
                    institution_id=student.institution_id,
                    activity_id=activity.id,
                    student_id=student.id,
                    attempt_number=1,
                    status=SubmissionStatus.DRAFT,
                    is_late=False,
                    created_at=now_utc,
                    updated_at=now_utc,
                )
                self._session.add(new_draft)
                await self._session.flush()
                # Re-select with selectinload to guarantee all attributes are populated
                st_draft = (
                    select(StudentSubmission)
                    .options(selectinload(StudentSubmission.attachments))
                    .where(StudentSubmission.id == new_draft.id)
                )
                new_draft = (await self._session.execute(st_draft)).scalar_one()
                attempts.append(new_draft)
                latest_attempt = new_draft
            elif latest_attempt and latest_attempt.status == SubmissionStatus.RETURNED:
                # Spawn next attempt as DRAFT
                next_number = latest_attempt.attempt_number + 1
                new_draft = StudentSubmission(
                    institution_id=student.institution_id,
                    activity_id=activity.id,
                    student_id=student.id,
                    attempt_number=next_number,
                    status=SubmissionStatus.DRAFT,
                    is_late=False,
                    created_at=now_utc,
                    updated_at=now_utc,
                )
                self._session.add(new_draft)
                await self._session.flush()
                st_draft = (
                    select(StudentSubmission)
                    .options(selectinload(StudentSubmission.attachments))
                    .where(StudentSubmission.id == new_draft.id)
                )
                new_draft = (await self._session.execute(st_draft)).scalar_one()
                attempts.append(new_draft)
                latest_attempt = new_draft

        # Fetch ActivityGrade if exists
        grade_stmt = select(ActivityGrade).where(
            ActivityGrade.activity_id == activity_id,
            ActivityGrade.student_id == student.id,
        )
        grade = (await self._session.execute(grade_stmt)).scalar_one_or_none()

        can_edit_draft = (
            activity.status == ActivityStatus.PUBLISHED
            and latest_attempt is not None
            and latest_attempt.status == SubmissionStatus.DRAFT
        )
        can_submit = can_edit_draft

        def _to_attempt_resp(att: StudentSubmission) -> StudentSubmissionAttemptResponse:
            att_items = [
                SubmissionAttachmentItemResponse(
                    id=a.id,
                    original_filename=a.original_filename,
                    file_size_bytes=a.file_size_bytes,
                    mime_type=a.mime_type,
                    created_at=a.created_at,
                )
                for a in (att.attachments or [])
            ]
            return StudentSubmissionAttemptResponse(
                id=att.id,
                activity_id=att.activity_id,
                student_id=att.student_id,
                attempt_number=att.attempt_number,
                status=att.status,
                student_response=att.student_response,
                submitted_at=att.submitted_at,
                is_late=att.is_late,
                return_feedback=att.return_feedback,
                returned_at=att.returned_at,
                created_at=att.created_at,
                updated_at=att.updated_at,
                attachments=att_items,
            )

        history_items = [
            _to_attempt_resp(att)
            for att in attempts
            if latest_attempt and att.id != latest_attempt.id
        ]
        current_resp = _to_attempt_resp(latest_attempt) if latest_attempt else None

        return StudentSubmissionDetailResponse(
            activity_id=activity.id,
            activity_title=activity.title,
            activity_status=activity.status,
            delivery_type=activity.delivery_type,
            due_date=activity.due_date,
            can_submit=can_submit,
            can_edit_draft=can_edit_draft,
            current_attempt=current_resp,
            history=history_items,
            grade_score=grade.score if grade else None,
            grade_feedback=grade.feedback if grade else None,
            graded_at=grade.graded_at if grade else None,
        )

    async def _get_active_draft_attempt(
        self,
        student: Student,
        activity_id: uuid.UUID,
    ) -> tuple[AcademicActivity, StudentSubmission]:
        """Helper to fetch published activity and its active DRAFT attempt."""
        activity = await self._get_authorized_activity(student, activity_id)
        if activity.status != ActivityStatus.PUBLISHED:
            raise AcademicDomainError("No se pueden realizar cambios en actividades cerradas o no publicadas.")

        # Ensure detail ensures draft existence
        detail = await self.get_submission_detail(student, activity_id)
        if not detail.current_attempt or detail.current_attempt.status != SubmissionStatus.DRAFT:
            raise AcademicDomainError("No hay un borrador activo disponible para modificar.")

        stmt = (
            select(StudentSubmission)
            .options(selectinload(StudentSubmission.attachments))
            .where(StudentSubmission.id == detail.current_attempt.id)
        )
        draft = (await self._session.execute(stmt)).scalar_one()
        return activity, draft

    async def save_submission_draft(
        self,
        student: Student,
        activity_id: uuid.UUID,
        data: StudentSubmissionDraftUpdateRequest,
    ) -> StudentSubmissionAttemptResponse:
        """Update student response in the active draft attempt."""
        activity, draft = await self._get_active_draft_attempt(student, activity_id)
        draft.student_response = data.student_response
        draft.updated_at = datetime.now(UTC)
        await self._session.flush()

        stmt = (
            select(StudentSubmission)
            .options(selectinload(StudentSubmission.attachments))
            .where(StudentSubmission.id == draft.id)
        )
        draft = (await self._session.execute(stmt)).scalar_one()

        att_items = [
            SubmissionAttachmentItemResponse(
                id=a.id,
                original_filename=a.original_filename,
                file_size_bytes=a.file_size_bytes,
                mime_type=a.mime_type,
                created_at=a.created_at,
            )
            for a in (draft.attachments or [])
        ]
        return StudentSubmissionAttemptResponse(
            id=draft.id,
            activity_id=draft.activity_id,
            student_id=draft.student_id,
            attempt_number=draft.attempt_number,
            status=draft.status,
            student_response=draft.student_response,
            submitted_at=draft.submitted_at,
            is_late=draft.is_late,
            return_feedback=draft.return_feedback,
            returned_at=draft.returned_at,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
            attachments=att_items,
        )

    async def upload_submission_file(
        self,
        student: Student,
        activity_id: uuid.UUID,
        filename: str,
        content: bytes,
        declared_mime_type: str | None = None,
    ) -> SubmissionAttachmentItemResponse:
        """Upload a file attachment to the active draft attempt (max 3 files, non-TEXT activity)."""
        activity, draft = await self._get_active_draft_attempt(student, activity_id)

        if activity.delivery_type == ActivityDeliveryType.TEXT:
            raise AcademicDomainError("Esta actividad está configurada como SOLO TEXTO y no admite archivos adjuntos.")

        existing_count = len(draft.attachments or [])
        if existing_count >= 3:
            raise AcademicDomainError("Se ha alcanzado el límite máximo de 3 archivos adjuntos para esta entrega.")

        storage = get_storage_service()
        attachment_id = uuid.uuid4()
        now_utc = datetime.now(UTC)

        rel_path, mime_type, size_bytes = await storage.save_submission_attachment(
            institution_id=student.institution_id,
            activity_id=activity.id,
            student_id=student.id,
            submission_id=draft.id,
            attachment_id=attachment_id,
            original_filename=filename,
            content=content,
            declared_mime_type=declared_mime_type,
        )

        attachment = SubmissionAttachment(
            id=attachment_id,
            institution_id=student.institution_id,
            submission_id=draft.id,
            file_path=rel_path,
            original_filename=filename,
            file_size_bytes=size_bytes,
            mime_type=mime_type,
            created_at=now_utc,
            updated_at=now_utc,
        )
        self._session.add(attachment)
        await self._session.flush()

        stmt = select(SubmissionAttachment).where(SubmissionAttachment.id == attachment.id)
        attachment = (await self._session.execute(stmt)).scalar_one()

        return SubmissionAttachmentItemResponse(
            id=attachment.id,
            original_filename=attachment.original_filename,
            file_size_bytes=attachment.file_size_bytes,
            mime_type=attachment.mime_type,
            created_at=attachment.created_at,
        )

    async def delete_submission_file(
        self,
        student: Student,
        activity_id: uuid.UUID,
        attachment_id: uuid.UUID,
    ) -> bool:
        """Delete an uploaded attachment from the active draft attempt."""
        activity, draft = await self._get_active_draft_attempt(student, activity_id)

        stmt = select(SubmissionAttachment).where(
            SubmissionAttachment.id == attachment_id,
            SubmissionAttachment.submission_id == draft.id,
            SubmissionAttachment.institution_id == student.institution_id,
        )
        attachment = (await self._session.execute(stmt)).scalar_one_or_none()
        if not attachment:
            raise NotFoundError("Archivo adjunto no encontrado en el borrador activo.")

        storage = get_storage_service()
        await storage.delete_file(attachment.file_path)
        await self._session.delete(attachment)
        await self._session.flush()
        return True

    async def submit_activity(
        self,
        student: Student,
        activity_id: uuid.UUID,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> StudentSubmissionDetailResponse:
        """
        Confirm and submit the activity.
        Enforces delivery_type constraints, evaluates is_late in UTC,
        updates ActivityGrade status to SUBMITTED, and records audit.
        """
        activity, draft = await self._get_active_draft_attempt(student, activity_id)

        attachments = draft.attachments or []
        has_text = bool(draft.student_response and draft.student_response.strip())
        att_count = len(attachments)

        if activity.delivery_type == ActivityDeliveryType.TEXT:
            if not has_text:
                raise AcademicDomainError("Debe escribir una respuesta de texto para completar la entrega.")
            if att_count > 0:
                raise AcademicDomainError("Esta actividad de solo texto no admite archivos adjuntos.")
        elif activity.delivery_type == ActivityDeliveryType.FILE:
            if att_count < 1:
                raise AcademicDomainError("Debe adjuntar al menos un archivo (máximo 3) para completar la entrega.")
            if att_count > 3:
                raise AcademicDomainError("No puede adjuntar más de 3 archivos.")
        elif activity.delivery_type == ActivityDeliveryType.TEXT_AND_FILE:
            if not has_text:
                raise AcademicDomainError("Debe escribir una respuesta de texto para completar la entrega.")
            if att_count < 1:
                raise AcademicDomainError("Debe adjuntar al menos un archivo (máximo 3) para completar la entrega.")
            if att_count > 3:
                raise AcademicDomainError("No puede adjuntar más de 3 archivos.")

        # Server-side UTC deadline evaluation
        now_utc = datetime.now(UTC)
        is_late = False
        if activity.due_date:
            due_utc = activity.due_date if activity.due_date.tzinfo else activity.due_date.replace(tzinfo=UTC)
            if now_utc > due_utc:
                is_late = True

        draft.is_late = is_late
        draft.submitted_at = now_utc
        draft.status = SubmissionStatus.LATE if is_late else SubmissionStatus.SUBMITTED

        # Synchronize ActivityGrade
        gr_stmt = select(ActivityGrade).where(
            ActivityGrade.activity_id == activity.id,
            ActivityGrade.student_id == student.id,
        )
        grade = (await self._session.execute(gr_stmt)).scalar_one_or_none()
        if not grade:
            grade = ActivityGrade(
                activity_id=activity.id,
                student_id=student.id,
                status=ActivitySubmissionStatus.SUBMITTED,
                score=None,
            )
            self._session.add(grade)
        else:
            grade.status = ActivitySubmissionStatus.SUBMITTED
            grade.score = None

        await self._session.flush()

        # Audit recording
        event_type = (
            AuditEventType.SUBMISSION_RESUBMITTED
            if draft.attempt_number > 1
            else AuditEventType.SUBMISSION_CREATED
        )
        await self._audit.record(
            AuditEvent(
                event_type=event_type,
                actor_id=actor_id or str(student.user_id),
                actor_ip=actor_ip,
                target_id=str(draft.id),
                target_type="StudentSubmission",
                institution_id=str(student.institution_id),
                metadata={
                    "activity_id": str(activity.id),
                    "attempt_number": draft.attempt_number,
                    "is_late": is_late,
                    "delivery_type": activity.delivery_type.value,
                },
            ),
            session=self._session,
        )

        return await self.get_submission_detail(student, activity_id)

    async def get_submission_attachment_for_download(
        self,
        student: Student,
        activity_id: uuid.UUID,
        attachment_id: uuid.UUID,
        *,
        actor_id: str | None = None,
        actor_ip: str = "0.0.0.0",
    ) -> tuple[SubmissionAttachment, str]:
        """
        Anti-IDOR download of student's own submission attachment.
        Verifies attachment belongs to a submission of this student and activity.
        """
        activity = await self._get_authorized_activity(student, activity_id)

        att_stmt = (
            select(SubmissionAttachment)
            .join(StudentSubmission, SubmissionAttachment.submission_id == StudentSubmission.id)
            .where(
                SubmissionAttachment.id == attachment_id,
                SubmissionAttachment.institution_id == student.institution_id,
                StudentSubmission.activity_id == activity.id,
                StudentSubmission.student_id == student.id,
            )
        )
        attachment = (await self._session.execute(att_stmt)).scalar_one_or_none()
        if not attachment:
            raise NotFoundError("Archivo adjunto no encontrado o no pertenece a tus entregas.")

        storage = get_storage_service()
        physical_path = storage.get_physical_path(attachment.file_path)

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.SUBMISSION_DOWNLOADED,
                actor_id=actor_id or str(student.user_id),
                actor_ip=actor_ip,
                target_id=str(attachment.id),
                target_type="SubmissionAttachment",
                institution_id=str(student.institution_id),
                metadata={
                    "activity_id": str(activity.id),
                    "original_filename": attachment.original_filename,
                },
            ),
            session=self._session,
        )
        return attachment, physical_path

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
