import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import get_session_factory
from sqlalchemy import select
from app.models.grade import Grade

async def check_grades():
    factory = get_session_factory()
    async with factory() as session:
        grades = (await session.execute(select(Grade).order_by(Grade.ordinal_order))).scalars().all()
        print(f"Total grades in DB: {len(grades)}")
        for g in grades:
            print(f"Grade ID: {g.id} | Code: {g.code} | Name: {g.name} | Level: {g.level} | Order: {g.ordinal_order}")

if __name__ == "__main__":
    asyncio.run(check_grades())
