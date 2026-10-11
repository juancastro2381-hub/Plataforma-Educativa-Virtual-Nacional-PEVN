"""
Test DIVIPOLA canonical extraction from official_institution_catalog
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"
engine = create_async_engine(DB_URL, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_extraction():
    async with async_session_factory() as session:
        # 1. Departments extraction
        # Mode of department_name for each department_code
        dept_sql = """
        WITH ranked_depts AS (
            SELECT 
                department_code,
                department_name,
                count(*) as cnt,
                ROW_NUMBER() OVER(PARTITION BY department_code ORDER BY count(*) DESC, department_name ASC) as rn
            FROM official_institution_catalog
            GROUP BY department_code, department_name
        )
        SELECT department_code, department_name
        FROM ranked_depts
        WHERE rn = 1
        ORDER BY department_code;
        """
        depts = (await session.execute(text(dept_sql))).all()
        print(f"Extracted {len(depts)} canonical departments:")
        dept_map = {}
        for code, name in depts:
            dept_map[code] = name
            print(f"  {code}: {name}")
            
        assert len(dept_map) == 33, f"Expected 33 departments, got {len(dept_map)}"

        # 2. Municipalities extraction
        # Mode of municipality_name and department_code for each municipality_code
        muni_sql = """
        WITH ranked_munis AS (
            SELECT 
                municipality_code,
                department_code,
                municipality_name,
                count(*) as cnt,
                ROW_NUMBER() OVER(PARTITION BY municipality_code ORDER BY count(*) DESC, municipality_name ASC) as rn
            FROM official_institution_catalog
            GROUP BY municipality_code, department_code, municipality_name
        )
        SELECT municipality_code, department_code, municipality_name
        FROM ranked_munis
        WHERE rn = 1
        ORDER BY municipality_code;
        """
        munis = (await session.execute(text(muni_sql))).all()
        print(f"\nExtracted {len(munis)} canonical municipalities:")
        muni_map = {}
        for m_code, d_code, m_name in munis:
            assert d_code in dept_map, f"Municipality {m_code} references unknown dept {d_code}"
            assert m_code not in muni_map, f"Duplicate municipality code {m_code}"
            muni_map[m_code] = (d_code, m_name)
            
        assert len(muni_map) == 1119, f"Expected 1119 municipalities, got {len(muni_map)}"
        print(f"SUCCESS: 1,119 unique municipalities validated, all mapping to valid department codes!")

        # Check existing 3 departments:
        # 08: ATLÁNTICO
        # 11: CAPITAL BOGOTÁ, D.C.
        # 25: CUNDINAMARCA
        for op_code in ["08", "11", "25"]:
            print(f"Op Dept {op_code}: extracted name = '{dept_map[op_code]}'")
            
        # Check existing 3 municipalities:
        # 08001: BARRANQUILLA
        # 11001: BOGOTÁ, D.C.
        # 25286: FUNZA
        for op_muni in ["08001", "11001", "25286"]:
            print(f"Op Muni {op_muni}: extracted = {muni_map[op_muni]}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
