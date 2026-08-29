import asyncio
import uuid
from sqlalchemy import select
from app.db.session import get_session_factory
from app.models.institution import Institution
from app.models.territory import Municipality
from app.models.user import User, DocumentType
from app.models.role import Role
from app.services.rector_onboarding_service import RectorOnboardingService
from app.services.rbac_bootstrap_service import RbacBootstrapService

async def test_full_rector_flow():
    factory = get_session_factory()
    async with factory() as session:
        # 1. Ensure RBAC exists
        bootstrap = RbacBootstrapService(session=session)
        await bootstrap.seed_canonical_rbac_if_needed()
        
        # 2. Get a municipality
        muni = (await session.execute(select(Municipality))).scalars().first()
        if not muni:
            print("No municipality found!")
            return
        
        # 3. Create a test admin user and test institution
        admin_user = User(
            email=f"admin_inviter_{uuid.uuid4().hex[:8]}@pevn.edu.co",
            username=f"admin_{uuid.uuid4().hex[:8]}",
            hashed_password="dummy_argon2_hash",
            first_name="Admin",
            last_name="Inviter",
            document_type=DocumentType.CC,
            document_number=f"DOC{uuid.uuid4().hex[:8]}",
            is_active=True,
            is_verified=True,
        )
        session.add(admin_user)
        await session.flush()
        
        inst = Institution(
            municipality_id=muni.id,
            dane_code=f"DANE{uuid.uuid4().hex[:8]}",
            name=f"Colegio Test {uuid.uuid4().hex[:6]}",
            email=f"inst_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            is_active=True,
        )
        session.add(inst)
        await session.flush()
        
        # 4. Execute Rector Invitation Service (First Invite)
        service = RectorOnboardingService(session=session)
        rector_email = f"rector_{uuid.uuid4().hex[:8]}@pevn.edu.co"
        invitation_1, token_1 = await service.invite_rector(
            institution_id=inst.id,
            email=rector_email,
            first_name="Carlos",
            last_name="Rector",
            invited_by_id=admin_user.id,
            document_type=DocumentType.CC,
            document_number=f"DOCREC{uuid.uuid4().hex[:6]}",
        )
        await session.commit()
        print("First Invitation created:", invitation_1.id, "created_at:", invitation_1.created_at, "updated_at:", invitation_1.updated_at)
        
        # 5. Execute Second Invite for same user (Triggers UPDATE rector_invitations SET is_revoked=true, updated_at=now())
        invitation_2, token_2 = await service.invite_rector(
            institution_id=inst.id,
            email=rector_email,
            first_name="Carlos",
            last_name="Rector",
            invited_by_id=admin_user.id,
            document_type=DocumentType.CC,
            document_number=f"DOCREC{uuid.uuid4().hex[:6]}",
        )
        await session.commit()
        print("Second Invitation created (revoked first):", invitation_2.id, "updated_at:", invitation_2.updated_at)
        
        # Verify first invitation is revoked and has updated_at
        await session.refresh(invitation_1)
        print("First Invitation revoked status:", invitation_1.is_revoked, "revoked_at:", invitation_1.revoked_at, "updated_at:", invitation_1.updated_at)
        assert invitation_1.is_revoked is True
        assert invitation_1.updated_at is not None
        print("REAL POSTGRESQL RECTOR INVITATION FLOW: 100% SUCCESSFUL!")

if __name__ == "__main__":
    asyncio.run(test_full_rector_flow())
