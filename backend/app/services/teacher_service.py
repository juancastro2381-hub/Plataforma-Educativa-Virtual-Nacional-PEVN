"""
PEVN Backend — Teacher Domain Service

Authoritative business logic for educator professional profiles,
institutional binding, and group/subject assignment eligibility.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    TeacherNotFoundError,
)
from app.core.logging import get_logger
from app.models.teacher import Teacher, TeacherContractType
from app.models.user import User

_logger = get_logger(__name__)


class TeacherService:
    """
    Domain service for Teacher professional profiles.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_teacher(
        self,
        *,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
        specialty_area: str | None = None,
        contract_type: TeacherContractType = TeacherContractType.PROPIEDAD,
        escalafon_grade: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Teacher:
        """
        Create an educator profile 1:1 linked to an existing User account.
        """
        # 1. Validate User Tenant Ownership
        user = (
            await self._session.execute(
                select(User).where(
                    User.id == user_id,
                    User.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not user:
            raise CrossTenantMismatchError(
                "La cuenta de usuario no pertenece a la institución especificada."
            )

        # 2. Check 1:1 User to Teacher Uniqueness
        existing = (
            await self._session.execute(
                select(Teacher).where(Teacher.user_id == user_id)
            )
        ).scalar_one_or_none()
        if existing:
            raise AcademicDomainError("El usuario ya posee un perfil docente asignado.")

        teacher = Teacher(
            user_id=user_id,
            institution_id=institution_id,
            specialty_area=specialty_area,
            contract_type=contract_type,
            escalafon_grade=escalafon_grade,
        )
        self._session.add(teacher)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.TEACHER_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(teacher.id),
                target_type="Teacher",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "user_id": str(user_id),
                    "contract_type": contract_type.value,
                },
            ),
            session=self._session,
        )

        return teacher

    async def get_teacher_by_id(
        self,
        *,
        teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> Teacher:
        """
        Retrieve an educator profile validating tenant isolation.
        """
        stmt = (
            select(Teacher)
            .options(selectinload(Teacher.user))
            .where(
                Teacher.id == teacher_id,
                Teacher.institution_id == institution_id,
            )
        )
        teacher = (await self._session.execute(stmt)).scalar_one_or_none()
        if not teacher:
            raise TeacherNotFoundError(
                f"Docente {teacher_id} no encontrado en la institución."
            )
        return teacher

    async def validate_teacher_eligibility(
        self,
        *,
        teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> bool:
        """
        Verify that the educator is eligible for academic workload allocations.
        """
        teacher = await self.get_teacher_by_id(
            teacher_id=teacher_id,
            institution_id=institution_id,
        )
        if not teacher.user.is_active:
            raise AcademicDomainError(
                "La cuenta del docente se encuentra inactiva o deshabilitada."
            )
        return True
