import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import get_session_factory
from sqlalchemy import select
from app.models.user import User
from app.models.institution import Institution
from app.core.security.tokens import token_service
from app.services.auth_service import AuthService

async def test_invitation_lifecycle():
    factory = get_session_factory()
    async with factory() as session:
        u = (await session.execute(select(User).where(User.username == "Admin_Municip_ValParaiso"))).scalar_one()
        inst = (await session.execute(select(Institution).where(Institution.dane_code == "118860001293"))).scalar_one()
        
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
            # 1. Invite Rector
            invite_payload = {
                "first_name": "TestRector",
                "last_name": "Valparaíso",
                "document_type": "CC",
                "document_number": "9876543210",
                "email": "test_rector_valparaiso@colegio.edu.co",
                "phone_number": "3123456789",
            }
            res = await client.post(
                f"/api/v1/institutions/{inst.id}/rector-invitation",
                json=invite_payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            print("1. Invite response:", res.status_code)
            invite_data = res.json()
            raw_token = invite_data.get("raw_invitation_token")
            inv_url = invite_data.get("invitation_url")
            print("   raw_token:", raw_token[:10] + "..." if raw_token else None)
            print("   invitation_url:", inv_url)
            assert res.status_code == 201
            assert "/auth/accept-invitation?token=" in (inv_url or "")

            # 2. Check GET /institutions now reports has_pending_invitation == True
            get_res = await client.get(
                "/api/v1/institutions",
                headers={"Authorization": f"Bearer {token}"},
            )
            items = get_res.json()["items"]
            target = next(i for i in items if i["id"] == str(inst.id))
            print("2. GET /institutions after invite:")
            print("   has_pending_invitation:", target["has_pending_invitation"])
            print("   has_active_rector:", target["has_active_rector"])
            assert target["has_pending_invitation"] is True
            assert target["has_active_rector"] is False

            # 3. Resend invitation
            resend_res = await client.post(
                f"/api/v1/institutions/{inst.id}/rector-invitation/resend",
                headers={"Authorization": f"Bearer {token}"},
            )
            print("3. Resend response:", resend_res.status_code)
            assert resend_res.status_code == 200
            resend_data = resend_res.json()
            new_raw_token = resend_data.get("raw_invitation_token")
            print("   new raw_token:", new_raw_token[:10] + "..." if new_raw_token else None)
            assert new_raw_token != raw_token

            # 4. Old token is now revoked and rejected at verify-invitation
            verify_old = await client.post(
                "/api/v1/auth/verify-invitation",
                json={"token": raw_token},
            )
            print("4. Verify old token status (should be 409/revoked):", verify_old.status_code)
            assert verify_old.status_code in (404, 409, 400, 422)

            # 5. New token is valid at verify-invitation
            verify_new = await client.post(
                "/api/v1/auth/verify-invitation",
                json={"token": new_raw_token},
            )
            print("5. Verify new token status (should be 200):", verify_new.status_code)
            assert verify_new.status_code == 200
            print("   verified for:", verify_new.json().get("email"))

            # 6. Accept invitation using new token to activate account
            accept_res = await client.post(
                "/api/v1/auth/accept-invitation",
                json={
                    "token": new_raw_token,
                    "password": "RectorPassword2026*",
                    "password_confirmation": "RectorPassword2026*",
                },
            )
            print("6. Accept invitation status:", accept_res.status_code)
            assert accept_res.status_code == 200

            # 7. Check GET /institutions now reports has_active_rector == True, has_pending_invitation == False
            get_res2 = await client.get(
                "/api/v1/institutions",
                headers={"Authorization": f"Bearer {token}"},
            )
            target2 = next(i for i in get_res2.json()["items"] if i["id"] == str(inst.id))
            print("7. GET /institutions after acceptance:")
            print("   has_pending_invitation:", target2["has_pending_invitation"])
            print("   has_active_rector:", target2["has_active_rector"])
            print("   active_rector_name:", target2["active_rector_name"])
            print("   active_rector_email:", target2["active_rector_email"])
            assert target2["has_pending_invitation"] is False
            assert target2["has_active_rector"] is True
            assert target2["active_rector_email"] == "test_rector_valparaiso@colegio.edu.co"

            # 8. Try duplicate invitation - must be rejected with 409 Conflict
            dup_res = await client.post(
                f"/api/v1/institutions/{inst.id}/rector-invitation",
                json=invite_payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            print("8. Duplicate invite response (must be 409):", dup_res.status_code)
            assert dup_res.status_code == 409
            print("   Error message:", dup_res.json()["error"]["message"])

            # 9. Cleanup test rector from Valparaiso so institution remains pristine for Product Owner manual acceptance
            from app.models.role import Role, UserRole
            from app.models.invitation import RectorInvitation
            rector_u = (await session.execute(select(User).where(User.email == "test_rector_valparaiso@colegio.edu.co"))).scalar_one_or_none()
            if rector_u:
                await session.delete(rector_u)
            await session.commit()
            print("9. Cleaned up test rector. Valparaíso institution restored to vacant state for PO testing.")

            # Final check that Valparaiso is back to vacant
            get_res3 = await client.get(
                "/api/v1/institutions",
                headers={"Authorization": f"Bearer {token}"},
            )
            target3 = next(i for i in get_res3.json()["items"] if i["id"] == str(inst.id))
            print("10. Valparaiso restored state: has_active_rector =", target3["has_active_rector"])
            assert target3["has_active_rector"] is False

if __name__ == "__main__":
    asyncio.run(test_invitation_lifecycle())
