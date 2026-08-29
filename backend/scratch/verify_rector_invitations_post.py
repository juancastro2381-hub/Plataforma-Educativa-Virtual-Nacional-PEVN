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
        print("POST-MIGRATION COLUMNS in rector_invitations:")
        col_names = []
        for r in cols.fetchall():
            print(" -", r)
            col_names.append(r[0])
        
        assert "updated_at" in col_names, "updated_at missing!"
        assert "created_at" in col_names, "created_at missing!"
        
        cnt = (await session.execute(text("SELECT count(*) FROM rector_invitations;"))).scalar()
        print("ROW COUNT:", cnt)
        
        null_cnt = (await session.execute(text("SELECT count(*) FROM rector_invitations WHERE updated_at IS NULL;"))).scalar()
        print("NULL updated_at count:", null_cnt)
        assert null_cnt == 0, "Found NULL updated_at!"
        print("MIGRATION 015 VERIFICATION PASSED!")

if __name__ == "__main__":
    asyncio.run(check())
