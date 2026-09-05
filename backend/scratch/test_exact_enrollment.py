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
    print("=== TESTING EXACT ENROLLMENT CREATION FOR COLEGIO AQUILEO PARRA ===")
    factory = get_session_factory()
    async with factory() as session:
        inst_id = uuid.UUID("f6efded7-e385-46e7-b224-a592ed942dbc")
        student_id = uuid.UUID("ff2bbca2-2e44-4db4-850d-bba634518173") # Ana Maria
        ay_id = uuid.UUID("fa448bfe-bc9e-476d-b7ed-14b9332689ef") # Año Escolar 2026
        group_id = uuid.UUID("631402e2-bf02-4cec-9bfe-badace5a8f9b") # 11-B

        # Search the user for this institution
        stmt_user = select(User).where(User.institution_id == inst_id)
        users = (await session.execute(stmt_user)).scalars().all()
        actor = users[0] if users else None
        print(f"Actor: {actor.email if actor else 'None'} ({actor.id if actor else 'None'})")

        service = EnrollmentService(session=session)
        try:
            enrollment = await service.create_enrollment(
                institution_id=inst_id,
                student_id=student_id,
                group_id=group_id,
                academic_year_id=ay_id,
                status=EnrollmentStatus.ACTIVE,
                actor_id=actor.id if actor else None,
                actor_ip="127.0.0.1",
                correlation_id="exact-test-456",
            )
            print(f"Service returned enrollment: {enrollment}")
            print(f"Enrollment ID: {enrollment.id}")
            print(f"Enrollment status: {enrollment.status}")

            await session.commit()
            print("Session commit SUCCESSFUL!")
            await session.refresh(enrollment)
            print(f"Enrollment refreshed: {enrollment.id}")

            # Now test response serialization with Pydantic
            from app.schemas.academic import EnrollmentResponse
            print("\n--- Testing Pydantic serialization ---")
            resp = EnrollmentResponse.model_validate(enrollment)
            print(f"Pydantic validation SUCCESS: {resp.model_dump_json()}")

        except Exception as e:
            print("\n!!! EXCEPTION CAUGHT !!!")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
