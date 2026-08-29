import asyncio
from sqlalchemy import text
from app.db.session import get_session_factory
from app.db.base import Base

async def audit_all_tables():
    factory = get_session_factory()
    async with factory() as session:
        # Get all physical tables and their columns in PostgreSQL
        res = await session.execute(text(
            "SELECT table_name, column_name "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "ORDER BY table_name, ordinal_position;"
        ))
        db_cols: dict[str, set[str]] = {}
        for tname, cname in res.fetchall():
            db_cols.setdefault(tname, set()).add(cname)
        
        print("=== DATABASE TABLES VS SQLALCHEMY MODELS AUDIT ===")
        for table in Base.metadata.tables.values():
            tname = table.name
            model_cols = set(table.columns.keys())
            if tname not in db_cols:
                print(f"MISSING TABLE IN DB: {tname}")
            else:
                missing_in_db = model_cols - db_cols[tname]
                if missing_in_db:
                    print(f"TABLE '{tname}' MISSING COLUMNS IN DB: {missing_in_db}")
                else:
                    print(f"TABLE '{tname}' OK (All {len(model_cols)} columns present)")

if __name__ == "__main__":
    asyncio.run(audit_all_tables())
