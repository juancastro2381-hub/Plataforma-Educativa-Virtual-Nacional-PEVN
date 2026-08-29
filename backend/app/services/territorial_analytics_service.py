"""
PEVN Backend — Territorial Analytics Domain Service

Provides high-performance, strictly isolated aggregation queries across
Colombian territorial hierarchies, official educational catalogs, and
provisioned institutional tenants.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from sqlalchemy import func, select, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import audit_service
from app.core.logging import get_logger
from app.core.security.interfaces import OrganizationalScope
from app.exceptions.errors import AuthorizationError, NotFoundError
from app.models.enrollment import Enrollment
from app.models.group import Group
from app.models.institution import Campus, Institution
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialInstitutionCatalog,
)
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.territory import Department, Municipality
from app.models.user import User
from app.schemas.analytics import (
    DepartmentAnalyticsItem,
    DepartmentAnalyticsResponse,
    InstitutionalKPIResponse,
    MunicipalityAnalyticsItem,
    MunicipalityAnalyticsResponse,
    TerritorialSectorBreakdown,
    TerritorialSummaryResponse,
    TerritorialZoneBreakdown,
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

        # department_id could be UUID string or 2-digit code
        stmt = select(Department).where(
            (Department.code == scope.department_id)
            | (Department.id.cast(func.text()) == scope.department_id)
        )
        res = await self._session.execute(stmt)
        dept = res.scalar_one_or_none()
        if dept:
            return dept.code, dept.name
        return scope.department_id, None

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

        # 3. Institutional Scope
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
        # Group by OfficialInstitutionCatalog.department_code, department_name
        stmt = (
            select(
                OfficialInstitutionCatalog.department_code,
                OfficialInstitutionCatalog.department_name,
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
                OfficialInstitutionCatalog.department_name,
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
        if scope.is_department():
            scoped_dept, _ = await self._resolve_department_code_from_scope(scope)
            if department_code and department_code != scoped_dept:
                raise AuthorizationError(
                    "No está autorizado para consultar municipios fuera de su departamento asignado.",
                    code="PERMISSION_DENIED",
                )
            department_code = scoped_dept
        elif not scope.is_national():
            raise AuthorizationError(
                "Se requiere alcance nacional o departamental para consultar la distribución municipal.",
                code="PERMISSION_DENIED",
            )

        stmt = (
            select(
                OfficialInstitutionCatalog.municipality_code,
                OfficialInstitutionCatalog.municipality_name,
                OfficialInstitutionCatalog.department_code,
                OfficialInstitutionCatalog.department_name,
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
                OfficialInstitutionCatalog.municipality_name,
                OfficialInstitutionCatalog.department_code,
                OfficialInstitutionCatalog.department_name,
            )
            .order_by(OfficialInstitutionCatalog.municipality_name)
        )

        if department_code:
            stmt = stmt.where(OfficialInstitutionCatalog.department_code == department_code)

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

        # Enforce scope containment
        if scope.is_institution():
            scoped_inst = scope.institution_id
            if scoped_inst and str(scoped_inst) != str(institution_id):
                raise AuthorizationError(
                    "No está autorizado para consultar métricas de otra institución educativa.",
                    code="PERMISSION_DENIED",
                )

        inst = await self._session.get(Institution, institution_id)
        if not inst:
            raise NotFoundError("Institución educativa no encontrada.")

        # Resolve department & municipality
        mun = await self._session.get(Municipality, inst.municipality_id)
        dept = await self._session.get(Department, mun.department_id) if mun else None

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
