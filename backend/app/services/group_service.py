"""
PEVN Backend — Group Domain Service

Authoritative business logic for educational groups (salones de clase),
capacity limit enforcement, director assignment, and multi-tenant validation.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    GroupNotFoundError,
)
from app.core.logging import get_logger
from app.models.academic_year import AcademicYear
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus
from app.models.teacher import Teacher

_logger = get_logger(__name__)


class GroupService:
    """
    Domain service for educational Group management.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_group(
        self,
        *,
        institution_id: uuid.UUID,
        campus_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        grade_id: uuid.UUID,
        name: str,
        shift: ShiftEnum = ShiftEnum.MANANA,
        capacity_limit: int = 35,
        director_teacher_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Group:
        """
        Create a classroom group section enforcing tenant and capacity invariants.
        """
        if capacity_limit <= 0:
            raise AcademicDomainError(
                "El límite de cupos del grupo debe ser mayor a cero."
            )

        # 1. Validate Campus Tenant Ownership
        campus = (
            await self._session.execute(
                select(Campus).where(
                    Campus.id == campus_id,
                    Campus.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not campus:
            raise CrossTenantMismatchError(
                "La sede especificada no pertenece a la institución."
            )

        # 2. Validate Academic Year Tenant Ownership
        ay = (
            await self._session.execute(
                select(AcademicYear).where(
                    AcademicYear.id == academic_year_id,
                    AcademicYear.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not ay:
            raise CrossTenantMismatchError(
                "El año lectivo no pertenece a la institución."
            )

        # 3. Validate Grade exists (National Catalog)
        grade = (
            await self._session.execute(select(Grade).where(Grade.id == grade_id))
        ).scalar_one_or_none()
        if not grade:
            raise AcademicDomainError("El grado especificado no existe.")

        # 4. Validate Director Teacher if provided
        if director_teacher_id:
            teacher = (
                await self._session.execute(
                    select(Teacher).where(
                        Teacher.id == director_teacher_id,
                        Teacher.institution_id == institution_id,
                    )
                )
            ).scalar_one_or_none()
            if not teacher:
                raise CrossTenantMismatchError(
                    "El docente director no pertenece a la institución."
                )

        # 5. Check Group Uniqueness
        dup_stmt = select(Group).where(
            Group.campus_id == campus_id,
            Group.academic_year_id == academic_year_id,
            Group.grade_id == grade_id,
            Group.name == name,
        )
        if (await self._session.execute(dup_stmt)).scalar_one_or_none():
            raise AcademicDomainError(
                f"Ya existe un grupo '{name}' para este grado en "
                "esta sede y año lectivo."
            )

        group = Group(
            campus_id=campus_id,
            academic_year_id=academic_year_id,
            grade_id=grade_id,
            name=name,
            shift=shift,
            capacity_limit=capacity_limit,
            group_director_teacher_id=director_teacher_id,
        )
        self._session.add(group)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GROUP_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(group.id),
                target_type="Group",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "name": name,
                    "shift": shift.value,
                    "capacity_limit": capacity_limit,
                },
            ),
            session=self._session,
        )

        return group

    async def get_group_by_id(
        self,
        *,
        group_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> Group:
        """
        Retrieve a group validating tenant isolation via its campus link.
        """
        stmt = (
            select(Group)
            .join(Campus, Group.campus_id == Campus.id)
            .where(
                Group.id == group_id,
                Campus.institution_id == institution_id,
            )
        )
        group = (await self._session.execute(stmt)).scalar_one_or_none()
        if not group:
            raise GroupNotFoundError(
                f"Grupo {group_id} no encontrado en la institución."
            )
        return group

    async def assign_group_director(
        self,
        *,
        group_id: uuid.UUID,
        teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Group:
        """
        Assign an institutional teacher as director of a group.
        """
        group = await self.get_group_by_id(
            group_id=group_id,
            institution_id=institution_id,
        )

        teacher = (
            await self._session.execute(
                select(Teacher).where(
                    Teacher.id == teacher_id,
                    Teacher.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not teacher:
            raise CrossTenantMismatchError(
                "El docente asignado como director no pertenece a la institución."
            )

        group.group_director_teacher_id = teacher_id
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GROUP_DIRECTOR_ASSIGNED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(group.id),
                target_type="Group",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"director_teacher_id": str(teacher_id)},
            ),
            session=self._session,
        )

        return group

    async def get_available_capacity(
        self,
        *,
        group_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> tuple[int, int, int]:
        """
        Calculate group capacity.

        Returns:
            tuple of (capacity_limit, active_enrolled_count, available_slots)
        """
        group = await self.get_group_by_id(
            group_id=group_id,
            institution_id=institution_id,
        )

        count_stmt = select(func.count(Enrollment.id)).where(
            Enrollment.group_id == group.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        active_count = (await self._session.execute(count_stmt)).scalar() or 0
        available = max(0, group.capacity_limit - active_count)

        return (group.capacity_limit, active_count, available)
