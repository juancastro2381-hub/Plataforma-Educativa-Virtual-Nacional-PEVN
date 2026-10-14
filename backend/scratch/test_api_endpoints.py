import os
from dotenv import load_dotenv
load_dotenv()

"""
Test API endpoints for NTA-02 territorial foundation
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security.tokens import token_service
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

try:
    from scratch._safe_db import get_safe_test_db_url
except ImportError:
    from _safe_db import get_safe_test_db_url

DB_URL = get_safe_test_db_url()
engine = create_async_engine(DB_URL, echo=False)

async def test_apis():
    async with engine.connect() as conn:
        # Get superadmin/national admin user ID
        na_user_id = (await conn.execute(text("""
            SELECT u.id FROM users u 
            JOIN user_roles ur ON u.id = ur.user_id 
            JOIN roles r ON ur.role_id = r.id 
            WHERE r.name IN ('superadmin', 'national_admin') AND u.is_active = true 
            LIMIT 1
        """))).scalar()
        print(f"National Admin User ID: {na_user_id}")

        # Get Atlántico Department Admin user ID
        da_atlantico_id = (await conn.execute(text("SELECT id FROM users WHERE username = 'Eduardo_Admin_Departamental'"))).scalar()
        print(f"Atlántico DA User ID: {da_atlantico_id}")

    # Generate tokens
    na_token = await token_service.create_access_token(subject=str(na_user_id))
    da_token = await token_service.create_access_token(subject=str(da_atlantico_id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        # 1. Test GET /api/v1/departments with NA token
        print("\n1. Testing GET /api/v1/departments ...")
        res_depts = await client.get("/api/v1/departments", headers={"Authorization": f"Bearer {na_token}"})
        print(f"Status: {res_depts.status_code}, Body: {res_depts.text}")
        assert res_depts.status_code == 200
        depts_data = res_depts.json()
        print(f"Total departments returned: {len(depts_data)}")
        assert len(depts_data) == 33
        
        dept_codes_returned = {d["code"]: d["name"] for d in depts_data}
        test_codes = ["05", "08", "11", "25", "76", "91", "99"]
        for tc in test_codes:
            assert tc in dept_codes_returned, f"Code {tc} missing in /departments!"
            print(f"  ✓ Found {tc}: {dept_codes_returned[tc]}")

        # 2. Test GET /api/v1/analytics/territorial/departments with NA token
        print("\n2. Testing GET /api/v1/analytics/territorial/departments ...")
        res_dist = await client.get("/api/v1/analytics/territorial/departments", headers={"Authorization": f"Bearer {na_token}"})
        print(f"Status: {res_dist.status_code}")
        assert res_dist.status_code == 200
        dist_data = res_dist.json()
        print(f"Total departments in analytics: {len(dist_data['items'])}")
        assert len(dist_data['items']) == 33

        # 3. Test GET /api/v1/analytics/territorial/municipalities?department_code=05 (Antioquia - 0 PEVN tenants)
        print("\n3. Testing GET /api/v1/analytics/territorial/municipalities?department_code=05 (Antioquia) ...")
        res_muni_05 = await client.get("/api/v1/analytics/territorial/municipalities?department_code=05", headers={"Authorization": f"Bearer {na_token}"})
        print(f"Status: {res_muni_05.status_code}")
        assert res_muni_05.status_code == 200
        munis_05 = res_muni_05.json()["items"]
        print(f"Municipalities in Antioquia (catalog group): {len(munis_05)}")
        # Note: Analytics groups by catalog (municipality_code, municipality_name) where 05001 has 2 variants: MEDELLIN and MEDELLÍN -> 126
        assert len(munis_05) >= 125
        print(f"  First municipality: {munis_05[0]['municipality_code']} - {munis_05[0]['municipality_name']} (Insts: {munis_05[0]['total_institutions']}, Provisioned: {munis_05[0]['provisioned_institutions']})")

        # Query operational municipalities for Antioquia directly
        async with engine.connect() as conn:
            op_muni_05_count = (await conn.execute(text("SELECT count(*) FROM municipalities m JOIN departments d ON m.department_id = d.id WHERE d.code = '05'"))).scalar()
            print(f"Operational municipalities in Antioquia: {op_muni_05_count}")
            assert op_muni_05_count == 125

        # 4. Test GET /api/v1/analytics/territorial/municipalities?department_code=99 (Vichada - 0 PEVN tenants)
        print("\n4. Testing GET /api/v1/analytics/territorial/municipalities?department_code=99 (Vichada) ...")
        res_muni_99 = await client.get("/api/v1/analytics/territorial/municipalities?department_code=99", headers={"Authorization": f"Bearer {na_token}"})
        print(f"Status: {res_muni_99.status_code}")
        assert res_muni_99.status_code == 200
        munis_99 = res_muni_99.json()["items"]
        print(f"Municipalities in Vichada (catalog group): {len(munis_99)}")
        assert len(munis_99) >= 4

        # Query operational municipalities for Vichada directly
        async with engine.connect() as conn:
            op_muni_99_count = (await conn.execute(text("SELECT count(*) FROM municipalities m JOIN departments d ON m.department_id = d.id WHERE d.code = '99'"))).scalar()
            print(f"Operational municipalities in Vichada: {op_muni_99_count}")
            assert op_muni_99_count == 4

        # 5. Test GET /api/v1/analytics/territorial/summary with NA token
        print("\n5. Testing GET /api/v1/analytics/territorial/summary ...")
        res_sum = await client.get("/api/v1/analytics/territorial/summary", headers={"Authorization": f"Bearer {na_token}"})
        print(f"Status: {res_sum.status_code}")
        assert res_sum.status_code == 200
        sum_data = res_sum.json()
        print(f"National Summary -> total_departments: {sum_data['total_departments']}, total_municipalities: {sum_data['total_municipalities']}")
        print(f"Provisioned institutions: {sum_data['provisioned_institutions']}, Total catalog institutions: {sum_data['total_institutions']}")
        assert sum_data['total_departments'] == 33
        assert sum_data['total_municipalities'] == 1119
        assert sum_data['provisioned_institutions'] == 31

        # 6. Anti-IDOR check: Atlántico DA accessing Atlántico vs Bogotá
        print("\n6. Testing Anti-IDOR Isolation with Atlántico Department Admin ...")
        # Atlántico institution ID: a89620bc-2669-464f-9c53-8e7243779fc0
        # Bogotá institution ID: 2dcc7e47-8fca-4b8b-b00d-6182b1b5285f
        res_da_atlantico = await client.get(
            "/api/v1/institutions/a89620bc-2669-464f-9c53-8e7243779fc0",
            headers={"Authorization": f"Bearer {da_token}"}
        )
        print(f"Atlántico DA -> Atlántico Inst Status: {res_da_atlantico.status_code}")
        assert res_da_atlantico.status_code == 200

        res_da_bogota = await client.get(
            "/api/v1/institutions/2dcc7e47-8fca-4b8b-b00d-6182b1b5285f",
            headers={"Authorization": f"Bearer {da_token}"}
        )
        print(f"Atlántico DA -> Bogotá Inst Status: {res_da_bogota.status_code}")
        assert res_da_bogota.status_code == 403
        print("  ✓ Cross-department Anti-IDOR blocked with HTTP 403 Forbidden!")

        print("\nALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_apis())
