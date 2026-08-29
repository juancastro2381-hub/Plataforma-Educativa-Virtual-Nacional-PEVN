import asyncio
from sqlalchemy import text, select
from app.db.session import get_session_factory
from app.models.role import RolePermission, Role, Permission
from app.services.rbac_bootstrap_service import RbacBootstrapService

async def verify():
    factory = get_session_factory()
    async with factory() as session:
        # 1. Check column schema in information_schema
        cols = await session.execute(text(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_name = 'role_permissions' "
            "ORDER BY ordinal_position;"
        ))
        print("POST-MIGRATION COLUMNS in role_permissions:")
        for r in cols.fetchall():
            print(" -", r)
        
        # 2. Test RBAC Bootstrap Service against real PostgreSQL
        print("\nRunning RbacBootstrapService on PostgreSQL...")
        bootstrap = RbacBootstrapService(session=session)
        result = await bootstrap.seed_canonical_rbac_if_needed()
        await session.commit()
        print("RBAC Bootstrap result:", result)
        
        # 3. Query RolePermission through SQLAlchemy ORM
        rp_count = (await session.execute(select(RolePermission))).scalars().all()
        print(f"Total RolePermission records queried via ORM: {len(rp_count)}")
        
        # 4. Query Role with selectinload permissions
        roles = (await session.execute(select(Role))).scalars().all()
        print(f"Total Roles queried: {len(roles)}")
        rector_role = next((r for r in roles if r.name == "rector"), None)
        if rector_role:
            print(f"Rector permissions loaded ({len(rector_role.permissions)}):", [p.identifier for p in rector_role.permissions[:5]], "...")

if __name__ == "__main__":
    asyncio.run(verify())
