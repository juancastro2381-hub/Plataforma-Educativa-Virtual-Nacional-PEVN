"""
PEVN Backend — Academic Year Domain Service

Authoritative business logic for academic school years, term periods,
and year lifecycle transitions.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

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
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.evaluation import SieePolicy
from app.schemas.academic import (
    AcademicPeriodResponse,
    AcademicPeriodTemplateType,
    DraftPeriodItem,
    PeriodTemplatePreviewResponse,
    PeriodTemplateProvisionRequest,
    PeriodTemplateProvisionResponse,
    SieeComplianceMetadata,
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

    async def create_academic_period(
        self,
        *,
        year_id: uuid.UUID,
        institution_id: uuid.UUID,
        period_number: int,
        name: str,
        weight_percentage: float,
        start_date: date,
        end_date: date,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> AcademicPeriod:
        """
        Create a new academic period within an academic school year.

        Invariants:
          - Year must belong to the institution (tenant boundary).
          - Year cannot be CLOSED.
          - start_date < end_date.
          - start_date and end_date within academic year date range.
          - period_number must be unique within the year.
          - weight_percentage > 0 and <= 100.
          - sum of period weights within the year must not exceed 100%.
        """
        academic_year = await self.get_academic_year_by_id(
            year_id=year_id,
            institution_id=institution_id,
        )

        if academic_year.status == AcademicYearStatus.CLOSED:
            raise AcademicDomainError(
                "No se pueden crear períodos en un año lectivo cerrado."
            )

        if start_date >= end_date:
            raise AcademicDomainError(
                "La fecha de inicio del período debe ser anterior a la fecha de finalización."
            )

        if start_date < academic_year.start_date or end_date > academic_year.end_date:
            raise AcademicDomainError(
                f"Las fechas del período ({start_date} a {end_date}) deben estar comprendidas "
                f"dentro de la vigencia del año lectivo ({academic_year.start_date} a {academic_year.end_date})."
            )

        # Unique period_number within this academic year
        existing_num_stmt = select(AcademicPeriod).where(
            AcademicPeriod.academic_year_id == academic_year.id,
            AcademicPeriod.period_number == period_number,
        )
        existing_num = (await self._session.execute(existing_num_stmt)).scalar_one_or_none()
        if existing_num:
            raise AcademicDomainError(
                f"El período número #{period_number} ya se encuentra registrado en este año lectivo."
            )

        if weight_percentage <= 0 or weight_percentage > 100:
            raise AcademicDomainError(
                "El porcentaje de ponderación debe ser mayor a 0% y menor o igual a 100%."
            )

        # Validate accumulated weight
        existing_weights_stmt = select(AcademicPeriod.weight_percentage).where(
            AcademicPeriod.academic_year_id == academic_year.id
        )
        existing_weights = (await self._session.execute(existing_weights_stmt)).scalars().all()
        accumulated_weight = sum(float(w) for w in existing_weights) + float(weight_percentage)
        if accumulated_weight > 100.001:
            raise AcademicDomainError(
                f"La ponderación acumulada ({accumulated_weight:.2f}%) superaría el 100% permitido "
                "para el año lectivo."
            )

        period = AcademicPeriod(
            academic_year_id=academic_year.id,
            period_number=period_number,
            name=name.strip(),
            weight_percentage=Decimal(str(round(weight_percentage, 2))),
            start_date=start_date,
            end_date=end_date,
            is_closed=False,
        )
        self._session.add(period)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACADEMIC_PERIOD_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(period.id),
                target_type="AcademicPeriod",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "academic_year_id": str(academic_year.id),
                    "period_number": period_number,
                    "name": period.name,
                    "weight_percentage": float(period.weight_percentage),
                },
            ),
            session=self._session,
        )

        return period

    @staticmethod
    def _get_template_specs(
        template_type: AcademicPeriodTemplateType,
        custom_period_count: int | None = None,
    ) -> list[tuple[int, str, float]]:
        if template_type == AcademicPeriodTemplateType.SEMESTRAL_2:
            return [
                (1, "Primer Semestre", 50.0),
                (2, "Segundo Semestre", 50.0),
            ]
        elif template_type == AcademicPeriodTemplateType.TRIMESTRAL_3:
            return [
                (1, "Primer Período", 33.33),
                (2, "Segundo Período", 33.33),
                (3, "Tercer Período", 33.34),
            ]
        elif template_type == AcademicPeriodTemplateType.PERIODS_5:
            return [
                (1, "Primer Período", 20.0),
                (2, "Segundo Período", 20.0),
                (3, "Tercer Período", 20.0),
                (4, "Cuarto Período", 20.0),
                (5, "Quinto Período", 20.0),
            ]
        elif template_type == AcademicPeriodTemplateType.CUSTOM:
            count = max(1, min(10, custom_period_count or 4))
            base_w = round(100.0 / count, 2)
            remainder = round(100.0 - (base_w * count), 2)
            names = [
                "Primer Período",
                "Segundo Período",
                "Tercer Período",
                "Cuarto Período",
                "Quinto Período",
                "Sexto Período",
                "Séptimo Período",
                "Octavo Período",
                "Noveno Período",
                "Décimo Período",
            ]
            specs = []
            for i in range(1, count + 1):
                w = base_w + (remainder if i == count else 0.0)
                name = names[i - 1] if i - 1 < len(names) else f"Período {i}"
                specs.append((i, name, round(w, 2)))
            return specs
        else:  # PERIODS_4
            return [
                (1, "Primer Período", 25.0),
                (2, "Segundo Período", 25.0),
                (3, "Tercer Período", 25.0),
                (4, "Cuarto Período", 25.0),
            ]

    @staticmethod
    def _get_template_label(
        template_type: AcademicPeriodTemplateType,
        count: int,
    ) -> str:
        labels = {
            AcademicPeriodTemplateType.SEMESTRAL_2: "2 períodos — Semestral (50% / 50%)",
            AcademicPeriodTemplateType.TRIMESTRAL_3: "3 períodos — Trimestral (33.33% / 33.33% / 33.34%)",
            AcademicPeriodTemplateType.PERIODS_4: "4 períodos — Cuatro períodos de evaluación (25% cada uno) [Referencia institucional]",
            AcademicPeriodTemplateType.PERIODS_5: "5 períodos — Cinco períodos de evaluación (20% cada uno)",
            AcademicPeriodTemplateType.CUSTOM: f"Configuración personalizada ({count} períodos)",
        }
        return labels.get(template_type, f"{count} períodos")

    async def preview_period_template(
        self,
        *,
        year_id: uuid.UUID,
        institution_id: uuid.UUID,
        template_type: AcademicPeriodTemplateType = AcademicPeriodTemplateType.PERIODS_4,
        custom_period_count: int | None = None,
    ) -> PeriodTemplatePreviewResponse:
        """
        Generate a non-destructive draft preview for academic evaluation periods.

        Invariants:
          - Validates tenant isolation and academic year ownership.
          - Retrieves existing periods without destructive reset or overwrite.
          - Reconciles existing records with the selected template structure.
          - Detects date overlaps, date boundary breaches, and weight distribution gaps.
          - Clearly labels generated dates as provisional and provides full regulatory context.
        """
        academic_year = await self.get_academic_year_by_id(
            year_id=year_id,
            institution_id=institution_id,
        )

        # 1. Fetch existing periods for this academic year
        existing_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.academic_year_id == academic_year.id)
            .order_by(AcademicPeriod.period_number.asc())
        )
        existing_periods = list((await self._session.execute(existing_stmt)).scalars().all())
        existing_responses = [AcademicPeriodResponse.model_validate(p) for p in existing_periods]

        # 2. Build period specifications for the chosen template
        template_specs = self._get_template_specs(template_type, custom_period_count)
        template_label = self._get_template_label(template_type, len(template_specs))

        # 3. Calculate provisional date slices based on academic year boundaries
        total_days = (academic_year.end_date - academic_year.start_date).days + 1
        num_periods = len(template_specs)
        slice_size = max(1, total_days // num_periods)
        remainder = total_days % num_periods

        generated_date_ranges: list[tuple[date, date]] = []
        for i in range(num_periods):
            offset_start = i * slice_size + min(i, remainder)
            offset_end = (i + 1) * slice_size + min(i + 1, remainder) - 1
            p_start = academic_year.start_date + timedelta(days=offset_start)
            p_end = academic_year.start_date + timedelta(days=offset_end)
            generated_date_ranges.append((p_start, p_end))

        # 4. Map existing periods by period_number
        existing_by_num = {p.period_number: p for p in existing_periods}

        # 5. Non-destructive reconciliation
        proposed_periods: list[DraftPeriodItem] = []
        covered_numbers = set()

        for idx, (p_num, default_name, default_weight) in enumerate(template_specs):
            covered_numbers.add(p_num)
            if p_num in existing_by_num:
                # Retain existing period exactly as configured in DB
                existing = existing_by_num[p_num]
                proposed_periods.append(
                    DraftPeriodItem(
                        period_number=existing.period_number,
                        name=existing.name,
                        weight_percentage=float(existing.weight_percentage),
                        start_date=existing.start_date,
                        end_date=existing.end_date,
                        is_existing=True,
                        existing_period_id=existing.id,
                        conflict_reason=None,
                    )
                )
            else:
                # Propose missing period with derived provisional dates
                p_start, p_end = generated_date_ranges[idx]
                proposed_periods.append(
                    DraftPeriodItem(
                        period_number=p_num,
                        name=default_name,
                        weight_percentage=default_weight,
                        start_date=p_start,
                        end_date=p_end,
                        is_existing=False,
                        existing_period_id=None,
                        conflict_reason=None,
                    )
                )

        # Include any existing periods outside template specification count
        for p in existing_periods:
            if p.period_number not in covered_numbers:
                proposed_periods.append(
                    DraftPeriodItem(
                        period_number=p.period_number,
                        name=p.name,
                        weight_percentage=float(p.weight_percentage),
                        start_date=p.start_date,
                        end_date=p.end_date,
                        is_existing=True,
                        existing_period_id=p.id,
                        conflict_reason=None,
                    )
                )

        # Sort combined periods by period_number
        proposed_periods.sort(key=lambda item: item.period_number)

        # 6. Comprehensive Conflict Analysis
        conflict_messages: list[str] = []

        total_weight_existing = sum(float(p.weight_percentage) for p in existing_periods)
        total_weight_proposed = sum(p.weight_percentage for p in proposed_periods if not p.is_existing)
        total_weight_combined = sum(p.weight_percentage for p in proposed_periods)

        # Weight validation
        if abs(total_weight_combined - 100.0) > 0.01:
            conflict_messages.append(
                f"La suma total de ponderaciones ({total_weight_combined:.2f}%) debe ser exactamente 100.00% "
                f"según los lineamientos del SIEE institucional (diferencia: {100.0 - total_weight_combined:+.2f}%)."
            )

        # Date ordering & bounds validation
        for p in proposed_periods:
            if p.start_date >= p.end_date:
                conflict_msg = (
                    f"El período #{p.period_number} ('{p.name}') tiene fecha de inicio ({p.start_date}) "
                    f"igual o posterior a su fecha de fin ({p.end_date})."
                )
                p.conflict_reason = conflict_msg
                conflict_messages.append(conflict_msg)
            elif p.start_date < academic_year.start_date or p.end_date > academic_year.end_date:
                conflict_msg = (
                    f"El período #{p.period_number} ('{p.name}') [{p.start_date} a {p.end_date}] "
                    f"excede la vigencia del año lectivo ({academic_year.start_date} a {academic_year.end_date})."
                )
                p.conflict_reason = conflict_msg
                conflict_messages.append(conflict_msg)

        # Date overlap check across periods
        sorted_by_dates = sorted(proposed_periods, key=lambda x: (x.start_date, x.period_number))
        for i in range(len(sorted_by_dates) - 1):
            curr = sorted_by_dates[i]
            nxt = sorted_by_dates[i + 1]
            if curr.end_date >= nxt.start_date:
                overlap_msg = (
                    f"Solapamiento de fechas: El período #{curr.period_number} ('{curr.name}') finaliza el {curr.end_date}, "
                    f"superponiéndose con el inicio del período #{nxt.period_number} ('{nxt.name}') ({nxt.start_date}). "
                    "Ajuste las fechas para evitar colisiones entre cortes de evaluación."
                )
                curr.conflict_reason = curr.conflict_reason or overlap_msg
                nxt.conflict_reason = nxt.conflict_reason or overlap_msg
                if overlap_msg not in conflict_messages:
                    conflict_messages.append(overlap_msg)

        has_conflicts = len(conflict_messages) > 0
        is_complete = not has_conflicts and abs(total_weight_combined - 100.0) <= 0.01

        disclaimer = (
            "Plantilla de referencia institucional — no obligatoria por el MEN. "
            "Conforme al Decreto 1290 de 2009 (Art. 4 Numeral 8) y la Ley 115 de 1994 (Art. 77), "
            "cada establecimiento educativo goza de autonomía para definir en su SIEE "
            "la periodicidad de informes y la ponderación de períodos, articulada con el calendario escolar territorial."
        )

        return PeriodTemplatePreviewResponse(
            academic_year_id=academic_year.id,
            academic_year_name=academic_year.name,
            academic_year_year=academic_year.year,
            academic_year_start=academic_year.start_date,
            academic_year_end=academic_year.end_date,
            calendar_type=academic_year.calendar_type,
            academic_year_status=academic_year.status,
            template_type=template_type,
            template_label=template_label,
            regulatory_disclaimer=disclaimer,
            existing_periods=existing_responses,
            proposed_periods=proposed_periods,
            total_weight_existing=round(total_weight_existing, 2),
            total_weight_proposed=round(total_weight_proposed, 2),
            total_weight_combined=round(total_weight_combined, 2),
            has_conflicts=has_conflicts,
            conflict_messages=conflict_messages,
            is_complete=is_complete,
        )

    async def provision_period_template(
        self,
        *,
        year_id: uuid.UUID,
        institution_id: uuid.UUID,
        payload: PeriodTemplateProvisionRequest,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> PeriodTemplateProvisionResponse:
        """
        Atomically provision, update, and optionally activate academic evaluation periods.

        Invariants:
          - Enforces institutional tenant isolation and year ownership.
          - Academic year must not be CLOSED.
          - Preserves existing period records without destructive resets.
          - Validates cumulative weights sum to exactly 100.00%.
          - Validates all dates within academic year bounds and strictly non-overlapping.
          - Enforces Rector SIEE compliance confirmation prior to activation.
          - Emits comprehensive audit events for provisioning, activation, and compliance.
        """
        academic_year = await self.get_academic_year_by_id(
            year_id=year_id,
            institution_id=institution_id,
        )

        if academic_year.status == AcademicYearStatus.CLOSED:
            raise AcademicDomainError(
                "No se pueden configurar ni aprovisionar períodos en un año lectivo cerrado."
            )

        if not payload.periods:
            raise AcademicDomainError("Debe incluir al menos un período en la configuración.")

        # 1. Decimal-safe weight total validation
        total_weight = sum(round(p.weight_percentage, 2) for p in payload.periods)
        if abs(total_weight - 100.0) > 0.01:
            raise AcademicDomainError(
                f"La suma de ponderaciones ({total_weight:.2f}%) debe ser exactamente 100.00% "
                f"conforme al SIEE institucional (diferencia: {100.0 - total_weight:+.2f}%)."
            )

        # 2. Sequential numbers and uniqueness
        period_numbers = [p.period_number for p in payload.periods]
        if len(period_numbers) != len(set(period_numbers)):
            raise AcademicDomainError("Los números de período no pueden repetirse dentro del año escolar.")

        # 3. Date boundary and ordering validation
        for p in payload.periods:
            if p.start_date >= p.end_date:
                raise AcademicDomainError(
                    f"El período #{p.period_number} ('{p.name}') tiene fecha de inicio ({p.start_date}) "
                    f"igual o posterior a su fecha de fin ({p.end_date})."
                )
            if p.start_date < academic_year.start_date or p.end_date > academic_year.end_date:
                raise AcademicDomainError(
                    f"El período #{p.period_number} ('{p.name}') [{p.start_date} a {p.end_date}] "
                    f"debe estar dentro de la vigencia del año lectivo ({academic_year.start_date} a {academic_year.end_date})."
                )

        # 4. Overlap validation
        sorted_periods = sorted(payload.periods, key=lambda x: (x.start_date, x.period_number))
        for i in range(len(sorted_periods) - 1):
            curr = sorted_periods[i]
            nxt = sorted_periods[i + 1]
            if curr.end_date >= nxt.start_date:
                raise AcademicDomainError(
                    f"Solapamiento detectado: El período #{curr.period_number} ('{curr.name}') finaliza el {curr.end_date}, "
                    f"que colisiona con el inicio del período #{nxt.period_number} ('{nxt.name}') ({nxt.start_date})."
                )

        # 5. Activation preconditions check
        if payload.activate_immediately:
            if not payload.compliance.confirmed_by_rector:
                raise AcademicDomainError(
                    "Para activar la configuración de períodos, el Rector debe confirmar formalmente "
                    "que ha sido revisada y concertada conforme al SIEE institucional y al calendario territorial."
                )

        # 6. Fetch existing periods in DB
        existing_stmt = select(AcademicPeriod).where(
            AcademicPeriod.academic_year_id == academic_year.id
        )
        existing_in_db = {p.period_number: p for p in (await self._session.execute(existing_stmt)).scalars().all()}

        provisioned_count = 0
        retained_count = 0

        # 7. Apply changes atomically
        for p in payload.periods:
            if p.period_number in existing_in_db:
                # Safe update of existing record without deleting or modifying grades/assessments
                existing_record = existing_in_db[p.period_number]
                existing_record.name = p.name.strip()
                existing_record.weight_percentage = Decimal(str(round(p.weight_percentage, 2)))
                existing_record.start_date = p.start_date
                existing_record.end_date = p.end_date
                retained_count += 1
            else:
                # Create brand new period
                new_period = AcademicPeriod(
                    academic_year_id=academic_year.id,
                    period_number=p.period_number,
                    name=p.name.strip(),
                    weight_percentage=Decimal(str(round(p.weight_percentage, 2))),
                    start_date=p.start_date,
                    end_date=p.end_date,
                    is_closed=False,
                )
                self._session.add(new_period)
                provisioned_count += 1

                await self._session.flush()

                await self._audit.record(
                    AuditEvent(
                        event_type=AuditEventType.ACADEMIC_PERIOD_CREATED,
                        actor_id=str(actor_id) if actor_id else None,
                        actor_ip=actor_ip,
                        target_id=str(new_period.id),
                        target_type="AcademicPeriod",
                        institution_id=str(institution_id),
                        correlation_id=correlation_id,
                        metadata={
                            "academic_year_id": str(academic_year.id),
                            "period_number": new_period.period_number,
                            "name": new_period.name,
                            "weight_percentage": float(new_period.weight_percentage),
                            "template_provisioned": True,
                        },
                    ),
                    session=self._session,
                )

        await self._session.flush()

        # 8. Record SIEE Compliance & Link/Upsert SieePolicy if provided
        siee_stmt = select(SieePolicy).where(
            SieePolicy.institution_id == institution_id,
            SieePolicy.academic_year_id == academic_year.id,
            SieePolicy.is_active == True,
        )
        active_siee = (await self._session.execute(siee_stmt)).scalar_one_or_none()

        compliance_summary = {
            "template_type": payload.template_type.value,
            "siee_version": payload.compliance.siee_version,
            "approval_act": payload.compliance.approval_act,
            "approval_date": str(payload.compliance.approval_date) if payload.compliance.approval_date else None,
            "calendar_source": payload.compliance.calendar_source,
            "calendar_source_url": payload.compliance.calendar_source_url,
            "reviewed_at": str(payload.compliance.reviewed_at) if payload.compliance.reviewed_at else None,
            "confirmed_by_rector": payload.compliance.confirmed_by_rector,
        }

        if active_siee and payload.compliance.approval_act:
            if not active_siee.description:
                active_siee.description = (
                    f"Aprobado mediante {payload.compliance.approval_act}. "
                    f"Calendario territorial: {payload.compliance.calendar_source or 'N/A'}."
                )

        # 9. Audit trail for template provisioning
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ACADEMIC_PERIODS_TEMPLATE_PROVISIONED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(academic_year.id),
                target_type="AcademicYear",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "year": academic_year.year,
                    "template_type": payload.template_type.value,
                    "provisioned_count": provisioned_count,
                    "retained_count": retained_count,
                    "total_periods": len(payload.periods),
                    "total_weight": total_weight,
                    **compliance_summary,
                },
            ),
            session=self._session,
        )

        is_activated = False
        # 10. Activation transition if requested
        if payload.activate_immediately:
            if academic_year.status == AcademicYearStatus.PLANNING:
                # Activate academic year using standard lifecycle method
                await self.activate_academic_year(
                    year_id=academic_year.id,
                    institution_id=institution_id,
                    actor_id=actor_id,
                    actor_ip=actor_ip,
                    correlation_id=correlation_id,
                )
            is_activated = True

            await self._audit.record(
                AuditEvent(
                    event_type=AuditEventType.ACADEMIC_PERIODS_ACTIVATED,
                    actor_id=str(actor_id) if actor_id else None,
                    actor_ip=actor_ip,
                    target_id=str(academic_year.id),
                    target_type="AcademicYear",
                    institution_id=str(institution_id),
                    correlation_id=correlation_id,
                    metadata={
                        "year": academic_year.year,
                        "periods_count": len(payload.periods),
                        "total_weight": total_weight,
                        "confirmed_by_rector": True,
                    },
                ),
                session=self._session,
            )

            await self._audit.record(
                AuditEvent(
                    event_type=AuditEventType.SIEE_COMPLIANCE_CONFIRMED,
                    actor_id=str(actor_id) if actor_id else None,
                    actor_ip=actor_ip,
                    target_id=str(academic_year.id),
                    target_type="AcademicYear",
                    institution_id=str(institution_id),
                    correlation_id=correlation_id,
                    metadata=compliance_summary,
                ),
                session=self._session,
            )

        # 11. Return refreshed periods
        refreshed_stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.academic_year_id == academic_year.id)
            .order_by(AcademicPeriod.period_number.asc())
        )
        final_periods = list((await self._session.execute(refreshed_stmt)).scalars().all())

        return PeriodTemplateProvisionResponse(
            academic_year_id=academic_year.id,
            provisioned_count=provisioned_count,
            retained_count=retained_count,
            total_periods=len(final_periods),
            total_weight=round(total_weight, 2),
            is_activated=is_activated,
            academic_year_status=academic_year.status,
            periods=[AcademicPeriodResponse.model_validate(p) for p in final_periods],
            compliance_summary=compliance_summary,
        )


