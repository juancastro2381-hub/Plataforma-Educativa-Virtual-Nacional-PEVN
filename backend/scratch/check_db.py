import asyncio
from _safe_db import safe_asyncpg_connect

async def main():
    conn = await safe_asyncpg_connect(mode="test")
    exists = await conn.fetchval("SELECT to_regclass('audit_logs') IS NOT NULL")
    print("audit_logs exists in PostgreSQL:", exists)
    if exists:
        count = await conn.fetchval("SELECT count(*) FROM audit_logs")
        print("audit_logs row count:", count)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
