"""
PEVN — NTA-02 Post-Migration Forensic Reconciliation Script
Verifies all database invariants, territorial distributions, tenant preservation,
and structural integrity after applying migration 026.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"
engine = create_async_engine(DB_URL, echo=False)

PILOT_DEPT_UUIDS = {
    "08": "caf3cc3f-a895-4fcd-b4b9-17405f3edf76",
    "11": "7b774116-56f1-4199-ac63-ff646e7e327b",
    "25": "9aea113f-54e2-4345-8cc6-46970a91c7c6",
}

PILOT_MUNI_UUIDS = {
    "08001": "709359d8-4c2f-4d90-be5d-2140a5ff458e",
    "11001": "75495d0b-e2f0-4d1b-9114-02589135a863",
    "25286": "63d46e72-6f03-4785-a2f0-4becf6a56134",
}

async def run_reconciliation():
    async with engine.connect() as conn:
        print("============================================================")
        print("PEVN NTA-02 POST-MIGRATION FORENSIC RECONCILIATION")
        print("============================================================")

        # 1. Territorial counts
        dept_count = (await conn.execute(text("SELECT count(*) FROM departments"))).scalar()
        dept_distinct = (await conn.execute(text("SELECT count(distinct code) FROM departments"))).scalar()
        muni_count = (await conn.execute(text("SELECT count(*) FROM municipalities"))).scalar()
        muni_distinct = (await conn.execute(text("SELECT count(distinct code) FROM municipalities"))).scalar()

        print(f"\n1. TERRITORIAL COUNTS:")
        print(f"  Departments: {dept_count} (Distinct codes: {dept_distinct})")
        print(f"  Municipalities: {muni_count} (Distinct codes: {muni_distinct})")
        assert dept_count == 33, f"Expected 33 departments, got {dept_count}"
        assert dept_distinct == 33, f"Expected 33 distinct department codes, got {dept_distinct}"
        assert muni_count == 1119, f"Expected 1119 municipalities, got {muni_count}"
        assert muni_distinct == 1119, f"Expected 1119 distinct municipality codes, got {muni_distinct}"

        # 2. Pilot UUID preservation
        print(f"\n2. PILOT UUID PRESERVATION:")
        depts_current = {r[0]: str(r[1]) for r in (await conn.execute(text("SELECT code, id FROM departments WHERE code IN ('08', '11', '25')"))).all()}
        for code, expected_uuid in PILOT_DEPT_UUIDS.items():
            actual_uuid = depts_current.get(code)
            assert actual_uuid == expected_uuid, f"Dept {code} UUID mismatch: expected {expected_uuid}, got {actual_uuid}"
            print(f"  Dept {code}: UUID {actual_uuid} [PRESERVED: MATCH]")

        munis_current = {r[0]: str(r[1]) for r in (await conn.execute(text("SELECT code, id FROM municipalities WHERE code IN ('08001', '11001', '25286')"))).all()}
        for code, expected_uuid in PILOT_MUNI_UUIDS.items():
            actual_uuid = munis_current.get(code)
            assert actual_uuid == expected_uuid, f"Muni {code} UUID mismatch: expected {expected_uuid}, got {actual_uuid}"
            print(f"  Muni {code}: UUID {actual_uuid} [PRESERVED: MATCH]")

        # 3. Relational integrity & zero orphans
        print(f"\n3. RELATIONAL INTEGRITY:")
        orphan_munis = (await conn.execute(text("SELECT count(*) FROM municipalities m LEFT JOIN departments d ON m.department_id = d.id WHERE d.id IS NULL"))).scalar()
        print(f"  Orphan municipalities: {orphan_munis}")
        assert orphan_munis == 0

        null_dept_codes = (await conn.execute(text("SELECT count(*) FROM departments WHERE code IS NULL OR code = ''"))).scalar()
        null_muni_codes = (await conn.execute(text("SELECT count(*) FROM municipalities WHERE code IS NULL OR code = ''"))).scalar()
        null_muni_dept_ids = (await conn.execute(text("SELECT count(*) FROM municipalities WHERE department_id IS NULL"))).scalar()
        print(f"  Null department codes: {null_dept_codes}")
        print(f"  Null municipality codes: {null_muni_codes}")
        print(f"  Null municipality department_id: {null_muni_dept_ids}")
        assert null_dept_codes == 0
        assert null_muni_codes == 0
        assert null_muni_dept_ids == 0

        # 4. Tenant preservation
        print(f"\n4. TENANT PRESERVATION:")
        inst_total = (await conn.execute(text("SELECT count(*) FROM institutions"))).scalar()
        inst_active = (await conn.execute(text("SELECT count(*) FROM institutions WHERE is_active = true"))).scalar()
        inst_inactive = (await conn.execute(text("SELECT count(*) FROM institutions WHERE is_active = false"))).scalar()
        camp_total = (await conn.execute(text("SELECT count(*) FROM campuses"))).scalar()
        camp_active = (await conn.execute(text("SELECT count(*) FROM campuses WHERE is_active = true"))).scalar()
        user_total = (await conn.execute(text("SELECT count(*) FROM users"))).scalar()
        user_active = (await conn.execute(text("SELECT count(*) FROM users WHERE is_active = true"))).scalar()
        ur_total = (await conn.execute(text("SELECT count(*) FROM user_roles"))).scalar()
        da_scoped = (await conn.execute(text("SELECT count(*) FROM user_roles WHERE department_id IS NOT NULL"))).scalar()

        print(f"  Institutions total: {inst_total} (Active: {inst_active}, Inactive: {inst_inactive})")
        print(f"  Campuses total: {camp_total} (Active: {camp_active})")
        print(f"  Users total: {user_total} (Active: {user_active})")
        print(f"  UserRoles total: {ur_total} (Scoped DAs: {da_scoped})")
        assert inst_total == 34
        assert inst_active == 31
        assert inst_inactive == 3
        assert camp_total == 18
        assert camp_active == 18
        assert da_scoped == 10

        # 5. Invalid institution municipality FK check
        invalid_inst_munis = (await conn.execute(text("SELECT count(*) FROM institutions i LEFT JOIN municipalities m ON i.municipality_id = m.id WHERE m.id IS NULL"))).scalar()
        print(f"  Institutions with invalid municipality_id: {invalid_inst_munis}")
        assert invalid_inst_munis == 0

        # 6. Complete 33 departments breakdown
        print(f"\n5. COMPLETE 33-DEPARTMENT RECONCILIATION TABLE:")
        dept_summary_sql = """
        SELECT 
            d.code,
            d.name,
            count(distinct m.id) as total_munis,
            count(distinct i.id) as total_insts,
            count(distinct case when i.is_active = true then i.id end) as active_insts,
            count(distinct case when i.is_active = false then i.id end) as inactive_insts,
            count(distinct c.id) as total_campuses
        FROM departments d
        LEFT JOIN municipalities m ON m.department_id = d.id
        LEFT JOIN institutions i ON i.municipality_id = m.id
        LEFT JOIN campuses c ON c.institution_id = i.id
        GROUP BY d.code, d.name
        ORDER BY d.code;
        """
        rows = (await conn.execute(text(dept_summary_sql))).all()
        header = f"{'Código':<8} | {'Nombre Canónico':<40} | {'Municipios':<11} | {'Inst Tot':<9} | {'Activas':<8} | {'Inactivas':<9} | {'Sedes':<6}"
        print(header)
        print("-" * len(header))
        zero_tenant_depts = 0
        for r in rows:
            code, name, munis, insts, act, inact, sedes = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
            if insts == 0:
                zero_tenant_depts += 1
            print(f"{code:<8} | {name:<40} | {munis:<11} | {insts:<9} | {act:<8} | {inact:<9} | {sedes:<6}")

        print(f"\n  Departments with zero PEVN tenants: {zero_tenant_depts} / 33")
        assert zero_tenant_depts == 30, f"Expected 30 zero-tenant departments, got {zero_tenant_depts}"
        print("  ✓ Zero tenant invariant verified: exactly 30 departments have 0 tenants, while pilot territories retain their exact institutions.")

        print("\n============================================================")
        print("ALL POST-MIGRATION INVARIANTS CERTIFIED SUCCESSFULLY!")
        print("============================================================")

if __name__ == "__main__":
    asyncio.run(run_reconciliation())
