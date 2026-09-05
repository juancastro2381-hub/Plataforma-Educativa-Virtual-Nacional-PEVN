import asyncio
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import get_session_factory

async def check_alembic_version():
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(text("SELECT version_num FROM alembic_version;"))
        version = res.scalar()
        print(f"Current Alembic revision in PostgreSQL: {version}")

if __name__ == "__main__":
    asyncio.run(check_alembic_version())
