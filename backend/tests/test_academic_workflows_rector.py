"""
Integration tests for Rector Academic Workflows (NTA-10-R5):
Academic Periods and Curricular Subjects Creation, Validation, and Tenant Isolation.
"""

from __future__ import annotations

import random
import uuid
from datetime import date
from typing import Any
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.academic_year import (
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.grade import EducationalLevel, Grade
from app.models.institution import Institution
from app.models.role import Role, UserRole
from app.models.subject import KnowledgeArea, Subject
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def academic_fixture(db_session: AsyncSession):
    """Fixture providing isolated institutions, rectors, grades, and knowledge areas."""
    # 0. Territory
    dept = Department(code=f"{random.randint(10, 99)}", name="Caquetá Test")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, code=f"18{random.randint(100, 999)}", name="Valparaíso Test")
    db_session.add(muni)
    await db_session.flush()

    # 1. Institutions
    inst_a = Institution(
        id=uuid.uuid4(),
        municipality_id=muni.id,
        dane_code=f"118860{uuid.uuid4().hex[:6]}",
        name="I.E TEST ACADEMIC WORKFLOWS A",
        email=f"inst_a_{uuid.uuid4().hex[:4]}@test.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        id=uuid.uuid4(),
        municipality_id=muni.id,
        dane_code=f"118860{uuid.uuid4().hex[:6]}",
        name="I.E TEST ACADEMIC WORKFLOWS B",
        email=f"inst_b_{uuid.uuid4().hex[:4]}@test.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    # 2. Actors helper
    async def create_rector(inst_id: uuid.UUID, prefix: str) -> tuple[User, dict[str, str]]:
        tag = uuid.uuid4().hex[:6]
        user = User(
            email=f"{prefix}_{tag}@test.gov.co",
            username=f"{prefix}_{tag}",
            hashed_password=password_hasher.hash("SecurePass123!"),
            first_name=f"Rector_{tag}",
            last_name="Test",
            document_type=DocumentType.CC,
            document_number=f"DOC{uuid.uuid4().hex[:8]}",
            institution_id=inst_id,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        role_res = await db_session.execute(select(Role).where(Role.name == "rector"))
        role = role_res.scalar_one()

        ur = UserRole(
            user_id=user.id,
            role_id=role.id,
            institution_id=inst_id,
            is_active=True,
        )
        db_session.add(ur)
        await db_session.flush()

        claims = {
            "roles": ["rector"],
            "institution_id": str(inst_id),
        }
        token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims=claims,
        )
        return user, {"Authorization": f"Bearer {token}"}

    rector_a, headers_a = await create_rector(inst_a.id, "rector_a")
    rector_b, headers_b = await create_rector(inst_b.id, "rector_b")

    # 3. Academic Years
    year_a = AcademicYear(
        id=uuid.uuid4(),
        institution_id=inst_a.id,
        year=2028,
        name="Año Escolar 2028",
        start_date=date(2028, 2, 1),
        end_date=date(2028, 11, 30),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    year_closed = AcademicYear(
        id=uuid.uuid4(),
        institution_id=inst_a.id,
        year=2025,
        name="Año Escolar 2025",
        start_date=date(2025, 2, 1),
        end_date=date(2025, 11, 30),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.CLOSED,
    )
    year_b = AcademicYear(
        id=uuid.uuid4(),
        institution_id=inst_b.id,
        year=2028,
        name="Año Escolar 2028 Inst B",
        start_date=date(2028, 2, 1),
        end_date=date(2028, 11, 30),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add_all([year_a, year_closed, year_b])
    await db_session.flush()

    # 4. Grade & Knowledge Area
    grade = Grade(
        id=uuid.uuid4(),
        code=f"G{uuid.uuid4().hex[:4]}",
        name="Grado Noveno Test",
        level=EducationalLevel.SECUNDARIA,
        ordinal_order=9,
    )
    ka = KnowledgeArea(
        id=uuid.uuid4(),
        name=f"Ciencias Aplicadas Test {uuid.uuid4().hex[:4]}",
        is_mandatory=True,
        institution_id=None,
    )
    db_session.add_all([grade, ka])
    await db_session.commit()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "rector_a": rector_a,
        "headers_a": headers_a,
        "rector_b": rector_b,
        "headers_b": headers_b,
        "year_a": year_a,
        "year_closed": year_closed,
        "year_b": year_b,
        "grade": grade,
        "ka": ka,
    }


@pytest.mark.asyncio
async def test_create_academic_period_success_and_list(
    client: AsyncClient, academic_fixture: dict
):
    """Test authorized Rector can create and list academic periods."""
    headers_a = academic_fixture["headers_a"]
    year_a = academic_fixture["year_a"]

    payload = {
        "period_number": 1,
        "name": "Primer Período",
        "weight_percentage": 25.0,
        "start_date": "2028-02-01",
        "end_date": "2028-04-15",
    }

    # Create Period 1
    resp = await client.post(
        f"/api/v1/academic-years/{year_a.id}/periods",
        json=payload,
        headers=headers_a,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["period_number"] == 1
    assert data["name"] == "Primer Período"
    assert data["weight_percentage"] == 25.0
    assert data["academic_year_id"] == str(year_a.id)
    assert data["is_closed"] is False

    # List via year endpoint
    resp_list = await client.get(
        f"/api/v1/academic-years/{year_a.id}/periods",
        headers=headers_a,
    )
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["name"] == "Primer Período"

    # List via academic-periods endpoint
    resp_direct_list = await client.get(
        f"/api/v1/academic-periods?year_id={year_a.id}",
        headers=headers_a,
    )
    assert resp_direct_list.status_code == 200
    assert resp_direct_list.json()["total"] == 1


@pytest.mark.asyncio
async def test_create_academic_period_validations(
    client: AsyncClient, academic_fixture: dict
):
    """Test business validations for period creation."""
    headers_a = academic_fixture["headers_a"]
    year_a = academic_fixture["year_a"]
    year_closed = academic_fixture["year_closed"]

    # 1. Invalid date order (start >= end)
    resp = await client.post(
        f"/api/v1/academic-years/{year_a.id}/periods",
        json={
            "period_number": 1,
            "name": "Período Fechas Inválidas",
            "weight_percentage": 25.0,
            "start_date": "2028-05-01",
            "end_date": "2028-04-01",
        },
        headers=headers_a,
    )
    assert resp.status_code == 400

    # 2. Dates outside year bounds (year ends 2028-11-30)
    resp = await client.post(
        f"/api/v1/academic-years/{year_a.id}/periods",
        json={
            "period_number": 1,
            "name": "Período Fuera de Rango",
            "weight_percentage": 25.0,
            "start_date": "2028-02-01",
            "end_date": "2028-12-15",
        },
        headers=headers_a,
    )
    assert resp.status_code == 400

    # 3. Cannot create period in CLOSED year
    resp = await client.post(
        f"/api/v1/academic-years/{year_closed.id}/periods",
        json={
            "period_number": 1,
            "name": "Período en Año Cerrado",
            "weight_percentage": 25.0,
            "start_date": "2025-02-01",
            "end_date": "2025-04-15",
        },
        headers=headers_a,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_academic_period_tenant_isolation(
    client: AsyncClient, academic_fixture: dict
):
    """Test Rector cannot create period in another institution's year."""
    headers_a = academic_fixture["headers_a"]
    year_b = academic_fixture["year_b"]

    # Rector A tries to create period in Year B
    resp = await client.post(
        f"/api/v1/academic-years/{year_b.id}/periods",
        json={
            "period_number": 1,
            "name": "Periodo Intruso",
            "weight_percentage": 25.0,
            "start_date": "2028-02-01",
            "end_date": "2028-04-15",
        },
        headers=headers_a,
    )
    assert resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_knowledge_areas_and_create_subject_workflow(
    client: AsyncClient, academic_fixture: dict
):
    """Test listing knowledge areas and creating curricular subjects."""
    headers_a = academic_fixture["headers_a"]
    inst_a = academic_fixture["inst_a"]
    grade = academic_fixture["grade"]
    ka = academic_fixture["ka"]

    # 1. List knowledge areas
    resp_ka = await client.get(
        "/api/v1/subjects/knowledge-areas",
        headers=headers_a,
    )
    assert resp_ka.status_code == 200
    ka_data = resp_ka.json()
    assert ka_data["total"] >= 1
    area_ids = [item["id"] for item in ka_data["items"]]
    assert str(ka.id) in area_ids

    # 2. Create Subject
    sub_payload = {
        "name": "Física Cuántica Básica",
        "grade_id": str(grade.id),
        "knowledge_area_id": str(ka.id),
        "weekly_hours": 3,
    }
    resp_sub = await client.post(
        "/api/v1/subjects",
        json=sub_payload,
        headers=headers_a,
    )
    assert resp_sub.status_code == 201, resp_sub.text
    sub_data = resp_sub.json()
    assert sub_data["name"] == "Física Cuántica Básica"
    assert sub_data["weekly_hours"] == 3
    assert sub_data["institution_id"] == str(inst_a.id)

    # 3. Duplicate subject name in same grade should fail
    resp_dup = await client.post(
        "/api/v1/subjects",
        json=sub_payload,
        headers=headers_a,
    )
    assert resp_dup.status_code == 400

    # 4. List subjects filtered by grade
    resp_list = await client.get(
        f"/api/v1/subjects?grade_id={grade.id}",
        headers=headers_a,
    )
    assert resp_list.status_code == 200
    names = [s["name"] for s in resp_list.json()["items"]]
    assert "Física Cuántica Básica" in names
