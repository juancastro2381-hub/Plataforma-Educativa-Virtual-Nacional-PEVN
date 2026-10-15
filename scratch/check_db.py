import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT count(*) FROM institutional_communications"))
        print("Communications count in db:", res.scalar())
        res = await conn.execute(text("SELECT count(*) FROM institutional_news"))
        print("News count in db:", res.scalar())
        res = await conn.execute(text("SELECT count(*) FROM student_submissions"))
        print("Submissions count in db:", res.scalar())
        res = await conn.execute(text("SELECT count(*) FROM students"))
        print("Students count in db:", res.scalar())
        res = await conn.execute(text("SELECT count(*) FROM institutions"))
        print("Institutions count in db:", res.scalar())

if __name__ == '__main__':
    asyncio.run(main())
