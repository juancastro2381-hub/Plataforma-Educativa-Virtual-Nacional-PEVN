import asyncio
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import get_session_factory

async def check_columns():
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'group_transfer_history'
                ORDER BY ordinal_position;
            """)
        )
        cols = result.fetchall()
        print("Columns in PostgreSQL table 'group_transfer_history':")
        for col in cols:
            print(f" - {col[0]} ({col[1]})")

if __name__ == "__main__":
    asyncio.run(check_columns())
