"""
Inspect canonical names in official_institution_catalog
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text, desc

DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"
engine = create_async_engine(DB_URL, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_names():
    async with async_session_factory() as session:
        # Check current operational departments
        op_depts = (await session.execute(text("SELECT code, name, id FROM departments ORDER BY code"))).all()
        print("CURRENT OPERATIONAL DEPARTMENTS:")
        for r in op_depts:
            print(f"  {r[0]}: {r[1]!r} (ID: {r[2]})")

        # Check all 33 departments in official_institution_catalog and their name frequencies
        print("\nCATALOG DEPARTMENTS & NAME FREQUENCIES:")
        dept_rows = (await session.execute(text("""
            SELECT department_code, department_name, count(*) as cnt
            FROM official_institution_catalog
            GROUP BY department_code, department_name
            ORDER BY department_code, cnt DESC
        """))).all()
        
        dept_name_map = {}
        for r in dept_rows:
            code, name, cnt = r[0], r[1], r[2]
            if code not in dept_name_map:
                dept_name_map[code] = []
            dept_name_map[code].append((name, cnt))
            
        for code in sorted(dept_name_map.keys()):
            variants = dept_name_map[code]
            print(f"  {code}: {variants}")

        # Check operational municipalities
        op_munis = (await session.execute(text("SELECT code, name, department_id, id FROM municipalities ORDER BY code"))).all()
        print("\nCURRENT OPERATIONAL MUNICIPALITIES:")
        for r in op_munis:
            print(f"  {r[0]}: {r[1]!r} (DeptID: {r[2]}, ID: {r[3]})")

        # Check total municipalities in catalog
        muni_count = (await session.execute(text("SELECT count(distinct municipality_code) FROM official_institution_catalog"))).scalar()
        print(f"\nTOTAL DISTINCT MUNICIPALITY CODES IN CATALOG: {muni_count}")

if __name__ == "__main__":
    asyncio.run(check_names())
