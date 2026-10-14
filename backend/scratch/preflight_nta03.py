import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
)

async def run_preflight():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("=== NTA-03 PREFLIGHT INSPECTION ===")
        
        # A. Total institutions
        r_inst = await conn.execute(text("SELECT count(*) FROM institutions"))
        total_inst = r_inst.scalar()
        print(f"A. Total PEVN institutions: {total_inst}")
        
        # B. Active institutions
        r_act = await conn.execute(text("SELECT count(*) FROM institutions WHERE is_active = true"))
        active_inst = r_act.scalar()
        print(f"B. Active institutions: {active_inst}")
        
        # C. Inactive institutions
        r_inact = await conn.execute(text("SELECT count(*) FROM institutions WHERE is_active = false"))
        inactive_inst = r_inact.scalar()
        print(f"C. Inactive institutions: {inactive_inst}")
        
        # D. Number of catalog institutions
        r_cat = await conn.execute(text("SELECT count(*) FROM official_institution_catalog"))
        total_cat = r_cat.scalar()
        print(f"D. Total catalog institutions: {total_cat}")
        
        # E. Duplicate catalog dane_codes
        r_dup_cat = await conn.execute(text("""
            SELECT dane_code, count(*) 
            FROM official_institution_catalog 
            GROUP BY dane_code 
            HAVING count(*) > 1
        """))
        dup_cats = r_dup_cat.fetchall()
        print(f"E. Duplicate catalog dane_codes: {len(dup_cats)}")
        if dup_cats:
            for d in dup_cats:
                print(f"   Duplicate: {d[0]} -> {d[1]} times")
                
        # F, G, H: Matches between institutions and catalog
        r_matches = await conn.execute(text("""
            SELECT 
                i.id AS inst_id,
                i.name AS inst_name,
                i.dane_code AS inst_dane,
                i.is_active,
                count(c.id) AS match_count
            FROM institutions i
            LEFT JOIN official_institution_catalog c ON i.dane_code = c.dane_code
            GROUP BY i.id, i.name, i.dane_code, i.is_active
            ORDER BY i.dane_code
        """))
        matches = r_matches.fetchall()
        
        exact_one = [m for m in matches if m.match_count == 1]
        zero_match = [m for m in matches if m.match_count == 0]
        multi_match = [m for m in matches if m.match_count > 1]
        
        print(f"F. Institutions matching exactly 1 catalog record: {len(exact_one)}")
        print(f"G. Institutions matching 0 catalog records: {len(zero_match)}")
        print(f"H. Institutions matching multiple catalog records: {len(multi_match)}")
        
        # I. Existing institutions already having any catalog relationship
        # Check if catalog_institution_id column exists
        col_check = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'institutions' AND column_name = 'catalog_institution_id'
        """))
        has_col = col_check.scalar_one_or_none()
        print(f"I. Does institutions.catalog_institution_id column exist?: {'YES' if has_col else 'NO'}")
        
        # J & K. Details of all 34 institutions and catalog matching candidates
        print("\n--- Detailed Institution Matching Table (J & K) ---")
        detail_query = await conn.execute(text("""
            SELECT 
                i.id AS inst_id,
                i.dane_code AS inst_dane,
                i.name AS inst_name,
                i.is_active,
                m.code AS muni_code,
                d.code AS dept_code,
                c.id AS cat_id,
                c.name AS cat_name,
                c.dane_code AS cat_dane,
                c.department_code AS cat_dept_code,
                c.municipality_code AS cat_muni_code
            FROM institutions i
            JOIN municipalities m ON i.municipality_id = m.id
            JOIN departments d ON m.department_id = d.id
            LEFT JOIN official_institution_catalog c ON i.dane_code = c.dane_code
            ORDER BY d.code, m.code, i.dane_code
        """))
        details = detail_query.fetchall()
        print(f"Total institutions retrieved: {len(details)}")
        for idx, row in enumerate(details, 1):
            match_status = "MATCH" if row.cat_id else "NO_MATCH"
            dane_match = "EQUAL" if row.inst_dane == row.cat_dane else "MISMATCH"
            print(f"{idx:02d}. [{match_status}|{dane_match}] Inst: {row.inst_dane} | '{row.inst_name}' (Active: {row.is_active})")
            print(f"    Muni: {row.muni_code}, Dept: {row.dept_code} -> Cat ID: {row.cat_id} | Cat Name: '{row.cat_name}'")
            
        # Check campuses and users count to ensure baseline
        camp_count = (await conn.execute(text("SELECT count(*) FROM campuses"))).scalar()
        user_count = (await conn.execute(text("SELECT count(*) FROM users"))).scalar()
        da_count = (await conn.execute(text("SELECT count(*) FROM user_roles WHERE role_id = (SELECT id FROM roles WHERE name = 'department_admin') AND department_id IS NOT NULL"))).scalar()
        print(f"\nCampuses count: {camp_count}")
        print(f"Users count: {user_count}")
        print(f"Scoped Department Admins: {da_count}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_preflight())
