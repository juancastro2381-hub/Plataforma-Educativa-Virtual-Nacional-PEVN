import asyncio
import os
import sys

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from sqlalchemy import select
from app.db.session import get_session_factory
from app.models.territory import Department, Municipality
from app.models.user import User
from app.models.role import Role, UserRole

async def main():
    async with get_session_factory()() as session:
        # 1. Check departments
        depts = (await session.execute(select(Department).where(Department.code == "11"))).scalars().all()
        print(f"Departments with code 11: {len(depts)}")
        for d in depts:
            print(f"  Dept: id={d.id}, code={d.code}, name={d.name}")

        # 2. Check municipality 11001
        munis = (await session.execute(select(Municipality).where(Municipality.code == "11001"))).scalars().all()
        print(f"Municipalities with code 11001: {len(munis)}")
        for m in munis:
            print(f"  Muni: id={m.id}, code={m.code}, name={m.name}, dept_id={m.department_id}")

        # 3. Check recent users with MUNICIPALITY_ADMIN
        admin_role = (await session.execute(select(Role).where(Role.name == "municipality_admin"))).scalar_one_or_none()
        print(f"Role municipality_admin: {admin_role.id if admin_role else None}")

        users = (await session.execute(select(User).order_by(User.created_at.desc()).limit(10))).scalars().all()
        print(f"Recent 10 users in DB:")
        for u in users:
            print(f"  User: id={u.id}, email={u.email}, username={u.username}, doc={u.document_type} {u.document_number}, active={u.is_active}, created_at={u.created_at}")
            # check roles
            urs = (await session.execute(select(UserRole).where(UserRole.user_id == u.id))).scalars().all()
            for ur in urs:
                print(f"    UserRole: role_id={ur.role_id}, dept_id={ur.department_id}, muni_id={ur.municipality_id}, is_active={ur.is_active}")

if __name__ == "__main__":
    asyncio.run(main())
