import asyncio
import os
import sys
import traceback
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.group import Group
from app.models.academic_year import AcademicYear
from app.models.academic_assignment import AcademicAssignment
from app.services.academic_assignment_service import AcademicAssignmentService
from app.schemas.academic import AcademicAssignmentCreateRequest, AcademicAssignmentResponse
from app.core.exceptions import DuplicateActiveAssignmentError

async def main():
    print("=== TESTING ACADEMIC ASSIGNMENT CREATION ===")
    factory = get_session_factory()
    async with factory() as session:
        inst_id = uuid.UUID("f6efded7-e385-46e7-b224-a592ed942dbc") # COLEGIO AQUILEO PARRA
        ay_id = uuid.UUID("fa448bfe-bc9e-476d-b7ed-14b9332689ef") # Año Escolar 2026
        group_id = uuid.UUID("631402e2-bf02-4cec-9bfe-badace5a8f9b") # 11-B
        teacher_id = uuid.UUID("3044caf0-260d-4909-ac4c-02e6d8eb4e65") # Juan Carlos Castro

        # Find subject for Grade 11
        stmt_s = select(Subject).where(
            Subject.institution_id == inst_id,
            Subject.name.ilike("%Cálculo%") | Subject.name.ilike("%Matemáticas%")
        )
        subjects = (await session.execute(stmt_s)).scalars().all()
        if not subjects:
            print("No matching subjects found!")
            return
        subject = subjects[0]
        print(f"Target Subject: {subject.name} (ID: {subject.id})")

        # Find teacher and user
        teacher = (await session.execute(select(Teacher).where(Teacher.id == teacher_id))).scalar_one()
        user_actor_id = teacher.user_id

        service = AcademicAssignmentService(session=session)

        # 1. Create Assignment
        print("\n--- 1. Creating Academic Assignment ---")
        assignment = await service.create_assignment(
            institution_id=inst_id,
            teacher_id=teacher_id,
            subject_id=subject.id,
            group_id=group_id,
            academic_year_id=ay_id,
            weekly_hours=5,
            is_active=True,
            actor_id=user_actor_id,
            actor_ip="127.0.0.1",
            correlation_id="assignment-test-01",
        )
        await session.commit()
        await session.refresh(assignment)
        print(f"Assignment created successfully: ID={assignment.id}, Hours={assignment.weekly_hours}, Active={assignment.is_active}")

        # 2. Test Pydantic Response Serialization
        resp = AcademicAssignmentResponse.model_validate(assignment)
        print(f"Serialized AcademicAssignmentResponse:\n{resp.model_dump_json(indent=2)}")

        # 3. Test Duplicate Active Assignment Rejection
        print("\n--- 2. Testing Duplicate Assignment Rejection ---")
        try:
            await service.create_assignment(
                institution_id=inst_id,
                teacher_id=teacher_id,
                subject_id=subject.id,
                group_id=group_id,
                academic_year_id=ay_id,
                weekly_hours=5,
                is_active=True,
            )
            print("ERROR: Duplicate assignment was not rejected!")
        except DuplicateActiveAssignmentError:
            print("SUCCESS: DuplicateActiveAssignmentError correctly raised!")

if __name__ == "__main__":
    asyncio.run(main())
