import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")

async def verify_nta03():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("=== NTA-03 POST-MIGRATION VERIFICATION ===")
        
        # 1. Total institutions
        total_inst = (await conn.execute(text("SELECT count(*) FROM institutions"))).scalar()
        active_inst = (await conn.execute(text("SELECT count(*) FROM institutions WHERE is_active = true"))).scalar()
        inactive_inst = (await conn.execute(text("SELECT count(*) FROM institutions WHERE is_active = false"))).scalar()
        print(f"Institutions: Total={total_inst}, Active={active_inst}, Inactive={inactive_inst}")
        assert total_inst == 34, f"Expected 34 institutions, got {total_inst}"
        assert active_inst == 31, f"Expected 31 active, got {active_inst}"
        assert inactive_inst == 3, f"Expected 3 inactive, got {inactive_inst}"
        
        # 2. Linked vs Null
        linked_count = (await conn.execute(text("SELECT count(*) FROM institutions WHERE catalog_institution_id IS NOT NULL"))).scalar()
        null_count = (await conn.execute(text("SELECT count(*) FROM institutions WHERE catalog_institution_id IS NULL"))).scalar()
        print(f"Linked institutions: {linked_count}")
        print(f"Null (synthetic) institutions: {null_count}")
        assert linked_count == 7, f"Expected 7 linked institutions, got {linked_count}"
        assert null_count == 27, f"Expected 27 null institutions, got {null_count}"
        
        # 3. Verify 100% DANE code consistency for linked institutions
        r_linked = await conn.execute(text("""
            SELECT 
                i.id AS inst_id,
                i.name AS inst_name,
                i.dane_code AS inst_dane,
                c.id AS cat_id,
                c.name AS cat_name,
                c.dane_code AS cat_dane,
                (i.dane_code = c.dane_code) AS dane_match
            FROM institutions i
            JOIN official_institution_catalog c ON i.catalog_institution_id = c.id
            ORDER BY i.dane_code
        """))
        linked_rows = r_linked.fetchall()
        print(f"\n--- Linked Institutions ({len(linked_rows)}) ---")
        for idx, row in enumerate(linked_rows, 1):
            print(f"{idx}. DANE: {row.inst_dane} | Inst: '{row.inst_name}' -> Cat: '{row.cat_name}' (Match: {row.dane_match})")
            assert row.dane_match is True, f"DANE code mismatch for {row.inst_name}"
            
        # 4. Verify unique partial index: No duplicate catalog_institution_id
        dup_check = await conn.execute(text("""
            SELECT catalog_institution_id, count(*)
            FROM institutions
            WHERE catalog_institution_id IS NOT NULL
            GROUP BY catalog_institution_id
            HAVING count(*) > 1
        """))
        dups = dup_check.fetchall()
        assert len(dups) == 0, f"Found duplicate catalog references: {dups}"
        print("Duplicate catalog references: 0 (PASS)")
        
        # 5. Check baseline entities
        camp_count = (await conn.execute(text("SELECT count(*) FROM campuses"))).scalar()
        user_count = (await conn.execute(text("SELECT count(*) FROM users"))).scalar()
        da_count = (await conn.execute(text("SELECT count(*) FROM user_roles WHERE role_id = (SELECT id FROM roles WHERE name = 'department_admin') AND department_id IS NOT NULL"))).scalar()
        dept_count = (await conn.execute(text("SELECT count(*) FROM departments"))).scalar()
        muni_count = (await conn.execute(text("SELECT count(*) FROM municipalities"))).scalar()
        
        print(f"\nBaseline Verification:")
        print(f"Campuses: {camp_count} (Expected 18)")
        print(f"Users: {user_count} (Expected 200)")
        print(f"Scoped Department Admins: {da_count} (Expected 10)")
        print(f"Departments: {dept_count} (Expected 33)")
        print(f"Municipalities: {muni_count} (Expected 1119)")
        
        assert camp_count == 18
        assert user_count == 200
        assert da_count == 10
        assert dept_count == 33
        assert muni_count == 1119
        
        # 6. Test foreign key and partial unique index constraints in transaction rollback
        print("\nTesting DB constraints...")
        sample_cat_id = linked_rows[0].cat_id
        dummy_inst_id = uuid.uuid4()
        muni_id = (await conn.execute(text("SELECT id FROM municipalities LIMIT 1"))).scalar()

    # A. Unique partial index test: duplicate catalog_id must fail
    async with engine.connect() as test_conn:
        trans = await test_conn.begin()
        failed_dup = False
        try:
            await test_conn.execute(text(f"""
                INSERT INTO institutions (id, municipality_id, dane_code, name, email, catalog_institution_id)
                VALUES ('{dummy_inst_id}', '{muni_id}', '999999999999', 'Duplicate Test', 'dup@test.com', '{sample_cat_id}')
            """))
        except Exception as e:
            failed_dup = True
            print(f"Duplicate catalog_institution_id correctly rejected: {type(e).__name__}")
        await trans.rollback()
        assert failed_dup, "Unique partial index did NOT reject duplicate catalog_institution_id!"

    # B. FK constraint test: non-existent catalog_id must fail
    async with engine.connect() as test_conn:
        trans = await test_conn.begin()
        fake_cat_id = uuid.uuid4()
        failed_fk = False
        try:
            await test_conn.execute(text(f"""
                INSERT INTO institutions (id, municipality_id, dane_code, name, email, catalog_institution_id)
                VALUES ('{dummy_inst_id}', '{muni_id}', '999999999999', 'FK Test', 'fk@test.com', '{fake_cat_id}')
            """))
        except Exception as e:
            failed_fk = True
            print(f"Invalid catalog_institution_id FK correctly rejected: {type(e).__name__}")
        await trans.rollback()
        assert failed_fk, "Foreign key did NOT reject invalid catalog_institution_id!"

    print("\nALL POST-MIGRATION INVARIANTS CERTIFIED PASS!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_nta03())
