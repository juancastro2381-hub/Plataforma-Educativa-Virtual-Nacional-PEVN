import asyncio
from sqlalchemy import text
from app.db.session import get_session_factory

async def main():
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'teachers' 
            ORDER BY ordinal_position;
        """))
        for row in res.fetchall():
            print(row)

if __name__ == "__main__":
    asyncio.run(main())
