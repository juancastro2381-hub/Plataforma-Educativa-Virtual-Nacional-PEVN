import asyncio
from app.db.session import get_session_factory
from app.models.user import User
from app.models.student import Student
from app.services.student_portal_service import StudentPortalService
from sqlalchemy import select

async def main():
    factory = get_session_factory()
    async with factory() as session:
        # Find Samuel Rua
        stmt = select(User).where(User.email == 'samuel.rua@colegio.edu.co')
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            print("Samuel not found")
            return
        print(f"Found Samuel user: {user.id} | {user.email}")
        portal_service = StudentPortalService(session=session)
        student = await portal_service.get_student_by_user_id(user.id, user.institution_id)
        print(f"Student entity: {student.id} | inst: {student.institution_id}")

        # List activities
        activities_resp = await portal_service.list_activities(student)
        print(f"Activities count: {activities_resp.total}")
        for act in activities_resp.items:
            print(f"  Activity: {act.id} | title: {act.title} | submission_status: {act.submission_status}")
            detail = await portal_service.get_submission_detail(student, act.id)
            print(f"    Submission detail retrieved: {detail.id} | status: {detail.status}")

if __name__ == '__main__':
    asyncio.run(main())
