import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from sqlalchemy import select, or_
from app.db.session import get_session_factory
from app.models.institution import Institution
from app.models.territory import Department, Municipality
from app.models.user import User
from app.models.role import UserRole
from app.services.user_service import UserService

async def main():
    async with get_session_factory()() as session:
        # Bogotá dept
        dept_bog = (await session.execute(select(Department).where(Department.code == "11"))).scalar_one()
        muni_bog = (await session.execute(select(Municipality).where(Municipality.code == "11001"))).scalar_one()

        service = UserService(session=session)
        users, total = await service.list_users(department_id=dept_bog.id)
        print(f"Current list_users for department Bogotá: total={total}")
        for u in users:
            print(" ", u.username, u.email, u.institution_id)

        # Now test with the proposed or_ condition
        inst_subq = select(Institution.id).join(Municipality, Institution.municipality_id == Municipality.id).where(Municipality.department_id == dept_bog.id)
        muni_subq = select(Municipality.id).where(Municipality.department_id == dept_bog.id)
        ur_subq = select(UserRole.user_id).where(
            or_(UserRole.department_id == dept_bog.id, UserRole.municipality_id.in_(muni_subq)),
            UserRole.is_active == True
        )
        new_stmt = select(User).where(or_(User.institution_id.in_(inst_subq), User.id.in_(ur_subq)))
        new_users = (await session.execute(new_stmt)).scalars().all()
        print(f"Proposed list_users for department Bogotá: total={len(new_users)}")
        for u in new_users:
            print(" ", u.username, u.email, u.institution_id)

if __name__ == "__main__":
    asyncio.run(main())
