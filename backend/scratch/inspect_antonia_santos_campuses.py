import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        print("=== 1. INSTITUCIÓN EDUCATIVA ANTONIA SANTOS DETAILS ===")
        inst_res = await conn.execute(text("""
            SELECT id, name, dane_code, email, is_active
            FROM institutions
            WHERE id = 'e49cbb18-89a9-49f1-97da-e80e9a95dbba'
               OR name ILIKE '%ANTONIA SANTOS%';
        """))
        for inst in inst_res.fetchall():
            print(f"Institution: {inst.id} | {inst.name} | DANE: {inst.dane_code} | Email: {inst.email} | Active: {inst.is_active}")
            inst_id = inst.id

            print("\n=== 2. CAMPUSES OF THIS INSTITUTION ===")
            camp_res = await conn.execute(text("""
                SELECT id, name, dane_sede_code, is_active
                FROM campuses
                WHERE institution_id = :inst_id
                ORDER BY name ASC;
            """), {"inst_id": inst_id})
            campuses = camp_res.fetchall()
            for camp in campuses:
                print(f"  Campus: {camp.id} | Name: '{camp.name}' | DANE Sede: {camp.dane_sede_code} | Active: {camp.is_active}")

                # Check coordinators on this campus
                coord_res = await conn.execute(text("""
                    SELECT u.id as user_id, u.email, u.first_name, u.last_name, u.is_active as user_active,
                           ur.id as ur_id, ur.is_active as role_active, u.created_at
                    FROM users u
                    JOIN user_roles ur ON u.id = ur.user_id
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.institution_id = :inst_id
                      AND ur.campus_id = :camp_id
                      AND r.name IN ('coordinator', 'academic_coordinator');
                """), {"inst_id": inst_id, "camp_id": camp.id})
                coords = coord_res.fetchall()
                if coords:
                    for c in coords:
                        print(f"    -> ASSIGNED: {c.user_id} | {c.first_name} {c.last_name} ({c.email}) | UserActive={c.user_active}, RoleActive={c.role_active} | Created: {c.created_at}")
                else:
                    print(f"    -> [VACANT - NO COORDINATOR ASSIGNED]")

            # Check Global coordinators on this institution
            print("\n=== 3. GLOBAL COORDINATORS OF THIS INSTITUTION ===")
            global_res = await conn.execute(text("""
                SELECT u.id as user_id, u.email, u.first_name, u.last_name, u.is_active as user_active,
                       ur.id as ur_id, ur.is_active as role_active, u.created_at
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.institution_id = :inst_id
                  AND ur.campus_id IS NULL
                  AND r.name IN ('coordinator', 'academic_coordinator');
            """), {"inst_id": inst_id})
            globals_ = global_res.fetchall()
            if globals_:
                for g in globals_:
                    print(f"    -> GLOBAL: {g.user_id} | {g.first_name} {g.last_name} ({g.email}) | UserActive={g.user_active}, RoleActive={g.role_active}")
            else:
                print("    -> [NO GLOBAL COORDINATORS]")

            # Check invitations
            print("\n=== 4. INVITATIONS FOR THIS INSTITUTION ===")
            inv_res = await conn.execute(text("""
                SELECT ci.id, ci.user_id, u.email, u.first_name, u.last_name, ci.campus_id, c.name as campus_name,
                       ci.is_used, ci.used_at, ci.is_revoked, ci.expires_at, ci.created_at
                FROM coordinator_invitations ci
                JOIN users u ON ci.user_id = u.id
                LEFT JOIN campuses c ON ci.campus_id = c.id
                WHERE ci.institution_id = :inst_id
                ORDER BY ci.created_at ASC;
            """), {"inst_id": inst_id})
            for inv in inv_res.fetchall():
                print(f"  Invitation: {inv.id} | User: {inv.first_name} {inv.last_name} ({inv.email}) | Campus: {inv.campus_name} ({inv.campus_id}) | Used: {inv.is_used} | Revoked: {inv.is_revoked} | Expires: {inv.expires_at}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
