"""
Forensic diagnostic script to inspect:
1. Migration status in PostgreSQL database
2. Users, roles, and teachers in the database
3. Trace /api/v1/teacher/dashboard and /api/v1/teacher/activities execution
4. Trace /api/v1/auth/refresh execution
"""
import asyncio
import uuid
from sqlalchemy import select, text
from app.db.session import get_session_factory, get_engine
from app.models.user import User
from app.models.role import UserRole, Role
from app.models.teacher import Teacher
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_activity import AcademicActivity, ActivityGrade, DailyAttendance, AcademicPlan
from app.services.teacher_portal_service import TeacherPortalService
from app.schemas.teacher_portal import TeacherDashboardSummaryResponse

async def main():
    factory = get_session_factory()
    async with factory() as session:
        print("=== 1. CHECK MIGRATIONS & TABLES IN POSTGRES ===")
        res = await session.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        tables = [r[0] for r in res.fetchall()]
        print("Tables in DB:", tables)
        for t in ["academic_activities", "activity_grades", "daily_attendances", "academic_plans"]:
            print(f"Table '{t}' exists: {t in tables}")

        res_alembic = await session.execute(text("SELECT version_num FROM alembic_version;"))
        print("Alembic version in DB:", [r[0] for r in res_alembic.fetchall()])

        print("\n=== 2. CHECK USERS & ROLES ===")
        res_users = await session.execute(
            select(User)
        )
        users = res_users.scalars().all()
        for u in users:
            roles_res = await session.execute(
                select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == u.id)
            )
            roles = [r[0] for r in roles_res.fetchall()]
            teacher_res = await session.execute(
                select(Teacher).where(Teacher.user_id == u.id)
            )
            t_rec = teacher_res.scalar_one_or_none()
            print(f"User: {u.email} (ID: {u.id}) | Inst: {u.institution_id} | Roles: {roles} | Teacher Rec: {t_rec.id if t_rec else None}")

        print("\n=== 3. TRACE TEACHER DASHBOARD FOR EACH USER ===")
        service = TeacherPortalService(session=session)
        for u in users:
            print(f"\nTesting for user: {u.email}")
            try:
                teacher = await service.get_teacher_profile(u.id, u.institution_id)
                print(f"  Teacher profile found: {teacher.id}")
                summary = await service.get_dashboard_summary(teacher)
                print(f"  Dashboard summary SUCCESS: {summary}")
                activities = await service.list_activities(teacher)
                print(f"  Activities list SUCCESS: count = {len(activities)}")
            except Exception as e:
                import traceback
                print(f"  FAILURE for {u.email}: {type(e).__name__}: {e}")
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
