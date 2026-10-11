"""
PEVN — NTA-02 Mandatory Preflight Script
Performs read-only inspection of the current database state before migration.
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, select, distinct
from app.models.territory import Department, Municipality
from app.models.institution import Institution, Campus
from app.models.role import Role, UserRole
from app.models.user import User
from app.models.official_catalog import OfficialInstitutionCatalog, OfficialCampusCatalog

DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"
engine = create_async_engine(DB_URL, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def run_preflight():
    async with async_session_factory() as session:
        # A. Current department count
        dept_count = (await session.execute(select(func.count(Department.id)))).scalar_one()
        
        # B. Current municipality count
        muni_count = (await session.execute(select(func.count(Municipality.id)))).scalar_one()
        
        # C. Current institution count
        inst_total = (await session.execute(select(func.count(Institution.id)))).scalar_one()
        
        # D. Active institution count
        inst_active = (await session.execute(select(func.count(Institution.id)).where(Institution.is_active == True))).scalar_one()
        
        # E. Inactive institution count
        inst_inactive = (await session.execute(select(func.count(Institution.id)).where(Institution.is_active == False))).scalar_one()
        
        # F. Current campuses
        campuses_total = (await session.execute(select(func.count(Campus.id)))).scalar_one()
        campuses_active = (await session.execute(select(func.count(Campus.id)).where(Campus.is_active == True))).scalar_one()
        campuses_inactive = (await session.execute(select(func.count(Campus.id)).where(Campus.is_active == False))).scalar_one()
        
        # G. Current department_admin assignments
        da_role = (await session.execute(select(Role).where(Role.name == "department_admin"))).scalar_one_or_none()
        da_assignments = []
        if da_role:
            da_stmt = select(UserRole).where(UserRole.role_id == da_role.id)
            da_assignments = (await session.execute(da_stmt)).scalars().all()
        
        # H. Existing department codes and UUIDs
        existing_depts = (await session.execute(select(Department).order_by(Department.code))).scalars().all()
        
        # I. Existing municipality codes and UUIDs
        existing_munis = (await session.execute(select(Municipality).order_by(Municipality.code))).scalars().all()
        
        print(f"=== PREFLIGHT COUNTS ===")
        print(f"Departments: {dept_count}")
        print(f"Municipalities: {muni_count}")
        print(f"Institutions: {inst_total} (Active: {inst_active}, Inactive: {inst_inactive})")
        print(f"Campuses: {campuses_total} (Active: {campuses_active}, Inactive: {campuses_inactive})")
        print(f"Total DA user_roles: {len(da_assignments)} (With dept_id: {sum(1 for ur in da_assignments if ur.department_id is not None)})")
        
        print("\n=== EXISTING DEPARTMENTS ===")
        for d in existing_depts:
            print(f"  Code: {d.code} | Name: {d.name} | ID: {d.id}")
            
        print("\n=== EXISTING MUNICIPALITIES ===")
        for m in existing_munis:
            print(f"  Code: {m.code} | Name: {m.name} | DeptID: {m.department_id} | ID: {m.id}")

        # Check catalog departments and municipalities
        cat_depts = (await session.execute(
            select(
                OfficialInstitutionCatalog.department_code,
                func.count(distinct(OfficialInstitutionCatalog.department_name)).label("name_variants"),
                func.array_agg(distinct(OfficialInstitutionCatalog.department_name)).label("names"),
                func.count(distinct(OfficialInstitutionCatalog.municipality_code)).label("mun_count"),
                func.count(OfficialInstitutionCatalog.id).label("inst_count")
            ).group_by(OfficialInstitutionCatalog.department_code)
            .order_by(OfficialInstitutionCatalog.department_code)
        )).all()
        
        print(f"\n=== CATALOG DEPARTMENTS ({len(cat_depts)}) ===")
        for cd in cat_depts:
            print(f"  Dept {cd.department_code}: Variants={cd.name_variants} Names={cd.names} Munis={cd.mun_count} Insts={cd.inst_count}")

        # Check catalog municipality name variants
        cat_munis_variants = (await session.execute(
            select(
                OfficialInstitutionCatalog.municipality_code,
                func.count(distinct(OfficialInstitutionCatalog.municipality_name)).label("name_variants"),
                func.array_agg(distinct(OfficialInstitutionCatalog.municipality_name)).label("names"),
                func.count(distinct(OfficialInstitutionCatalog.department_code)).label("dept_variants"),
                func.array_agg(distinct(OfficialInstitutionCatalog.department_code)).label("dept_codes")
            ).group_by(OfficialInstitutionCatalog.municipality_code)
            .having(func.count(distinct(OfficialInstitutionCatalog.municipality_name)) > 1)
        )).all()
        
        print(f"\n=== MUNICIPALITIES WITH MULTIPLE NAME VARIANTS IN CATALOG: {len(cat_munis_variants)} ===")
        for cm in cat_munis_variants[:10]:
            print(f"  Muni {cm.municipality_code}: Depts={cm.dept_codes} Names={cm.names}")
            
        # Check if any municipality code belongs to multiple department codes in catalog
        multi_dept_munis = (await session.execute(
            select(
                OfficialInstitutionCatalog.municipality_code,
                func.count(distinct(OfficialInstitutionCatalog.department_code)).label("dept_count"),
                func.array_agg(distinct(OfficialInstitutionCatalog.department_code)).label("depts")
            ).group_by(OfficialInstitutionCatalog.municipality_code)
            .having(func.count(distinct(OfficialInstitutionCatalog.department_code)) > 1)
        )).all()
        print(f"\n=== MUNICIPALITIES ASSIGNED TO MULTIPLE DEPARTMENTS: {len(multi_dept_munis)} ===")
        for mdm in multi_dept_munis:
            print(f"  Muni {mdm.municipality_code}: Depts={mdm.depts}")

        # Check total distinct municipality codes in catalog
        total_cat_munis = (await session.execute(
            select(func.count(distinct(OfficialInstitutionCatalog.municipality_code)))
        )).scalar_one()
        print(f"\nTotal distinct municipality codes in catalog: {total_cat_munis}")

if __name__ == "__main__":
    asyncio.run(run_preflight())
