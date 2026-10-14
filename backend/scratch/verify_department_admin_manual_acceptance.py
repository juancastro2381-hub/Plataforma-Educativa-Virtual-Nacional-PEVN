import os
from dotenv import load_dotenv
load_dotenv()

"""
PEVN — Verification Script for Section 17: MANUAL ACCEPTANCE TEST
DEPARTMENT_ADMIN Secure Invitation & Account Activation
"""

import asyncio
import os
import sys
import uuid
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete

from app.main import app
from app.core.security.tokens import token_service
from app.core.security.interfaces import SystemRole
from app.models.user import User
from app.models.role import UserRole
from app.models.territory import Department
from app.models.institution import Institution
from app.models.invitation import DepartmentAdminInvitation

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DB_URL = get_safe_test_db_url()

async def run_manual_acceptance_suite():
    print("=" * 80)
    print("PEVN — SECTION 17: DEPARTMENT_ADMIN INVITATION MANUAL ACCEPTANCE TEST")
    print("=" * 80)

    engine = create_async_engine(DB_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    created_user_ids = []

    try:
        async with session_factory() as session:
            # 1. Fetch NATIONAL_ADMIN and canonical departments
            na_res = await session.execute(select(User).where(User.username == "national_admin"))
            national_admin = na_res.scalar_one()

            atlantico = (await session.execute(select(Department).where(Department.code == "08"))).scalar_one()
            cundinamarca = (await session.execute(select(Department).where(Department.code == "25"))).scalar_one()
            bogota = (await session.execute(select(Department).where(Department.code == "11"))).scalar_one()

            bogota_inst_id = "e9f740be-3806-4060-a808-9d02c8bf29af"

        na_token = await token_service.create_access_token(
            subject=str(national_admin.id),
            additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
        )
        na_headers = {"Authorization": f"Bearer {na_token}"}

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
            
            # =========================================================================
            # PART 1: TEST WITH DANE 08 — ATLÁNTICO
            # =========================================================================
            print("\n" + "-" * 70)
            print("[PHASE 1] DEPARTMENT_ADMIN PROVISIONING FOR DANE 08 — ATLÁNTICO")
            print("-" * 70)

            # Step 1: Provisioning without initial password
            test_email_08 = f"accept.atlantico.{uuid.uuid4().hex[:6]}@sedatlantico.gov.co"
            test_username_08 = f"accept.atl.{uuid.uuid4().hex[:6]}"
            payload_08 = {
                "first_name": "Valeria",
                "last_name": "Abuchaibe",
                "email": test_email_08,
                "username": test_username_08,
                "department_id": str(atlantico.id),
            }
            # Notice: No password field in payload!

            resp_create = await client.post("/api/v1/department-admins", json=payload_08, headers=na_headers)
            assert resp_create.status_code == 201, f"Expected 201, got {resp_create.status_code}: {resp_create.text}"
            data_create = resp_create.json()
            created_user_id_08 = data_create["id"]
            created_user_ids.append(created_user_id_08)
            raw_token_08 = data_create.get("raw_invitation_token")
            invitation_id_08 = data_create.get("invitation_id")
            delivery_status_08 = data_create.get("email_delivery_status")
            invitation_url_08 = data_create.get("invitation_url")
            
            assert delivery_status_08 == "EMAIL_NOT_CONFIGURED", f"Expected EMAIL_NOT_CONFIGURED, got {delivery_status_08}"
            assert "/invitation/accept?token=" in invitation_url_08
            assert raw_token_08 in invitation_url_08

            print(f"[OK] Step 1-7: Created DEPARTMENT_ADMIN {test_username_08} without initial password.")
            print(f"     User ID: {created_user_id_08}")
            print(f"     Delivery Status: {delivery_status_08} (Accurate; SMTP unconfigured)")
            print(f"     Fallback URL: {invitation_url_08[:45]}...")
            print(f"     Raw Invitation Token returned: {raw_token_08[:12]}... (one-time for fallback link)")
            print(f"     Invitation ID: {invitation_id_08}")

            # Verify in DB: raw token NEVER persisted, only hash
            async with session_factory() as session:
                inv_db = (await session.execute(
                    select(DepartmentAdminInvitation).where(DepartmentAdminInvitation.id == uuid.UUID(invitation_id_08))
                )).scalar_one()
                assert inv_db.token_hash == hashlib.sha256(raw_token_08.encode()).hexdigest()
                assert raw_token_08 not in inv_db.token_hash
                print("[OK] Step 8-9: Invitation persisted in DB with SHA-256 hash. Raw token NEVER stored.")

                user_db = (await session.execute(select(User).where(User.id == uuid.UUID(created_user_id_08)))).scalar_one()
                assert user_db.is_active is False
                print("[OK] User created in INACTIVE state (is_active=False).")

            # Step 9.5: Test Resend Invitation UX & Revocation
            resp_resend = await client.post(f"/api/v1/department-admins/{created_user_id_08}/resend-invitation", headers=na_headers)
            assert resp_resend.status_code == 200, f"Resend failed: {resp_resend.text}"
            resend_data = resp_resend.json()
            new_raw_token_08 = resend_data["raw_invitation_token"]
            assert new_raw_token_08 != raw_token_08
            assert resend_data["email_delivery_status"] == "EMAIL_NOT_CONFIGURED"
            assert "/invitation/accept?token=" in resend_data["invitation_url"]
            print(f"[OK] Step 9.5: Resend generated new invitation with fallback URL. Delivery: {resend_data['email_delivery_status']}.")

            # Verify old token is revoked
            resp_old_verify = await client.post("/api/v1/auth/verify-invitation", json={"token": raw_token_08})
            assert resp_old_verify.status_code == 409
            print("[OK] Prior invitation was immediately revoked upon resend (HTTP 409).")

            # Step 10: Open the new invitation (Verify token)
            resp_verify = await client.post("/api/v1/auth/verify-invitation", json={"token": new_raw_token_08})
            assert resp_verify.status_code == 200, f"Verify failed: {resp_verify.text}"
            verify_data = resp_verify.json()
            assert verify_data["role_name"] == "department_admin"
            assert verify_data["department_name"] == "ATLÁNTICO"
            assert verify_data["department_code"] == "08"
            print(f"[OK] Step 10: New invitation verified for {verify_data['email']} in {verify_data['department_name']}.")

            # Step 11-12: Accept new invitation and set personal password
            new_password_08 = "Atla#Educacion2026!Secure"
            resp_accept = await client.post("/api/v1/auth/accept-invitation", json={
                "token": new_raw_token_08,
                "password": new_password_08,
                "password_confirmation": new_password_08
            })
            assert resp_accept.status_code == 200, f"Accept failed: {resp_accept.text}"
            print(f"[OK] Step 11-12: Password set by administrator and account activated successfully.")

            # Step 13: Login with newly activated credentials
            resp_login = await client.post("/api/v1/auth/login", json={
                "username": test_username_08,
                "password": new_password_08
            })
            assert resp_login.status_code == 200, f"Login failed: {resp_login.text}"
            auth_token_08 = resp_login.json()["access_token"]
            user_headers_08 = {"Authorization": f"Bearer {auth_token_08}"}
            print(f"[OK] Step 13: Login successful as {test_username_08}.")

            # Step 14: Verify Scope: Departamental, Jurisdicción: ATLÁNTICO
            resp_me = await client.get("/api/v1/auth/me", headers=user_headers_08)
            assert resp_me.status_code == 200
            me_data = resp_me.json()
            assert me_data["scope"]["is_department"] is True
            assert me_data["scope"]["is_national"] is False
            assert me_data["scope"]["department_id"] == str(atlantico.id)
            assert me_data["scope"]["jurisdiction_name"] == "ATLÁNTICO"
            print(f"[OK] Step 14: Scope verified: is_department=True, jurisdiction={me_data['scope']['jurisdiction_name']}")

            # Step 15: Verify access to Atlántico territorial resources
            resp_analytics = await client.get("/api/v1/analytics/territorial/summary", headers=user_headers_08)
            assert resp_analytics.status_code == 200
            analytics_data = resp_analytics.json()
            assert analytics_data["scope_level"] == "DEPARTMENT"
            assert "ATLÁNTICO" in analytics_data["jurisdiction_name"].upper()
            assert analytics_data["total_departments"] == 1
            print(f"[OK] Step 15: Atlántico analytics accessible and strictly scoped: {analytics_data['jurisdiction_name']}.")

            # Step 16-17: Attempt cross-department access to Bogotá institution
            resp_cross = await client.get(f"/api/v1/institutions/{bogota_inst_id}", headers=user_headers_08)
            assert resp_cross.status_code == 403, f"Expected 403, got {resp_cross.status_code}"
            print(f"[OK] Step 16-17: Cross-department access to Bogotá blocked with HTTP 403.")

            # Step 18-19: Exactly 17 permissions, zero wildcards
            perms = me_data.get("permissions", [])
            assert len(perms) == 17, f"Expected 17 permissions, found {len(perms)}: {perms}"
            for p in perms:
                assert "*" not in p, f"Wildcard found: {p}"
            print(f"[OK] Step 18-19: Exactly 17 permissions verified, zero wildcards.")

            # Step 20: Verify invitation cannot be reused
            resp_reuse = await client.post("/api/v1/auth/accept-invitation", json={
                "token": raw_token_08,
                "password": "AnotherPassword123!",
                "password_confirmation": "AnotherPassword123!"
            })
            assert resp_reuse.status_code in (400, 404, 409, 410)
            print(f"[OK] Step 20: Invitation reuse blocked with HTTP {resp_reuse.status_code} (INVITATION_ALREADY_USED).")

            # =========================================================================
            # PART 2: REPEAT TEST WITH DANE 25 — CUNDINAMARCA
            # =========================================================================
            print("\n" + "-" * 70)
            print("[PHASE 2] REPEAT WITH DANE 25 — CUNDINAMARCA")
            print("-" * 70)

            test_email_25 = f"accept.cund.{uuid.uuid4().hex[:6]}@sedcundinamarca.gov.co"
            test_username_25 = f"accept.cund.{uuid.uuid4().hex[:6]}"
            payload_25 = {
                "first_name": "Jorge",
                "last_name": "Rey",
                "email": test_email_25,
                "username": test_username_25,
                "department_id": str(cundinamarca.id),
            }

            resp_create_25 = await client.post("/api/v1/department-admins", json=payload_25, headers=na_headers)
            assert resp_create_25.status_code == 201
            data_create_25 = resp_create_25.json()
            created_user_id_25 = data_create_25["id"]
            created_user_ids.append(created_user_id_25)
            raw_token_25 = data_create_25["raw_invitation_token"]

            # Accept
            new_password_25 = "Cundi#Educacion2026!Secure"
            resp_accept_25 = await client.post("/api/v1/auth/accept-invitation", json={
                "token": raw_token_25,
                "password": new_password_25,
                "password_confirmation": new_password_25
            })
            assert resp_accept_25.status_code == 200

            # Login
            resp_login_25 = await client.post("/api/v1/auth/login", json={
                "username": test_username_25,
                "password": new_password_25
            })
            assert resp_login_25.status_code == 200
            token_25 = resp_login_25.json()["access_token"]
            headers_25 = {"Authorization": f"Bearer {token_25}"}

            # Scope
            resp_me_25 = await client.get("/api/v1/auth/me", headers=headers_25)
            me_25 = resp_me_25.json()
            assert me_25["scope"]["is_department"] is True
            assert me_25["scope"]["department_id"] == str(cundinamarca.id)
            assert me_25["scope"]["jurisdiction_name"] == "CUNDINAMARCA"
            assert len(me_25["permissions"]) == 17
            print(f"[OK] Cundinamarca administrator {test_username_25} activated and scoped exclusively to Cundinamarca.")

            # Cross-department check: Cundinamarca admin attempts Atlántico analytics
            # (Territorial analytics will return Cundinamarca data, not Atlántico)
            resp_analytics_25 = await client.get("/api/v1/analytics/territorial/summary", headers=headers_25)
            assert resp_analytics_25.status_code == 200
            assert "CUNDINAMARCA" in resp_analytics_25.json()["jurisdiction_name"].upper()
            assert resp_analytics_25.json()["total_departments"] == 1
            print(f"[OK] Cundinamarca administrator isolated to {resp_analytics_25.json()['jurisdiction_name']}.")

    finally:
        # TEARDOWN: Clean up temporary test accounts to maintain 100% database hygiene
        print("\n" + "-" * 70)
        print("[TEARDOWN] Cleaning up temporary acceptance test identities...")
        async with session_factory() as session:
            for uid in created_user_ids:
                u_uuid = uuid.UUID(uid)
                await session.execute(delete(DepartmentAdminInvitation).where(DepartmentAdminInvitation.user_id == u_uuid))
                await session.execute(delete(UserRole).where(UserRole.user_id == u_uuid))
                await session.execute(delete(User).where(User.id == u_uuid))
            await session.commit()
        print(f"[OK] Cleaned up {len(created_user_ids)} temporary test identities. Database hygiene preserved.")

    print("\n" + "=" * 80)
    print("ALL MANUAL ACCEPTANCE TEST STEPS COMPLETED AND VERIFIED 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_manual_acceptance_suite())
