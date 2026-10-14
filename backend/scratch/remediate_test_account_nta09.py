import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.base_class import Base
from app.models.user import DocumentType
from app.services.municipality_admin_service import MunicipalityAdminService

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DB_URL = get_safe_test_db_url()

async def main():
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        service = MunicipalityAdminService(session=session)
        print("Starting targeted remediation of manual acceptance test account...")
        user = await service.remediate_test_account(
            username="Admin_municipio_Juan",
            email="juanprb@colegio.edu.co",
            document_type=DocumentType.CC,
            document_number="123456",
            actor_id=None,
            actor_ip="127.0.0.1",
            correlation_id="NTA-09-R2-REMEDIATION-MANUAL-ACCEPTANCE",
        )
        await session.commit()
        print(f"SUCCESS: Remediated user {user.username} (ID: {user.id})")
        print(f" - is_active: {user.is_active}")
        print(f" - is_verified: {user.is_verified}")
        print(f" - must_change_password: {user.must_change_password}")
        print(" - active sessions revoked, unguessable password hash set, audit event recorded.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
