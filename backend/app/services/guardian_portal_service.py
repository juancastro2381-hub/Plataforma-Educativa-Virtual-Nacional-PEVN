"""
PEVN Backend — Guardian Portal Domain Service

Authoritative application service providing strictly-isolated, anti-IDOR,
parental follow-up academic access for authenticated guardians/acudientes:
- Guardian profile resolution from authenticated user token
- Multi-child resolution for the child-context selector
- Centralized Guardian-to-Student authorization boundary
- Child academic overview and performance indicators
- Homework / task follow-up monitoring (Read-only observer role)
- Child evaluation grades and educator remarks
- Daily attendance and absence logs
- Child virtual classroom scheduling agenda
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import IAuditService
from app.audit.service import audit_service
from app.core.exceptions import GuardianNotFoundError
from app.core.logging import get_logger
from app.exceptions.errors import NotFoundError
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.group import Group
from app.models.guardian import Guardian, StudentGuardian
from app.models.institution import Institution
from app.models.student import Student
from app.models.user import User
from app.schemas.guardian_portal import (
    GuardianChildActivitiesListResponse,
    GuardianChildAttendanceListResponse,
    GuardianChildGradesListResponse,
    GuardianChildItemResponse,
    GuardianChildOverviewResponse,
    GuardianChildVirtualClassroomsListResponse,
    GuardianChildrenListResponse,
    GuardianProfileResponse,
)
from app.schemas.student_portal import StudentVirtualClassroomItemResponse
from app.services.student_portal_service import StudentPortalService

_logger = get_logger(__name__)


class GuardianPortalService:
    """
    Application service managing Guardian Portal operations.
    Enforces that guardian identity is derived from token and child access
    is validated via active StudentGuardian associations.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit
        self._student_service = StudentPortalService(session=session, audit=audit)

    async def get_guardian_by_user_id(
        self,
        user_id: uuid.UUID,
        institution_id: uuid.UUID | None = None,
    ) -> Guardian:
        """
        Derive authenticated guardian domain entity strictly from current_user.id.
        Anti-IDOR: Never trusts client-supplied guardian_id.
        """
        stmt = (
            select(Guardian)
            .where(Guardian.user_id == user_id)
            .options(
                selectinload(Guardian.user),
                selectinload(Guardian.institution),
            )
        )
        if institution_id is not None:
            stmt = stmt.where(Guardian.institution_id == institution_id)

        guardian = (await self._session.execute(stmt)).scalar_one_or_none()
        if not guardian:
            raise GuardianNotFoundError("Perfil de acudiente no encontrado para el usuario actual.")
        return guardian

    async def get_profile(
        self,
        guardian: Guardian,
    ) -> GuardianProfileResponse:
        """Construct the guardian profile with linked student count."""
        count_stmt = (
            select(func.count(StudentGuardian.id))
            .join(Student, StudentGuardian.student_id == Student.id)
            .where(
                StudentGuardian.guardian_id == guardian.id,
                Student.institution_id == guardian.institution_id,
            )
        )
        total_students = (await self._session.execute(count_stmt)).scalar_one()

        email = guardian.user.email if guardian.user else guardian.email
        full_name = guardian.user.full_name if guardian.user else f"{guardian.first_name} {guardian.last_name}"
        doc_type = guardian.user.document_type if guardian.user else guardian.document_type
        doc_num = guardian.user.document_number if guardian.user else guardian.document_number

        return GuardianProfileResponse(
            guardian_id=guardian.id,
            user_id=guardian.user_id or guardian.id,
            first_name=guardian.first_name,
            last_name=guardian.last_name,
            full_name=full_name,
            email=email,
            document_type=doc_type,
            document_number=doc_num,
            phone=guardian.phone,
            address=guardian.address,
            institution_id=guardian.institution_id,
            institution_name=guardian.institution.name,
            total_linked_students=total_students,
        )

    async def list_authorized_students(
        self,
        guardian: Guardian,
    ) -> GuardianChildrenListResponse:
        """
        List all authorized student children linked to the guardian in the current institution.
        This serves as the authoritative data source for the child-switcher frontend component.
        """
        stmt = (
            select(StudentGuardian, Student)
            .join(Student, StudentGuardian.student_id == Student.id)
            .join(User, Student.user_id == User.id)
            .where(
                StudentGuardian.guardian_id == guardian.id,
                Student.institution_id == guardian.institution_id,
            )
            .options(
                selectinload(StudentGuardian.student).selectinload(Student.user),
                selectinload(StudentGuardian.student).selectinload(Student.institution),
            )
        )
        rows = (await self._session.execute(stmt)).all()

        items: list[GuardianChildItemResponse] = []
        for sg, student in rows:
            enrollment = await self._student_service.get_active_enrollment(student.id)

            group_name = enrollment.group.name if enrollment and enrollment.group else None
            group_id = enrollment.group.id if enrollment and enrollment.group else None
            grade_name = enrollment.group.grade.name if enrollment and enrollment.group and enrollment.group.grade else None
            campus_name = enrollment.group.campus.name if enrollment and enrollment.group and enrollment.group.campus else None
            academic_year_name = enrollment.academic_year.name if enrollment and enrollment.academic_year else None
            enrollment_status = enrollment.status.value if enrollment else None

            items.append(
                GuardianChildItemResponse(
                    student_id=student.id,
                    first_name=student.user.first_name,
                    last_name=student.user.last_name,
                    full_name=student.user.full_name,
                    code_simat=student.code_simat,
                    document_type=student.user.document_type,
                    document_number=student.user.document_number,
                    birth_date=student.birth_date,
                    relationship_type=sg.relationship_type,
                    is_primary_contact=sg.is_primary_contact,
                    is_authorized_pickup=sg.is_authorized_pickup,
                    institution_id=student.institution_id,
                    institution_name=student.institution.name,
                    campus_name=campus_name,
                    grade_name=grade_name,
                    group_id=group_id,
                    group_name=group_name,
                    academic_year_name=academic_year_name,
                    enrollment_status=enrollment_status,
                )
            )

        return GuardianChildrenListResponse(items=items, total=len(items))

    async def authorize_student_access(
        self,
        guardian: Guardian,
        student_id: uuid.UUID,
    ) -> tuple[Student, StudentGuardian]:
        """
        Centralized Guardian-to-Student authorization check.
        Guarantees:
        1. Student exists.
        2. Student belongs to guardian's institution_id.
        3. Active StudentGuardian association exists for this guardian.

        Anti-IDOR: Returns 404 on ANY failure (never reveals cross-tenant or unlinked records).
        """
        stmt = (
            select(StudentGuardian, Student)
            .join(Student, StudentGuardian.student_id == Student.id)
            .join(User, Student.user_id == User.id)
            .where(
                StudentGuardian.guardian_id == guardian.id,
                StudentGuardian.student_id == student_id,
                Student.institution_id == guardian.institution_id,
            )
            .options(
                selectinload(StudentGuardian.student).selectinload(Student.user),
                selectinload(StudentGuardian.student).selectinload(Student.institution),
            )
        )
        row = (await self._session.execute(stmt)).first()
        if not row:
            raise NotFoundError("Estudiante no encontrado o no vinculado legalmente a su cuenta.")

        sg, student = row
        return student, sg

    async def get_child_overview(
        self,
        guardian: Guardian,
        student_id: uuid.UUID,
    ) -> GuardianChildOverviewResponse:
        """Compile consolidated academic follow-up summary for a single authorized child."""
        student, sg = await self.authorize_student_access(guardian, student_id)

        enrollment = await self._student_service.get_active_enrollment(student.id)
        group_name = enrollment.group.name if enrollment and enrollment.group else None
        group_id = enrollment.group.id if enrollment and enrollment.group else None
        grade_name = enrollment.group.grade.name if enrollment and enrollment.group and enrollment.group.grade else None
        campus_name = enrollment.group.campus.name if enrollment and enrollment.group and enrollment.group.campus else None
        academic_year_name = enrollment.academic_year.name if enrollment and enrollment.academic_year else None
        enrollment_status = enrollment.status.value if enrollment else None

        child_item = GuardianChildItemResponse(
            student_id=student.id,
            first_name=student.user.first_name,
            last_name=student.user.last_name,
            full_name=student.user.full_name,
            code_simat=student.code_simat,
            document_type=student.user.document_type,
            document_number=student.user.document_number,
            birth_date=student.birth_date,
            relationship_type=sg.relationship_type,
            is_primary_contact=sg.is_primary_contact,
            is_authorized_pickup=sg.is_authorized_pickup,
            institution_id=student.institution_id,
            institution_name=student.institution.name,
            campus_name=campus_name,
            grade_name=grade_name,
            group_id=group_id,
            group_name=group_name,
            academic_year_name=academic_year_name,
            enrollment_status=enrollment_status,
        )

        subjects = await self._student_service.list_subjects(student)
        activities = await self._student_service.list_activities(student)
        grades = await self._student_service.list_grades(student)
        attendance = await self._student_service.list_attendance(student)
        classrooms = await self._student_service.list_virtual_classrooms(student)

        pending_count = sum(1 for a in activities.items if a.submission_status == "PENDING")
        overdue_count = sum(1 for a in activities.items if a.submission_status == "OVERDUE")
        graded_count = sum(1 for a in activities.items if a.submission_status == "GRADED")

        upcoming_act = [a for a in activities.items if a.submission_status in ("PENDING", "OVERDUE")][:5]
        upcoming_vc = [vc for vc in classrooms.items if vc.status in ("SCHEDULED", "RUNNING")][:5]
        recent_gr = grades.items[:5]

        return GuardianChildOverviewResponse(
            child=child_item,
            total_subjects=subjects.total,
            pending_tasks_count=pending_count,
            overdue_tasks_count=overdue_count,
            graded_tasks_count=graded_count,
            average_score=grades.average_score,
            attendance_summary=attendance.summary,
            upcoming_virtual_classrooms=upcoming_vc,
            pending_activities=upcoming_act,
            recent_grades=recent_gr,
        )

    async def list_child_activities(
        self,
        guardian: Guardian,
        student_id: uuid.UUID,
        *,
        subject_id: uuid.UUID | None = None,
        submission_status: str | None = None,
    ) -> GuardianChildActivitiesListResponse:
        """List tasks and homework for the authorized child (parental follow-up mode)."""
        student, _ = await self.authorize_student_access(guardian, student_id)
        res = await self._student_service.list_activities(
            student,
            subject_id=subject_id,
            submission_status=submission_status,
        )
        return GuardianChildActivitiesListResponse(
            student_id=student.id,
            student_name=student.user.full_name,
            items=res.items,
            total=res.total,
        )

    async def list_child_grades(
        self,
        guardian: Guardian,
        student_id: uuid.UUID,
        *,
        subject_id: uuid.UUID | None = None,
    ) -> GuardianChildGradesListResponse:
        """List evaluation grades and teacher remarks for the authorized child."""
        student, _ = await self.authorize_student_access(guardian, student_id)
        res = await self._student_service.list_grades(
            student,
            subject_id=subject_id,
        )
        return GuardianChildGradesListResponse(
            student_id=student.id,
            student_name=student.user.full_name,
            items=res.items,
            total=res.total,
            average_score=res.average_score,
        )

    async def list_child_attendance(
        self,
        guardian: Guardian,
        student_id: uuid.UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> GuardianChildAttendanceListResponse:
        """List daily attendance marks and statistics for the authorized child."""
        student, _ = await self.authorize_student_access(guardian, student_id)
        res = await self._student_service.list_attendance(
            student,
            start_date=start_date,
            end_date=end_date,
        )
        return GuardianChildAttendanceListResponse(
            student_id=student.id,
            student_name=student.user.full_name,
            items=res.items,
            total=res.total,
            summary=res.summary,
        )

    async def list_child_virtual_classrooms(
        self,
        guardian: Guardian,
        student_id: uuid.UUID,
    ) -> GuardianChildVirtualClassroomsListResponse:
        """List virtual classroom schedule/agenda for the authorized child."""
        student, _ = await self.authorize_student_access(guardian, student_id)
        res = await self._student_service.list_virtual_classrooms(student)
        return GuardianChildVirtualClassroomsListResponse(
            student_id=student.id,
            student_name=student.user.full_name,
            items=res.items,
            total=res.total,
        )

    async def get_child_virtual_classroom(
        self,
        guardian: Guardian,
        student_id: uuid.UUID,
        classroom_id: uuid.UUID,
    ) -> StudentVirtualClassroomItemResponse:
        """Retrieve virtual classroom agenda details for the authorized child."""
        student, _ = await self.authorize_student_access(guardian, student_id)
        return await self._student_service.get_virtual_classroom(student, classroom_id)
