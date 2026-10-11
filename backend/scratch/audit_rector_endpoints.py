import asyncio
import sys
import uuid
sys.path.insert(0, '.')
import httpx
from sqlalchemy import select
from app.db.session import get_session_factory
from app.models.user import User
from app.models.role import Role, UserRole
from app.core.security.tokens import token_service

async def audit():
    factory = get_session_factory()
    async with factory() as session:
        # 1. Fetch miguel.villa
        user = (await session.execute(select(User).where(User.email == "miguel.villa@colegio.edu.co"))).scalar_one()
        ur_stmt = select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id, UserRole.is_active == True)
        roles = list((await session.execute(ur_stmt)).scalars().all())
        
        print(f"USER: {user.email} (ID: {user.id})")
        print(f"INSTITUTION_ID: {user.institution_id}")
        print(f"ROLES: {roles}")
        
        # 2. Create access token matching runtime AuthContext
        additional_claims = {
            "roles": roles,
            "institution_id": str(user.institution_id) if user.institution_id else None,
        }
        token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims=additional_claims,
        )
        
    headers = {
        "Authorization": f"Bearer {token}",
        "x-institution-context": str(user.institution_id),
    }
    
    endpoints = [
        ("GET", "/api/v1/institutions/me"),
        ("GET", f"/api/v1/institutions/{user.institution_id}"),
        ("GET", "/api/v1/institutions/44c67aeb-f016-4667-9835-96642dba5a08/settings/coordinator-delegation"),
        ("PATCH", "/api/v1/institutions/44c67aeb-f016-4667-9835-96642dba5a08/settings/coordinator-delegation"),
        ("GET", "/api/v1/academic-years"),
        ("GET", "/api/v1/grades"),
        ("GET", "/api/v1/subjects"),
        ("GET", "/api/v1/groups"),
        ("GET", "/api/v1/teachers"),
        ("GET", "/api/v1/students"),
        ("GET", "/api/v1/guardians"),
        ("GET", "/api/v1/enrollments"),
        ("GET", "/api/v1/virtual-classrooms"),
        ("GET", "/api/v1/communications"),
        ("GET", "/api/v1/news"),
        ("GET", "/api/v1/incidents"),
        ("GET", "/api/v1/users"),
        # Tenant isolation check: accessing another institution
        ("GET", "/api/v1/institutions/00000000-0000-0000-0000-000000000001"),
        # Territorial catalog check
        ("GET", "/api/v1/institutions/catalog-explorer?municipality_code=18860"),
        ("GET", "/api/v1/institutions"),
    ]
    
    print("\n--- ENDPOINT AUDIT RESULTS ---")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        for method, path in endpoints:
            try:
                json_body = {"coordinator_delegation_enabled": True} if method == "PATCH" else None
                resp = await client.request(method, path, headers=headers, json=json_body)
                print(f"[{resp.status_code}] {method} {path} -> {resp.text[:120]}")
            except Exception as e:
                print(f"[ERR] {method} {path} -> {e}")

if __name__ == "__main__":
    asyncio.run(audit())
