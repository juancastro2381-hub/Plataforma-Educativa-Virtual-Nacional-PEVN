import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import asyncio
import uuid
from sqlalchemy import select
from app.db.session import get_session_factory
from app.models.user import User
from app.models.role import UserRole, Role
from app.models.institution import Institution
from app.models.territory import Municipality, Department
from app.services.auth_service import AuthService
from app.services.institution_service import InstitutionService
from app.core.security.interfaces import SystemRole

async def main():
    session_factory = get_session_factory()
    async with session_factory() as session:
        # 1. Inspect municipal admin users
        role_stmt = select(Role).where(Role.name == "municipality_admin")
        role_res = await session.execute(role_stmt)
        muni_role = role_res.scalar_one_or_none()
        print(f"Role 'municipality_admin': {muni_role.id if muni_role else 'NOT FOUND'}")
        
        # Check permissions for municipality_admin
        if muni_role:
            from app.models.role import RolePermission, Permission
            perm_stmt = (
                select(Permission.resource, Permission.action)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == muni_role.id)
            )
            rows = (await session.execute(perm_stmt)).all()
            perms = [f"{r}:{a}" for r, a in rows]
            print(f"Permissions for municipality_admin in DB: {len(perms)}")
            print(f"  institutions:read in DB? {'institutions:read' in perms}")
            print(f"  users:create_rector in DB? {'users:create_rector' in perms}")
            print(f"  All DB perms: {sorted(perms)}")

        # 2. Inspect users with municipality_admin
        user_roles_stmt = (
            select(UserRole)
            .where(UserRole.role_id == muni_role.id if muni_role else False)
        )
        urs = (await session.execute(user_roles_stmt)).scalars().all()
        print(f"\nUserRoles for municipality_admin: {len(urs)}")
        for ur in urs:
            user = await session.get(User, ur.user_id)
            muni = await session.get(Municipality, ur.municipality_id) if ur.municipality_id else None
            print(f"User: id={user.id if user else 'None'}, username={user.username if user else 'None'}, email={user.email if user else 'None'}, is_active={user.is_active if user else 'None'}, muni_id={ur.municipality_id}, muni_name={muni.name if muni else 'None'}")
            
            # Check institutions in this municipality
            if ur.municipality_id:
                inst_stmt = select(Institution).where(Institution.municipality_id == ur.municipality_id)
                insts = (await session.execute(inst_stmt)).scalars().all()
                print(f"  Institutions in {muni.name if muni else ur.municipality_id}: {len(insts)}")
                for inst in insts:
                    print(f"    - [{inst.dane_code}] {inst.name} (active={inst.is_active})")
                    # Check if there is an active rector or pending invitation
                    from app.models.invitation import RectorInvitation
                    inv_stmt = select(RectorInvitation).where(RectorInvitation.institution_id == inst.id)
                    invs = (await session.execute(inv_stmt)).scalars().all()
                    print(f"      Invitations: {len(invs)}")
                    for inv in invs:
                        print(f"        * inv_id={inv.id}, user_id={inv.user_id}, is_used={inv.is_used}, expires_at={inv.expires_at}")

        # 3. List all institutions in database
        all_insts = (await session.execute(select(Institution))).scalars().all()
        print(f"\nTotal institutions in DB: {len(all_insts)}")
        for inst in all_insts[:10]:
            print(f"  Inst: {inst.dane_code} - {inst.name} (muni_id={inst.municipality_id})")

if __name__ == "__main__":
    asyncio.run(main())
