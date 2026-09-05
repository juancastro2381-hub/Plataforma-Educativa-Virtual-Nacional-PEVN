import asyncio
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.base_class import Base
# Import all models
import app.models  # noqa: F401
from app.db.session import get_session_factory

async def check_all_tables():
    factory = get_session_factory()
    async with factory() as session:
        print("\n=== COMPARISON OF SQLALCHEMY MODELS VS POSTGRESQL TABLES ===")
        for table_name, table in Base.metadata.tables.items():
            result = await session.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :tname;
                """),
                {"tname": table_name}
            )
            db_cols = {row[0] for row in result.fetchall()}
            if not db_cols:
                print(f"TABLE NOT FOUND IN DB: {table_name}")
                continue
            model_cols = {col.name for col in table.columns}
            missing_in_db = model_cols - db_cols
            extra_in_db = db_cols - model_cols
            if missing_in_db:
                print(f"[MISSING] TABLE '{table_name}' MISSING COLUMNS IN POSTGRESQL: {missing_in_db}")
            elif extra_in_db:
                print(f"[EXTRA] Table '{table_name}' has extra columns in DB: {extra_in_db}")
            else:
                print(f"[OK] Table '{table_name}' is 100% in sync with model ({len(model_cols)} columns).")

if __name__ == "__main__":
    asyncio.run(check_all_tables())
