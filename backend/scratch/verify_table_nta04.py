import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("Checking institution_onboarding_requests table:")
        columns = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'institution_onboarding_requests'
            ORDER BY ordinal_position;
        """))
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]}, default={col[3]})")
            
        print("\nChecking indexes:")
        indexes = await conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'institution_onboarding_requests';
        """))
        for idx in indexes:
            print(f"  {idx[0]}: {idx[1]}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
