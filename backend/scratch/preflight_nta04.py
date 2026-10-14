import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DATABASE_URL = get_safe_test_db_url()

async def preflight():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("=== NTA-04 PRE-IMPLEMENTATION BASELINE CAPTURE ===")
        
        depts = (await conn.execute(text("SELECT count(*) FROM departments"))).scalar()
        munis = (await conn.execute(text("SELECT count(*) FROM municipalities"))).scalar()
        inst_total = (await conn.execute(text("SELECT count(*) FROM institutions"))).scalar()
        inst_active = (await conn.execute(text("SELECT count(*) FROM institutions WHERE is_active = true"))).scalar()
        inst_inactive = (await conn.execute(text("SELECT count(*) FROM institutions WHERE is_active = false"))).scalar()
        inst_catalog_linked = (await conn.execute(text("SELECT count(*) FROM institutions WHERE catalog_institution_id IS NOT NULL"))).scalar()
        inst_synthetic = (await conn.execute(text("SELECT count(*) FROM institutions WHERE catalog_institution_id IS NULL"))).scalar()
        campuses = (await conn.execute(text("SELECT count(*) FROM campuses"))).scalar()
        users = (await conn.execute(text("SELECT count(*) FROM users"))).scalar()
        users_active = (await conn.execute(text("SELECT count(*) FROM users WHERE is_active = true"))).scalar()
        da_scoped = (await conn.execute(text("""
            SELECT count(*) 
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'department_admin' AND ur.department_id IS NOT NULL
        """))).scalar()
        catalog_total = (await conn.execute(text("SELECT count(*) FROM official_institution_catalog"))).scalar()
        
        # Check orphans
        muni_orphans = (await conn.execute(text("""
            SELECT count(*) FROM municipalities m LEFT JOIN departments d ON m.department_id = d.id WHERE d.id IS NULL
        """))).scalar()
        inst_muni_orphans = (await conn.execute(text("""
            SELECT count(*) FROM institutions i LEFT JOIN municipalities m ON i.municipality_id = m.id WHERE m.id IS NULL
        """))).scalar()
        campus_orphans = (await conn.execute(text("""
            SELECT count(*) FROM campuses c LEFT JOIN institutions i ON c.institution_id = i.id WHERE i.id IS NULL
        """))).scalar()
        
        # Alembic current
        alembic_rev = (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar()

        print(f"Departments: {depts}")
        print(f"Municipalities: {munis}")
        print(f"Institutions Total: {inst_total}")
        print(f"Institutions Active: {inst_active}")
        print(f"Institutions Inactive: {inst_inactive}")
        print(f"Institutions Catalog-Linked (Real): {inst_catalog_linked}")
        print(f"Institutions Synthetic (NULL Catalog): {inst_synthetic}")
        print(f"Campuses Total: {campuses}")
        print(f"Users Total: {users} (Active: {users_active})")
        print(f"Scoped Department Admins: {da_scoped}")
        print(f"Official Catalog Universe: {catalog_total}")
        print(f"Municipality Orphans: {muni_orphans}")
        print(f"Institution Municipality Orphans: {inst_muni_orphans}")
        print(f"Campus Orphans: {campus_orphans}")
        print(f"Alembic Current Revision: {alembic_rev}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(preflight())
