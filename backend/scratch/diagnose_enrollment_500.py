import asyncio
import os
import sys
import traceback
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.models.student import Student
from app.models.user import User
from app.models.academic_year import AcademicYear
from app.models.group import Group
from app.models.institution import Campus, Institution
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.services.enrollment_service import EnrollmentService
from app.schemas.academic import EnrollmentCreateRequest

async def main():
    print("=== FORENSIC DIAGNOSIS: ENROLLMENT FORMALIZATION ===")
    factory = get_session_factory()
    async with factory() as session:
        # 1. Search Student Ana Maria / TI: 2121212121 / SIMAT: 22233
        print("\n--- 1. Searching Student Ana Maria ---")
        stmt_student = (
            select(Student)
            .options(selectinload(Student.user), selectinload(Student.institution))
        )
        students = (await session.execute(stmt_student)).scalars().all()
        print(f"Total students found in DB: {len(students)}")
        target_student = None
        for s in students:
            user_info = f"{s.user.first_name} {s.user.last_name} ({s.user.document_type}: {s.user.document_number})" if s.user else "No User"
            print(f"  Student ID: {s.id}, SIMAT: {s.code_simat}, Institution: {s.institution_id}, User: {user_info}")
            if s.code_simat == "22233" or (s.user and s.user.document_number == "2121212121"):
                target_student = s
                print(f"  --> MATCHED TARGET STUDENT: {s.id}")

        # 2. Search Academic Years
        print("\n--- 2. Searching Academic Years ---")
        stmt_ay = select(AcademicYear)
        ays = (await session.execute(stmt_ay)).scalars().all()
        print(f"Total Academic Years found in DB: {len(ays)}")
        target_ay = None
        for ay in ays:
            print(f"  AY ID: {ay.id}, Year: {ay.year}, Name: {ay.name}, Status: {ay.status}, Inst: {ay.institution_id}")
            if ay.year == 2026 or "2026" in ay.name:
                target_ay = ay
                print(f"  --> MATCHED TARGET AY: {ay.id}")

        # 3. Search Groups
        print("\n--- 3. Searching Groups ---")
        stmt_grp = select(Group).options(selectinload(Group.campus))
        groups = (await session.execute(stmt_grp)).scalars().all()
        print(f"Total Groups found in DB: {len(groups)}")
        target_grp = None
        for g in groups:
            campus_inst = g.campus.institution_id if g.campus else "No Campus"
            print(f"  Group ID: {g.id}, Name: {g.name}, Shift: {g.shift}, AY_id: {g.academic_year_id}, Campus: {g.campus_id}, Inst: {campus_inst}, Cap: {g.capacity_limit}")
            if "11-B" in g.name or "11" in g.name:
                target_grp = g
                print(f"  --> MATCHED TARGET GROUP: {g.id}")

        # 4. Search Users (Rector/Admin) to determine caller context
        print("\n--- 4. Searching Institutional Users ---")
        stmt_users = select(User).where(User.institution_id.isnot(None))
        users = (await session.execute(stmt_users)).scalars().all()
        for u in users:
            print(f"  User ID: {u.id}, Email: {u.email}, Name: {u.first_name} {u.last_name}, Inst: {u.institution_id}")

        # 5. Attempt EnrollmentService.create_enrollment
        if target_student and target_ay and target_grp:
            print("\n--- 5. Simulating EnrollmentService.create_enrollment ---")
            inst_id = target_student.institution_id
            print(f"Using Institution ID: {inst_id}")
            service = EnrollmentService(session=session)
            try:
                enrollment = await service.create_enrollment(
                    institution_id=inst_id,
                    student_id=target_student.id,
                    group_id=target_grp.id,
                    academic_year_id=target_ay.id,
                    status=EnrollmentStatus.ACTIVE,
                    actor_id=users[0].id if users else None,
                    actor_ip="127.0.0.1",
                    correlation_id="forensic-test-123",
                )
                print(f"Enrollment created successfully: {enrollment.id}")
                await session.flush()
                print("Session flush succeeded.")
                # We do not commit to avoid dirtying DB unless desired
                await session.rollback()
                print("Rolled back simulation.")
            except Exception as e:
                print("\n!!! EXCEPTION CAPTURED DURING SIMULATION !!!")
                print(f"Exception Type: {type(e).__name__}")
                print(f"Exception Message: {e}")
                traceback.print_exc()
        else:
            print("\nCould not run simulation: Missing target_student, target_ay, or target_grp.")

if __name__ == "__main__":
    asyncio.run(main())
