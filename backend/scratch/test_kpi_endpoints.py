import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.main import app
from app.core.security.tokens import token_service
from app.core.security.interfaces import SystemRole

from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DB_URL = get_safe_test_db_url()

async def main():
    engine = create_async_engine(DB_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        user = (await session.execute(select(User).where(User.username == "admin_nacional"))).scalar_one()
        user_id = user.id

    token = await token_service.create_access_token(
        subject=str(user_id),
        additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
    )
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        # Test 1: GET /api/v1/department-admins/kpis
        res_kpis = await client.get("/api/v1/department-admins/kpis", headers=headers)
        print("KPIs endpoint status:", res_kpis.status_code)
        kpis_data = res_kpis.json()
        print("KPIs data:", kpis_data)
        assert res_kpis.status_code == 200
        assert kpis_data["total"] == kpis_data["active"] + kpis_data["inactive"], "Invariant violated!"
        print("[OK] KPI Invariant verified: total = active + inactive")

        # Test 2: GET /api/v1/department-admins
        res_list = await client.get("/api/v1/department-admins", headers=headers)
        print("\nList endpoint status:", res_list.status_code)
        list_data = res_list.json()
        print("List total:", list_data["total"])
        print("List items count:", len(list_data["items"]))
        print("List embedded kpis:", list_data["kpis"])
        for it in list_data["items"]:
            print(f"  - {it['username']} | {it['full_name']} | dept={it['department_code']} ({it['department_name']}) | active={it['is_active']}")

if __name__ == "__main__":
    asyncio.run(main())
