"""
PEVN Backend — Group Transfer Domain Service

Authoritative business logic for student classroom transfers (Traslados de Grupo),
enforcing atomic execution, destination capacity validation via SELECT FOR UPDATE,
and immutable historical audit logging in group_transfer_history.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    CrossTenantMismatchError,
    EnrollmentNotFoundError,
    GroupCapacityExceededError,
    GroupNotFoundError,
    InvalidTransferError,
)
from app.core.logging import get_logger
from app.models.enrollment import (
    Enrollment,
    EnrollmentStatus,
    GroupTransferHistory,
)
from app.models.group import Group
from app.models.institution import Campus
from app.models.student import Student
from app.models.user import User

_logger = get_logger(__name__)


class TransferService:
    """
    Domain service for student Group Transfer transactions.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def transfer_student_group(
        self,
        *,
        enrollment_id: uuid.UUID,
        target_group_id: uuid.UUID,
        institution_id: uuid.UUID,
        transferred_by_user_id: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> tuple[Enrollment, GroupTransferHistory]:
        """
        Execute an atomic group transfer for an active student enrollment.

        Transaction Workflow:
          1. Validate current enrollment & institutional tenancy.
          2. Ensure enrollment is ACTIVE.
          3. Validate target group tenancy & academic year match.
          4. Lock target group row (SELECT FOR UPDATE) and verify capacity.
          5. Create immutable GroupTransferHistory record.
          6. Update enrollment.group_id to destination group.
          7. Record audit log and return updated records.
        """
        # 1. Fetch current Enrollment with tenancy validation
        stmt = (
            select(Enrollment)
            .join(Student, Enrollment.student_id == Student.id)
            .options(
                selectinload(Enrollment.student),
                selectinload(Enrollment.group),
                selectinload(Enrollment.academic_year),
            )
            .where(
                Enrollment.id == enrollment_id,
                Student.institution_id == institution_id,
            )
        )
        enrollment = (await self._session.execute(stmt)).scalar_one_or_none()
        if not enrollment:
            raise EnrollmentNotFoundError(
                f"Matrícula {enrollment_id} no encontrada en la institución."
            )

        # 2. Invariant: Only ACTIVE enrollments can be transferred
        if enrollment.status != EnrollmentStatus.ACTIVE:
            raise InvalidTransferError(
                "No se puede trasladar una matrícula en estado "
                f"'{enrollment.status.value}'."
            )

        previous_group_id = enrollment.group_id
        if previous_group_id == target_group_id:
            raise InvalidTransferError(
                "El estudiante ya se encuentra matriculado en el grupo destino."
            )

        # 3. Validate Authorizing User Tenancy
        auth_user = (
            await self._session.execute(
                select(User).where(
                    User.id == transferred_by_user_id,
                    User.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not auth_user:
            raise CrossTenantMismatchError(
                "El usuario que autoriza el traslado no pertenece a la institución."
            )

        # 4. Fetch & Lock Target Group row (SELECT FOR UPDATE)
        target_group_stmt = (
            select(Group)
            .join(Campus, Group.campus_id == Campus.id)
            .where(
                Group.id == target_group_id,
                Campus.institution_id == institution_id,
            )
            .with_for_update()
        )
        target_group = (
            await self._session.execute(target_group_stmt)
        ).scalar_one_or_none()
        if not target_group:
            raise GroupNotFoundError(
                f"Grupo destino {target_group_id} no pertenece a la institución."
            )

        # Ensure target group belongs to the exact same academic year
        if target_group.academic_year_id != enrollment.academic_year_id:
            raise InvalidTransferError(
                "El grupo destino no pertenece al mismo año lectivo de la matrícula."
            )

        # 5. Check Target Group Capacity under Row Lock
        count_stmt = select(func.count(Enrollment.id)).where(
            Enrollment.group_id == target_group.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        current_target_enrolled = (
            await self._session.execute(count_stmt)
        ).scalar() or 0
        if current_target_enrolled >= target_group.capacity_limit:
            raise GroupCapacityExceededError(
                f"El grupo destino '{target_group.name}' no tiene cupos disponibles "
                f"({current_target_enrolled}/{target_group.capacity_limit})."
            )

        # 6. Create Immutable GroupTransferHistory audit entry
        transfer_history = GroupTransferHistory(
            enrollment_id=enrollment.id,
            previous_group_id=previous_group_id,
            new_group_id=target_group.id,
            transferred_by_user_id=transferred_by_user_id,
            reason=reason,
        )
        self._session.add(transfer_history)

        # 7. Update Enrollment Group pointer
        enrollment.group_id = target_group.id
        await self._session.flush()

        # 8. Emit Centralized Audit Log
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ENROLLMENT_TRANSFERRED,
                actor_id=str(actor_id or transferred_by_user_id),
                actor_ip=actor_ip,
                target_id=str(enrollment.id),
                target_type="Enrollment",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "student_id": str(enrollment.student_id),
                    "from_group_id": str(previous_group_id),
                    "to_group_id": str(target_group.id),
                    "reason": reason,
                },
            ),
            session=self._session,
        )

        return enrollment, transfer_history
