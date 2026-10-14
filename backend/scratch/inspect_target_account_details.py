import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT u.id, u.username, u.email, u.document_type, u.document_number,
                   u.is_active, u.is_verified, u.must_change_password,
                   (SELECT count(*) FROM refresh_tokens rt WHERE rt.user_id = u.id AND rt.is_revoked = false) as active_refresh_tokens,
                   (SELECT count(*) FROM audit_logs a WHERE a.target_id = cast(u.id as varchar) OR a.actor_id = u.id) as audit_logs_count
            FROM users u
            WHERE u.id = '1727a8ca-f73d-4091-b829-8791e6f72749';
        """))
        row = res.fetchone()
        print("Target Account Status:", dict(row._mapping))
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
