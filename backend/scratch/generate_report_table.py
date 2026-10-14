import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")

async def gen():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT 
                i.name AS inst_name,
                i.id AS inst_id,
                i.dane_code AS inst_dane,
                i.catalog_institution_id AS cat_id,
                c.name AS cat_name,
                i.is_active,
                m.code AS muni_code,
                d.code AS dept_code
            FROM institutions i
            JOIN municipalities m ON i.municipality_id = m.id
            JOIN departments d ON m.department_id = d.id
            LEFT JOIN official_institution_catalog c ON i.catalog_institution_id = c.id
            ORDER BY 
                (i.catalog_institution_id IS NULL),
                d.code,
                m.code,
                i.name
        """))
        rows = res.fetchall()
        for idx, r in enumerate(rows, 1):
            cat_id_str = str(r.cat_id) if r.cat_id else "NULL"
            cat_name_str = r.cat_name if r.cat_name else "N/A"
            status = "VERIFIED REAL MATCH" if r.cat_id else "SYNTHETIC FIXTURE (NULL)"
            print(f"| {idx:02d} | `{r.inst_name}` | `{r.inst_id}` | `{r.inst_dane}` | `{cat_id_str}` | `{cat_name_str}` | **{status}** |")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(gen())
