import asyncio
from sqlalchemy import select
from app.db.session import get_session_factory
from app.models.user import User
from app.models.teacher import Teacher
from app.services.teacher_portal_service import TeacherPortalService

async def main():
    factory = get_session_factory()
    async with factory() as session:
        user_stmt = select(User).where(User.email == "juan@example.com")
        u = (await session.execute(user_stmt)).scalar_one_or_none()
        print(f"User: {u.email} (id: {u.id}, inst: {u.institution_id})")

        service = TeacherPortalService(session=session)
        teacher = await service.get_teacher_profile(u.id, u.institution_id)
        print(f"Teacher profile: {teacher.id}, name: {teacher.user.first_name if teacher.user else None}")
        
        summary = await service.get_dashboard_summary(teacher)
        print("Dashboard summary:", summary)

        activities = await service.list_activities(teacher)
        print("Activities:", len(activities))

if __name__ == "__main__":
    asyncio.run(main())
