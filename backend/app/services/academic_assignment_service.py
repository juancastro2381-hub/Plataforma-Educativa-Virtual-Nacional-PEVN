"""
PEVN Backend — Academic Assignment Domain Service

Authoritative business logic for teacher workload assignments (Carga Académica Docente),
enforcing the single-active instructor invariant per (subject, group, academic year),
teacher replacement workflows preserving historical records, and multi-tenant isolation.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicAssignmentNotFoundError,
    AcademicDomainError,
    CrossTenantMismatchError,
    DuplicateActiveAssignmentError,
    GroupNotFoundError,
    TeacherNotFoundError,
)
from app.core.logging import get_logger
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicYear
from app.models.group import Group
from app.models.institution import Campus
from app.models.subject import Subject
from app.models.teacher import Teacher

_logger = get_logger(__name__)


class AcademicAssignmentService:
    """
    Domain service for Teacher Academic Assignments and workload management.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_assignment(
        self,
        *,
        institution_id: uuid.UUID,
        teacher_id: uuid.UUID,
        subject_id: uuid.UUID,
        group_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        weekly_hours: int,
        is_active: bool = True,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> AcademicAssignment:
        """
        Create a teacher academic assignment enforcing tenant and
        single-active invariants.
        """
        if weekly_hours <= 0:
            raise AcademicDomainError(
                "La intensidad horaria semanal debe ser mayor a cero."
            )

        # 1. Validate Teacher Tenant Ownership
        teacher = (
            await self._session.execute(
                select(Teacher).where(
                    Teacher.id == teacher_id,
                    Teacher.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not teacher:
            raise TeacherNotFoundError(
                f"Docente {teacher_id} no encontrado en la institución."
            )

        # 2. Validate Subject Tenant Ownership
        subject = (
            await self._session.execute(
                select(Subject).where(
                    Subject.id == subject_id,
                    Subject.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not subject:
            raise AcademicDomainError(
                f"Materia {subject_id} no pertenece a la institución."
            )

        # 3. Validate Group and Campus Tenant Ownership
        group = (
            await self._session.execute(
                select(Group)
                .join(Campus, Group.campus_id == Campus.id)
                .where(
                    Group.id == group_id,
                    Campus.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not group:
            raise GroupNotFoundError(f"Grupo {group_id} no pertenece a la institución.")

        # 4. Validate Academic Year Tenant Ownership
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

        if group.academic_year_id != academic_year_id:
            raise AcademicDomainError(
                "El grupo no corresponde al año lectivo indicado."
            )

        # 5. Check Single Active Assignment Invariant
        if is_active:
            active_stmt = select(AcademicAssignment).where(
                AcademicAssignment.subject_id == subject_id,
                AcademicAssignment.group_id == group_id,
                AcademicAssignment.academic_year_id == academic_year_id,
                AcademicAssignment.is_active.is_(True),
            )
            if (await self._session.execute(active_stmt)).scalar_one_or_none():
                raise DuplicateActiveAssignmentError()

        assignment = AcademicAssignment(
            teacher_id=teacher_id,
            subject_id=subject_id,
            group_id=group_id,
            academic_year_id=academic_year_id,
            weekly_hours=weekly_hours,
            is_active=is_active,
        )
        self._session.add(assignment)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACADEMIC_ASSIGNMENT_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(assignment.id),
                target_type="AcademicAssignment",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "teacher_id": str(teacher_id),
                    "subject_id": str(subject_id),
                    "group_id": str(group_id),
                    "weekly_hours": weekly_hours,
                },
            ),
            session=self._session,
        )

        return assignment

    async def get_assignment_by_id(
        self,
        *,
        assignment_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> AcademicAssignment:
        """
        Retrieve an assignment validating tenant isolation via teacher link.
        """
        stmt = (
            select(AcademicAssignment)
            .join(Teacher, AcademicAssignment.teacher_id == Teacher.id)
            .options(
                selectinload(AcademicAssignment.teacher),
                selectinload(AcademicAssignment.subject),
                selectinload(AcademicAssignment.group),
                selectinload(AcademicAssignment.academic_year),
            )
            .where(
                AcademicAssignment.id == assignment_id,
                Teacher.institution_id == institution_id,
            )
        )
        assignment = (await self._session.execute(stmt)).scalar_one_or_none()
        if not assignment:
            raise AcademicAssignmentNotFoundError(
                "Asignación académica "
                f"{assignment_id} no encontrada en la institución."
            )
        return assignment

    async def replace_teacher(
        self,
        *,
        assignment_id: uuid.UUID,
        new_teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> tuple[AcademicAssignment, AcademicAssignment]:
        """
        Atomically replace active instructor for a subject in a group,
        deactivating previous assignment while preserving full history.
        """
        # 1. Fetch current assignment
        current = await self.get_assignment_by_id(
            assignment_id=assignment_id,
            institution_id=institution_id,
        )

        if not current.is_active:
            raise AcademicDomainError(
                "No se puede sustituir el docente de una asignación inactiva."
            )

        if current.teacher_id == new_teacher_id:
            raise AcademicDomainError(
                "El docente ya es el titular activo de esta materia en el grupo."
            )

        # 2. Validate New Teacher Tenant Ownership
        new_teacher = (
            await self._session.execute(
                select(Teacher).where(
                    Teacher.id == new_teacher_id,
                    Teacher.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not new_teacher:
            raise TeacherNotFoundError(
                f"Nuevo docente {new_teacher_id} no pertenece a la institución."
            )

        # 3. Deactivate current assignment
        current.is_active = False

        # 4. Create new replacement assignment
        new_assignment = AcademicAssignment(
            teacher_id=new_teacher.id,
            subject_id=current.subject_id,
            group_id=current.group_id,
            academic_year_id=current.academic_year_id,
            weekly_hours=current.weekly_hours,
            is_active=True,
        )
        self._session.add(new_assignment)
        await self._session.flush()

        # 5. Emit Audit Log
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACADEMIC_ASSIGNMENT_REPLACED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(new_assignment.id),
                target_type="AcademicAssignment",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "previous_assignment_id": str(current.id),
                    "previous_teacher_id": str(current.teacher_id),
                    "new_teacher_id": str(new_teacher.id),
                    "subject_id": str(current.subject_id),
                    "group_id": str(current.group_id),
                },
            ),
            session=self._session,
        )

        return current, new_assignment

    async def deactivate_assignment(
        self,
        *,
        assignment_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> AcademicAssignment:
        """
        Deactivate an active assignment.
        """
        assignment = await self.get_assignment_by_id(
            assignment_id=assignment_id,
            institution_id=institution_id,
        )

        if not assignment.is_active:
            raise AcademicDomainError(
                "La asignación académica ya se encuentra inactiva."
            )

        assignment.is_active = False
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACADEMIC_ASSIGNMENT_DEACTIVATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(assignment.id),
                target_type="AcademicAssignment",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"status": "INACTIVE"},
            ),
            session=self._session,
        )

        return assignment
