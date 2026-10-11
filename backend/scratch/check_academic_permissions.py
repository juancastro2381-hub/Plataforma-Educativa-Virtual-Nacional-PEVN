import sys
sys.path.insert(0, ".")
import asyncio
from app.db.session import get_session_factory
from sqlalchemy import text

async def check():
    factory = get_session_factory()
    async with factory() as session:
        query = text("""
            SELECT r.name, p.resource, p.action 
            FROM role_permissions rp
            JOIN roles r ON r.id = rp.role_id
            JOIN permissions p ON p.id = rp.permission_id
            WHERE p.resource IN ('academic_periods', 'subjects')
            ORDER BY r.name, p.resource, p.action;
        """)
        res = await session.execute(query)
        rows = res.fetchall()
        for r in rows:
            print(f"Role: {r[0]:<20} Resource: {r[1]:<20} Action: {r[2]}")

if __name__ == "__main__":
    asyncio.run(check())
