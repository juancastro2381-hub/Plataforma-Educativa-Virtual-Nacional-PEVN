import asyncio
from sqlalchemy import text
from app.db.session import get_session_factory

async def check():
    factory = get_session_factory()
    async with factory() as session:
        # Check column names
        cols = await session.execute(text(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_name = 'role_permissions' "
            "ORDER BY ordinal_position;"
        ))
        print("CURRENT COLUMNS in role_permissions:")
        for r in cols.fetchall():
            print(" -", r)
        
        # Check row count
        cnt = await session.execute(text("SELECT count(*) FROM role_permissions;"))
        print("ROW COUNT:", cnt.scalar())

if __name__ == "__main__":
    asyncio.run(check())
