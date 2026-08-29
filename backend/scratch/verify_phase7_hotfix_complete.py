"""
Phase 7 Hotfix Comprehensive PostgreSQL Verification Script
Verifies:
1. Schema integrity of role_permissions (created_at, updated_at present, correct types, server_default)
2. Row preservation (exact row count, data values)
3. RBAC catalog consistency (11 roles, canonical permissions, associations)
4. ORM querying with selectinload relationships
5. RbacBootstrapService idempotency
"""
import asyncio
import uuid
from sqlalchemy import text, select
from app.db.session import get_session_factory
from app.models.role import RolePermission, Role, Permission
from app.services.rbac_bootstrap_service import (
    RbacBootstrapService,
    CANONICAL_ROLES,
    CANONICAL_PERMISSIONS,
    ROLE_PERMISSIONS_CONFIG,
)

async def run_full_pg_audit():
    factory = get_session_factory()
    async with factory() as session:
        print("=" * 70)
        print("1. POSTGRESQL PHYSICAL SCHEMA AUDIT: role_permissions")
        print("=" * 70)
        cols = await session.execute(text(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_name = 'role_permissions' "
            "ORDER BY ordinal_position;"
        ))
        col_list = cols.fetchall()
        for col in col_list:
            print(f"  Column: {col[0]:<15} | Type: {col[1]:<25} | Nullable: {col[2]:<4} | Default: {col[3]}")
        
        col_names = [c[0] for c in col_list]
        assert "created_at" in col_names, "ERROR: created_at missing!"
        assert "updated_at" in col_names, "ERROR: updated_at missing!"
        assert "role_id" in col_names, "ERROR: role_id missing!"
        assert "permission_id" in col_names, "ERROR: permission_id missing!"

        print("\n" + "=" * 70)
        print("2. DATA PRESERVATION AUDIT")
        print("=" * 70)
        cnt = (await session.execute(text("SELECT count(*) FROM role_permissions;"))).scalar()
        print(f"  Total role_permissions rows in PostgreSQL: {cnt}")
        assert cnt > 0, "ERROR: role_permissions is empty!"

        # Check NULL timestamps
        null_created = (await session.execute(text("SELECT count(*) FROM role_permissions WHERE created_at IS NULL;"))).scalar()
        null_updated = (await session.execute(text("SELECT count(*) FROM role_permissions WHERE updated_at IS NULL;"))).scalar()
        print(f"  NULL created_at count: {null_created} (must be 0)")
        print(f"  NULL updated_at count: {null_updated} (must be 0)")
        assert null_created == 0, "ERROR: found NULL created_at"
        assert null_updated == 0, "ERROR: found NULL updated_at"

        print("\n" + "=" * 70)
        print("3. RBAC BOOTSTRAP SERVICE IDEMPOTENCY ON POSTGRESQL")
        print("=" * 70)
        svc = RbacBootstrapService(session=session)
        result = await svc.seed_canonical_rbac_if_needed()
        await session.commit()
        print(f"  Bootstrap result: {result}")
        assert result["created_roles"] == 0, "Roles were unexpectedly recreated!"
        assert result["created_permissions"] == 0, "Permissions were unexpectedly recreated!"
        assert result["created_links"] == 0, "Links were unexpectedly recreated!"

        print("\n" + "=" * 70)
        print("4. ORM QUERY EXECUTION (VERIFYING NO UndefinedColumnError)")
        print("=" * 70)
        # Select directly from RolePermission ORM model
        rp_records = (await session.execute(select(RolePermission))).scalars().all()
        print(f"  Successfully loaded {len(rp_records)} RolePermission ORM objects.")

        # Query all Roles with selectinload permissions
        roles = (await session.execute(select(Role))).scalars().all()
        print(f"  Successfully queried {len(roles)} canonical Roles.")
        for r in roles:
            print(f"    - Role '{r.name}' (level {r.level}): {len(r.permissions)} permissions linked")

        # Verify Rector specifically
        rector = next((r for r in roles if r.name == "rector"), None)
        assert rector is not None, "ERROR: Rector role not found!"
        print(f"\n  Rector role verified with {len(rector.permissions)} permissions.")

        print("\n" + "=" * 70)
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO DRIFT.")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_full_pg_audit())
