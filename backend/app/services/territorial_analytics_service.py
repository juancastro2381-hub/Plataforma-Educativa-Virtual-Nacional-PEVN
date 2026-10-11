"""
PEVN Backend — Territorial Analytics Domain Service

Provides high-performance, strictly isolated aggregation queries across
Colombian territorial hierarchies, official educational catalogs, and
provisioned institutional tenants.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from sqlalchemy import func, select, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import audit_service
from app.core.logging import get_logger
from app.core.security.authorization import scope_contains
from app.core.security.interfaces import OrganizationalScope
from app.exceptions.errors import AuthorizationError, NotFoundError
from app.models.enrollment import Enrollment
from app.models.group import Group
from app.models.institution import Campus, Institution
from app.models.invitation import DepartmentAdminInvitation
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialInstitutionCatalog,
)
from app.models.onboarding import InstitutionOnboardingRequest
from app.models.role import Role, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.territory import Department, Municipality
from app.models.user import User
from app.schemas.analytics import (
    DepartmentAnalyticsItem,
    DepartmentAnalyticsResponse,
    DepartmentDetailControlCenterResponse,
    DepartmentMatrixRow,
    DepartmentMunicipalityRow,
    InstitutionalKPIResponse,
    MunicipalityAnalyticsItem,
    MunicipalityAnalyticsResponse,
    TerritorialControlCenterResponse,
    TerritorialSectorBreakdown,
    TerritorialSummaryResponse,
    TerritorialZoneBreakdown,
    Tier1CatalogMetrics,
    Tier2PipelineMetrics,
    Tier3TenancyMetrics,
    Tier4GovernanceMetrics,
)

_logger = get_logger(__name__)


class TerritorialAnalyticsService:
    """
    Hierarchical, multi-tenant aware analytics engine.
    All operations are strictly bounded by the caller's OrganizationalScope.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit_svc: audit_service.__class__ = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit_svc

    async def _resolve_department_code_from_scope(
        self, scope: OrganizationalScope
    ) -> tuple[str | None, str | None]:
        """Resolve department code and name from scope identifier if present."""
        if not scope.department_id:
            return None, None

        parsed_uuid = None
        try:
            parsed_uuid = uuid.UUID(str(scope.department_id))
        except (ValueError, TypeError):
            pass

        conditions = [Department.code == str(scope.department_id)]
        if parsed_uuid is not None:
            conditions.append(Department.id == parsed_uuid)

        stmt = select(Department).where(or_(*conditions))
        res = await self._session.execute(stmt)
        dept = res.scalar_one_or_none()
        if dept:
            return dept.code, dept.name
        return str(scope.department_id), None

    async def get_national_summary(
        self, scope: OrganizationalScope
    ) -> TerritorialSummaryResponse:
        """
        Compute high-level summary KPIs bounded by OrganizationalScope.
        """
        now = datetime.now(UTC)

        # 1. National Scope
        if scope.is_national():
            # Total Departments
            dept_count = (
                await self._session.execute(select(func.count(Department.id)))
            ).scalar_one() or 0

            # Total Municipalities
            mun_count = (
                await self._session.execute(select(func.count(Municipality.id)))
            ).scalar_one() or 0

            # Total Institutions in Catalog
            cat_inst_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id))
                )
            ).scalar_one() or 0

            # Provisioned Institutions in PEvN
            prov_inst_count = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(Institution.is_active == True)
                )
            ).scalar_one() or 0

            # Total Campuses in Catalog
            cat_campus_count = (
                await self._session.execute(
                    select(func.count(OfficialCampusCatalog.id))
                )
            ).scalar_one() or 0

            # Active Operational Users in PEvN
            active_students = (
                await self._session.execute(
                    select(func.count(Student.id))
                    .join(User, Student.user_id == User.id)
                    .where(User.is_active == True)
                )
            ).scalar_one() or 0

            active_teachers = (
                await self._session.execute(
                    select(func.count(Teacher.id))
                    .join(User, Teacher.user_id == User.id)
                    .where(User.is_active == True)
                )
            ).scalar_one() or 0

            active_groups = (
                await self._session.execute(select(func.count(Group.id)))
            ).scalar_one() or 0

            # Sector Breakdown
            sector_stmt = select(
                func.sum(
                    case((OfficialInstitutionCatalog.sector == "OFICIAL", 1), else_=0)
                ).label("official_count"),
                func.sum(
                    case((OfficialInstitutionCatalog.sector != "OFICIAL", 1), else_=0)
                ).label("non_official_count"),
            )
            sector_res = (await self._session.execute(sector_stmt)).one()
            official_count = sector_res.official_count or 0
            non_official_count = sector_res.non_official_count or 0

            # Zone Breakdown
            zone_stmt = select(
                func.sum(
                    case((OfficialInstitutionCatalog.zone == "URBANA", 1), else_=0)
                ).label("urban_count"),
                func.sum(
                    case((OfficialInstitutionCatalog.zone == "RURAL", 1), else_=0)
                ).label("rural_count"),
            )
            zone_res = (await self._session.execute(zone_stmt)).one()
            urban_count = zone_res.urban_count or 0
            rural_count = zone_res.rural_count or 0

            rate = (
                round((prov_inst_count / cat_inst_count) * 100, 2)
                if cat_inst_count > 0
                else 0.0
            )

            return TerritorialSummaryResponse(
                scope_level="NATIONAL",
                jurisdiction_name="República de Colombia",
                total_departments=dept_count,
                total_municipalities=mun_count,
                total_institutions=cat_inst_count,
                provisioned_institutions=prov_inst_count,
                provisioning_rate_percent=rate,
                total_campuses=cat_campus_count,
                active_students=active_students,
                active_teachers=active_teachers,
                active_groups=active_groups,
                sector_breakdown=TerritorialSectorBreakdown(
                    official=official_count,
                    non_official=non_official_count,
                ),
                zone_breakdown=TerritorialZoneBreakdown(
                    urban=urban_count,
                    rural=rural_count,
                ),
                computed_at=now,
            )

        # 2. Departmental Scope
        if scope.is_department():
            dept_code, dept_name = await self._resolve_department_code_from_scope(scope)
            jurisdiction = dept_name or f"Departamento {dept_code}"

            mun_count = (
                await self._session.execute(
                    select(func.count(Municipality.id)).join(Department).where(Department.code == dept_code)
                )
            ).scalar_one() or 0

            cat_inst_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.department_code == dept_code
                    )
                )
            ).scalar_one() or 0

            prov_inst_count = (
                await self._session.execute(
                    select(func.count(Institution.id))
                    .join(Municipality, Institution.municipality_id == Municipality.id)
                    .join(Department, Municipality.department_id == Department.id)
                    .where(Department.code == dept_code, Institution.is_active == True)
                )
            ).scalar_one() or 0

            cat_campus_count = (
                await self._session.execute(
                    select(func.count(OfficialCampusCatalog.id))
                    .join(OfficialInstitutionCatalog, OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id)
                    .where(OfficialInstitutionCatalog.department_code == dept_code)
                )
            ).scalar_one() or 0

            rate = (
                round((prov_inst_count / cat_inst_count) * 100, 2)
                if cat_inst_count > 0
                else 0.0
            )

            # Department sector
            sector_stmt = select(
                func.sum(
                    case((OfficialInstitutionCatalog.sector == "OFICIAL", 1), else_=0)
                ).label("official_count"),
                func.sum(
                    case((OfficialInstitutionCatalog.sector != "OFICIAL", 1), else_=0)
                ).label("non_official_count"),
            ).where(OfficialInstitutionCatalog.department_code == dept_code)
            sector_res = (await self._session.execute(sector_stmt)).one()
            official_count = sector_res.official_count or 0
            non_official_count = sector_res.non_official_count or 0

            # Department zone
            zone_stmt = select(
                func.sum(
                    case((OfficialInstitutionCatalog.zone == "URBANA", 1), else_=0)
                ).label("urban_count"),
                func.sum(
                    case((OfficialInstitutionCatalog.zone == "RURAL", 1), else_=0)
                ).label("rural_count"),
            ).where(OfficialInstitutionCatalog.department_code == dept_code)
            zone_res = (await self._session.execute(zone_stmt)).one()
            urban_count = zone_res.urban_count or 0
            rural_count = zone_res.rural_count or 0

            return TerritorialSummaryResponse(
                scope_level="DEPARTMENT",
                jurisdiction_name=jurisdiction,
                total_departments=1,
                total_municipalities=mun_count,
                total_institutions=cat_inst_count,
                provisioned_institutions=prov_inst_count,
                provisioning_rate_percent=rate,
                total_campuses=cat_campus_count,
                active_students=0,
                active_teachers=0,
                active_groups=0,
                sector_breakdown=TerritorialSectorBreakdown(
                    official=official_count,
                    non_official=non_official_count,
                ),
                zone_breakdown=TerritorialZoneBreakdown(
                    urban=urban_count,
                    rural=rural_count,
                ),
                computed_at=now,
            )

        # 3. Municipal Scope
        if scope.is_municipality():
            muni_uuid = uuid.UUID(scope.municipality_id) if isinstance(scope.municipality_id, str) else scope.municipality_id
            muni = await self._session.get(Municipality, muni_uuid)
            if not muni:
                raise NotFoundError("Municipio no encontrado.")
            muni_code = muni.code
            jurisdiction = f"{muni.name} ({muni_code})"

            cat_inst_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.municipality_code == muni_code
                    )
                )
            ).scalar_one() or 0

            prov_inst_count = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(
                        Institution.municipality_id == muni.id,
                        Institution.is_active == True,
                    )
                )
            ).scalar_one() or 0

            cat_campus_count = (
                await self._session.execute(
                    select(func.count(OfficialCampusCatalog.id))
                    .join(OfficialInstitutionCatalog, OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id)
                    .where(OfficialInstitutionCatalog.municipality_code == muni_code)
                )
            ).scalar_one() or 0

            rate = (
                round((prov_inst_count / cat_inst_count) * 100, 2)
                if cat_inst_count > 0
                else 0.0
            )

            # Municipal sector breakdown
            sector_stmt = select(
                func.sum(
                    case((OfficialInstitutionCatalog.sector == "OFICIAL", 1), else_=0)
                ).label("official_count"),
                func.sum(
                    case((OfficialInstitutionCatalog.sector != "OFICIAL", 1), else_=0)
                ).label("non_official_count"),
            ).where(OfficialInstitutionCatalog.municipality_code == muni_code)
            sector_res = (await self._session.execute(sector_stmt)).one()
            official_count = sector_res.official_count or 0
            non_official_count = sector_res.non_official_count or 0

            # Municipal zone breakdown
            zone_stmt = select(
                func.sum(
                    case((OfficialInstitutionCatalog.zone == "URBANA", 1), else_=0)
                ).label("urban_count"),
                func.sum(
                    case((OfficialInstitutionCatalog.zone == "RURAL", 1), else_=0)
                ).label("rural_count"),
            ).where(OfficialInstitutionCatalog.municipality_code == muni_code)
            zone_res = (await self._session.execute(zone_stmt)).one()
            urban_count = zone_res.urban_count or 0
            rural_count = zone_res.rural_count or 0

            return TerritorialSummaryResponse(
                scope_level="MUNICIPALITY",
                jurisdiction_name=jurisdiction,
                total_departments=1,
                total_municipalities=1,
                total_institutions=cat_inst_count,
                provisioned_institutions=prov_inst_count,
                provisioning_rate_percent=rate,
                total_campuses=cat_campus_count,
                active_students=0,
                active_teachers=0,
                active_groups=0,
                sector_breakdown=TerritorialSectorBreakdown(
                    official=official_count,
                    non_official=non_official_count,
                ),
                zone_breakdown=TerritorialZoneBreakdown(
                    urban=urban_count,
                    rural=rural_count,
                ),
                computed_at=now,
            )

        # 4. Institutional Scope
        inst_id = scope.institution_id
        inst = None
        if inst_id:
            inst_uuid = uuid.UUID(inst_id) if isinstance(inst_id, str) else inst_id
            inst = await self._session.get(Institution, inst_uuid)

        if not inst:
            raise NotFoundError("Institución educativa no encontrada.")

        campus_count = (
            await self._session.execute(
                select(func.count(Campus.id)).where(Campus.institution_id == inst.id)
            )
        ).scalar_one() or 0

        std_count = (
            await self._session.execute(
                select(func.count(Student.id))
                .join(User, Student.user_id == User.id)
                .where(Student.institution_id == inst.id, User.is_active == True)
            )
        ).scalar_one() or 0

        teacher_count = (
            await self._session.execute(
                select(func.count(Teacher.id))
                .join(User, Teacher.user_id == User.id)
                .where(Teacher.institution_id == inst.id, User.is_active == True)
            )
        ).scalar_one() or 0

        group_count = (
            await self._session.execute(
                select(func.count(Group.id))
                .join(Campus, Group.campus_id == Campus.id)
                .where(Campus.institution_id == inst.id)
            )
        ).scalar_one() or 0

        return TerritorialSummaryResponse(
            scope_level="INSTITUTION",
            jurisdiction_name=inst.name,
            total_departments=1,
            total_municipalities=1,
            total_institutions=1,
            provisioned_institutions=1,
            provisioning_rate_percent=100.0,
            total_campuses=campus_count,
            active_students=std_count,
            active_teachers=teacher_count,
            active_groups=group_count,
            sector_breakdown=TerritorialSectorBreakdown(official=1, non_official=0),
            zone_breakdown=TerritorialZoneBreakdown(urban=1, rural=0),
            computed_at=now,
        )

    async def get_department_distribution(
        self, scope: OrganizationalScope
    ) -> DepartmentAnalyticsResponse:
        """
        Get analytics breakdown by department.
        """
        now = datetime.now(UTC)

        if not (scope.is_national() or scope.is_department()):
            raise AuthorizationError(
                "Se requiere alcance nacional o departamental para consultar el desglose departamental.",
                code="PERMISSION_DENIED",
            )

        dept_code_filter = None
        if scope.is_department():
            dept_code_filter, _ = await self._resolve_department_code_from_scope(scope)

        # Query department stats
        # Group by OfficialInstitutionCatalog.department_code
        stmt = (
            select(
                OfficialInstitutionCatalog.department_code,
                func.max(OfficialInstitutionCatalog.department_name).label("department_name"),
                func.count(func.distinct(OfficialInstitutionCatalog.municipality_code)).label("mun_count"),
                func.count(OfficialInstitutionCatalog.id).label("total_inst"),
                func.sum(
                    case((OfficialInstitutionCatalog.sector == "OFICIAL", 1), else_=0)
                ).label("official_count"),
                func.sum(
                    case((OfficialInstitutionCatalog.sector != "OFICIAL", 1), else_=0)
                ).label("non_official_count"),
            )
            .group_by(
                OfficialInstitutionCatalog.department_code,
            )
            .order_by(OfficialInstitutionCatalog.department_code)
        )

        if dept_code_filter:
            stmt = stmt.where(OfficialInstitutionCatalog.department_code == dept_code_filter)

        res = await self._session.execute(stmt)
        rows = res.all()

        items: list[DepartmentAnalyticsItem] = []
        for r in rows:
            # Query campuses for this department
            campuses_count = (
                await self._session.execute(
                    select(func.count(OfficialCampusCatalog.id))
                    .join(OfficialInstitutionCatalog, OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id)
                    .where(OfficialInstitutionCatalog.department_code == r.department_code)
                )
            ).scalar_one() or 0

            # Provisioned institutions count for this department
            prov_count = (
                await self._session.execute(
                    select(func.count(Institution.id))
                    .join(Municipality, Institution.municipality_id == Municipality.id)
                    .join(Department, Municipality.department_id == Department.id)
                    .where(Department.code == r.department_code, Institution.is_active == True)
                )
            ).scalar_one() or 0

            items.append(
                DepartmentAnalyticsItem(
                    department_code=r.department_code,
                    department_name=r.department_name,
                    total_municipalities=r.mun_count or 0,
                    total_institutions=r.total_inst or 0,
                    official_institutions=r.official_count or 0,
                    non_official_institutions=r.non_official_count or 0,
                    total_campuses=campuses_count,
                    provisioned_institutions=prov_count,
                )
            )

        return DepartmentAnalyticsResponse(
            items=items,
            total_count=len(items),
            computed_at=now,
        )

    async def get_municipality_distribution(
        self,
        scope: OrganizationalScope,
        department_code: str | None = None,
    ) -> MunicipalityAnalyticsResponse:
        """
        Get analytics breakdown by municipality, optionally filtered by department.
        """
        now = datetime.now(UTC)

        # Enforce scope
        muni_code_filter = None
        if scope.is_municipality():
            muni_uuid = uuid.UUID(scope.municipality_id) if isinstance(scope.municipality_id, str) else scope.municipality_id
            muni = await self._session.get(Municipality, muni_uuid)
            if not muni:
                raise NotFoundError("Municipio no encontrado.")
            dept = await self._session.get(Department, muni.department_id)
            if department_code and dept and department_code != dept.code:
                raise AuthorizationError(
                    "No está autorizado para consultar municipios fuera de su departamento asignado.",
                    code="PERMISSION_DENIED",
                )
            muni_code_filter = muni.code
            department_code = dept.code if dept else None
        elif scope.is_department():
            scoped_dept, _ = await self._resolve_department_code_from_scope(scope)
            if department_code and department_code != scoped_dept:
                raise AuthorizationError(
                    "No está autorizado para consultar municipios fuera de su departamento asignado.",
                    code="PERMISSION_DENIED",
                )
            department_code = scoped_dept
        elif not scope.is_national():
            raise AuthorizationError(
                "Se requiere alcance nacional, departamental o municipal para consultar la distribución municipal.",
                code="PERMISSION_DENIED",
            )

        stmt = (
            select(
                OfficialInstitutionCatalog.municipality_code,
                func.max(OfficialInstitutionCatalog.municipality_name).label("municipality_name"),
                OfficialInstitutionCatalog.department_code,
                func.max(OfficialInstitutionCatalog.department_name).label("department_name"),
                func.count(OfficialInstitutionCatalog.id).label("total_inst"),
                func.sum(
                    case((OfficialInstitutionCatalog.sector == "OFICIAL", 1), else_=0)
                ).label("official_count"),
                func.sum(
                    case((OfficialInstitutionCatalog.sector != "OFICIAL", 1), else_=0)
                ).label("non_official_count"),
            )
            .group_by(
                OfficialInstitutionCatalog.municipality_code,
                OfficialInstitutionCatalog.department_code,
            )
            .order_by(func.max(OfficialInstitutionCatalog.municipality_name))
        )

        if department_code:
            stmt = stmt.where(OfficialInstitutionCatalog.department_code == department_code)
        if muni_code_filter:
            stmt = stmt.where(OfficialInstitutionCatalog.municipality_code == muni_code_filter)

        res = await self._session.execute(stmt)
        rows = res.all()

        items: list[MunicipalityAnalyticsItem] = []
        for r in rows:
            campuses_count = (
                await self._session.execute(
                    select(func.count(OfficialCampusCatalog.id))
                    .join(OfficialInstitutionCatalog, OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id)
                    .where(OfficialInstitutionCatalog.municipality_code == r.municipality_code)
                )
            ).scalar_one() or 0

            prov_count = (
                await self._session.execute(
                    select(func.count(Institution.id))
                    .join(Municipality, Institution.municipality_id == Municipality.id)
                    .where(Municipality.code == r.municipality_code, Institution.is_active == True)
                )
            ).scalar_one() or 0

            items.append(
                MunicipalityAnalyticsItem(
                    municipality_code=r.municipality_code,
                    municipality_name=r.municipality_name,
                    department_code=r.department_code,
                    department_name=r.department_name,
                    total_institutions=r.total_inst or 0,
                    official_institutions=r.official_count or 0,
                    non_official_institutions=r.non_official_count or 0,
                    total_campuses=campuses_count,
                    provisioned_institutions=prov_count,
                )
            )

        return MunicipalityAnalyticsResponse(
            department_code=department_code,
            items=items,
            total_count=len(items),
            computed_at=now,
        )

    async def get_institutional_kpis(
        self,
        scope: OrganizationalScope,
        institution_id: uuid.UUID,
    ) -> InstitutionalKPIResponse:
        """
        Get specific KPIs for an institution, strictly validated against caller's scope.
        """
        now = datetime.now(UTC)

        inst = await self._session.get(Institution, institution_id)
        if not inst:
            raise NotFoundError("Institución educativa no encontrada.")

        # Resolve department & municipality
        mun = await self._session.get(Municipality, inst.municipality_id) if inst.municipality_id else None
        dept = await self._session.get(Department, mun.department_id) if mun and mun.department_id else None

        # Enforce scope containment via scope_contains
        target_scope = OrganizationalScope(
            country_code="CO",
            department_id=str(mun.department_id) if mun and mun.department_id else None,
            municipality_id=str(inst.municipality_id) if inst.municipality_id else None,
            institution_id=str(inst.id),
        )
        if not scope_contains(scope, target_scope):
            raise AuthorizationError(
                "No está autorizado para consultar métricas de una institución fuera de su jurisdicción territorial.",
                code="PERMISSION_DENIED",
            )

        campus_count = (
            await self._session.execute(
                select(func.count(Campus.id)).where(Campus.institution_id == inst.id)
            )
        ).scalar_one() or 0

        group_count = (
            await self._session.execute(
                select(func.count(Group.id))
                .join(Campus, Group.campus_id == Campus.id)
                .where(Campus.institution_id == inst.id)
            )
        ).scalar_one() or 0

        std_count = (
            await self._session.execute(
                select(func.count(Student.id))
                .join(User, Student.user_id == User.id)
                .where(Student.institution_id == inst.id, User.is_active == True)
            )
        ).scalar_one() or 0

        teacher_count = (
            await self._session.execute(
                select(func.count(Teacher.id))
                .join(User, Teacher.user_id == User.id)
                .where(Teacher.institution_id == inst.id, User.is_active == True)
            )
        ).scalar_one() or 0

        enrollment_count = (
            await self._session.execute(
                select(func.count(Enrollment.id))
                .join(Student, Enrollment.student_id == Student.id)
                .where(Student.institution_id == inst.id, Enrollment.status == "ACTIVA")
            )
        ).scalar_one() or 0

        return InstitutionalKPIResponse(
            institution_id=inst.id,
            dane_code=inst.dane_code,
            name=inst.name,
            department_name=dept.name if dept else "N/A",
            municipality_name=mun.name if mun else "N/A",
            total_campuses=campus_count,
            total_groups=group_count,
            total_students=std_count,
            total_teachers=teacher_count,
            total_enrollments=enrollment_count,
            computed_at=now,
        )

    async def _resolve_department_from_scope(
        self, scope: OrganizationalScope
    ) -> Department | None:
        """Resolve Department model instance from scope identifier (code or UUID)."""
        if not scope.department_id:
            return None

        parsed_uuid = None
        try:
            parsed_uuid = uuid.UUID(str(scope.department_id))
        except (ValueError, TypeError):
            pass

        conditions = [Department.code == str(scope.department_id)]
        if parsed_uuid is not None:
            conditions.append(Department.id == parsed_uuid)

        stmt = select(Department).where(or_(*conditions))
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_territorial_control_center(
        self, scope: OrganizationalScope
    ) -> TerritorialControlCenterResponse:
        """
        Compute consolidated 4-Tier Territorial Control Center KPIs and matrix.
        Strictly enforces OrganizationalScope and Anti-IDOR:
        - NATIONAL (superadmin, national_admin): Complete 33-department matrix and national totals.
        - DEPARTMENT (department_admin): Exactly 1 department in matrix (caller's assigned jurisdiction).
        - Institutional or unauthenticated: HTTP 403 Forbidden.
        """
        now = datetime.now(UTC)

        if not scope.is_national() and not scope.is_department():
            raise AuthorizationError(
                "No está autorizado para acceder al Centro de Control Territorial.",
                code="PERMISSION_DENIED",
            )

        if scope.is_national():
            # -------------------------------------------------------------------
            # NATIONAL SCOPE
            # -------------------------------------------------------------------
            total_departments = (
                await self._session.execute(select(func.count(Department.id)))
            ).scalar_one() or 0
            total_municipalities = (
                await self._session.execute(select(func.count(Municipality.id)))
            ).scalar_one() or 0
            total_establishments = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id))
                )
            ).scalar_one() or 0
            total_campuses = (
                await self._session.execute(
                    select(func.count(OfficialCampusCatalog.id))
                )
            ).scalar_one() or 0
            official_sector_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.sector == "OFICIAL"
                    )
                )
            ).scalar_one() or 0
            non_official_sector_count = max(0, total_establishments - official_sector_count)
            urban_zone_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.zone == "URBANA"
                    )
                )
            ).scalar_one() or 0
            rural_zone_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.zone == "RURAL"
                    )
                )
            ).scalar_one() or 0

            tier1_catalog = Tier1CatalogMetrics(
                total_departments=total_departments,
                total_municipalities=total_municipalities,
                total_establishments=total_establishments,
                total_campuses=total_campuses,
                official_sector_count=official_sector_count,
                non_official_sector_count=non_official_sector_count,
                urban_zone_count=urban_zone_count,
                rural_zone_count=rural_zone_count,
            )

            # Tier 2: Pipeline
            req_counts = dict(
                (
                    await self._session.execute(
                        select(
                            InstitutionOnboardingRequest.status,
                            func.count(InstitutionOnboardingRequest.id),
                        ).group_by(InstitutionOnboardingRequest.status)
                    )
                ).all()
            )
            total_requests = sum(req_counts.values())
            tier2_pipeline = Tier2PipelineMetrics(
                total_requests=total_requests,
                submitted=req_counts.get("SUBMITTED", 0),
                under_review=req_counts.get("UNDER_REVIEW", 0),
                approved=req_counts.get("APPROVED", 0),
                provisioned=req_counts.get("PROVISIONED", 0),
                rejected=req_counts.get("REJECTED", 0),
                cancelled=req_counts.get("CANCELLED", 0),
            )

            # Tier 3: Tenancy
            total_institutions = (
                await self._session.execute(select(func.count(Institution.id)))
            ).scalar_one() or 0
            active_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(Institution.is_active == True)
                )
            ).scalar_one() or 0
            inactive_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(Institution.is_active == False)
                )
            ).scalar_one() or 0
            catalog_linked_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(
                        Institution.catalog_institution_id.isnot(None)
                    )
                )
            ).scalar_one() or 0
            synthetic_fixture_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(
                        Institution.catalog_institution_id.is_(None)
                    )
                )
            ).scalar_one() or 0
            provisioned_campuses = (
                await self._session.execute(select(func.count(Campus.id)))
            ).scalar_one() or 0
            active_operational_campuses = (
                await self._session.execute(
                    select(func.count(Campus.id)).where(Campus.is_active == True)
                )
            ).scalar_one() or 0
            total_users = (
                await self._session.execute(select(func.count(User.id)))
            ).scalar_one() or 0
            active_students = (
                await self._session.execute(
                    select(func.count(Student.id))
                    .join(User, Student.user_id == User.id)
                    .where(User.is_active == True)
                )
            ).scalar_one() or 0
            active_teachers = (
                await self._session.execute(
                    select(func.count(Teacher.id))
                    .join(User, Teacher.user_id == User.id)
                    .where(User.is_active == True)
                )
            ).scalar_one() or 0

            tier3_tenancy = Tier3TenancyMetrics(
                total_institutions=total_institutions,
                active_institutions=active_institutions,
                inactive_institutions=inactive_institutions,
                catalog_linked_institutions=catalog_linked_institutions,
                synthetic_fixture_institutions=synthetic_fixture_institutions,
                provisioned_campuses=provisioned_campuses,
                active_operational_campuses=active_operational_campuses,
                total_users=total_users,
                active_students=active_students,
                active_teachers=active_teachers,
            )

            # Tier 4: Governance
            da_users_count = (
                await self._session.execute(
                    select(func.count(func.distinct(User.id)))
                    .join(UserRole, User.id == UserRole.user_id)
                    .join(Role, UserRole.role_id == Role.id)
                    .where(
                        Role.name == "department_admin",
                        UserRole.department_id.isnot(None),
                        UserRole.is_active == True,
                    )
                )
            ).scalar_one() or 0

            covered_departments = (
                await self._session.execute(
                    select(func.count(func.distinct(UserRole.department_id)))
                    .join(Role, UserRole.role_id == Role.id)
                    .where(
                        Role.name == "department_admin",
                        UserRole.department_id.isnot(None),
                        UserRole.is_active == True,
                    )
                )
            ).scalar_one() or 0

            vacant_departments = max(0, total_departments - covered_departments)
            pending_invitations = (
                await self._session.execute(
                    select(func.count(DepartmentAdminInvitation.id)).where(
                        DepartmentAdminInvitation.is_used == False,
                        DepartmentAdminInvitation.is_revoked == False,
                        DepartmentAdminInvitation.expires_at > func.now(),
                    )
                )
            ).scalar_one() or 0
            coverage_percentage = (
                round((covered_departments / total_departments) * 100, 1)
                if total_departments > 0
                else 0.0
            )

            tier4_governance = Tier4GovernanceMetrics(
                total_departments=total_departments,
                department_admin_users_count=da_users_count,
                covered_departments=covered_departments,
                vacant_departments=vacant_departments,
                pending_invitations=pending_invitations,
                coverage_percentage=coverage_percentage,
            )

            # 33-Department Matrix
            dept_rows = (
                await self._session.execute(
                    select(Department).order_by(Department.code)
                )
            ).scalars().all()

            cat_est_counts = dict(
                (
                    await self._session.execute(
                        select(
                            OfficialInstitutionCatalog.department_code,
                            func.count(OfficialInstitutionCatalog.id),
                        ).group_by(OfficialInstitutionCatalog.department_code)
                    )
                ).all()
            )

            cat_cmp_counts = dict(
                (
                    await self._session.execute(
                        select(
                            OfficialInstitutionCatalog.department_code,
                            func.count(OfficialCampusCatalog.id),
                        )
                        .join(
                            OfficialInstitutionCatalog,
                            OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id,
                        )
                        .group_by(OfficialInstitutionCatalog.department_code)
                    )
                ).all()
            )

            pipe_counts = dict(
                (
                    await self._session.execute(
                        select(
                            InstitutionOnboardingRequest.department_id,
                            func.count(InstitutionOnboardingRequest.id),
                        )
                        .where(
                            InstitutionOnboardingRequest.status.in_(
                                ["SUBMITTED", "UNDER_REVIEW", "APPROVED"]
                            )
                        )
                        .group_by(InstitutionOnboardingRequest.department_id)
                    )
                ).all()
            )

            inst_counts = (
                await self._session.execute(
                    select(
                        Municipality.department_id,
                        Institution.is_active,
                        func.count(Institution.id),
                    )
                    .join(Municipality, Institution.municipality_id == Municipality.id)
                    .group_by(Municipality.department_id, Institution.is_active)
                )
            ).all()
            act_inst_by_dept: dict[uuid.UUID, int] = {}
            inact_inst_by_dept: dict[uuid.UUID, int] = {}
            for d_id, is_act, cnt in inst_counts:
                if is_act:
                    act_inst_by_dept[d_id] = act_inst_by_dept.get(d_id, 0) + cnt
                else:
                    inact_inst_by_dept[d_id] = inact_inst_by_dept.get(d_id, 0) + cnt

            active_da_rows = (
                await self._session.execute(
                    select(
                        UserRole.department_id,
                        User.first_name,
                        User.last_name,
                        User.email,
                    )
                    .join(User, UserRole.user_id == User.id)
                    .join(Role, UserRole.role_id == Role.id)
                    .where(
                        Role.name == "department_admin",
                        UserRole.department_id.isnot(None),
                        UserRole.is_active == True,
                    )
                )
            ).all()
            da_by_dept: dict[uuid.UUID, tuple[str, str | None]] = {}
            for dept_id, fn, ln, em in active_da_rows:
                if dept_id not in da_by_dept:
                    full_name = f"{fn or ''} {ln or ''}".strip() or "Administrador Departamental"
                    da_by_dept[dept_id] = (full_name, em)

            pending_inv_depts = set(
                (
                    await self._session.execute(
                        select(DepartmentAdminInvitation.department_id).where(
                            DepartmentAdminInvitation.is_used == False,
                            DepartmentAdminInvitation.is_revoked == False,
                            DepartmentAdminInvitation.expires_at > func.now(),
                        )
                    )
                ).scalars().all()
            )

            matrix = []
            for d in dept_rows:
                da_info = da_by_dept.get(d.id)
                if da_info:
                    gov_status = "COVERED"
                    admin_name, admin_email = da_info
                elif d.id in pending_inv_depts:
                    gov_status = "INVITED"
                    admin_name, admin_email = None, None
                else:
                    gov_status = "VACANT"
                    admin_name, admin_email = None, None

                d_est = cat_est_counts.get(d.code, 0)
                d_cmp = cat_cmp_counts.get(d.code, 0)
                d_pipe = pipe_counts.get(d.id, 0)
                d_act = act_inst_by_dept.get(d.id, 0)
                d_inact = inact_inst_by_dept.get(d.id, 0)
                rate = round((d_act / d_est) * 100, 2) if d_est > 0 else 0.0

                matrix.append(
                    DepartmentMatrixRow(
                        department_id=d.id,
                        department_code=d.code,
                        department_name=d.name,
                        governance_status=gov_status,
                        admin_name=admin_name,
                        admin_email=admin_email,
                        total_establishments=d_est,
                        total_campuses=d_cmp,
                        pipeline_in_progress=d_pipe,
                        active_institutions=d_act,
                        inactive_institutions=d_inact,
                        provisioning_rate_percent=rate,
                    )
                )

            return TerritorialControlCenterResponse(
                scope_level="NATIONAL",
                jurisdiction_name="República de Colombia",
                tier1_catalog=tier1_catalog,
                tier2_pipeline=tier2_pipeline,
                tier3_tenancy=tier3_tenancy,
                tier4_governance=tier4_governance,
                department_matrix=matrix,
                computed_at=now,
            )

        else:
            # -------------------------------------------------------------------
            # DEPARTMENT SCOPE (department_admin)
            # -------------------------------------------------------------------
            dept = await self._resolve_department_from_scope(scope)
            if not dept:
                raise AuthorizationError(
                    "Departamento no asignado o inválido.",
                    code="PERMISSION_DENIED",
                )

            # Tier 1 scoped to this department
            total_departments = 1
            total_municipalities = (
                await self._session.execute(
                    select(func.count(Municipality.id)).where(
                        Municipality.department_id == dept.id
                    )
                )
            ).scalar_one() or 0
            total_establishments = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.department_code == dept.code
                    )
                )
            ).scalar_one() or 0
            total_campuses = (
                await self._session.execute(
                    select(func.count(OfficialCampusCatalog.id))
                    .join(
                        OfficialInstitutionCatalog,
                        OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id,
                    )
                    .where(OfficialInstitutionCatalog.department_code == dept.code)
                )
            ).scalar_one() or 0
            official_sector_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.department_code == dept.code,
                        OfficialInstitutionCatalog.sector == "OFICIAL",
                    )
                )
            ).scalar_one() or 0
            non_official_sector_count = max(0, total_establishments - official_sector_count)
            urban_zone_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.department_code == dept.code,
                        OfficialInstitutionCatalog.zone == "URBANA",
                    )
                )
            ).scalar_one() or 0
            rural_zone_count = (
                await self._session.execute(
                    select(func.count(OfficialInstitutionCatalog.id)).where(
                        OfficialInstitutionCatalog.department_code == dept.code,
                        OfficialInstitutionCatalog.zone == "RURAL",
                    )
                )
            ).scalar_one() or 0

            tier1_catalog = Tier1CatalogMetrics(
                total_departments=total_departments,
                total_municipalities=total_municipalities,
                total_establishments=total_establishments,
                total_campuses=total_campuses,
                official_sector_count=official_sector_count,
                non_official_sector_count=non_official_sector_count,
                urban_zone_count=urban_zone_count,
                rural_zone_count=rural_zone_count,
            )

            # Tier 2 scoped to dept
            req_counts = dict(
                (
                    await self._session.execute(
                        select(
                            InstitutionOnboardingRequest.status,
                            func.count(InstitutionOnboardingRequest.id),
                        )
                        .where(InstitutionOnboardingRequest.department_id == dept.id)
                        .group_by(InstitutionOnboardingRequest.status)
                    )
                ).all()
            )
            total_requests = sum(req_counts.values())
            tier2_pipeline = Tier2PipelineMetrics(
                total_requests=total_requests,
                submitted=req_counts.get("SUBMITTED", 0),
                under_review=req_counts.get("UNDER_REVIEW", 0),
                approved=req_counts.get("APPROVED", 0),
                provisioned=req_counts.get("PROVISIONED", 0),
                rejected=req_counts.get("REJECTED", 0),
                cancelled=req_counts.get("CANCELLED", 0),
            )

            # Tier 3 scoped to dept
            mun_ids_subq = select(Municipality.id).where(
                Municipality.department_id == dept.id
            )
            total_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(
                        Institution.municipality_id.in_(mun_ids_subq)
                    )
                )
            ).scalar_one() or 0
            active_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(
                        Institution.municipality_id.in_(mun_ids_subq),
                        Institution.is_active == True,
                    )
                )
            ).scalar_one() or 0
            inactive_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(
                        Institution.municipality_id.in_(mun_ids_subq),
                        Institution.is_active == False,
                    )
                )
            ).scalar_one() or 0
            catalog_linked_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(
                        Institution.municipality_id.in_(mun_ids_subq),
                        Institution.catalog_institution_id.isnot(None),
                    )
                )
            ).scalar_one() or 0
            synthetic_fixture_institutions = (
                await self._session.execute(
                    select(func.count(Institution.id)).where(
                        Institution.municipality_id.in_(mun_ids_subq),
                        Institution.catalog_institution_id.is_(None),
                    )
                )
            ).scalar_one() or 0
            inst_ids_subq = select(Institution.id).where(
                Institution.municipality_id.in_(mun_ids_subq)
            )
            provisioned_campuses = (
                await self._session.execute(
                    select(func.count(Campus.id)).where(
                        Campus.institution_id.in_(inst_ids_subq)
                    )
                )
            ).scalar_one() or 0
            active_operational_campuses = (
                await self._session.execute(
                    select(func.count(Campus.id)).where(
                        Campus.institution_id.in_(inst_ids_subq),
                        Campus.is_active == True,
                    )
                )
            ).scalar_one() or 0
            total_users = (
                await self._session.execute(
                    select(func.count(User.id)).where(
                        User.institution_id.in_(inst_ids_subq)
                    )
                )
            ).scalar_one() or 0
            active_students = (
                await self._session.execute(
                    select(func.count(Student.id)).where(
                        Student.institution_id.in_(inst_ids_subq)
                    )
                )
            ).scalar_one() or 0
            active_teachers = (
                await self._session.execute(
                    select(func.count(Teacher.id)).where(
                        Teacher.institution_id.in_(inst_ids_subq)
                    )
                )
            ).scalar_one() or 0

            tier3_tenancy = Tier3TenancyMetrics(
                total_institutions=total_institutions,
                active_institutions=active_institutions,
                inactive_institutions=inactive_institutions,
                catalog_linked_institutions=catalog_linked_institutions,
                synthetic_fixture_institutions=synthetic_fixture_institutions,
                provisioned_campuses=provisioned_campuses,
                active_operational_campuses=active_operational_campuses,
                total_users=total_users,
                active_students=active_students,
                active_teachers=active_teachers,
            )

            # Tier 4 scoped to dept
            da_users_count = (
                await self._session.execute(
                    select(func.count(func.distinct(User.id)))
                    .join(UserRole, User.id == UserRole.user_id)
                    .join(Role, UserRole.role_id == Role.id)
                    .where(
                        Role.name == "department_admin",
                        UserRole.department_id == dept.id,
                        UserRole.is_active == True,
                    )
                )
            ).scalar_one() or 0
            covered_departments = 1
            vacant_departments = 0
            pending_invitations = (
                await self._session.execute(
                    select(func.count(DepartmentAdminInvitation.id)).where(
                        DepartmentAdminInvitation.department_id == dept.id,
                        DepartmentAdminInvitation.is_used == False,
                        DepartmentAdminInvitation.is_revoked == False,
                        DepartmentAdminInvitation.expires_at > func.now(),
                    )
                )
            ).scalar_one() or 0

            tier4_governance = Tier4GovernanceMetrics(
                total_departments=1,
                department_admin_users_count=da_users_count,
                covered_departments=covered_departments,
                vacant_departments=vacant_departments,
                pending_invitations=pending_invitations,
                coverage_percentage=100.0,
            )

            # Matrix: EXACTLY 1 row for the assigned department
            d_est = total_establishments
            d_cmp = total_campuses
            d_pipe = total_requests
            d_act = active_institutions
            d_inact = inactive_institutions
            rate = round((d_act / d_est) * 100, 2) if d_est > 0 else 0.0

            da_info = (
                await self._session.execute(
                    select(User.first_name, User.last_name, User.email)
                    .join(UserRole, User.id == UserRole.user_id)
                    .join(Role, UserRole.role_id == Role.id)
                    .where(
                        Role.name == "department_admin",
                        UserRole.department_id == dept.id,
                        UserRole.is_active == True,
                    )
                )
            ).first()
            admin_name = f"{da_info[0] or ''} {da_info[1] or ''}".strip() if da_info else None
            admin_email = da_info[2] if da_info else None

            single_matrix_row = DepartmentMatrixRow(
                department_id=dept.id,
                department_code=dept.code,
                department_name=dept.name,
                governance_status="COVERED",
                admin_name=admin_name,
                admin_email=admin_email,
                total_establishments=d_est,
                total_campuses=d_cmp,
                pipeline_in_progress=d_pipe,
                active_institutions=d_act,
                inactive_institutions=d_inact,
                provisioning_rate_percent=rate,
            )

            return TerritorialControlCenterResponse(
                scope_level="DEPARTMENT",
                jurisdiction_name=dept.name,
                tier1_catalog=tier1_catalog,
                tier2_pipeline=tier2_pipeline,
                tier3_tenancy=tier3_tenancy,
                tier4_governance=tier4_governance,
                department_matrix=[single_matrix_row],
                computed_at=now,
            )

    async def get_department_control_center_detail(
        self,
        scope: OrganizationalScope,
        department_code: str,
    ) -> DepartmentDetailControlCenterResponse:
        """
        Exhaustive municipal breakdown of a department for inspection modal/drawer.
        Strictly enforces Anti-IDOR:
        - NATIONAL: Can view any valid department.
        - DEPARTMENT: Can view ONLY assigned department (HTTP 403 on foreign department).
        - Other scopes: HTTP 403 Forbidden.
        """
        now = datetime.now(UTC)

        if scope.is_institution():
            raise AuthorizationError(
                "No está autorizado para acceder al Centro de Control Territorial.",
                code="PERMISSION_DENIED",
            )

        if scope.is_department():
            caller_dept = await self._resolve_department_from_scope(scope)
            if not caller_dept or caller_dept.code != department_code:
                raise AuthorizationError(
                    "No está autorizado para consultar detalles territoriales de otro departamento.",
                    code="PERMISSION_DENIED",
                )
        elif not scope.is_national():
            raise AuthorizationError(
                "No está autorizado para acceder al Centro de Control Territorial.",
                code="PERMISSION_DENIED",
            )

        dept = (
            await self._session.execute(
                select(Department).where(Department.code == department_code)
            )
        ).scalar_one_or_none()

        if not dept:
            raise NotFoundError(
                f"Departamento con código '{department_code}' no encontrado."
            )

        mun_rows = (
            await self._session.execute(
                select(Municipality)
                .where(Municipality.department_id == dept.id)
                .order_by(Municipality.code)
            )
        ).scalars().all()

        cat_est_by_mun = dict(
            (
                await self._session.execute(
                    select(
                        OfficialInstitutionCatalog.municipality_code,
                        func.count(OfficialInstitutionCatalog.id),
                    )
                    .where(OfficialInstitutionCatalog.department_code == dept.code)
                    .group_by(OfficialInstitutionCatalog.municipality_code)
                )
            ).all()
        )

        cat_cmp_by_mun = dict(
            (
                await self._session.execute(
                    select(
                        OfficialInstitutionCatalog.municipality_code,
                        func.count(OfficialCampusCatalog.id),
                    )
                    .join(
                        OfficialInstitutionCatalog,
                        OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id,
                    )
                    .where(OfficialInstitutionCatalog.department_code == dept.code)
                    .group_by(OfficialInstitutionCatalog.municipality_code)
                )
            ).all()
        )

        mun_ids = [m.id for m in mun_rows]
        inst_counts = (
            await self._session.execute(
                select(
                    Institution.municipality_id,
                    Institution.is_active,
                    func.count(Institution.id),
                )
                .where(Institution.municipality_id.in_(mun_ids))
                .group_by(Institution.municipality_id, Institution.is_active)
            )
        ).all()
        act_inst_by_mun: dict[uuid.UUID, int] = {}
        inact_inst_by_mun: dict[uuid.UUID, int] = {}
        for m_id, is_act, cnt in inst_counts:
            if is_act:
                act_inst_by_mun[m_id] = act_inst_by_mun.get(m_id, 0) + cnt
            else:
                inact_inst_by_mun[m_id] = inact_inst_by_mun.get(m_id, 0) + cnt

        pipe_by_mun = dict(
            (
                await self._session.execute(
                    select(
                        InstitutionOnboardingRequest.municipality_id,
                        func.count(InstitutionOnboardingRequest.id),
                    )
                    .where(
                        InstitutionOnboardingRequest.department_id == dept.id,
                        InstitutionOnboardingRequest.status.in_(
                            ["SUBMITTED", "UNDER_REVIEW", "APPROVED"]
                        ),
                    )
                    .group_by(InstitutionOnboardingRequest.municipality_id)
                )
            ).all()
        )

        da_info = (
            await self._session.execute(
                select(User.first_name, User.last_name, User.email)
                .join(UserRole, User.id == UserRole.user_id)
                .join(Role, UserRole.role_id == Role.id)
                .where(
                    Role.name == "department_admin",
                    UserRole.department_id == dept.id,
                    UserRole.is_active == True,
                )
            )
        ).first()

        admin_name = f"{da_info[0] or ''} {da_info[1] or ''}".strip() if da_info else None
        admin_email = da_info[2] if da_info else None

        pending_inv = (
            await self._session.execute(
                select(func.count(DepartmentAdminInvitation.id)).where(
                    DepartmentAdminInvitation.department_id == dept.id,
                    DepartmentAdminInvitation.is_used == False,
                    DepartmentAdminInvitation.is_revoked == False,
                    DepartmentAdminInvitation.expires_at > func.now(),
                )
            )
        ).scalar_one() or 0

        gov_status = "COVERED" if admin_name else ("INVITED" if pending_inv > 0 else "VACANT")

        municipality_rows = []
        tot_est = 0
        tot_cmp = 0
        tot_act = 0
        tot_inact = 0
        tot_pipe = 0

        for m in mun_rows:
            m_est = cat_est_by_mun.get(m.code, 0)
            m_cmp = cat_cmp_by_mun.get(m.code, 0)
            m_act = act_inst_by_mun.get(m.id, 0)
            m_inact = inact_inst_by_mun.get(m.id, 0)
            m_pipe = pipe_by_mun.get(m.id, 0)

            tot_est += m_est
            tot_cmp += m_cmp
            tot_act += m_act
            tot_inact += m_inact
            tot_pipe += m_pipe

            municipality_rows.append(
                DepartmentMunicipalityRow(
                    municipality_id=m.id,
                    municipality_code=m.code,
                    municipality_name=m.name,
                    total_establishments=m_est,
                    total_campuses=m_cmp,
                    active_institutions=m_act,
                    inactive_institutions=m_inact,
                    pipeline_in_progress=m_pipe,
                )
            )

        return DepartmentDetailControlCenterResponse(
            department_id=dept.id,
            department_code=dept.code,
            department_name=dept.name,
            governance_status=gov_status,
            admin_name=admin_name,
            admin_email=admin_email,
            total_municipalities=len(mun_rows),
            total_establishments=tot_est,
            total_campuses=tot_cmp,
            active_institutions=tot_act,
            inactive_institutions=tot_inact,
            pipeline_in_progress=tot_pipe,
            municipalities=municipality_rows,
            computed_at=now,
        )
