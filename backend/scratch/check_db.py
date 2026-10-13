import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db")
    exists = await conn.fetchval("SELECT to_regclass('audit_logs') IS NOT NULL")
    print("audit_logs exists in PostgreSQL:", exists)
    if exists:
        count = await conn.fetchval("SELECT count(*) FROM audit_logs")
        print("audit_logs row count:", count)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
