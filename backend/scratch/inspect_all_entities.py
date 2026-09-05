import asyncio
import os
import sys
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

async def inspect_db():
    factory = get_session_factory()
    async with factory() as session:
        print("\n--- INSTITUTIONS ---")
        institutions = (await session.execute(select(Institution))).scalars().all()
        for inst in institutions:
            print(f"Inst ID: {inst.id}, Name: {inst.name}, DANE: {inst.dane_code}")

        print("\n--- CAMPUSES ---")
        campuses = (await session.execute(select(Campus))).scalars().all()
        for c in campuses:
            print(f"Campus ID: {c.id}, Name: {c.name}, DANE: {c.dane_sede_code}, Inst ID: {c.institution_id}")

        print("\n--- STUDENTS ---")
        students = (await session.execute(select(Student).options(selectinload(Student.user)))).scalars().all()
        for s in students:
            user_str = f"{s.user.first_name} {s.user.last_name} ({s.user.document_type}:{s.user.document_number})" if s.user else "NO USER"
            print(f"Student ID: {s.id}, SIMAT: {s.code_simat}, Inst ID: {s.institution_id}, User: {user_str}")

        print("\n--- ACADEMIC YEARS ---")
        years = (await session.execute(select(AcademicYear))).scalars().all()
        for y in years:
            print(f"Year ID: {y.id}, Year: {y.year}, Name: {y.name}, Status: {y.status}, Inst ID: {y.institution_id}")

        print("\n--- GROUPS ---")
        groups = (await session.execute(select(Group).options(selectinload(Group.campus)))).scalars().all()
        for g in groups:
            campus_inst = g.campus.institution_id if g.campus else "NO CAMPUS"
            print(f"Group ID: {g.id}, Name: {g.name}, Shift: {g.shift}, AY_ID: {g.academic_year_id}, Campus: {g.campus_id} (Campus Inst: {campus_inst})")

        print("\n--- USERS (Sample) ---")
        users = (await session.execute(select(User).limit(10))).scalars().all()
        for u in users:
            print(f"User ID: {u.id}, Email: {u.email}, Name: {u.first_name} {u.last_name}, Inst: {u.institution_id}")

if __name__ == "__main__":
    asyncio.run(inspect_db())
