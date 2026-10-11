import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

for url in [
    "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5432/pevn_db",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/pevn_db",
    "postgresql+asyncpg://pevn_admin:pevn_admin_dev_pass@localhost:5432/pevn_db",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
]:
    try:
        engine = create_async_engine(url)
        async def test(eng=engine):
            async with eng.connect() as conn:
                res = await conn.execute(text("SELECT current_database(), current_user"))
                print(f"SUCCESS with {url} -> {res.fetchone()}")
        asyncio.run(test())
    except Exception as e:
        print(f"FAILED {url} -> {type(e).__name__}: {e}")
