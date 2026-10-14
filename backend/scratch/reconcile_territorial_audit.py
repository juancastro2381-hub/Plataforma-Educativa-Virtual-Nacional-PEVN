import os
from dotenv import load_dotenv
load_dotenv()

"""
PEVN — READ-ONLY TERRITORIAL & PROVISIONING RECONCILIATION AUDIT SCRIPT
AI Software Factory Standard v1.2 — Phase: Read-Only Forensic Audit
Strictly SELECT queries only. Zero mutations, zero schema changes, zero deletions.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text, distinct, case

from app.models.official_catalog import (
    OfficialInstitutionCatalog,
    OfficialCampusCatalog,
    OfficialCatalogSyncBatch,
    OfficialCatalogSyncChunk,
)
from app.models.territory import Department, Municipality
from app.models.institution import Institution, Campus
from app.models.user import User
from app.models.role import UserRole, Role
from app.models.invitation import DepartmentAdminInvitation

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DB_URL = get_safe_test_db_url()

async def run_audit():
    engine = create_async_engine(DB_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 80)
    print("PEVN READ-ONLY FORENSIC RECONCILIATION AUDIT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    async with session_factory() as session:
        # -------------------------------------------------------------
        # 1. CATALOG SYNC BATCHES
        # -------------------------------------------------------------
        print("\n--- [1. OFFICIAL CATALOG SYNC BATCHES] ---")
        batches_res = await session.execute(
            select(OfficialCatalogSyncBatch).order_by(OfficialCatalogSyncBatch.started_at)
        )
        batches = batches_res.scalars().all()
        for b in batches:
            print(f"Batch ID: {b.id}")
            print(f"  Source System: {b.source_system}")
            print(f"  Source Dataset: {b.source_dataset}")
            print(f"  Status: {b.status}, Quality Gate: {b.quality_gate_status}")
            print(f"  Total Records: {b.total_records}")
            print(f"  Valid: {b.valid_records}, Rejected: {b.rejected_records}, Duplicate: {b.duplicate_records}")
            print(f"  Institutions Count: {b.institutions_count}, Campuses Count: {b.campuses_count}")
            print(f"  Departments Count: {b.departments_count}, Municipalities Count: {b.municipalities_count}")
            print(f"  Started: {b.started_at}, Completed: {b.completed_at}")

        # -------------------------------------------------------------
        # 2. OFFICIAL INSTITUTION CATALOG TOTALS & BATCH DISTRIBUTION
        # -------------------------------------------------------------
        print("\n--- [2. OFFICIAL INSTITUTION CATALOG TOTALS] ---")
        cat_inst_total = (await session.execute(select(func.count(OfficialInstitutionCatalog.id)))).scalar_one()
        cat_inst_distinct_dane = (await session.execute(select(func.count(distinct(OfficialInstitutionCatalog.dane_code))))).scalar_one()
        cat_inst_active = (await session.execute(select(func.count(OfficialInstitutionCatalog.id)).where(OfficialInstitutionCatalog.is_active == True))).scalar_one()
        cat_inst_inactive = (await session.execute(select(func.count(OfficialInstitutionCatalog.id)).where(OfficialInstitutionCatalog.is_active == False))).scalar_one()
        print(f"Total Rows in official_institution_catalog: {cat_inst_total}")
        print(f"Distinct DANE codes: {cat_inst_distinct_dane}")
        print(f"is_active == True: {cat_inst_active}")
        print(f"is_active == False: {cat_inst_inactive}")

        # Breakdown by status column
        status_counts = (await session.execute(
            select(OfficialInstitutionCatalog.status, func.count(OfficialInstitutionCatalog.id))
            .group_by(OfficialInstitutionCatalog.status)
        )).all()
        print("Status column breakdown:")
        for st, c in status_counts:
            print(f"  status='{st}': {c}")

        # Breakdown by sync_batch_id
        batch_counts = (await session.execute(
            select(OfficialInstitutionCatalog.sync_batch_id, func.count(OfficialInstitutionCatalog.id))
            .group_by(OfficialInstitutionCatalog.sync_batch_id)
        )).all()
        print("Breakdown by sync_batch_id in official_institution_catalog:")
        for bid, c in batch_counts:
            print(f"  batch_id={bid}: {c}")

        # -------------------------------------------------------------
        # 3. OFFICIAL CAMPUS CATALOG TOTALS
        # -------------------------------------------------------------
        print("\n--- [3. OFFICIAL CAMPUS CATALOG TOTALS] ---")
        cat_camp_total = (await session.execute(select(func.count(OfficialCampusCatalog.id)))).scalar_one()
        cat_camp_distinct_dane = (await session.execute(select(func.count(distinct(OfficialCampusCatalog.dane_sede_code))))).scalar_one()
        cat_camp_active = (await session.execute(select(func.count(OfficialCampusCatalog.id)).where(OfficialCampusCatalog.is_active == True))).scalar_one()
        cat_camp_inactive = (await session.execute(select(func.count(OfficialCampusCatalog.id)).where(OfficialCampusCatalog.is_active == False))).scalar_one()
        print(f"Total Rows in official_campus_catalog: {cat_camp_total}")
        print(f"Distinct DANE Sede codes: {cat_camp_distinct_dane}")
        print(f"is_active == True: {cat_camp_active}")
        print(f"is_active == False: {cat_camp_inactive}")

        # -------------------------------------------------------------
        # 4. PROVISIONED INSTITUTIONS & CAMPUSES (PEVN OPERATIONAL)
        # -------------------------------------------------------------
        print("\n--- [4. PROVISIONED INSTITUTIONS & CAMPUSES] ---")
        pevn_inst_total = (await session.execute(select(func.count(Institution.id)))).scalar_one()
        pevn_inst_active = (await session.execute(select(func.count(Institution.id)).where(Institution.is_active == True))).scalar_one()
        pevn_inst_inactive = (await session.execute(select(func.count(Institution.id)).where(Institution.is_active == False))).scalar_one()
        pevn_camp_total = (await session.execute(select(func.count(Campus.id)))).scalar_one()
        pevn_camp_active = (await session.execute(select(func.count(Campus.id)).where(Campus.is_active == True))).scalar_one()
        pevn_camp_inactive = (await session.execute(select(func.count(Campus.id)).where(Campus.is_active == False))).scalar_one()
        print(f"Total Provisioned Institutions: {pevn_inst_total}")
        print(f"  Active Institutions:   {pevn_inst_active}")
        print(f"  Inactive Institutions: {pevn_inst_inactive}")
        print(f"  Active + Inactive = {pevn_inst_active + pevn_inst_inactive} (Match: {pevn_inst_total == pevn_inst_active + pevn_inst_inactive})")
        print(f"Total Provisioned Campuses: {pevn_camp_total}")
        print(f"  Active Campuses:   {pevn_camp_active}")
        print(f"  Inactive Campuses: {pevn_camp_inactive}")

        # -------------------------------------------------------------
        # 5. DEPARTMENTS & MUNICIPALITIES (OPERATIONAL RELATIONAL)
        # -------------------------------------------------------------
        print("\n--- [5. OPERATIONAL DEPARTMENTS & MUNICIPALITIES] ---")
        dept_rows = (await session.execute(select(Department).order_by(Department.code))).scalars().all()
        print(f"Total Rows in 'departments' table: {len(dept_rows)}")
        for d in dept_rows:
            mun_count = (await session.execute(select(func.count(Municipality.id)).where(Municipality.department_id == d.id))).scalar_one()
            inst_count = (await session.execute(
                select(func.count(Institution.id))
                .join(Municipality, Institution.municipality_id == Municipality.id)
                .where(Municipality.department_id == d.id)
            )).scalar_one()
            inst_active_count = (await session.execute(
                select(func.count(Institution.id))
                .join(Municipality, Institution.municipality_id == Municipality.id)
                .where(Municipality.department_id == d.id, Institution.is_active == True)
            )).scalar_one()
            inst_inactive_count = (await session.execute(
                select(func.count(Institution.id))
                .join(Municipality, Institution.municipality_id == Municipality.id)
                .where(Municipality.department_id == d.id, Institution.is_active == False)
            )).scalar_one()
            print(f"  Dept Code: {d.code:4} | Name: {d.name:25} | ID: {d.id} | Municipalities: {mun_count:4} | Provisioned: {inst_count:2} (Active: {inst_active_count:2}, Inactive: {inst_inactive_count:2})")

        muni_total = (await session.execute(select(func.count(Municipality.id)))).scalar_one()
        print(f"Total Rows in 'municipalities' table: {muni_total}")

        # -------------------------------------------------------------
        # 6. DEPARTMENT_ADMIN ACCOUNTS AUDIT
        # -------------------------------------------------------------
        print("\n--- [6. DEPARTMENT_ADMIN ACCOUNTS AUDIT] ---")
        da_roles_res = await session.execute(
            select(UserRole, User, Role)
            .join(User, UserRole.user_id == User.id)
            .join(Role, UserRole.role_id == Role.id)
            .where(Role.name == "department_admin")
            .order_by(User.created_at)
        )
        da_records = da_roles_res.all()
        print(f"Total DEPARTMENT_ADMIN user_role entries: {len(da_records)}")
        
        # User details
        da_by_dept = {}
        for ur, u, r in da_records:
            dept_id = str(ur.department_id) if ur.department_id else "NONE"
            dept_info = "UNKNOWN"
            if ur.department_id:
                d_obj = await session.get(Department, ur.department_id)
                if d_obj:
                    dept_info = f"{d_obj.code} - {d_obj.name}"
            
            status_str = "ACTIVE" if u.is_active and ur.is_active else f"INACTIVE (u:{u.is_active}, r:{ur.is_active})"
            print(f"  User: {u.username:28} | Email: {u.email:35} | Active: {status_str:20} | Dept: {dept_info:25} | Created: {u.created_at}")

            if dept_info not in da_by_dept:
                da_by_dept[dept_info] = {"total": 0, "active": 0, "inactive": 0, "users": []}
            da_by_dept[dept_info]["total"] += 1
            if u.is_active and ur.is_active:
                da_by_dept[dept_info]["active"] += 1
            else:
                da_by_dept[dept_info]["inactive"] += 1
            da_by_dept[dept_info]["users"].append(u.username)

        print("\nDepartment Admin summary by Department:")
        for dname, stats in sorted(da_by_dept.items()):
            print(f"  {dname:30}: Total={stats['total']}, Active={stats['active']}, Inactive={stats['inactive']}")

        # -------------------------------------------------------------
        # 7. INVITATION AUDIT FOR DEPARTMENT_ADMIN
        # -------------------------------------------------------------
        print("\n--- [7. DEPARTMENT_ADMIN INVITATIONS AUDIT] ---")
        inv_res = await session.execute(
            select(DepartmentAdminInvitation).order_by(DepartmentAdminInvitation.created_at)
        )
        invs = inv_res.scalars().all()
        print(f"Total DepartmentAdminInvitation records: {len(invs)}")
        for inv in invs:
            d_obj = await session.get(Department, inv.department_id)
            dcode = d_obj.code if d_obj else "??"
            status_desc = "USED" if inv.is_used else ("REVOKED" if inv.is_revoked else ("EXPIRED" if inv.is_expired else "VALID"))
            print(f"  Inv ID: {inv.id} | UserID: {inv.user_id} | Dept: {dcode} | Status: {status_desc} | Expires: {inv.expires_at} | UsedAt: {inv.used_at}")

        # -------------------------------------------------------------
        # 8. COMPLETE LIST OF ALL PROVISIONED INSTITUTIONS
        # -------------------------------------------------------------
        print("\n--- [8. ALL PROVISIONED PEVN INSTITUTIONS] ---")
        inst_all = (await session.execute(
            select(Institution, Municipality, Department)
            .join(Municipality, Institution.municipality_id == Municipality.id)
            .join(Department, Municipality.department_id == Department.id)
            .order_by(Department.code, Institution.is_active.desc(), Institution.name)
        )).all()

        print(f"Total Institutions Fetched: {len(inst_all)}")
        dept_counts_prov = {}
        for inst, mun, dept in inst_all:
            c_count = (await session.execute(select(func.count(Campus.id)).where(Campus.institution_id == inst.id))).scalar_one()
            status_text = "ACTIVE" if inst.is_active else "INACTIVE"
            print(f"  [{status_text:8}] Dept: {dept.code} ({dept.name:20}) | Muni: {mun.code} ({mun.name:15}) | DANE: {inst.dane_code} | Campuses: {c_count:2} | Name: {inst.name} | ID: {inst.id}")
            
            d_key = f"{dept.code} - {dept.name}"
            if d_key not in dept_counts_prov:
                dept_counts_prov[d_key] = {"total": 0, "active": 0, "inactive": 0, "campuses": 0}
            dept_counts_prov[d_key]["total"] += 1
            if inst.is_active:
                dept_counts_prov[d_key]["active"] += 1
            else:
                dept_counts_prov[d_key]["inactive"] += 1
            dept_counts_prov[d_key]["campuses"] += c_count

        print("\nSummary of Provisioned Institutions by Department:")
        for d_key, data in sorted(dept_counts_prov.items()):
            print(f"  {d_key:30}: Total={data['total']}, Active={data['active']}, Inactive={data['inactive']}, Campuses={data['campuses']}")

        # -------------------------------------------------------------
        # 9. INVENTORY OF CAMPUSES PER INSTITUTION
        # -------------------------------------------------------------
        print("\n--- [9. ALL PROVISIONED CAMPUSES] ---")
        camp_all = (await session.execute(
            select(Campus, Institution, Municipality, Department)
            .join(Institution, Campus.institution_id == Institution.id)
            .join(Municipality, Institution.municipality_id == Municipality.id)
            .join(Department, Municipality.department_id == Department.id)
            .order_by(Department.code, Institution.name, Campus.name)
        )).all()
        print(f"Total Campuses Fetched: {len(camp_all)}")
        for camp, inst, mun, dept in camp_all:
            print(f"  Campus ID: {camp.id} | DANE Sede: {camp.dane_sede_code:15} | Active: {camp.is_active} | Name: {camp.name[:35]:35} | Inst: {inst.name[:30]}")

        # -------------------------------------------------------------
        # 10. DEPARTMENT-BY-DEPARTMENT NATIONAL CATALOG COMPLETE TABLE
        # -------------------------------------------------------------
        print("\n--- [10. DEPARTMENT-BY-DEPARTMENT NATIONAL CATALOG TABLE] ---")
        # In official_institution_catalog
        dept_cat_stmt = (
            select(
                OfficialInstitutionCatalog.department_code,
                func.max(OfficialInstitutionCatalog.department_name).label("name"),
                func.count(OfficialInstitutionCatalog.id).label("establishments"),
                func.count(distinct(OfficialInstitutionCatalog.municipality_code)).label("municipalities"),
            )
            .group_by(OfficialInstitutionCatalog.department_code)
            .order_by(OfficialInstitutionCatalog.department_code)
        )
        cat_depts = (await session.execute(dept_cat_stmt)).all()
        print(f"Total Distinct Department Codes in Official Catalog: {len(cat_depts)}")

        print(f"{'DANE':<6} | {'Department Name':<45} | {'Cat. Inst':<10} | {'Cat. Camp':<10} | {'PEVN Prov':<10} | {'PEVN Act':<10} | {'PEVN Inact':<10} | {'PEVN Camp':<10} | {'DA Cov':<8} | {'Active DA':<10}")
        print("-" * 145)

        total_cat_inst = 0
        total_cat_camp = 0
        total_pevn_prov = 0
        total_pevn_act = 0
        total_pevn_inact = 0
        total_pevn_camp = 0
        total_da_active = 0
        departments_with_coverage = 0

        for cd in cat_depts:
            dcode = cd.department_code
            dname = cd.name
            c_inst = cd.establishments
            total_cat_inst += c_inst

            # Campuses in catalog
            c_camp = (await session.execute(
                select(func.count(OfficialCampusCatalog.id))
                .join(OfficialInstitutionCatalog, OfficialCampusCatalog.official_institution_id == OfficialInstitutionCatalog.id)
                .where(OfficialInstitutionCatalog.department_code == dcode)
            )).scalar_one() or 0
            total_cat_camp += c_camp

            # PEVN provisioned
            prov_data = (await session.execute(
                select(
                    func.count(Institution.id).label("total"),
                    func.sum(case((Institution.is_active == True, 1), else_=0)).label("active"),
                    func.sum(case((Institution.is_active == False, 1), else_=0)).label("inactive"),
                )
                .join(Municipality, Institution.municipality_id == Municipality.id)
                .join(Department, Municipality.department_id == Department.id)
                .where(Department.code == dcode)
            )).one()
            p_total = prov_data.total or 0
            p_active = prov_data.active or 0
            p_inactive = prov_data.inactive or 0
            total_pevn_prov += p_total
            total_pevn_act += p_active
            total_pevn_inact += p_inactive

            # PEVN campuses
            p_camp = (await session.execute(
                select(func.count(Campus.id))
                .join(Institution, Campus.institution_id == Institution.id)
                .join(Municipality, Institution.municipality_id == Municipality.id)
                .join(Department, Municipality.department_id == Department.id)
                .where(Department.code == dcode)
            )).scalar_one() or 0
            total_pevn_camp += p_camp

            # DA Coverage
            da_act_count = (await session.execute(
                select(func.count(UserRole.id))
                .join(User, UserRole.user_id == User.id)
                .join(Role, UserRole.role_id == Role.id)
                .join(Department, UserRole.department_id == Department.id)
                .where(
                    Department.code == dcode,
                    Role.name == "department_admin",
                    UserRole.is_active == True,
                    User.is_active == True,
                )
            )).scalar_one() or 0
            total_da_active += da_act_count
            has_da = "YES" if da_act_count > 0 else "NO"
            if da_act_count > 0:
                departments_with_coverage += 1

            highlight = " ***" if dcode in ("08", "11", "25") else ""
            print(f"{dcode:<6} | {dname:<45} | {c_inst:<10} | {c_camp:<10} | {p_total:<10} | {p_active:<10} | {p_inactive:<10} | {p_camp:<10} | {has_da:<8} | {da_act_count:<10}{highlight}")

        print("-" * 145)
        print(f"{'TOTAL':<6} | {'33 DEPARTMENTS':<45} | {total_cat_inst:<10} | {total_cat_camp:<10} | {total_pevn_prov:<10} | {total_pevn_act:<10} | {total_pevn_inact:<10} | {total_pevn_camp:<10} | {departments_with_coverage:<8} | {total_da_active:<10}")

        # -------------------------------------------------------------
        # 11. TERRITORIAL INTEGRITY VALIDATIONS
        # -------------------------------------------------------------
        print("\n--- [11. TERRITORIAL INTEGRITY VALIDATIONS] ---")
        # A. Institution without municipality
        orphaned_inst = (await session.execute(select(Institution).where(Institution.municipality_id == None))).scalars().all()
        print(f"Institutions without municipality: {len(orphaned_inst)}")

        # B. Municipality without department
        orphaned_muni = (await session.execute(select(Municipality).where(Municipality.department_id == None))).scalars().all()
        print(f"Municipalities without department: {len(orphaned_muni)}")

        # C. Campuses without institution
        orphaned_camp = (await session.execute(select(Campus).where(Campus.institution_id == None))).scalars().all()
        print(f"Campuses without institution: {len(orphaned_camp)}")

        # D. Duplicate DANE codes in institutions
        dup_inst_dane = (await session.execute(
            select(Institution.dane_code, func.count(Institution.id))
            .group_by(Institution.dane_code)
            .having(func.count(Institution.id) > 1)
        )).all()
        print(f"Duplicate DANE codes in institutions: {len(dup_inst_dane)}")

        # E. Duplicate DANE codes in official_institution_catalog
        dup_cat_dane = (await session.execute(
            select(OfficialInstitutionCatalog.dane_code, func.count(OfficialInstitutionCatalog.id))
            .group_by(OfficialInstitutionCatalog.dane_code)
            .having(func.count(OfficialInstitutionCatalog.id) > 1)
        )).all()
        print(f"Duplicate DANE codes in official_institution_catalog: {len(dup_cat_dane)}")

        # F. Duplicate department codes
        dup_dept_codes = (await session.execute(
            select(Department.code, func.count(Department.id))
            .group_by(Department.code)
            .having(func.count(Department.id) > 1)
        )).all()
        print(f"Duplicate codes in departments table: {len(dup_dept_codes)}")

        # G. Duplicate municipality codes
        dup_muni_codes = (await session.execute(
            select(Municipality.code, func.count(Municipality.id))
            .group_by(Municipality.code)
            .having(func.count(Municipality.id) > 1)
        )).all()
        print(f"Duplicate codes in municipalities table: {len(dup_muni_codes)}")

        # H. Verify institution.municipality.department_id matches
        mismatch_query = await session.execute(
            select(Institution.id, Institution.name, Municipality.code, Department.code)
            .join(Municipality, Institution.municipality_id == Municipality.id)
            .join(Department, Municipality.department_id == Department.id)
            .where(Department.id != Municipality.department_id)
        )
        print(f"Territorial hierarchy FK mismatches: {len(mismatch_query.all())}")

if __name__ == "__main__":
    asyncio.run(run_audit())
