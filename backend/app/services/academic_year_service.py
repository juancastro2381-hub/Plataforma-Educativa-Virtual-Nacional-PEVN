"""
PEVN Backend — Academic Year Domain Service

Authoritative business logic for academic school years, term periods,
and year lifecycle transitions.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    AcademicYearLifecycleError,
    AcademicYearNotFoundError,
)
from app.core.logging import get_logger
from app.models.academic_year import (
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)

_logger = get_logger(__name__)


class AcademicYearService:
    """
    Domain service for Academic Year entities and lifecycle operations.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_academic_year(
        self,
        *,
        institution_id: uuid.UUID,
        year: int,
        name: str,
        start_date: date,
        end_date: date,
        calendar_type: AcademicYearCalendarType = (AcademicYearCalendarType.CALENDAR_A),
        status: AcademicYearStatus = AcademicYearStatus.PLANNING,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> AcademicYear:
        """
        Create a new academic school year for an institution.

        Invariants:
          - start_date < end_date
          - Unique year per institution
        """
        if start_date >= end_date:
            raise AcademicDomainError(
                "La fecha de inicio debe ser anterior a la fecha de finalización."
            )

        # Check year uniqueness per institution
        existing_stmt = select(AcademicYear).where(
            AcademicYear.institution_id == institution_id,
            AcademicYear.year == year,
        )
        existing = (await self._session.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            raise AcademicDomainError(
                f"Ya existe un año lectivo {year} para esta institución."
            )

        academic_year = AcademicYear(
            institution_id=institution_id,
            year=year,
            name=name,
            start_date=start_date,
            end_date=end_date,
            calendar_type=calendar_type,
            status=status,
        )
        self._session.add(academic_year)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACADEMIC_YEAR_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(academic_year.id),
                target_type="AcademicYear",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "year": year,
                    "name": name,
                    "status": status.value,
                },
            ),
            session=self._session,
        )

        return academic_year

    async def get_academic_year_by_id(
        self,
        *,
        year_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> AcademicYear:
        """
        Retrieve an academic year validating tenant isolation.
        """
        stmt = select(AcademicYear).where(
            AcademicYear.id == year_id,
            AcademicYear.institution_id == institution_id,
        )
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        if not result:
            raise AcademicYearNotFoundError(
                f"Año lectivo {year_id} no encontrado en la institución."
            )
        return result

    async def get_active_academic_year(
        self,
        *,
        institution_id: uuid.UUID,
    ) -> AcademicYear | None:
        """
        Retrieve the currently ACTIVE academic year for the institution.
        """
        stmt = select(AcademicYear).where(
            AcademicYear.institution_id == institution_id,
            AcademicYear.status == AcademicYearStatus.ACTIVE,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def activate_academic_year(
        self,
        *,
        year_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> AcademicYear:
        """
        Transition academic year status to ACTIVE.

        Invariants:
          - Only PLANNING can transition to ACTIVE.
          - No other ACTIVE year simultaneously without closing.
        """
        academic_year = await self.get_academic_year_by_id(
            year_id=year_id,
            institution_id=institution_id,
        )

        if academic_year.status != AcademicYearStatus.PLANNING:
            raise AcademicYearLifecycleError(
                "Solo un año en estado PLANEACIÓN puede ser activado "
                f"(actual: {academic_year.status.value})."
            )

        active_current = await self.get_active_academic_year(
            institution_id=institution_id
        )
        if active_current and active_current.id != academic_year.id:
            raise AcademicYearLifecycleError(
                f"Ya existe un año lectivo activo ({active_current.year}). "
                "Debe cerrarlo antes de activar otro."
            )

        academic_year.status = AcademicYearStatus.ACTIVE
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACADEMIC_YEAR_ACTIVATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(academic_year.id),
                target_type="AcademicYear",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"year": academic_year.year, "status": "ACTIVE"},
            ),
            session=self._session,
        )

        return academic_year

    async def close_academic_year(
        self,
        *,
        year_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> AcademicYear:
        """
        Transition academic year status to CLOSED.
        """
        academic_year = await self.get_academic_year_by_id(
            year_id=year_id,
            institution_id=institution_id,
        )

        if academic_year.status == AcademicYearStatus.CLOSED:
            raise AcademicYearLifecycleError("El año lectivo ya se encuentra cerrado.")

        academic_year.status = AcademicYearStatus.CLOSED
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACADEMIC_YEAR_CLOSED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(academic_year.id),
                target_type="AcademicYear",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"year": academic_year.year, "status": "CLOSED"},
            ),
            session=self._session,
        )

        return academic_year
