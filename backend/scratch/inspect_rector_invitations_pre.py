import asyncio
from sqlalchemy import text
from app.db.session import get_session_factory

async def check():
    factory = get_session_factory()
    async with factory() as session:
        cols = await session.execute(text(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_name = 'rector_invitations' "
            "ORDER BY ordinal_position;"
        ))
        print("CURRENT COLUMNS in rector_invitations:")
        for r in cols.fetchall():
            print(" -", r)
        cnt = (await session.execute(text("SELECT count(*) FROM rector_invitations;"))).scalar()
        print("ROW COUNT:", cnt)

if __name__ == "__main__":
    asyncio.run(check())
