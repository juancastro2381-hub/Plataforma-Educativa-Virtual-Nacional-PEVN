import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, dane_code, name, created_at FROM institutions ORDER BY created_at"))
        for r in res.fetchall():
            print(f"{r.created_at} | {r.dane_code} | {r.name}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
