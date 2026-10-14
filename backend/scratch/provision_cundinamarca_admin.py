import os
from dotenv import load_dotenv
load_dotenv()

"""
Provision dedicated legitimate manual-test administrator for Cundinamarca (DANE 25).
"""
import asyncio
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.services.department_admin_service import DepartmentAdminService
from app.schemas.department_admin import DepartmentAdminCreateRequest

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DB_URL = get_safe_test_db_url()

async def main():
    engine = create_async_engine(DB_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        service = DepartmentAdminService(session=session)
        payload = DepartmentAdminCreateRequest(
            first_name="Administrador",
            last_name="Cundinamarca",
            email="admin.cundinamarca@pevn.edu.co",
            username="admin_cundinamarca",
            password="CundinamarcaAdmin2026*!",
            department_id=uuid.UUID("9aea113f-54e2-4345-8cc6-46970a91c7c6"),
            is_active=True,
        )
        res = await service.create_department_admin(
            payload,
            actor_ip="127.0.0.1",
            correlation_id="manual_test_cundinamarca_provisioning",
        )
        await session.commit()
        print(f"Created Cundinamarca Administrator: {res.username} ({res.id}) for department {res.department_name} (code {res.department_code})")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
