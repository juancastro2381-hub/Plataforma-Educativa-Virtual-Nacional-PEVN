import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from app.db.session import get_session_factory
from app.services.territorial_analytics_service import TerritorialAnalyticsService

async def main():
    async with get_session_factory()() as session:
        service = TerritorialAnalyticsService(session=session)
        # Department 11 is Bogotá
        detail = await service.get_control_center_department_detail("11")
        print("Department:", detail.department_code, detail.department_name, detail.department_id)
        print("Municipalities count:", len(detail.municipalities))
        for m in detail.municipalities[:5]:
            print("  Muni:", type(m.municipality_id), m.municipality_id, "Code:", m.municipality_code, "Name:", m.municipality_name)

if __name__ == "__main__":
    asyncio.run(main())
