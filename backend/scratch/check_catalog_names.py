import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DATABASE_URL = get_safe_test_db_url()

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        for name in ['Colegio San Pedro', 'Colegio Distrital Santander', 'Colegio Mayor', 'Colegio Departamental', 'Colegio Santa Clara', 'Colegio Test']:
            res = await conn.execute(text(f"SELECT dane_code, name, department_name, municipality_name FROM official_institution_catalog WHERE name ILIKE '%{name}%' LIMIT 3"))
            rows = res.fetchall()
            print(f"Search for '{name}': {len(rows)} matches")
            for r in rows:
                print(f"   {r[0]} | {r[1]} | {r[2]} | {r[3]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
