"""
PEVN Backend — School Coexistence & Student Incidents Domain Service (Phase 15)

Authoritative business logic for "Observador del Estudiante" and Ley 1620 de 2013
coexistence situations, with strict teacher academic scoping and Anti-IDOR family isolation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    GuardianNotFoundError,
    StudentNotFoundError,
)
from app.core.logging import get_logger
from app.core.security.interfaces import AuthorizationContext, SystemRole
from app.exceptions.errors import AuthorizationError, NotFoundError
from app.models.coexistence_incident import (
    CoexistenceSituationType,
    IncidentFollowUp,
    IncidentStatus,
    StudentIncident,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.guardian import Guardian, StudentGuardian
from app.models.student import Student
from app.models.user import User
from app.services.academic_scope_helper import (
    get_teacher_authorized_group_ids,
    is_directive_actor,
)

if TYPE_CHECKING:
    from app.schemas.incident import (
        IncidentFollowUpPayload,
        StudentIncidentCloseRequest,
        StudentIncidentCreateRequest,
        StudentIncidentUpdateRequest,
    )

_logger = get_logger(__name__)


class CoexistenceIncidentService:
    """
    Domain service for Student Coexistence, Observador del Estudiante, and Ley 1620 cases.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def _validate_teacher_student_scope(
        self,
        *,
        teacher_user_id: uuid.UUID,
        institution_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> None:
        """
        Ensure non-directive teacher only manages incidents for students enrolled in their assigned groups.
        """
        authorized_group_ids = await get_teacher_authorized_group_ids(
            self._session,
            user_id=teacher_user_id,
            institution_id=institution_id,
        )
        if not authorized_group_ids:
            raise NotFoundError("Estudiante no encontrado en su ámbito pedagógico asignado.")

        enr_stmt = select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.group_id.in_(authorized_group_ids),
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        enrollment = (await self._session.execute(enr_stmt)).scalar_one_or_none()
        if not enrollment:
            raise NotFoundError("Estudiante no encontrado en su ámbito pedagógico asignado.")

    async def create_incident(
        self,
        *,
        institution_id: uuid.UUID,
        reporter_user: User,
        payload: StudentIncidentCreateRequest,
        auth: AuthorizationContext | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> StudentIncident:
        """
        Create a new coexistence situation in the student's Observador record.
        Validates teacher scope (DECISION-15-04) and tenant containment.
        """
        # 1. Validate student exists in this institution
        student_stmt = select(Student).where(
            Student.id == payload.student_id,
            Student.institution_id == institution_id,
        )
        student = (await self._session.execute(student_stmt)).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError("Estudiante no encontrado en la institución.")

        # 2. Check teacher scope if non-directive actor
        if not is_directive_actor(auth, user=reporter_user):
            await self._validate_teacher_student_scope(
                teacher_user_id=reporter_user.id,
                institution_id=institution_id,
                student_id=student.id,
            )

        incident_date = payload.incident_date or datetime.now(UTC)

        incident = StudentIncident(
            institution_id=institution_id,
            student_id=student.id,
            reporter_user_id=reporter_user.id,
            situation_type=payload.situation_type,
            incident_date=incident_date,
            location=payload.location.strip() if payload.location else None,
            description=payload.description.strip(),
            student_version=payload.student_version.strip() if payload.student_version else None,
            pedagogical_measures=payload.pedagogical_measures.strip(),
            commitments=payload.commitments.strip() if payload.commitments else None,
            status=payload.status,
            is_visible_to_guardian=payload.is_visible_to_guardian,
            is_visible_to_student=payload.is_visible_to_student,
        )
        self._session.add(incident)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.INCIDENT_RECORDED,
                actor_id=str(reporter_user.id),
                actor_ip=actor_ip,
                target_id=str(incident.id),
                target_type="StudentIncident",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "student_id": str(student.id),
                    "situation_type": incident.situation_type.value,
                    "status": incident.status.value,
                },
            ),
            session=self._session,
        )

        return await self.get_incident_by_id(
            incident_id=incident.id,
            institution_id=institution_id,
        )

    async def update_incident(
        self,
        *,
        incident_id: uuid.UUID,
        institution_id: uuid.UUID,
        caller_user: User,
        payload: StudentIncidentUpdateRequest,
        auth: AuthorizationContext | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> StudentIncident:
        """
        Update incident description, commitments, or family visibility flags.
        """
        incident = await self.get_incident_by_id(
            incident_id=incident_id,
            institution_id=institution_id,
        )

        # Non-directive actor check
        if not is_directive_actor(auth, user=caller_user):
            await self._validate_teacher_student_scope(
                teacher_user_id=caller_user.id,
                institution_id=institution_id,
                student_id=incident.student_id,
            )

        if payload.situation_type is not None:
            incident.situation_type = payload.situation_type
        if payload.incident_date is not None:
            incident.incident_date = payload.incident_date
        if payload.location is not None:
            incident.location = payload.location.strip() if payload.location else None
        if payload.description is not None:
            incident.description = payload.description.strip()
        if payload.student_version is not None:
            incident.student_version = payload.student_version.strip() if payload.student_version else None
        if payload.pedagogical_measures is not None:
            incident.pedagogical_measures = payload.pedagogical_measures.strip()
        if payload.commitments is not None:
            incident.commitments = payload.commitments.strip() if payload.commitments else None
        if payload.status is not None:
            incident.status = payload.status
        if payload.is_visible_to_guardian is not None:
            incident.is_visible_to_guardian = payload.is_visible_to_guardian
        if payload.is_visible_to_student is not None:
            incident.is_visible_to_student = payload.is_visible_to_student

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.INCIDENT_UPDATED,
                actor_id=str(caller_user.id),
                actor_ip=actor_ip,
                target_id=str(incident.id),
                target_type="StudentIncident",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
            ),
            session=self._session,
        )

        return await self.get_incident_by_id(
            incident_id=incident.id,
            institution_id=institution_id,
        )

    async def add_follow_up(
        self,
        *,
        incident_id: uuid.UUID,
        institution_id: uuid.UUID,
        author_user: User,
        payload: IncidentFollowUpPayload,
        auth: AuthorizationContext | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> IncidentFollowUp:
        """
        Add a chronological follow-up counseling or agreement log to an incident.
        """
        incident = await self.get_incident_by_id(
            incident_id=incident_id,
            institution_id=institution_id,
        )

        if not is_directive_actor(auth, user=author_user):
            await self._validate_teacher_student_scope(
                teacher_user_id=author_user.id,
                institution_id=institution_id,
                student_id=incident.student_id,
            )

        follow_up = IncidentFollowUp(
            incident_id=incident.id,
            author_user_id=author_user.id,
            follow_up_date=payload.follow_up_date or datetime.now(UTC),
            notes=payload.notes.strip(),
        )
        self._session.add(follow_up)
        incident.status = IncidentStatus.EN_SEGUIMIENTO
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.INCIDENT_UPDATED,
                actor_id=str(author_user.id),
                actor_ip=actor_ip,
                target_id=str(incident.id),
                target_type="StudentIncident",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"action": "add_follow_up"},
            ),
            session=self._session,
        )

        stmt = (
            select(IncidentFollowUp)
            .options(selectinload(IncidentFollowUp.author))
            .where(IncidentFollowUp.id == follow_up.id)
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def close_incident(
        self,
        *,
        incident_id: uuid.UUID,
        institution_id: uuid.UUID,
        closed_by_user: User,
        payload: StudentIncidentCloseRequest,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> StudentIncident:
        """
        Resolve and close a coexistence situation.
        """
        incident = await self.get_incident_by_id(
            incident_id=incident_id,
            institution_id=institution_id,
        )
        incident.status = IncidentStatus.CERRADO
        incident.closed_at = datetime.now(UTC)
        incident.closed_by_user_id = closed_by_user.id

        if payload.resolution_notes:
            follow_up = IncidentFollowUp(
                incident_id=incident.id,
                author_user_id=closed_by_user.id,
                follow_up_date=datetime.now(UTC),
                notes=f"CIERRE FORMAL: {payload.resolution_notes.strip()}",
            )
            self._session.add(follow_up)

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.INCIDENT_CLOSED,
                actor_id=str(closed_by_user.id),
                actor_ip=actor_ip,
                target_id=str(incident.id),
                target_type="StudentIncident",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
            ),
            session=self._session,
        )

        return await self.get_incident_by_id(
            incident_id=incident.id,
            institution_id=institution_id,
        )

    async def get_incident_by_id(
        self,
        *,
        incident_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> StudentIncident:
        """
        Retrieve incident validating tenant isolation.
        """
        stmt = (
            select(StudentIncident)
            .options(
                selectinload(StudentIncident.student).selectinload(Student.user),
                selectinload(StudentIncident.reporter),
                selectinload(StudentIncident.closed_by),
                selectinload(StudentIncident.follow_ups).selectinload(IncidentFollowUp.author),
            )
            .where(
                StudentIncident.id == incident_id,
                StudentIncident.institution_id == institution_id,
            )
        )
        incident = (await self._session.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundError("Registro de convivencia escolar no encontrado.")
        return incident

    async def list_incidents(
        self,
        *,
        institution_id: uuid.UUID,
        caller_user: User,
        auth: AuthorizationContext | None = None,
        student_id: uuid.UUID | None = None,
        situation_type: CoexistenceSituationType | None = None,
        status: IncidentStatus | None = None,
    ) -> list[StudentIncident]:
        """
        List incidents within institutional boundary and teacher scope.
        """
        query = (
            select(StudentIncident)
            .options(
                selectinload(StudentIncident.student).selectinload(Student.user),
                selectinload(StudentIncident.reporter),
                selectinload(StudentIncident.closed_by),
                selectinload(StudentIncident.follow_ups).selectinload(IncidentFollowUp.author),
            )
            .where(StudentIncident.institution_id == institution_id)
        )

        if student_id:
            query = query.where(StudentIncident.student_id == student_id)
        if situation_type:
            query = query.where(StudentIncident.situation_type == situation_type)
        if status:
            query = query.where(StudentIncident.status == status)

        # Scoping for teachers
        if not is_directive_actor(auth, user=caller_user):
            authorized_group_ids = await get_teacher_authorized_group_ids(
                self._session,
                user_id=caller_user.id,
                institution_id=institution_id,
            )
            if not authorized_group_ids:
                return []
            query = query.join(Enrollment, Enrollment.student_id == StudentIncident.student_id).where(
                Enrollment.group_id.in_(authorized_group_ids),
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )

        query = query.order_by(StudentIncident.incident_date.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_student_incidents(
        self,
        *,
        student: Student,
    ) -> list[StudentIncident]:
        """
        List student's own observations (Observador) where is_visible_to_student is True (DECISION-15-01).
        """
        stmt = (
            select(StudentIncident)
            .options(
                selectinload(StudentIncident.reporter),
                selectinload(StudentIncident.follow_ups).selectinload(IncidentFollowUp.author),
            )
            .where(
                StudentIncident.student_id == student.id,
                StudentIncident.institution_id == student.institution_id,
                StudentIncident.is_visible_to_student == True,  # noqa: E712
            )
            .order_by(StudentIncident.incident_date.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_guardian_student_incidents(
        self,
        *,
        guardian: Guardian,
        student_id: uuid.UUID,
    ) -> list[StudentIncident]:
        """
        List incidents for an authorized legal child where is_visible_to_guardian is True.
        Enforces strict Anti-IDOR validation via active StudentGuardian link.
        """
        # Validate that student belongs to guardian and same tenant
        link_stmt = select(StudentGuardian).where(
            StudentGuardian.guardian_id == guardian.id,
            StudentGuardian.student_id == student_id,
        )
        link = (await self._session.execute(link_stmt)).scalar_one_or_none()
        if not link:
            raise NotFoundError("Estudiante no encontrado en sus vínculos de tutoría legal autorizados.")

        stmt = (
            select(StudentIncident)
            .options(
                selectinload(StudentIncident.reporter),
                selectinload(StudentIncident.follow_ups).selectinload(IncidentFollowUp.author),
            )
            .where(
                StudentIncident.student_id == student_id,
                StudentIncident.institution_id == guardian.institution_id,
                StudentIncident.is_visible_to_guardian == True,  # noqa: E712
            )
            .order_by(StudentIncident.incident_date.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
