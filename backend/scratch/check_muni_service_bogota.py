import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from app.db.session import get_session_factory
from app.services.municipality_admin_service import MunicipalityAdminService
from app.models.territory import Department

async def main():
    async with get_session_factory()() as session:
        service = MunicipalityAdminService(session=session)
        # Find Bogotá department
        dept = (await session.execute(Department.__table__.select().where(Department.code == "11"))).first()
        print("Bogota Department in DB:", dept)
        if dept:
            munis = await service.list_municipalities(department_id=dept.id)
            print(f"Municipalities in department 11: {len(munis)}")
            for m in munis:
                print(f"  Muni: id={m.id} (type={type(m.id)}), code={m.code}, name={m.name}, dept_id={m.department_id}")

if __name__ == "__main__":
    asyncio.run(main())
