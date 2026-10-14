import os
from dotenv import load_dotenv
load_dotenv()

"""
Test NTA-02 migration SQL within an explicit rollback transaction to verify invariants.
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

DB_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
engine = create_async_engine(DB_URL, echo=False)

async def test_migration():
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            print("=== CAPTURING BASELINE ===")
            dept_ids_before = {r[0]: str(r[1]) for r in (await conn.execute(text("SELECT code, id FROM departments"))).all()}
            muni_ids_before = {r[0]: (str(r[1]), str(r[2])) for r in (await conn.execute(text("SELECT code, id, department_id FROM municipalities"))).all()}
            inst_count_before = (await conn.execute(text("SELECT count(*) FROM institutions"))).scalar()
            camp_count_before = (await conn.execute(text("SELECT count(*) FROM campuses"))).scalar()
            user_count_before = (await conn.execute(text("SELECT count(*) FROM users"))).scalar()
            ur_count_before = (await conn.execute(text("SELECT count(*) FROM user_roles"))).scalar()
            
            print(f"Depts before: {len(dept_ids_before)} -> {dept_ids_before}")
            print(f"Munis before: {len(muni_ids_before)} -> {muni_ids_before}")
            print(f"Institutions before: {inst_count_before}")
            print(f"Campuses before: {camp_count_before}")
            print(f"Users before: {user_count_before}")
            print(f"UserRoles before: {ur_count_before}")

            print("\n=== EXECUTING DEPARTMENTS INSERT ===")
            dept_sql = """
            WITH ranked_depts AS (
                SELECT 
                    department_code,
                    CASE 
                        WHEN department_code = '44' THEN 'LA GUAJIRA'
                        ELSE department_name 
                    END as department_name,
                    count(*) as cnt,
                    ROW_NUMBER() OVER(PARTITION BY department_code ORDER BY count(*) DESC, department_name ASC) as rn
                FROM official_institution_catalog
                GROUP BY department_code, department_name
            )
            INSERT INTO departments (id, code, name)
            SELECT 
                gen_random_uuid(),
                department_code,
                department_name
            FROM ranked_depts
            WHERE rn = 1
            ON CONFLICT (code) DO NOTHING;
            """
            await conn.execute(text(dept_sql))
            
            dept_count_after = (await conn.execute(text("SELECT count(*) FROM departments"))).scalar()
            dept_distinct_after = (await conn.execute(text("SELECT count(distinct code) FROM departments"))).scalar()
            print(f"Depts after: count={dept_count_after}, distinct={dept_distinct_after}")
            assert dept_count_after == 33
            assert dept_distinct_after == 33

            print("\n=== EXECUTING MUNICIPALITIES INSERT ===")
            muni_sql = """
            WITH ranked_munis AS (
                SELECT 
                    municipality_code,
                    department_code,
                    municipality_name,
                    count(*) as cnt,
                    ROW_NUMBER() OVER(PARTITION BY municipality_code ORDER BY count(*) DESC, municipality_name ASC) as rn
                FROM official_institution_catalog
                GROUP BY municipality_code, department_code, municipality_name
            )
            INSERT INTO municipalities (id, department_id, code, name)
            SELECT 
                gen_random_uuid(),
                d.id,
                rm.municipality_code,
                rm.municipality_name
            FROM ranked_munis rm
            JOIN departments d ON d.code = rm.department_code
            WHERE rm.rn = 1
            ON CONFLICT (code) DO NOTHING;
            """
            await conn.execute(text(muni_sql))

            muni_count_after = (await conn.execute(text("SELECT count(*) FROM municipalities"))).scalar()
            muni_distinct_after = (await conn.execute(text("SELECT count(distinct code) FROM municipalities"))).scalar()
            print(f"Munis after: count={muni_count_after}, distinct={muni_distinct_after}")
            assert muni_count_after == 1119
            assert muni_distinct_after == 1119

            print("\n=== VERIFYING INTEGRITY & ZERO REGRESSIONS ===")
            # 1. Existing department IDs preserved
            dept_ids_after = {r[0]: str(r[1]) for r in (await conn.execute(text("SELECT code, id FROM departments"))).all()}
            for code, orig_id in dept_ids_before.items():
                assert dept_ids_after[code] == orig_id, f"Dept {code} ID changed from {orig_id} to {dept_ids_after[code]}"
            print("  ✓ Existing 3 pilot department UUIDs preserved exactly.")

            # 2. Existing municipality IDs and department_id preserved
            muni_ids_after = {r[0]: (str(r[1]), str(r[2])) for r in (await conn.execute(text("SELECT code, id, department_id FROM municipalities"))).all()}
            for code, (orig_id, orig_dept_id) in muni_ids_before.items():
                curr_id, curr_dept_id = muni_ids_after[code]
                assert curr_id == orig_id, f"Muni {code} ID changed from {orig_id} to {curr_id}"
                assert curr_dept_id == orig_dept_id, f"Muni {code} DeptID changed from {orig_dept_id} to {curr_dept_id}"
            print("  ✓ Existing 3 pilot municipality UUIDs and department FKs preserved exactly.")

            # 3. Orphan municipalities check
            orphans = (await conn.execute(text("SELECT count(*) FROM municipalities m LEFT JOIN departments d ON m.department_id = d.id WHERE d.id IS NULL"))).scalar()
            assert orphans == 0, f"Found {orphans} orphan municipalities!"
            print("  ✓ Zero orphan municipalities.")

            # 4. Check institutions count
            inst_count_after = (await conn.execute(text("SELECT count(*) FROM institutions"))).scalar()
            assert inst_count_after == inst_count_before, f"Institutions count changed from {inst_count_before} to {inst_count_after}"
            print("  ✓ Total institutions preserved (34).")

            # 5. Check campuses count
            camp_count_after = (await conn.execute(text("SELECT count(*) FROM campuses"))).scalar()
            assert camp_count_after == camp_count_before, f"Campuses count changed from {camp_count_before} to {camp_count_after}"
            print("  ✓ Total campuses preserved (18).")

            # 6. Check users and user_roles
            user_count_after = (await conn.execute(text("SELECT count(*) FROM users"))).scalar()
            ur_count_after = (await conn.execute(text("SELECT count(*) FROM user_roles"))).scalar()
            assert user_count_after == user_count_before
            assert ur_count_after == ur_count_before
            print("  ✓ Total users and user_roles preserved.")

            print("\nALL VERIFICATIONS PASSED IN DRY-RUN TRANSACTION!")
        finally:
            await trans.rollback()
            print("=== TRANSACTION ROLLED BACK (Database remains pristine) ===")

if __name__ == "__main__":
    asyncio.run(test_migration())
