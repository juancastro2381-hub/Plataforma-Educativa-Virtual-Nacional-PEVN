"""
Diagnostic script to check schema differences between SQLAlchemy models and the live DB.
Read-only.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from app.core.config import get_settings
from app.db.base import Base

async def check_diff():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.connect() as conn:
        def sync_check(connection):
            mc = MigrationContext.configure(connection)
            diffs = compare_metadata(mc, Base.metadata)
            return diffs
            
        diffs = await conn.run_sync(sync_check)
        print("Alembic schema diffs:")
        for d in diffs:
            print(" -", d)

if __name__ == "__main__":
    asyncio.run(check_diff())
