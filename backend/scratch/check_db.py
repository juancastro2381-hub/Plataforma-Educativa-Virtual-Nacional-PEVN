import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def main():
    raw_url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("Neither TEST_DATABASE_URL nor DATABASE_URL environment variable is set.")
    url = raw_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    exists = await conn.fetchval("SELECT to_regclass('audit_logs') IS NOT NULL")
    print("audit_logs exists in PostgreSQL:", exists)
    if exists:
        count = await conn.fetchval("SELECT count(*) FROM audit_logs")
        print("audit_logs row count:", count)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
