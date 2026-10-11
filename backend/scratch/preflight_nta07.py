"""
PEVN Backend — Preflight Inspection for NTA-07: MUNICIPALITY_ADMIN RBAC Implementation
Performs automated inspection of the current database and codebase state.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from sqlalchemy import text
from app.db.session import get_session_factory
from app.services.rbac_bootstrap_service import (
    CANONICAL_ROLES,
    CANONICAL_PERMISSIONS,
    ROLE_PERMISSIONS_CONFIG,
)
from app.core.security.interfaces import SystemRole, OrganizationalScope
from app.core.security.authorization import scope_contains

async def run_preflight():
    print("=" * 80)
    print("PEVN — NTA-07 PREFLIGHT INSPECTION REPORT")
    print("=" * 80)

    # 1. Inspect Canonical RBAC in code
    print("\n--- 1. CANONICAL ROLES IN CODE ---")
    for r in CANONICAL_ROLES:
        print(f"  Role: {r['name']:<22} Level: {r['level']:<4} Display: {r['display_name']}")
    print(f"Total Canonical Roles Defined: {len(CANONICAL_ROLES)}")

    # 2. Inspect Permissions for MUNICIPALITY_ADMIN vs DEPARTMENT_ADMIN
    print("\n--- 2. PERMISSIONS IN CODE ---")
    dept_perms = ROLE_PERMISSIONS_CONFIG.get(SystemRole.DEPARTMENT_ADMIN.value, [])
    muni_perms = ROLE_PERMISSIONS_CONFIG.get(SystemRole.MUNICIPALITY_ADMIN.value, [])
    print(f"DEPARTMENT_ADMIN permissions count: {len(dept_perms)}")
    print(f"MUNICIPALITY_ADMIN permissions count: {len(muni_perms)}")
    print(f"Are permissions identical?: {set(dept_perms) == set(muni_perms)}")
    print(f"MUNICIPALITY_ADMIN permissions list: {muni_perms}")

    # 3. Database inspection
    session_maker = get_session_factory()
    async with session_maker() as db:
        # Check roles table in DB
        roles_res = await db.execute(text("SELECT name, display_name, level FROM roles ORDER BY level DESC, name ASC;"))
        db_roles = roles_res.fetchall()
        print("\n--- 3. DATABASE ROLES TABLE ---")
        for r in db_roles:
            print(f"  DB Role: {r.name:<22} Level: {r.level:<4} Display: {r.display_name}")
        print(f"Total Roles in DB: {len(db_roles)}")

        # Check user_roles columns in DB
        cols_res = await db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_roles'
            ORDER BY ordinal_position;
        """))
        print("\n--- 4. USER_ROLES TABLE SCHEMA ---")
        for c in cols_res.fetchall():
            print(f"  Column: {c.column_name:<20} Type: {c.data_type:<20} Nullable: {c.is_nullable}")

        # Check departments & municipalities count
        dept_cnt = (await db.execute(text("SELECT count(*) FROM departments;"))).scalar()
        muni_cnt = (await db.execute(text("SELECT count(*) FROM municipalities;"))).scalar()
        inst_cnt = (await db.execute(text("SELECT count(*) FROM institutions;"))).scalar()
        users_cnt = (await db.execute(text("SELECT count(*) FROM users;"))).scalar()
        print("\n--- 5. TERRITORIAL DATABASE ENTITIES ---")
        print(f"  Departments:    {dept_cnt}")
        print(f"  Municipalities: {muni_cnt}")
        print(f"  Institutions:   {inst_cnt}")
        print(f"  Users:          {users_cnt}")

        # Check municipalities in Bogotá (11001) and Antioquia/Medellín (05001)
        muni_samples = await db.execute(text("""
            SELECT m.id, m.code, m.name, d.code as dept_code, d.name as dept_name,
                   (SELECT count(*) FROM institutions i WHERE i.municipality_id = m.id) as inst_count
            FROM municipalities m
            JOIN departments d ON m.department_id = d.id
            WHERE m.code IN ('11001', '05001', '25269', '25899')
            ORDER BY m.code;
        """))
        print("\n--- 6. SAMPLE MUNICIPALITIES ---")
        for m in muni_samples.fetchall():
            print(f"  Muni: {m.code} - {m.name:<20} Dept: {m.dept_code} - {m.dept_name:<20} Institutions: {m.inst_count} (ID: {m.id})")

        # Check existing department_admin accounts
        dept_admins = await db.execute(text("""
            SELECT u.username, u.email, u.is_active, r.name as role_name, ur.department_id, d.code as dept_code, d.name as dept_name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN departments d ON ur.department_id = d.id
            WHERE r.name = 'department_admin';
        """))
        print("\n--- 7. EXISTING DEPARTMENT_ADMIN ACCOUNTS ---")
        for da in dept_admins.fetchall():
            print(f"  User: {da.username:<20} Dept: {da.dept_code or 'None':<5} {da.dept_name or 'None':<20} Active: {da.is_active}")

        # Check existing municipality_admin accounts
        muni_admins = await db.execute(text("""
            SELECT u.username, u.email, u.is_active, r.name as role_name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'municipality_admin';
        """))
        print("\n--- 8. EXISTING MUNICIPALITY_ADMIN ACCOUNTS ---")
        rows = muni_admins.fetchall()
        if not rows:
            print("  (None found)")
        for ma in rows:
            print(f"  User: {ma.username:<20} Active: {ma.is_active}")

        # Check Alembic current version
        alembic_res = await db.execute(text("SELECT version_num FROM alembic_version;"))
        print(f"\n--- 9. ALEMBIC VERSION IN DB ---")
        print(f"  Current DB revision: {alembic_res.scalar()}")

    print("\n" + "=" * 80)
    print("PREFLIGHT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_preflight())
