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
        print("=== DATABASE TABLES ===")
        tables = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        for t in tables.fetchall():
            print(f"- {t[0]}")
            
        print("\n=== TARGET TEST ACCOUNT CHECK ===")
        user = await conn.execute(text("""
            SELECT u.id, u.username, u.email, u.document_type, u.document_number,
                   u.is_active, u.is_verified, u.must_change_password, u.hashed_password,
                   ur.role_id, r.name as role_name, ur.municipality_id, m.name as mun_name, m.code as mun_code
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            LEFT JOIN municipalities m ON ur.municipality_id = m.id
            WHERE u.username = 'Admin_municipio_Juan'
               OR u.email = 'juanprb@colegio.edu.co'
               OR u.document_number = '123456';
        """))
        rows = user.fetchall()
        print(f"Found {len(rows)} matching users:")
        for r in rows:
            print(dict(r._mapping))
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
