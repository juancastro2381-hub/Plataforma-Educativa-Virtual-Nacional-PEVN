"""
PEVN Backend — Guardian Domain Service

Authoritative business logic for legal guardians and parent actors (Acudientes),
supporting decoupled national document identification per [OPEN-DECISION-3A-01].
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    GuardianNotFoundError,
    StudentNotFoundError,
)
from app.core.logging import get_logger
from app.models.guardian import (
    Guardian,
    GuardianRelationshipType,
    StudentGuardian,
)
from app.models.student import Student
from app.models.user import DocumentType

_logger = get_logger(__name__)


class GuardianService:
    """
    Domain service for Guardian and Student-Guardian associations.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_guardian(
        self,
        *,
        first_name: str,
        last_name: str,
        document_type: DocumentType,
        document_number: str,
        phone: str,
        email: str | None = None,
        address: str | None = None,
        relationship_type: GuardianRelationshipType = (GuardianRelationshipType.MADRE),
        user_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Guardian:
        """
        Create a guardian record.
        Email and user_id are optional per [OPEN-DECISION-3A-01].
        """
        # Check document uniqueness
        dup_stmt = select(Guardian).where(
            Guardian.document_type == document_type,
            Guardian.document_number == document_number,
        )
        existing = (await self._session.execute(dup_stmt)).scalar_one_or_none()
        if existing:
            raise AcademicDomainError(
                "Ya existe un acudiente registrado con documento "
                f"{document_type.value} {document_number}."
            )

        guardian = Guardian(
            first_name=first_name,
            last_name=last_name,
            document_type=document_type,
            document_number=document_number,
            phone=phone,
            email=email,
            address=address,
            relationship_type=relationship_type,
            user_id=user_id,
        )
        self._session.add(guardian)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GUARDIAN_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(guardian.id),
                target_type="Guardian",
                correlation_id=correlation_id,
                metadata={
                    "document_type": document_type.value,
                    "document_number": document_number,
                },
            ),
            session=self._session,
        )

        return guardian

    async def get_guardian_by_id(
        self,
        *,
        guardian_id: uuid.UUID,
    ) -> Guardian:
        """
        Retrieve a guardian by primary key ID.
        """
        stmt = select(Guardian).where(Guardian.id == guardian_id)
        guardian = (await self._session.execute(stmt)).scalar_one_or_none()
        if not guardian:
            raise GuardianNotFoundError(f"Acudiente {guardian_id} no encontrado.")
        return guardian

    async def associate_guardian_to_student(
        self,
        *,
        student_id: uuid.UUID,
        guardian_id: uuid.UUID,
        institution_id: uuid.UUID,
        relationship_type: GuardianRelationshipType = (GuardianRelationshipType.PADRE),
        is_primary_contact: bool = False,
        is_authorized_pickup: bool = True,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> StudentGuardian:
        """
        Associate a guardian to a student, validating student tenant boundary.
        """
        # 1. Validate Student Tenant Ownership
        student = (
            await self._session.execute(
                select(Student).where(
                    Student.id == student_id,
                    Student.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError(
                f"Estudiante {student_id} no encontrado en la institución."
            )

        # 2. Validate Guardian exists
        guardian = await self.get_guardian_by_id(guardian_id=guardian_id)

        # 3. Check for existing association
        dup_stmt = select(StudentGuardian).where(
            StudentGuardian.student_id == student_id,
            StudentGuardian.guardian_id == guardian_id,
        )
        if (await self._session.execute(dup_stmt)).scalar_one_or_none():
            raise AcademicDomainError(
                "El acudiente ya se encuentra vinculado a este estudiante."
            )

        assoc = StudentGuardian(
            student_id=student_id,
            guardian_id=guardian_id,
            relationship_type=relationship_type,
            is_primary_contact=is_primary_contact,
            is_authorized_pickup=is_authorized_pickup,
        )
        self._session.add(assoc)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GUARDIAN_ASSOCIATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(student_id),
                target_type="StudentGuardian",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "guardian_id": str(guardian.id),
                    "relationship_type": relationship_type.value,
                },
            ),
            session=self._session,
        )

        return assoc
