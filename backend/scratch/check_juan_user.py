import asyncio
from sqlalchemy import select
from app.db.session import get_session_factory
from app.models.user import User
from app.models.role import UserRole, Role
from app.models.teacher import Teacher

async def main():
    factory = get_session_factory()
    async with factory() as session:
        for email in ["juan@example.com", "juancarlos@example.com", "rectorg@colegio.edu.co"]:
            user_stmt = select(User).where(User.email == email)
            u = (await session.execute(user_stmt)).scalar_one_or_none()
            if u:
                roles_res = await session.execute(
                    select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == u.id)
                )
                roles = [r[0] for r in roles_res.fetchall()]
                teacher_res = await session.execute(
                    select(Teacher).where(Teacher.user_id == u.id)
                )
                t_rec = teacher_res.scalar_one_or_none()
                print(f"User: {u.email} | ID: {u.id} | Inst: {u.institution_id} | Roles: {roles} | Teacher: {t_rec.id if t_rec else 'NONE'}")
            else:
                print(f"User {email} NOT FOUND in DB")

if __name__ == "__main__":
    asyncio.run(main())
