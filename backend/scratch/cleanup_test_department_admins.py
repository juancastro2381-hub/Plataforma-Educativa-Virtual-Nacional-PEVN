"""
PEVN — Synthetic Test Account Cleanup Script
AI Software Factory v1.2

Target: Safely remove ONLY the synthetic test accounts created exclusively by
`verify_department_admin_lifecycle.py` in the development/test environment.

Strictly Preserves:
- Legitimate administrators ('department_admin', 'Eduardo_Admin_Departamental', etc.)
- Legitimate departments and institutions
- System audit records (actor_id set to NULL per schema constraint or preserved)
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"

PRESERVED_USERNAMES = {"department_admin", "Eduardo_Admin_Departamental", "admin_nacional", "superadmin"}

async def cleanup(dry_run: bool = True):
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        # 1. Identify synthetic users matching the exact lifecycle test patterns
        res = await conn.execute(text("""
            SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.created_at
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
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
        targets = res.fetchall()

        print(f"=== SYNTHETIC ACCOUNT CLEANUP (DryRun={dry_run}) ===")
        print(f"Found {len(targets)} synthetic candidate accounts.")

        for t in targets:
            if t.username in PRESERVED_USERNAMES:
                raise RuntimeError(f"ABORT: Target matches preserved username: {t.username}")
            print(f"Candidate: {t.id} | {t.username} | {t.first_name} {t.last_name} | {t.email}")

        if not dry_run and targets:
            target_ids = [t.id for t in targets]
            
            # Step A: Delete refresh tokens for target users
            tok_del = await conn.execute(
                text("DELETE FROM refresh_tokens WHERE user_id = ANY(:uids)"),
                {"uids": target_ids}
            )
            print(f"Deleted refresh_tokens: {tok_del.rowcount}")

            # Step B: Delete user_roles for target users
            ur_del = await conn.execute(
                text("DELETE FROM user_roles WHERE user_id = ANY(:uids)"),
                {"uids": target_ids}
            )
            print(f"Deleted user_roles: {ur_del.rowcount}")

            # Step C: Nullify actor_id in audit_logs for target users to preserve audit logs integrity
            audit_null = await conn.execute(
                text("UPDATE audit_logs SET actor_id = NULL WHERE actor_id = ANY(:uids)"),
                {"uids": target_ids}
            )
            print(f"Nullified actor_id in audit_logs: {audit_null.rowcount}")

            # Step D: Delete users
            u_del = await conn.execute(
                text("DELETE FROM users WHERE id = ANY(:uids)"),
                {"uids": target_ids}
            )
            print(f"Deleted users: {u_del.rowcount}")

            await conn.commit()
            print("Successfully committed cleanup transaction.")

    await engine.dispose()

if __name__ == "__main__":
    import sys
    dry = "--execute" not in sys.argv
    asyncio.run(cleanup(dry_run=dry))
