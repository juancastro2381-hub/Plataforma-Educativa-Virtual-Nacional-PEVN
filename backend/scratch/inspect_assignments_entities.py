import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.models.teacher import Teacher
from app.models.user import User
from app.models.subject import Subject, KnowledgeArea
from app.models.group import Group
from app.models.academic_year import AcademicYear
from app.models.grade import Grade
from app.models.institution import Institution, Campus

async def main():
    print("=== INSPECTING ASSIGNMENT ENTITIES IN DATABASE ===")
    factory = get_session_factory()
    async with factory() as session:
        # 1. Inspect Teachers
        print("\n--- 1. Teachers ---")
        stmt_t = select(Teacher).options(selectinload(Teacher.user), selectinload(Teacher.institution))
        teachers = (await session.execute(stmt_t)).scalars().all()
        for t in teachers:
            user_name = f"{t.user.first_name} {t.user.last_name}" if t.user else "No User"
            inst_name = t.institution.name if t.institution else "No Inst"
            print(f"Teacher ID: {t.id} | User: {user_name} | Inst: {t.institution_id} ({inst_name}) | Specialty: {t.specialty_area}")

        # 2. Inspect Knowledge Areas & Subjects
        print("\n--- 2. Knowledge Areas ---")
        kas = (await session.execute(select(KnowledgeArea))).scalars().all()
        for ka in kas:
            print(f"KA ID: {ka.id} | Name: {ka.name} | Inst: {ka.institution_id} | Mandatory: {ka.is_mandatory}")

        print("\n--- 3. Subjects ---")
        stmt_s = select(Subject).options(selectinload(Subject.knowledge_area), selectinload(Subject.grade))
        subjects = (await session.execute(stmt_s)).scalars().all()
        print(f"Total Subjects: {len(subjects)}")
        for s in subjects:
            ka_name = s.knowledge_area.name if s.knowledge_area else "No KA"
            grade_name = s.grade.name if s.grade else "No Grade"
            print(f"Subject ID: {s.id} | Name: {s.name} | Inst: {s.institution_id} | Area: {ka_name} | Grade: {grade_name} | Hours: {s.weekly_hours}")

        # 4. Inspect Groups
        print("\n--- 4. Groups ---")
        stmt_g = select(Group).options(selectinload(Group.campus), selectinload(Group.grade), selectinload(Group.academic_year))
        groups = (await session.execute(stmt_g)).scalars().all()
        for g in groups:
            campus_name = g.campus.name if g.campus else "No Campus"
            grade_name = g.grade.name if g.grade else "No Grade"
            ay_name = g.academic_year.name if g.academic_year else "No AY"
            print(f"Group ID: {g.id} | Name: {g.name} | Shift: {g.shift} | Campus: {campus_name} (Inst: {g.campus.institution_id if g.campus else 'N/A'}) | Grade: {grade_name} | AY: {ay_name} ({g.academic_year_id})")

        # 5. Inspect Academic Years
        print("\n--- 5. Academic Years ---")
        ays = (await session.execute(select(AcademicYear))).scalars().all()
        for ay in ays:
            print(f"AY ID: {ay.id} | Year: {ay.year} | Name: {ay.name} | Status: {ay.status} | Inst: {ay.institution_id}")

if __name__ == "__main__":
    asyncio.run(main())
