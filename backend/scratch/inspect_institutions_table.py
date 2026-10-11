import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import get_settings

async def check():
    engine = create_async_engine(get_settings().DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'institutions'
            ORDER BY ordinal_position;
        """))
        print("Columns in 'institutions' table:")
        for row in res.fetchall():
            print(" -", dict(row._mapping))

if __name__ == "__main__":
    asyncio.run(check())
