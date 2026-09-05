import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_session_factory
from app.models.teacher import Teacher
from app.models.user import User
from app.models.role import UserRole, Role

async def main():
    factory = get_session_factory()
    async with factory() as session:
        stmt = (
            select(Teacher)
            .options(
                selectinload(Teacher.user).selectinload(User.user_roles).selectinload(UserRole.role),
                selectinload(Teacher.institution)
            )
        )
        teachers = (await session.execute(stmt)).scalars().all()
        print(f"Total Teachers in DB: {len(teachers)}")
        for t in teachers:
            u = t.user
            if u:
                roles = [ur.role.name for ur in u.user_roles if ur.role and ur.is_active]
                print(f"Teacher ID: {t.id} | Name: {u.first_name} {u.last_name} | Email: {u.email} | Doc: {u.document_type} {u.document_number} | Active: {u.is_active} | MustChangePwd: {u.must_change_password} | Roles: {roles} | Inst: {t.institution_id}")
            else:
                print(f"Teacher ID: {t.id} | User ID: {t.user_id} (User NOT LOADED)")

if __name__ == "__main__":
    asyncio.run(main())
