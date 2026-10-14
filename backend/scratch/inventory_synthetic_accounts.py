import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DB_URL = get_safe_test_db_url()

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active,
                   ur.department_id, d.code as dept_code, d.name as dept_name, u.created_at,
                   (SELECT count(*) FROM audit_logs a WHERE a.actor_id = u.id) as actor_audits,
                   (SELECT count(*) FROM audit_logs a WHERE a.target_id = cast(u.id as varchar)) as target_audits,
                   (SELECT count(*) FROM refresh_tokens rt WHERE rt.user_id = u.id) as tokens
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN departments d ON ur.department_id = d.id
            WHERE r.name = 'department_admin'
              AND (
                  u.first_name IN ('AdminBogota', 'AdminAtlantico', 'AdminCundinamarca', 'Spoofed')
                  OR u.username LIKE 'admin.bogota.%'
                  OR u.username LIKE 'admin.atlantico.%'
                  OR u.username LIKE 'admin.cundinamarca.%'
                  OR u.username LIKE 'spoofed.%'
              )
            ORDER BY u.created_at ASC;
        """))
        rows = res.fetchall()
        print(f"=== SYNTHETIC LIFECYCLE TEST ACCOUNTS INVENTORY (Count: {len(rows)}) ===")
        for idx, r in enumerate(rows, 1):
            full_name = f"{r.first_name} {r.last_name}"
            print(f"{idx:02d} | ID: {r.id} | {r.username.ljust(26)} | {full_name.ljust(26)} | active={str(r.is_active).ljust(5)} | dept={str(r.dept_code).ljust(4)} ({str(r.dept_name).ljust(22)}) | audits(actor={r.actor_audits}, target={r.target_audits}, tokens={r.tokens}) | created={r.created_at}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
