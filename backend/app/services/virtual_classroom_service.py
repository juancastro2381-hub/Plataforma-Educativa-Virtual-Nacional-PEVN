"""
PEVN Backend — Virtual Classroom Domain Service

Authoritative business logic and application orchestration for virtual classrooms,
real-time meeting delivery, role and enrollment authorization, provider decoupling,
and multi-tenant isolation.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicAssignmentNotFoundError,
    CrossTenantMismatchError,
    UnauthorizedMeetingAccessError,
    VirtualClassroomLifecycleError,
    VirtualClassroomNotFoundError,
)
from app.core.logging import get_logger
from app.core.meeting import (
    EndMeetingOptions,
    IMeetingProvider,
    JoinMeetingOptions,
    MeetingCreateOptions,
    get_meeting_provider,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.group import Group
from app.models.institution import Campus
from app.models.student import Student
from app.models.user import User
from app.models.virtual_classroom import (
    MeetingParticipantRole,
    VirtualClassroom,
    VirtualClassroomStatus,
)
from app.services.attendance_service import AttendanceService

_logger = get_logger(__name__)


class VirtualClassroomService:
    """
    Domain service orchestrating Virtual Classroom sessions and real-time
    meeting delivery.
    """

    def __init__(
        self,
        session: AsyncSession,
        provider: IMeetingProvider | None = None,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._provider: IMeetingProvider = provider or get_meeting_provider()
        self._audit = audit
        self._attendance_service = AttendanceService(session, audit)

    async def create_virtual_classroom(
        self,
        *,
        institution_id: uuid.UUID,
        host_user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        academic_assignment_id: uuid.UUID | None = None,
        scheduled_start_time: datetime | None = None,
        scheduled_end_time: datetime | None = None,
        is_recording_enabled: bool = True,
        is_breakout_enabled: bool = False,
        max_participants: int = 100,
        provider_metadata: dict[str, Any] | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> VirtualClassroom:
        """
        Create and provision a new virtual classroom session anchored to
        an academic course.
        """
        # Validate academic assignment if provided
        if academic_assignment_id is not None:
            assign_query = (
                select(AcademicAssignment)
                .join(Group, AcademicAssignment.group_id == Group.id)
                .join(Campus, Group.campus_id == Campus.id)
                .options(
                    selectinload(AcademicAssignment.group).selectinload(Group.campus)
                )
                .where(AcademicAssignment.id == academic_assignment_id)
            )
            assign_res = await self._session.execute(assign_query)
            assignment = assign_res.scalars().first()

            if not assignment:
                raise AcademicAssignmentNotFoundError()

            if assignment.group.campus.institution_id != institution_id:
                raise CrossTenantMismatchError(
                    "La asignación académica pertenece a otra institución."
                )

        # Generate secure unique meeting identifier and passwords
        external_meeting_id = f"pevn-{str(institution_id)[:8]}-{uuid.uuid4().hex[:12]}"
        mod_password = secrets.token_urlsafe(16)
        att_password = secrets.token_urlsafe(16)

        # Provision meeting on external provider
        create_options = MeetingCreateOptions(
            meeting_id=external_meeting_id,
            title=title,
            moderator_password=mod_password,
            attendee_password=att_password,
            is_recording_enabled=is_recording_enabled,
            is_breakout_enabled=is_breakout_enabled,
            max_participants=max_participants,
            welcome_message=f"Bienvenido a la sesión: {title}",
            metadata={"institution_id": str(institution_id)},
        )
        await self._provider.create_meeting(create_options)

        # Persist virtual classroom entity
        classroom = VirtualClassroom(
            institution_id=institution_id,
            academic_assignment_id=academic_assignment_id,
            host_user_id=host_user_id,
            title=title,
            description=description,
            bbb_meeting_id=external_meeting_id,
            moderator_password_hash=mod_password,
            attendee_password_hash=att_password,
            status=VirtualClassroomStatus.SCHEDULED,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            is_recording_enabled=is_recording_enabled,
            is_breakout_enabled=is_breakout_enabled,
            max_participants=max_participants,
            provider_metadata=provider_metadata or {},
        )
        self._session.add(classroom)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.MEETING_CREATED,
                actor_id=str(actor_id) if actor_id else str(host_user_id),
                actor_ip=actor_ip,
                target_id=str(classroom.id),
                target_type="VirtualClassroom",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "title": classroom.title,
                    "bbb_meeting_id": external_meeting_id,
                    "academic_assignment_id": (
                        str(academic_assignment_id) if academic_assignment_id else None
                    ),
                },
            ),
            session=self._session,
        )

        return classroom

    async def launch_virtual_classroom(
        self,
        *,
        classroom_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> VirtualClassroom:
        """
        Transitions a virtual classroom from SCHEDULED to RUNNING status.
        """
        classroom = await self.get_virtual_classroom(
            classroom_id=classroom_id,
            institution_id=institution_id,
        )

        if classroom.status in (
            VirtualClassroomStatus.ENDED,
            VirtualClassroomStatus.CANCELLED,
        ):
            raise VirtualClassroomLifecycleError(
                f"No se puede iniciar un aula en estado {classroom.status.value}."
            )

        # Check provider state and create meeting if not active
        is_running = await self._provider.is_meeting_running(classroom.bbb_meeting_id)
        if not is_running:
            create_options = MeetingCreateOptions(
                meeting_id=classroom.bbb_meeting_id,
                title=classroom.title,
                moderator_password=classroom.moderator_password_hash,
                attendee_password=classroom.attendee_password_hash,
                is_recording_enabled=classroom.is_recording_enabled,
                is_breakout_enabled=classroom.is_breakout_enabled,
                max_participants=classroom.max_participants,
            )
            await self._provider.create_meeting(create_options)

        classroom.status = VirtualClassroomStatus.RUNNING
        if classroom.actual_start_time is None:
            classroom.actual_start_time = datetime.now(tz=UTC)

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.MEETING_LAUNCHED,
                actor_id=str(actor_id) if actor_id else str(classroom.host_user_id),
                actor_ip=actor_ip,
                target_id=str(classroom.id),
                target_type="VirtualClassroom",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"status": classroom.status.value},
            ),
            session=self._session,
        )

        return classroom

    async def generate_join_url(
        self,
        *,
        classroom_id: uuid.UUID,
        institution_id: uuid.UUID,
        user: User,
        user_roles: list[str],
        redirect_url: str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> str:
        """
        Resolves caller authority and generates a signed join URL.
        """
        query = (
            select(VirtualClassroom)
            .options(
                selectinload(VirtualClassroom.academic_assignment).selectinload(
                    AcademicAssignment.group
                )
            )
            .where(
                VirtualClassroom.id == classroom_id,
                VirtualClassroom.institution_id == institution_id,
            )
        )
        res = await self._session.execute(query)
        classroom = res.scalars().first()

        if not classroom:
            raise VirtualClassroomNotFoundError()

        if classroom.status in (
            VirtualClassroomStatus.ENDED,
            VirtualClassroomStatus.CANCELLED,
        ):
            raise VirtualClassroomLifecycleError(
                "La sesión de aula virtual ya ha concluido o fue cancelada."
            )

        # Determine Role & Authority
        is_host = user.id == classroom.host_user_id
        is_admin = any(
            r in ("rector", "academic_coordinator", "superadmin") for r in user_roles
        )

        if is_host or is_admin:
            role = MeetingParticipantRole.MODERATOR
            password = classroom.moderator_password_hash
        else:
            # Verify Student Eligibility
            if classroom.academic_assignment is not None:
                group_id = classroom.academic_assignment.group_id
                enrollment_query = (
                    select(Enrollment)
                    .join(Student, Enrollment.student_id == Student.id)
                    .where(
                        Student.user_id == user.id,
                        Enrollment.group_id == group_id,
                        Enrollment.status == EnrollmentStatus.ACTIVE,
                    )
                )
                enr_res = await self._session.execute(enrollment_query)
                active_enrollment = enr_res.scalars().first()

                if not active_enrollment:
                    raise UnauthorizedMeetingAccessError(
                        "El estudiante no cuenta con matrícula activa en este salón."
                    )
            # Ad-hoc room: user must belong to same institution
            elif user.institution_id != institution_id:
                raise UnauthorizedMeetingAccessError(
                    "No pertenece a la institución educativa correspondiente."
                )

            role = MeetingParticipantRole.VIEWER
            password = classroom.attendee_password_hash

        # Construct signed join URL via provider
        user_full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        join_options = JoinMeetingOptions(
            meeting_id=classroom.bbb_meeting_id,
            user_name=user_full_name,
            password=password,
            user_id=str(user.id),
            role=role.value,
            redirect_url=redirect_url,
        )
        join_url = await self._provider.generate_join_url(join_options)

        # Record join attendance
        await self._attendance_service.record_join(
            classroom_id=classroom.id,
            user_id=user.id,
            role=role,
        )

        # If still SCHEDULED, transition to RUNNING automatically
        if classroom.status == VirtualClassroomStatus.SCHEDULED:
            classroom.status = VirtualClassroomStatus.RUNNING
            if classroom.actual_start_time is None:
                classroom.actual_start_time = datetime.now(tz=UTC)
            await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.MEETING_JOINED,
                actor_id=str(user.id),
                actor_ip=actor_ip,
                target_id=str(classroom.id),
                target_type="VirtualClassroom",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"role": role.value},
            ),
            session=self._session,
        )

        return join_url

    async def end_virtual_classroom(
        self,
        *,
        classroom_id: uuid.UUID,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
        user_roles: list[str],
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> VirtualClassroom:
        """
        Terminates an active virtual classroom session on provider and database.
        """
        classroom = await self.get_virtual_classroom(
            classroom_id=classroom_id,
            institution_id=institution_id,
        )

        is_host = user_id == classroom.host_user_id
        is_admin = any(
            r in ("rector", "academic_coordinator", "superadmin") for r in user_roles
        )

        if not (is_host or is_admin):
            raise UnauthorizedMeetingAccessError(
                "Solo el docente anfitrión o un directivo pueden finalizar la clase."
            )

        # Call provider termination
        end_options = EndMeetingOptions(
            meeting_id=classroom.bbb_meeting_id,
            moderator_password=classroom.moderator_password_hash,
        )
        await self._provider.end_meeting(end_options)

        classroom.status = VirtualClassroomStatus.ENDED
        classroom.actual_end_time = datetime.now(tz=UTC)

        # Close all open attendances
        await self._attendance_service.close_open_attendances(classroom_id=classroom.id)

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.MEETING_ENDED,
                actor_id=str(user_id),
                actor_ip=actor_ip,
                target_id=str(classroom.id),
                target_type="VirtualClassroom",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"status": classroom.status.value},
            ),
            session=self._session,
        )

        return classroom

    async def get_virtual_classroom(
        self,
        *,
        classroom_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> VirtualClassroom:
        """
        Retrieve virtual classroom enforcing tenant boundary (Blind 404).
        """
        query = (
            select(VirtualClassroom)
            .options(
                selectinload(VirtualClassroom.academic_assignment),
                selectinload(VirtualClassroom.host_user),
            )
            .where(
                VirtualClassroom.id == classroom_id,
                VirtualClassroom.institution_id == institution_id,
            )
        )
        res = await self._session.execute(query)
        classroom = res.scalars().first()

        if not classroom:
            raise VirtualClassroomNotFoundError()

        return classroom

    async def list_virtual_classrooms(
        self,
        *,
        institution_id: uuid.UUID,
        academic_assignment_id: uuid.UUID | None = None,
        status: VirtualClassroomStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[VirtualClassroom], int]:
        """
        List virtual classrooms within tenant scope with pagination.
        """
        filters = [VirtualClassroom.institution_id == institution_id]

        if academic_assignment_id is not None:
            filters.append(
                VirtualClassroom.academic_assignment_id == academic_assignment_id
            )
        if status is not None:
            filters.append(VirtualClassroom.status == status)

        count_query = select(func.count(VirtualClassroom.id)).where(*filters)
        count_res = await self._session.execute(count_query)
        total = count_res.scalar() or 0

        query = (
            select(VirtualClassroom)
            .options(
                selectinload(VirtualClassroom.academic_assignment),
                selectinload(VirtualClassroom.host_user),
            )
            .where(*filters)
            .order_by(VirtualClassroom.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self._session.execute(query)
        items = list(res.scalars().all())

        return items, total
