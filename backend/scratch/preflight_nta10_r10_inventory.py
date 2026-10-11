import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        print("=== 1. ALL COORDINATORS IN DATABASE ===")
        res = await conn.execute(text("""
            SELECT u.id as user_id, u.email, u.first_name, u.last_name, u.is_active as user_active, u.is_verified,
                   ur.id as ur_id, ur.is_active as role_active, ur.institution_id, i.name as institution_name,
                   ur.campus_id, c.name as campus_name, c.dane_sede_code, u.created_at
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN institutions i ON ur.institution_id = i.id
            LEFT JOIN campuses c ON ur.campus_id = c.id
            WHERE r.name IN ('coordinator', 'academic_coordinator')
            ORDER BY ur.institution_id, ur.campus_id, u.created_at ASC;
        """))
        coordinators = res.fetchall()
        for c in coordinators:
            print(f"User: {c.user_id} | Email: {c.email} | Name: {c.first_name} {c.last_name}")
            print(f"  UserActive: {c.user_active} | Verified: {c.is_verified} | RoleActive: {c.role_active}")
            print(f"  Inst: {c.institution_id} ({c.institution_name})")
            print(f"  Campus: {c.campus_id} ({c.campus_name}, DANE: {c.dane_sede_code})")
            print(f"  Created: {c.created_at}\n")

        print("=== 2. ALL COORDINATOR INVITATIONS IN DATABASE ===")
        inv_res = await conn.execute(text("""
            SELECT ci.id, ci.institution_id, i.name as institution_name,
                   ci.campus_id, c.name as campus_name,
                   ci.user_id, u.email, u.first_name, u.last_name,
                   ci.is_used, ci.used_at, ci.is_revoked, ci.revoked_at,
                   ci.expires_at, ci.created_at
            FROM coordinator_invitations ci
            JOIN users u ON ci.user_id = u.id
            LEFT JOIN institutions i ON ci.institution_id = i.id
            LEFT JOIN campuses c ON ci.campus_id = c.id
            ORDER BY ci.created_at DESC;
        """))
        invitations = inv_res.fetchall()
        for inv in invitations:
            print(f"Inv: {inv.id} | User: {inv.user_id} ({inv.email}) | Name: {inv.first_name} {inv.last_name}")
            print(f"  Inst: {inv.institution_id} ({inv.institution_name}) | Campus: {inv.campus_id} ({inv.campus_name})")
            print(f"  Used: {inv.is_used} ({inv.used_at}) | Revoked: {inv.is_revoked} | Expires: {inv.expires_at} | Created: {inv.created_at}\n")

        print("=== 3. CONFLICT DETECTION: CAMPUS-SPECIFIC DUPLICATES ===")
        campus_conflicts = await conn.execute(text("""
            SELECT ur.institution_id, i.name as institution_name,
                   ur.campus_id, c.name as campus_name, c.dane_sede_code,
                   count(DISTINCT u.id) as count_coordinators,
                   string_agg(u.first_name || ' ' || u.last_name || ' (' || u.email || ', active=' || u.is_active::text || ', verif=' || u.is_verified::text || ')', ' ; ') as coordinators_list
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN institutions i ON ur.institution_id = i.id
            LEFT JOIN campuses c ON ur.campus_id = c.id
            WHERE r.name IN ('coordinator', 'academic_coordinator')
              AND ur.campus_id IS NOT NULL
            GROUP BY ur.institution_id, i.name, ur.campus_id, c.name, c.dane_sede_code
            HAVING count(DISTINCT u.id) > 1;
        """))
        conflicts = campus_conflicts.fetchall()
        if not conflicts:
            print("No campus-specific duplicates found via SQL query.")
        else:
            for conf in conflicts:
                print(f"CONFLICT IN CAMPUS: {conf.campus_name} (ID: {conf.campus_id}, DANE: {conf.dane_sede_code})")
                print(f"  Institution: {conf.institution_name} (ID: {conf.institution_id})")
                print(f"  Coordinators ({conf.count_coordinators}): {conf.coordinators_list}\n")

        print("=== 4. CONFLICT DETECTION: INSTITUTION-WIDE VS CAMPUS-SPECIFIC ===")
        inst_conflicts = await conn.execute(text("""
            SELECT ur.institution_id, i.name as institution_name,
                   count(DISTINCT CASE WHEN ur.campus_id IS NULL THEN u.id END) as global_count,
                   count(DISTINCT CASE WHEN ur.campus_id IS NOT NULL THEN u.id END) as campus_count,
                   count(DISTINCT CASE WHEN ur.campus_id IS NULL THEN u.id END) as count_global
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN institutions i ON ur.institution_id = i.id
            WHERE r.name IN ('coordinator', 'academic_coordinator')
            GROUP BY ur.institution_id, i.name
            HAVING count(DISTINCT CASE WHEN ur.campus_id IS NULL THEN u.id END) > 0
               AND count(DISTINCT CASE WHEN ur.campus_id IS NOT NULL THEN u.id END) > 0;
        """))
        iconf = inst_conflicts.fetchall()
        if not iconf:
            print("No institution-wide vs campus-specific co-existence conflicts found.")
        else:
            for ic in iconf:
                print(f"CONFLICT IN INSTITUTION: {ic.institution_name} (ID: {ic.institution_id})")
                print(f"  Global coordinators: {ic.global_count} | Campus coordinators: {ic.campus_count}\n")

        print("=== 5. CONFLICT DETECTION: MULTIPLE INSTITUTION-WIDE ===")
        multi_global = await conn.execute(text("""
            SELECT ur.institution_id, i.name as institution_name,
                   count(DISTINCT u.id) as global_count,
                   string_agg(u.first_name || ' ' || u.last_name || ' (' || u.email || ')', ' ; ') as coordinators_list
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN institutions i ON ur.institution_id = i.id
            WHERE r.name IN ('coordinator', 'academic_coordinator')
              AND ur.campus_id IS NULL
            GROUP BY ur.institution_id, i.name
            HAVING count(DISTINCT u.id) > 1;
        """))
        mg = multi_global.fetchall()
        if not mg:
            print("No multiple institution-wide coordinators found.")
        else:
            for g in mg:
                print(f"CONFLICT: MULTIPLE GLOBAL IN {g.institution_name}: {g.global_count} coordinators: {g.coordinators_list}\n")

if __name__ == "__main__":
    asyncio.run(main())
