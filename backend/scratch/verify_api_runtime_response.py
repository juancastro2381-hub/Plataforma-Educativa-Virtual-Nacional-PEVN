import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import get_session_factory
from sqlalchemy import select
from app.models.user import User
from app.core.security.tokens import token_service
from app.services.auth_service import AuthService

async def test_api_for_users():
    factory = get_session_factory()
    async with factory() as session:
        for uname in ["Admin_Municip_ValParaiso", "Admin_Municip_BAQ", "Admin_Caquetá_Ana"]:
            u = (await session.execute(select(User).where(User.username == uname))).scalar_one_or_none()
            if not u:
                print(f"User {uname} not found!")
                continue
            
            auth_context = AuthService.build_auth_context(u)
            token = await token_service.create_access_token(
                subject=str(u.id),
                additional_claims={
                    "roles": [r.value for r in auth_context.roles],
                    "permissions": [str(p) for p in auth_context.permissions],
                }
            )
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
                res = await client.get("/api/v1/institutions", headers={"Authorization": f"Bearer {token}"})
                print(f"\n=======================================================")
                print(f"User: {uname} (status {res.status_code}): {res.text}")
                if res.status_code != 200:
                    continue
                data = res.json()
                print(f"Total institutions accessible: {data.get('total')}")
                for inst in data.get("items", []):
                    print(f"  - [{inst['dane_code']}] {inst['name']}")
                    print(f"    has_active_rector: {inst.get('has_active_rector')}")
                    print(f"    active_rector: {inst.get('active_rector_name')} ({inst.get('active_rector_email')})")
                    print(f"    has_pending_invitation: {inst.get('has_pending_invitation')}")

if __name__ == "__main__":
    asyncio.run(test_api_for_users())
