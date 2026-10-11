import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from pydantic import ValidationError
from app.schemas.municipality_admin import MunicipalityAdminCreateRequest

def test_payload(name, data):
    print(f"--- Testing {name} ---")
    try:
        req = MunicipalityAdminCreateRequest(**data)
        print("SUCCESS:", req.model_dump())
    except ValidationError as e:
        print("VALIDATION ERROR:")
        for err in e.errors():
            print(f"  loc={err.get('loc')}, msg={err.get('msg')}, type={err.get('type')}")

# Test 1: Frontend payload when password is empty string
test_payload("empty password string", {
    "municipality_id": "75495d0b-e2f0-4d1b-9114-02589135a863",
    "first_name": "Juan",
    "last_name": "Castro",
    "document_type": "CC",
    "document_number": "1012345678",
    "email": "juan@alcaldia.gov.co",
    "username": "juan.admin",
    "password": "", # if empty string passed
    "is_active": True
})

# Test 2: If document_number is empty string
test_payload("empty document_number string", {
    "municipality_id": "75495d0b-e2f0-4d1b-9114-02589135a863",
    "first_name": "Juan",
    "last_name": "Castro",
    "document_type": "CC",
    "document_number": "",
    "email": "juan@alcaldia.gov.co",
    "username": "juan.admin",
    "is_active": True
})

# Test 3: What did frontend actually send?
# Let's check MunicipalityAdminsView.tsx:
# const payload: MunicipalityAdminCreateRequest = {
#   municipality_id: createMuniId,
#   first_name: createForm.first_name.trim(),
#   last_name: createForm.last_name.trim(),
#   document_type: createForm.document_type || 'CC',
#   document_number: createForm.document_number?.trim() || undefined,
#   email: createForm.email.trim().toLowerCase(),
#   username: createForm.username.trim(),
#   password: createForm.password?.trim() || undefined,
#   is_active: createForm.is_active ?? true,
# }
# Wait! In JavaScript/TypeScript, what if createMuniId is:
# 1) What is in `municipalities` list in frontend?
# Does municipality option have id as string or DANE code or something else?

