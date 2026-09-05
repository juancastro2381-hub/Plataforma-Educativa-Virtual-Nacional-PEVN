"""
PEVN Backend — SIEE Policy Domain Service (Phase 16B)

Authoritative business logic for institutional evaluation policies (Decreto 1290 de 2009):
- National multi-tenant policy resolution by institution and academic year
- Dynamic, data-driven grading scale mapping (BAJO, BASICO, ALTO, SUPERIOR)
- Remediation/recovery grade cap enforcement
- Promotion criteria configuration
- Versioned, immutable audit trail for institutional SIEE policies
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service as _default_audit_service
from app.core.exceptions import (
    CrossTenantMismatchError,
    SieePolicyNotFoundError,
    SieePolicyValidationError,
)
from app.core.logging import get_logger
from app.models.academic_year import AcademicYear
from app.models.evaluation import PerformanceLevelEnum, SieePolicy
from app.models.institution import Institution

_logger = get_logger(__name__)


class SieePolicyService:
    """
    Authoritative domain service for institutional SIEE policies.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService | None = None,
        audit_service: IAuditService | None = None,
    ) -> None:
        self._session = session
        self._audit = audit_service or audit or _default_audit_service

    # =======================================================================
    # Policy Resolution & Queries
    # =======================================================================

    async def get_active_policy(
        self,
        institution_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> SieePolicy | None:
        """
        Retrieve the single authoritative active SIEE policy for an institution and academic year.
        """
        stmt = (
            select(SieePolicy)
            .where(
                SieePolicy.institution_id == institution_id,
                SieePolicy.academic_year_id == academic_year_id,
                SieePolicy.is_active.is_(True),
            )
            .order_by(SieePolicy.version.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_or_create_default_policy(
        self,
        institution_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> SieePolicy:
        """
        Resolve the active SIEE policy, bootstrapping default standard institutional values if none exists.
        """
        # Validate AcademicYear tenant boundary
        year = await self._session.get(AcademicYear, academic_year_id)
        if not year or year.institution_id != institution_id:
            raise CrossTenantMismatchError(
                "El año lectivo no pertenece a la institución educativa especificada."
            )

        active_policy = await self.get_active_policy(institution_id, academic_year_id)
        if active_policy:
            return active_policy

        # Bootstrap standard Colombian institutional SIEE defaults
        default_policy = SieePolicy(
            institution_id=institution_id,
            academic_year_id=academic_year_id,
            version=1,
            name="Sistema Institucional de Evaluación de los Estudiantes",
            description="Política SIEE estándar nacional inicial.",
            min_passing_score=Decimal("3.00"),
            max_score=Decimal("5.00"),
            low_threshold_max=Decimal("2.99"),
            basic_threshold_max=Decimal("3.99"),
            high_threshold_max=Decimal("4.59"),
            recovery_grade_cap=Decimal("3.00"),
            max_failed_subjects_for_promotion=2,
            max_failed_core_subjects=1,
            min_attendance_percentage=Decimal("75.00"),
            attendance_affects_promotion=True,
            rounding_decimals=1,
            is_active=True,
            created_by_user_id=user_id,
        )
        self._session.add(default_policy)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.SIEE_POLICY_CREATED,
                actor_id=str(user_id) if user_id else None,
                actor_ip="127.0.0.1",
                target_id=str(default_policy.id),
                target_type="SieePolicy",
                institution_id=str(institution_id),
                metadata={
                    "version": 1,
                    "bootstrapped": True,
                    "academic_year_id": str(academic_year_id),
                    "recovery_grade_cap": "3.00",
                },
            )
        )

        return default_policy

    async def list_policy_history(
        self,
        institution_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> list[SieePolicy]:
        """
        List all historical and active versions of SIEE policies for auditing.
        """
        stmt = (
            select(SieePolicy)
            .where(
                SieePolicy.institution_id == institution_id,
                SieePolicy.academic_year_id == academic_year_id,
            )
            .order_by(SieePolicy.version.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # =======================================================================
    # Policy Creation & Versioning
    # =======================================================================

    async def create_policy_version(
        self,
        institution_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        data: dict[str, Any],
        user_id: uuid.UUID,
    ) -> SieePolicy:
        """
        Publish a new version of the institutional SIEE policy.
        Preserves previous versions immutably and enforces the single-active-policy invariant.
        """
        # 1. Validate AcademicYear tenant boundary
        year = await self._session.get(AcademicYear, academic_year_id)
        if not year or year.institution_id != institution_id:
            raise CrossTenantMismatchError(
                "El año lectivo no pertenece a la institución educativa especificada."
            )

        # 2. Extract & Validate Numerical Thresholds
        min_passing = Decimal(str(data.get("min_passing_score", "3.00")))
        max_score = Decimal(str(data.get("max_score", "5.00")))
        low_max = Decimal(str(data.get("low_threshold_max", "2.99")))
        basic_max = Decimal(str(data.get("basic_threshold_max", "3.99")))
        high_max = Decimal(str(data.get("high_threshold_max", "4.59")))
        recovery_cap = Decimal(str(data.get("recovery_grade_cap", "3.00")))
        min_att = Decimal(str(data.get("min_attendance_percentage", "75.00")))
        max_failed_sub = int(data.get("max_failed_subjects_for_promotion", 2))
        max_failed_core = int(data.get("max_failed_core_subjects", 1))
        rounding_dec = int(data.get("rounding_decimals", 1))
        is_active = bool(data.get("is_active", True))

        if not (Decimal("0.00") < min_passing < max_score):
            raise SieePolicyValidationError(
                f"min_passing_score ({min_passing}) debe ser mayor a 0 y menor a max_score ({max_score})."
            )

        if not (low_max < basic_max < high_max < max_score):
            raise SieePolicyValidationError(
                "Las bandas de desempeño deben cumplir: low_threshold_max < basic_threshold_max < high_threshold_max < max_score."
            )

        if not (min_passing <= recovery_cap <= max_score):
            raise SieePolicyValidationError(
                f"recovery_grade_cap ({recovery_cap}) debe estar entre la nota mínima de aprobación ({min_passing}) y max_score ({max_score})."
            )

        if not (Decimal("0.00") <= min_att <= Decimal("100.00")):
            raise SieePolicyValidationError(
                "min_attendance_percentage debe estar entre 0.00 y 100.00."
            )

        if max_failed_sub < 0 or max_failed_core < 0:
            raise SieePolicyValidationError(
                "Los umbrales de reprobación de asignaturas no pueden ser negativos."
            )

        # 3. Calculate next version number
        version_stmt = select(func.coalesce(func.max(SieePolicy.version), 0)).where(
            SieePolicy.institution_id == institution_id,
            SieePolicy.academic_year_id == academic_year_id,
        )
        max_version = (await self._session.execute(version_stmt)).scalar_one()
        new_version = max_version + 1

        # 4. If this new version is active, deactivate existing active versions
        if is_active:
            deactivate_stmt = (
                update(SieePolicy)
                .where(
                    SieePolicy.institution_id == institution_id,
                    SieePolicy.academic_year_id == academic_year_id,
                    SieePolicy.is_active.is_(True),
                )
                .values(is_active=False, updated_at=datetime.now(UTC))
            )
            await self._session.execute(deactivate_stmt)
            await self._session.flush()

        # 5. Insert new version
        new_policy = SieePolicy(
            institution_id=institution_id,
            academic_year_id=academic_year_id,
            version=new_version,
            name=data.get("name", f"Política SIEE v{new_version}"),
            description=data.get("description"),
            min_passing_score=min_passing,
            max_score=max_score,
            low_threshold_max=low_max,
            basic_threshold_max=basic_max,
            high_threshold_max=high_max,
            recovery_grade_cap=recovery_cap,
            max_failed_subjects_for_promotion=max_failed_sub,
            max_failed_core_subjects=max_failed_core,
            min_attendance_percentage=min_att,
            attendance_affects_promotion=bool(data.get("attendance_affects_promotion", True)),
            rounding_decimals=rounding_dec,
            is_active=is_active,
            created_by_user_id=user_id,
        )
        self._session.add(new_policy)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.SIEE_POLICY_UPDATED,
                actor_id=str(user_id) if user_id else None,
                actor_ip="127.0.0.1",
                target_id=str(new_policy.id),
                target_type="SieePolicy",
                institution_id=str(institution_id),
                metadata={
                    "version": new_version,
                    "is_active": is_active,
                    "academic_year_id": str(academic_year_id),
                    "recovery_grade_cap": str(recovery_cap),
                    "max_failed_subjects": max_failed_sub,
                },
            )
        )

        return new_policy

    # =======================================================================
    # Performance Level Mapping (Deterministic & Policy-Driven)
    # =======================================================================

    @staticmethod
    def map_score_to_performance_level(
        score: Decimal | float | int,
        policy: SieePolicy,
    ) -> PerformanceLevelEnum:
        """
        Map a numeric grade to the Colombian National Qualitative Scale
        (BAJO, BASICO, ALTO, SUPERIOR) driven by the active institutional policy.
        Score boundaries are enforced inclusively from 0.00 through 5.00.
        """
        score_dec = Decimal(str(score))

        # Clamping to valid bounds
        if score_dec < Decimal("0.00"):
            score_dec = Decimal("0.00")
        elif score_dec > policy.max_score:
            score_dec = policy.max_score

        if score_dec <= policy.low_threshold_max:
            return PerformanceLevelEnum.BAJO
        elif score_dec <= policy.basic_threshold_max:
            return PerformanceLevelEnum.BASICO
        elif score_dec <= policy.high_threshold_max:
            return PerformanceLevelEnum.ALTO
        else:
            return PerformanceLevelEnum.SUPERIOR
