"""
PEVN Backend — Institutional Communication Domain Service (Phase 15)

Authoritative business logic for official circulars, targeted communications,
active feed expiration (DECISION-15-02), and unforgeable read/acknowledgment receipts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import AcademicDomainError
from app.core.logging import get_logger
from app.exceptions.errors import ConflictError, NotFoundError
from app.models.communication import (
    CommunicationAudience,
    CommunicationCategory,
    CommunicationPriority,
    CommunicationReceipt,
    InstitutionalCommunication,
    PublishingStatus,
    TargetScopeType,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.group import Group
from app.models.guardian import Guardian, StudentGuardian
from app.models.student import Student
from app.models.user import User

if TYPE_CHECKING:
    from app.schemas.communication import (
        CommunicationAudiencePayload,
        CommunicationCreateRequest,
        CommunicationUpdateRequest,
    )

_logger = get_logger(__name__)


class CommunicationService:
    """
    Domain service for Institutional Communications and Read Receipts.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_communication(
        self,
        *,
        institution_id: uuid.UUID,
        author_user_id: uuid.UUID,
        payload: CommunicationCreateRequest,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> InstitutionalCommunication:
        """
        Create a new official institutional communication with optional audience targeting.
        """
        published_at = datetime.now(UTC) if payload.status == PublishingStatus.PUBLICADO else None

        communication = InstitutionalCommunication(
            institution_id=institution_id,
            author_user_id=author_user_id,
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            content=payload.content.strip(),
            category=payload.category,
            priority=payload.priority,
            target_scope=payload.target_scope,
            attachment_url=payload.attachment_url.strip() if payload.attachment_url else None,
            requires_acknowledgment=payload.requires_acknowledgment,
            status=payload.status,
            published_at=published_at,
            expires_at=payload.expires_at,
        )
        self._session.add(communication)
        await self._session.flush()

        if payload.audiences:
            for aud in payload.audiences:
                audience_record = CommunicationAudience(
                    communication_id=communication.id,
                    campus_id=aud.campus_id,
                    grade_id=aud.grade_id,
                    group_id=aud.group_id,
                    role_name=aud.role_name,
                )
                self._session.add(audience_record)
            await self._session.flush()

        # Audit event
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COMMUNICATION_CREATED,
                actor_id=str(author_user_id),
                actor_ip=actor_ip,
                target_id=str(communication.id),
                target_type="InstitutionalCommunication",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "title": communication.title,
                    "category": communication.category.value,
                    "priority": communication.priority.value,
                    "target_scope": communication.target_scope.value,
                    "status": communication.status.value,
                },
            ),
            session=self._session,
        )

        return await self.get_communication_by_id(
            communication_id=communication.id,
            institution_id=institution_id,
        )

    async def update_communication(
        self,
        *,
        communication_id: uuid.UUID,
        institution_id: uuid.UUID,
        payload: CommunicationUpdateRequest,
        actor_id: uuid.UUID,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> InstitutionalCommunication:
        """
        Modify existing communication fields and reconfigure audience targeting.
        """
        communication = await self.get_communication_by_id(
            communication_id=communication_id,
            institution_id=institution_id,
        )

        if payload.title is not None:
            communication.title = payload.title.strip()
        if payload.summary is not None:
            communication.summary = payload.summary.strip()
        if payload.content is not None:
            communication.content = payload.content.strip()
        if payload.category is not None:
            communication.category = payload.category
        if payload.priority is not None:
            communication.priority = payload.priority
        if payload.target_scope is not None:
            communication.target_scope = payload.target_scope
        if payload.attachment_url is not None:
            communication.attachment_url = payload.attachment_url.strip() if payload.attachment_url else None
        if payload.requires_acknowledgment is not None:
            communication.requires_acknowledgment = payload.requires_acknowledgment
        if payload.status is not None:
            communication.status = payload.status
            if payload.status == PublishingStatus.PUBLICADO and communication.published_at is None:
                communication.published_at = datetime.now(UTC)
        if payload.expires_at is not None:
            communication.expires_at = payload.expires_at

        # Update audiences if supplied
        if payload.audiences is not None:
            # Clear existing
            for aud in list(communication.audiences):
                await self._session.delete(aud)
            await self._session.flush()

            for aud in payload.audiences:
                audience_record = CommunicationAudience(
                    communication_id=communication.id,
                    campus_id=aud.campus_id,
                    grade_id=aud.grade_id,
                    group_id=aud.group_id,
                    role_name=aud.role_name,
                )
                self._session.add(audience_record)
            await self._session.flush()

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COMMUNICATION_UPDATED,
                actor_id=str(actor_id),
                actor_ip=actor_ip,
                target_id=str(communication.id),
                target_type="InstitutionalCommunication",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "title": communication.title,
                    "status": communication.status.value,
                },
            ),
            session=self._session,
        )

        return await self.get_communication_by_id(
            communication_id=communication_id,
            institution_id=institution_id,
        )

    async def publish_communication(
        self,
        *,
        communication_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> InstitutionalCommunication:
        """
        Transition draft communication to published status.
        """
        communication = await self.get_communication_by_id(
            communication_id=communication_id,
            institution_id=institution_id,
        )
        communication.status = PublishingStatus.PUBLICADO
        communication.published_at = datetime.now(UTC)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COMMUNICATION_PUBLISHED,
                actor_id=str(actor_id),
                actor_ip=actor_ip,
                target_id=str(communication.id),
                target_type="InstitutionalCommunication",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
            ),
            session=self._session,
        )
        return communication

    async def archive_communication(
        self,
        *,
        communication_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> InstitutionalCommunication:
        """
        Archive communication.
        """
        communication = await self.get_communication_by_id(
            communication_id=communication_id,
            institution_id=institution_id,
        )
        communication.status = PublishingStatus.ARCHIVADO
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COMMUNICATION_ARCHIVED,
                actor_id=str(actor_id),
                actor_ip=actor_ip,
                target_id=str(communication.id),
                target_type="InstitutionalCommunication",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
            ),
            session=self._session,
        )
        return communication

    async def get_communication_by_id(
        self,
        *,
        communication_id: uuid.UUID,
        institution_id: uuid.UUID,
        caller_user: User | None = None,
        register_read: bool = False,
    ) -> InstitutionalCommunication:
        """
        Retrieve communication enforcing tenant isolation (Anti-IDOR).
        """
        stmt = (
            select(InstitutionalCommunication)
            .options(
                selectinload(InstitutionalCommunication.author),
                selectinload(InstitutionalCommunication.audiences),
                selectinload(InstitutionalCommunication.receipts),
            )
            .where(
                InstitutionalCommunication.id == communication_id,
                InstitutionalCommunication.institution_id == institution_id,
            )
        )
        comm = (await self._session.execute(stmt)).scalar_one_or_none()
        if not comm:
            raise NotFoundError("Comunicado institucional no encontrado.")

        if register_read and caller_user:
            await self._record_read_receipt(comm.id, caller_user.id)

        return comm

    async def list_communications(
        self,
        *,
        institution_id: uuid.UUID,
        category: CommunicationCategory | None = None,
        priority: CommunicationPriority | None = None,
        status: PublishingStatus | None = None,
        include_expired: bool = False,
    ) -> list[InstitutionalCommunication]:
        """
        List communications for administrative overview.
        """
        query = (
            select(InstitutionalCommunication)
            .options(
                selectinload(InstitutionalCommunication.author),
                selectinload(InstitutionalCommunication.audiences),
                selectinload(InstitutionalCommunication.receipts),
            )
            .where(InstitutionalCommunication.institution_id == institution_id)
        )
        if category:
            query = query.where(InstitutionalCommunication.category == category)
        if priority:
            query = query.where(InstitutionalCommunication.priority == priority)
        if status:
            query = query.where(InstitutionalCommunication.status == status)
        if not include_expired:
            now = datetime.now(UTC)
            query = query.where(
                or_(
                    InstitutionalCommunication.expires_at == None,  # noqa: E711
                    InstitutionalCommunication.expires_at > now,
                )
            )

        query = query.order_by(InstitutionalCommunication.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def _record_read_receipt(
        self,
        communication_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CommunicationReceipt:
        """
        Idempotently record read timestamp when user opens communication.
        """
        receipt_stmt = select(CommunicationReceipt).where(
            CommunicationReceipt.communication_id == communication_id,
            CommunicationReceipt.user_id == user_id,
        )
        receipt = (await self._session.execute(receipt_stmt)).scalar_one_or_none()
        if not receipt:
            receipt = CommunicationReceipt(
                communication_id=communication_id,
                user_id=user_id,
                read_at=datetime.now(UTC),
            )
            self._session.add(receipt)
            await self._session.flush()
        return receipt

    async def acknowledge_communication(
        self,
        *,
        communication_id: uuid.UUID,
        institution_id: uuid.UUID,
        user: User,
        client_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> CommunicationReceipt:
        """
        Formally record receipt acknowledgment from recipient with immutable timestamp and client IP.
        """
        comm = await self.get_communication_by_id(
            communication_id=communication_id,
            institution_id=institution_id,
        )

        receipt_stmt = select(CommunicationReceipt).where(
            CommunicationReceipt.communication_id == comm.id,
            CommunicationReceipt.user_id == user.id,
        )
        receipt = (await self._session.execute(receipt_stmt)).scalar_one_or_none()
        now = datetime.now(UTC)
        if not receipt:
            receipt = CommunicationReceipt(
                communication_id=comm.id,
                user_id=user.id,
                read_at=now,
                acknowledged_at=now,
                client_ip=client_ip,
            )
            self._session.add(receipt)
        else:
            receipt.acknowledged_at = now
            receipt.client_ip = client_ip

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COMMUNICATION_ACKNOWLEDGED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                target_id=str(comm.id),
                target_type="InstitutionalCommunication",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "user_email": user.email,
                    "communication_title": comm.title,
                },
            ),
            session=self._session,
        )

        return receipt

    async def list_student_communications(
        self,
        *,
        student: Student,
        user: User,
    ) -> list[tuple[InstitutionalCommunication, bool, bool]]:
        """
        Retrieve active, non-expired communications targeted to this student's grade/group/institution.
        Returns list of (communication, is_read, is_acknowledged).
        """
        # 1. Resolve student active group and grade enrollments
        enrollment_stmt = (
            select(Enrollment)
            .options(selectinload(Enrollment.group))
            .where(
                Enrollment.student_id == student.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        enrollments = list((await self._session.execute(enrollment_stmt)).scalars().all())
        student_group_ids = [e.group_id for e in enrollments]
        student_grade_ids = [e.group.grade_id for e in enrollments if e.group]
        student_campus_ids = [e.group.campus_id for e in enrollments if e.group]

        # 2. Query communications matching audience
        now = datetime.now(UTC)
        query = (
            select(InstitutionalCommunication)
            .options(
                selectinload(InstitutionalCommunication.author),
                selectinload(InstitutionalCommunication.audiences),
                selectinload(InstitutionalCommunication.receipts),
            )
            .where(
                InstitutionalCommunication.institution_id == student.institution_id,
                InstitutionalCommunication.status == PublishingStatus.PUBLICADO,
                or_(
                    InstitutionalCommunication.expires_at == None,  # noqa: E711
                    InstitutionalCommunication.expires_at > now,
                ),
            )
            .order_by(InstitutionalCommunication.created_at.desc())
        )
        all_comms = list((await self._session.execute(query)).scalars().all())

        results: list[tuple[InstitutionalCommunication, bool, bool]] = []
        for comm in all_comms:
            # Check target scope match
            is_match = False
            if comm.target_scope in (TargetScopeType.TODOS_INSTITUCION, TargetScopeType.SOLO_ESTUDIANTES):
                is_match = True
            elif not comm.audiences:
                is_match = True
            else:
                for aud in comm.audiences:
                    if aud.role_name and aud.role_name != "student":
                        continue
                    if aud.group_id and aud.group_id in student_group_ids:
                        is_match = True
                        break
                    if aud.grade_id and aud.grade_id in student_grade_ids:
                        is_match = True
                        break
                    if aud.campus_id and aud.campus_id in student_campus_ids:
                        is_match = True
                        break
                    if not aud.group_id and not aud.grade_id and not aud.campus_id and aud.role_name == "student":
                        is_match = True
                        break

            if is_match:
                user_receipt = next((r for r in comm.receipts if r.user_id == user.id), None)
                is_read = user_receipt is not None
                is_ack = user_receipt.is_acknowledged if user_receipt else False
                results.append((comm, is_read, is_ack))

        return results

    async def list_guardian_communications(
        self,
        *,
        guardian: Guardian,
        user: User,
    ) -> list[tuple[InstitutionalCommunication, bool, bool]]:
        """
        Retrieve active communications targeted to guardians of enrolled children.
        """
        # 1. Resolve enrolled groups and grades of guardian's children
        link_stmt = select(StudentGuardian).where(StudentGuardian.guardian_id == guardian.id)
        links = list((await self._session.execute(link_stmt)).scalars().all())
        student_ids = [l.student_id for l in links]

        children_group_ids: list[uuid.UUID] = []
        children_grade_ids: list[uuid.UUID] = []
        children_campus_ids: list[uuid.UUID] = []

        if student_ids:
            enr_stmt = (
                select(Enrollment)
                .options(selectinload(Enrollment.group))
                .where(
                    Enrollment.student_id.in_(student_ids),
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
            enrollments = list((await self._session.execute(enr_stmt)).scalars().all())
            children_group_ids = [e.group_id for e in enrollments]
            children_grade_ids = [e.group.grade_id for e in enrollments if e.group]
            children_campus_ids = [e.group.campus_id for e in enrollments if e.group]

        # 2. Query communications matching guardian scope
        now = datetime.now(UTC)
        query = (
            select(InstitutionalCommunication)
            .options(
                selectinload(InstitutionalCommunication.author),
                selectinload(InstitutionalCommunication.audiences),
                selectinload(InstitutionalCommunication.receipts),
            )
            .where(
                InstitutionalCommunication.institution_id == guardian.institution_id,
                InstitutionalCommunication.status == PublishingStatus.PUBLICADO,
                or_(
                    InstitutionalCommunication.expires_at == None,  # noqa: E711
                    InstitutionalCommunication.expires_at > now,
                ),
            )
            .order_by(InstitutionalCommunication.created_at.desc())
        )
        all_comms = list((await self._session.execute(query)).scalars().all())

        results: list[tuple[InstitutionalCommunication, bool, bool]] = []
        for comm in all_comms:
            is_match = False
            if comm.target_scope in (TargetScopeType.TODOS_INSTITUCION, TargetScopeType.SOLO_ACUDIENTES):
                is_match = True
            elif not comm.audiences:
                is_match = True
            else:
                for aud in comm.audiences:
                    if aud.role_name and aud.role_name != "guardian":
                        continue
                    if aud.group_id and aud.group_id in children_group_ids:
                        is_match = True
                        break
                    if aud.grade_id and aud.grade_id in children_grade_ids:
                        is_match = True
                        break
                    if aud.campus_id and aud.campus_id in children_campus_ids:
                        is_match = True
                        break
                    if not aud.group_id and not aud.grade_id and not aud.campus_id and aud.role_name == "guardian":
                        is_match = True
                        break

            if is_match:
                user_receipt = next((r for r in comm.receipts if r.user_id == user.id), None)
                is_read = user_receipt is not None
                is_ack = user_receipt.is_acknowledged if user_receipt else False
                results.append((comm, is_read, is_ack))

        return results
