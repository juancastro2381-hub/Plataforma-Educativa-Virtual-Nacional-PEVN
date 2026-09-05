"""
PEVN Backend — Enrollment Domain Service

Authoritative business logic for student enrollments (Matrículas),
enforcing the single-active enrollment invariant per academic year,
transactional group capacity locking via SELECT FOR UPDATE, and historical immutability.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from http import HTTPStatus

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    EnrollmentNotFoundError,
    GroupCapacityExceededError,
    GroupNotFoundError,
    StudentAlreadyEnrolledActiveError,
    StudentNotFoundError,
)
from app.core.logging import get_logger
from app.core.security.interfaces import AuthorizationContext
from app.models.academic_year import AcademicYear, AcademicYearStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.group import Group
from app.models.institution import Campus
from app.models.student import Student
from app.models.user import User
from app.services.academic_scope_helper import (
    get_teacher_authorized_group_ids,
    is_directive_actor,
)

_logger = get_logger(__name__)


class EnrollmentService:
    """
    Domain service for Student Enrollment and lifecycle management.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_enrollment(
        self,
        *,
        institution_id: uuid.UUID,
        student_id: uuid.UUID,
        group_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        enrollment_date: date | None = None,
        status: EnrollmentStatus = EnrollmentStatus.ACTIVE,
        status_reason: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Enrollment:
        """
        Create a new student enrollment contract.

        Invariants:
          - Multi-tenant validation across Student, Group, Campus, and Academic Year.
          - Student may only have ONE ACTIVE enrollment per academic year.
          - Group capacity checked with row-level locking (SELECT FOR UPDATE).
        """
        target_date = enrollment_date or datetime.now(tz=UTC).date()

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
                f"Estudiante {student_id} no pertenece a la institución."
            )

        # 2. Validate Academic Year Tenant Ownership & Active Status
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
        if ay.status != AcademicYearStatus.ACTIVE:
            raise AcademicDomainError(
                "No se pueden crear matrículas en un año lectivo que no esté activo.",
                code="ACADEMIC_YEAR_NOT_ACTIVE",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        # 3. Validate Group and Campus Tenant Ownership WITH ROW LOCKING
        group_stmt = (
            select(Group)
            .join(Campus, Group.campus_id == Campus.id)
            .where(
                Group.id == group_id,
                Campus.institution_id == institution_id,
            )
            .with_for_update()
        )
        group = (await self._session.execute(group_stmt)).scalar_one_or_none()
        if not group:
            raise GroupNotFoundError(
                f"Grupo {group_id} no encontrado en la institución."
            )

        if group.academic_year_id != academic_year_id:
            raise AcademicDomainError(
                "El grupo no corresponde al año lectivo indicado."
            )

        # 4. Check Active Enrollment Invariant
        if status == EnrollmentStatus.ACTIVE:
            active_stmt = select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.academic_year_id == academic_year_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            existing_active = (
                await self._session.execute(active_stmt)
            ).scalar_one_or_none()
            if existing_active:
                raise StudentAlreadyEnrolledActiveError()

            # 5. Check Group Capacity under Row Lock
            count_stmt = select(func.count(Enrollment.id)).where(
                Enrollment.group_id == group.id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            current_enrolled = (await self._session.execute(count_stmt)).scalar() or 0
            if current_enrolled >= group.capacity_limit:
                raise GroupCapacityExceededError(
                    f"El grupo '{group.name}' no tiene cupos disponibles "
                    f"({current_enrolled}/{group.capacity_limit})."
                )

        enrollment = Enrollment(
            student_id=student_id,
            group_id=group_id,
            academic_year_id=academic_year_id,
            enrollment_date=target_date,
            status=status,
            status_reason=status_reason,
        )
        self._session.add(enrollment)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ENROLLMENT_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(enrollment.id),
                target_type="Enrollment",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "student_id": str(student_id),
                    "group_id": str(group_id),
                    "academic_year_id": str(academic_year_id),
                    "status": status.value,
                },
            ),
            session=self._session,
        )

        return enrollment

    async def list_enrollments(
        self,
        *,
        institution_id: uuid.UUID,
        user: User | None = None,
        auth: AuthorizationContext | None = None,
        student_id: uuid.UUID | None = None,
        group_id: uuid.UUID | None = None,
        academic_year_id: uuid.UUID | None = None,
        status_filter: EnrollmentStatus | None = None,
    ) -> list[Enrollment]:
        """
        List enrollments within the institution.
        If caller is a Teacher without directive roles, strictly restricts results
        to enrollments in groups within the teacher's authorized academic scope.
        """
        is_directive = is_directive_actor(auth, user=user)

        query = (
            select(Enrollment)
            .join(Student, Enrollment.student_id == Student.id)
            .options(
                selectinload(Enrollment.student).selectinload(Student.user),
                selectinload(Enrollment.group),
                selectinload(Enrollment.academic_year),
            )
            .where(Student.institution_id == institution_id)
        )

        if not is_directive:
            if not user:
                return []
            authorized_group_ids = await get_teacher_authorized_group_ids(
                self._session,
                user_id=user.id,
                institution_id=institution_id,
            )
            if not authorized_group_ids:
                return []
            query = query.where(Enrollment.group_id.in_(authorized_group_ids))

        if student_id:
            query = query.where(Enrollment.student_id == student_id)
        if group_id:
            query = query.where(Enrollment.group_id == group_id)
        if academic_year_id:
            query = query.where(Enrollment.academic_year_id == academic_year_id)
        if status_filter:
            query = query.where(Enrollment.status == status_filter)

        query = query.order_by(Enrollment.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_enrollment_by_id(
        self,
        *,
        enrollment_id: uuid.UUID,
        institution_id: uuid.UUID,
        user: User | None = None,
        auth: AuthorizationContext | None = None,
    ) -> Enrollment:
        """
        Retrieve an enrollment record validating tenant isolation and teacher academic scope.
        """
        is_directive = is_directive_actor(auth, user=user)

        stmt = (
            select(Enrollment)
            .join(Student, Enrollment.student_id == Student.id)
            .options(
                selectinload(Enrollment.student),
                selectinload(Enrollment.group),
                selectinload(Enrollment.academic_year),
                selectinload(Enrollment.transfer_history),
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

        if not is_directive:
            if not user:
                raise EnrollmentNotFoundError(f"Matrícula {enrollment_id} no encontrada.")
            authorized_group_ids = await get_teacher_authorized_group_ids(
                self._session,
                user_id=user.id,
                institution_id=institution_id,
            )
            if enrollment.group_id not in authorized_group_ids:
                raise EnrollmentNotFoundError(
                    f"Matrícula {enrollment_id} no encontrada en su ámbito académico."
                )

        return enrollment

    async def activate_enrollment(
        self,
        *,
        enrollment_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Enrollment:
        """
        Transition a PRE_ENROLLED record to ACTIVE status.
        """
        enrollment = await self.get_enrollment_by_id(
            enrollment_id=enrollment_id,
            institution_id=institution_id,
        )

        if enrollment.status != EnrollmentStatus.PRE_ENROLLED:
            raise AcademicDomainError(
                "Solo una prematrícula puede activarse "
                f"(estado actual: {enrollment.status.value})."
            )

        # Check Active Invariant
        active_stmt = select(Enrollment).where(
            Enrollment.student_id == enrollment.student_id,
            Enrollment.academic_year_id == enrollment.academic_year_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        if (await self._session.execute(active_stmt)).scalar_one_or_none():
            raise StudentAlreadyEnrolledActiveError()

        # Check capacity with row lock
        group_stmt = (
            select(Group).where(Group.id == enrollment.group_id).with_for_update()
        )
        group = (await self._session.execute(group_stmt)).scalar_one()

        count_stmt = select(func.count(Enrollment.id)).where(
            Enrollment.group_id == group.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        current_enrolled = (await self._session.execute(count_stmt)).scalar() or 0
        if current_enrolled >= group.capacity_limit:
            raise GroupCapacityExceededError(
                f"El grupo '{group.name}' no tiene cupos disponibles "
                f"({current_enrolled}/{group.capacity_limit})."
            )

        enrollment.status = EnrollmentStatus.ACTIVE
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ENROLLMENT_ACTIVATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(enrollment.id),
                target_type="Enrollment",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"status": "ACTIVE"},
            ),
            session=self._session,
        )

        return enrollment

    async def withdraw_enrollment(
        self,
        *,
        enrollment_id: uuid.UUID,
        institution_id: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Enrollment:
        """
        Transition an ACTIVE enrollment to WITHDRAWN status preserving history.
        """
        enrollment = await self.get_enrollment_by_id(
            enrollment_id=enrollment_id,
            institution_id=institution_id,
        )

        if enrollment.status not in (
            EnrollmentStatus.ACTIVE,
            EnrollmentStatus.PRE_ENROLLED,
        ):
            raise AcademicDomainError(
                f"No se puede retirar matrícula en estado {enrollment.status.value}."
            )

        enrollment.status = EnrollmentStatus.WITHDRAWN
        enrollment.status_reason = reason
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ENROLLMENT_WITHDRAWN,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(enrollment.id),
                target_type="Enrollment",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"reason": reason, "status": "WITHDRAWN"},
            ),
            session=self._session,
        )

        return enrollment

    async def graduate_enrollment(
        self,
        *,
        enrollment_id: uuid.UUID,
        institution_id: uuid.UUID,
        reason: str = "Culminación exitosa del año lectivo",
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Enrollment:
        """
        Transition an ACTIVE enrollment to GRADUATED status.
        """
        enrollment = await self.get_enrollment_by_id(
            enrollment_id=enrollment_id,
            institution_id=institution_id,
        )

        if enrollment.status != EnrollmentStatus.ACTIVE:
            raise AcademicDomainError(
                "Solo una matrícula activa puede graduarse "
                f"(actual: {enrollment.status.value})."
            )

        enrollment.status = EnrollmentStatus.GRADUATED
        enrollment.status_reason = reason
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ENROLLMENT_GRADUATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(enrollment.id),
                target_type="Enrollment",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"reason": reason, "status": "GRADUATED"},
            ),
            session=self._session,
        )

        return enrollment

    async def get_active_enrollment(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> Enrollment | None:
        """
        Retrieve current active enrollment for a student in a specific year.
        """
        stmt = (
            select(Enrollment)
            .join(Student, Enrollment.student_id == Student.id)
            .options(
                selectinload(Enrollment.group),
                selectinload(Enrollment.academic_year),
            )
            .where(
                Enrollment.student_id == student_id,
                Enrollment.academic_year_id == academic_year_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
                Student.institution_id == institution_id,
            )
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_enrollment_history(
        self,
        *,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> list[Enrollment]:
        """
        Retrieve all historical enrollments for a student.
        """
        stmt = (
            select(Enrollment)
            .join(Student, Enrollment.student_id == Student.id)
            .options(
                selectinload(Enrollment.group),
                selectinload(Enrollment.academic_year),
                selectinload(Enrollment.transfer_history),
            )
            .where(
                Enrollment.student_id == student_id,
                Student.institution_id == institution_id,
            )
            .order_by(Enrollment.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
