from pydantic import ValidationError
from app.schemas.academic import TeacherCreateRequest

def test_validation():
    try:
        TeacherCreateRequest.model_validate({
            "user_id": "8788",
            "specialty_area": "Licenciatura en Ciencias Básicas",
            "contract_type": "PROPIEDAD",
            "escalafon_grade": "14"
        })
        print("Validation succeeded unexpectedly!")
    except ValidationError as e:
        print("EXACT VALIDATION ERROR FOR user_id='8788':")
        for err in e.errors():
            print(" - loc:", err["loc"])
            print(" - msg:", err["msg"])
            print(" - type:", err["type"])

if __name__ == "__main__":
    test_validation()
