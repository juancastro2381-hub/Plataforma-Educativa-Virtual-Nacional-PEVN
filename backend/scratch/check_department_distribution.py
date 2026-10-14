import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DB_URL = get_safe_test_db_url()

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        print("=== ALL DEPARTMENT_ADMIN USERS IN DATABASE ===")
        res = await conn.execute(text("""
            SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active,
                   ur.department_id, d.code as dept_code, d.name as dept_name, u.created_at
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN departments d ON ur.department_id = d.id
            WHERE r.name = 'department_admin'
            ORDER BY u.created_at ASC;
        """))
        rows = res.fetchall()
        for idx, r in enumerate(rows, 1):
            print(f"{idx:02d}. {str(r.id)[:8]} | {r.username.ljust(28)} | {(r.first_name + ' ' + r.last_name).ljust(30)} | active={str(r.is_active).ljust(5)} | dept={str(r.dept_code).ljust(4)} ({str(r.dept_name).ljust(22)}) | {r.created_at}")

        print("\n=== DEPARTMENT DISTRIBUTION BREAKDOWN ===")
        dist_res = await conn.execute(text("""
            SELECT 
                COALESCE(d.code, 'NO_DEPT') as dept_code,
                COALESCE(d.name, 'SIN ASIGNACION DEPARTAMENTAL') as dept_name,
                count(u.id) as total,
                sum(case when u.is_active then 1 else 0 end) as active,
                sum(case when not u.is_active then 1 else 0 end) as inactive
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN departments d ON ur.department_id = d.id
            WHERE r.name = 'department_admin'
            GROUP BY d.code, d.name
            ORDER BY d.code;
        """))
        dist_rows = dist_res.fetchall()
        print(f"{'DANE'.ljust(8)} | {'Departamento'.ljust(30)} | {'Total'.rjust(6)} | {'Activos'.rjust(8)} | {'Inactivos'.rjust(10)} | {'Total == Act+Inact'}")
        print("-" * 85)
        for dr in dist_rows:
            valid = (dr.total == (dr.active + dr.inactive))
            print(f"{dr.dept_code.ljust(8)} | {dr.dept_name.ljust(30)} | {str(dr.total).rjust(6)} | {str(dr.active).rjust(8)} | {str(dr.inactive).rjust(10)} | {valid}")

        print("\n=== DISTINCT DEPARTMENTS WITH >= 1 DEPARTMENT_ADMIN ===")
        distinct_depts = await conn.execute(text("""
            SELECT count(DISTINCT ur.department_id)
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = 'department_admin' AND ur.department_id IS NOT NULL;
        """))
        print("Distinct provisioned departments count:", distinct_depts.scalar())

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
