import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
import asyncio
from app.db.session import get_session_factory
from sqlalchemy import text

async def check():
    session_factory = get_session_factory()
    async with session_factory() as session:
        users = (await session.execute(text("""
            SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active, r.name as role_name
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.id AND ur.is_active = true
            JOIN roles r ON r.id = ur.role_id
            WHERE r.name IN ('national_admin', 'department_admin', 'municipality_admin', 'rector', 'coordinator', 'academic_coordinator', 'guardian')
            ORDER BY r.name, u.username
        """))).mappings().all()
        for u in users:
            role = u['role_name']
            uname = u['username'] or ''
            email = u['email'] or ''
            fname = f"{u['first_name']} {u['last_name']}"
            act = u['is_active']
            print(f"{role:22} | {uname:18} | {email:32} | {fname:25} | active={act}")

asyncio.run(check())
