import asyncio
import os
import sys
import traceback
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.student import Student
from app.models.user import User, DocumentType
from app.models.academic_year import AcademicYear
from app.models.group import Group
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.services.student_service import StudentService
from app.services.enrollment_service import EnrollmentService
from app.schemas.academic import StudentNewUserPayload, EnrollmentResponse

async def main():
    print("=== TESTING COMPLETE STUDENT CREATION -> ENROLLMENT FLOW ===")
    factory = get_session_factory()
    async with factory() as session:
        inst_id = uuid.UUID("f6efded7-e385-46e7-b224-a592ed942dbc") # COLEGIO AQUILEO PARRA
        ay_id = uuid.UUID("fa448bfe-bc9e-476d-b7ed-14b9332689ef") # Año Escolar 2026
        group_id = uuid.UUID("631402e2-bf02-4cec-9bfe-badace5a8f9b") # 11-B

        # 1. Provision new student
        stu_service = StudentService(session=session)
        new_doc = f"99{uuid.uuid4().hex[:6]}"
        new_simat = f"SIMAT-{uuid.uuid4().hex[:6]}"
        new_user_payload = StudentNewUserPayload(
            first_name="Camila",
            last_name="Torres",
            document_type=DocumentType.TI,
            document_number=new_doc,
            email=f"camila.{new_doc}@colegio.edu.co",
        )
        print(f"Provisioning student Camila Torres (Doc: {new_doc}, SIMAT: {new_simat})...")
        from datetime import date
        student = await stu_service.create_student(
            institution_id=inst_id,
            new_user=new_user_payload,
            code_simat=new_simat,
            birth_date=date(2010, 6, 15),
            stratum=2,
            eps_health_provider="Compensar EPS",
        )
        await session.commit()
        await session.refresh(student)
        print(f"Student provisioned successfully: ID={student.id}, User_ID={student.user_id}")

        # 2. Formalize enrollment for this new student in 11-B
        enr_service = EnrollmentService(session=session)
        print(f"Formalizing enrollment in group 11-B for year 2026...")
        enrollment = await enr_service.create_enrollment(
            institution_id=inst_id,
            student_id=student.id,
            group_id=group_id,
            academic_year_id=ay_id,
            status=EnrollmentStatus.ACTIVE,
            actor_id=student.user_id,
            actor_ip="127.0.0.1",
            correlation_id="camila-enrollment-test",
        )
        await session.commit()
        await session.refresh(enrollment)
        print(f"Enrollment committed and refreshed: ID={enrollment.id}, Status={enrollment.status}")

        # 3. Test Pydantic Response Serialization
        response = EnrollmentResponse.model_validate(enrollment)
        print(f"EnrollmentResponse serialized successfully: {response.model_dump_json(indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
