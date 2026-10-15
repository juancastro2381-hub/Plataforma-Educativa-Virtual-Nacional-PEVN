import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.db.session import get_session_factory
from app.models.user import User
from app.models.student import Student
from app.services.student_portal_service import StudentPortalService
from app.services.communication_service import CommunicationService
from app.services.news_service import NewsService
from sqlalchemy import select

async def main():
    factory = get_session_factory()
    async with factory() as session:
        # Find Ramiro Rey
        stmt = select(User).where(User.first_name.ilike('%Ramiro%'))
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            print("User Ramiro not found by first_name. Searching all students...")
            stmt2 = select(User).join(Student, Student.user_id == User.id)
            users = (await session.execute(stmt2)).scalars().all()
            for u in users:
                print(f"Student user: {u.id} | {u.email} | {u.first_name} {u.last_name}")
            return

        print(f"Found Ramiro user: {user.id} | {user.email} | {user.first_name} {user.last_name}")
        portal_service = StudentPortalService(session=session)
        student = await portal_service.get_student_by_user_id(user.id, user.institution_id)
        print(f"Found student entity: {student.id} | SIMAT: {student.code_simat} | inst: {student.institution_id}")

        # Test comms
        comm_service = CommunicationService(session=session)
        try:
            comms = await comm_service.list_student_communications(student=student, user=user)
            print(f"Comms retrieved: {len(comms)}")
        except Exception as e:
            print(f"Comms error: {type(e).__name__}: {e}")

        # Test news
        news_service = NewsService(session=session)
        try:
            news = await news_service.list_news(institution_id=student.institution_id)
            print(f"News retrieved: {len(news)}")
        except Exception as e:
            print(f"News error: {type(e).__name__}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
