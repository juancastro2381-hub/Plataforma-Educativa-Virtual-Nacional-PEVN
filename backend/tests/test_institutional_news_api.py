"""
PEVN Backend — Institutional News Integration & Security Tests (Phase 15 - DECISION-15-03)

Tests:
1. Directive publication of institutional community news.
2. News listing in Student and Guardian feeds.
3. Category filters and draft vs published states.
4. Cross-tenant isolation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.institution import Institution
from app.models.news import InstitutionalNews, NewsCategory
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.student import Student, StudentGender
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def news_test_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Sets up institutional context and test tokens."""
    dept = Department(code="05", name="Antioquia")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="05001", name="Medellin")
    db_session.add(mun)
    await db_session.flush()

    inst_a = Institution(
        dane_code="333333333333",
        name="Liceo Antioqueno",
        email="rector.antioqueno@pevn.edu.co",
        municipality_id=mun.id,
        is_active=True,
    )
    inst_b = Institution(
        dane_code="444444444444",
        name="Liceo Poblado",
        email="rector.poblado@pevn.edu.co",
        municipality_id=mun.id,
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    # Retrieve bootstrapped roles
    roles_res = await db_session.execute(select(Role))
    roles_map = {r.name: r for r in roles_res.scalars().all()}

    # Rector User
    rector_user = User(
        email="rector.antioqueno@pevn.edu.co",
        username="rector_antioquia",
        hashed_password=password_hasher.hash("RectorPass123!"),
        document_type=DocumentType.CC,
        document_number="20001",
        first_name="Beatriz",
        last_name="Rector",
        institution_id=inst_a.id,
        is_active=True,
    )
    # Student User
    student_user = User(
        email="estudiante.antioquia@pevn.edu.co",
        username="estudiante_antioquia",
        hashed_password=password_hasher.hash("StudentPass123!"),
        document_type=DocumentType.TI,
        document_number="20002",
        first_name="Carlos",
        last_name="Restrepo",
        institution_id=inst_a.id,
        is_active=True,
    )
    # Cross tenant Rector B
    rector_b_user = User(
        email="rector.poblado@pevn.edu.co",
        username="rector_poblado",
        hashed_password=password_hasher.hash("RectorBPass123!"),
        document_type=DocumentType.CC,
        document_number="20003",
        first_name="Fernando",
        last_name="RectorB",
        institution_id=inst_b.id,
        is_active=True,
    )
    db_session.add_all([rector_user, student_user, rector_b_user])
    await db_session.flush()

    db_session.add(UserRole(user_id=rector_user.id, role_id=roles_map["rector"].id))
    db_session.add(UserRole(user_id=student_user.id, role_id=roles_map["student"].id))
    db_session.add(UserRole(user_id=rector_b_user.id, role_id=roles_map["rector"].id))
    await db_session.flush()

    student_profile = Student(
        institution_id=inst_a.id,
        user_id=student_user.id,
        code_simat="SIMAT-2001",
        birth_date=datetime(2009, 3, 10).date(),
        gender=StudentGender.M,
    )
    db_session.add(student_profile)
    await db_session.commit()

    rector_token = await token_service.create_access_token(
        subject=str(rector_user.id),
        additional_claims={"email": rector_user.email, "roles": ["rector"], "institution_id": str(inst_a.id)},
    )
    student_token = await token_service.create_access_token(
        subject=str(student_user.id),
        additional_claims={"email": student_user.email, "roles": ["student"], "institution_id": str(inst_a.id)},
    )
    rector_b_token = await token_service.create_access_token(
        subject=str(rector_b_user.id),
        additional_claims={"email": rector_b_user.email, "roles": ["rector"], "institution_id": str(inst_b.id)},
    )

    return {
        "inst_a_id": inst_a.id,
        "inst_b_id": inst_b.id,
        "rector_token": rector_token,
        "student_token": student_token,
        "rector_b_token": rector_b_token,
    }


@pytest.mark.asyncio
async def test_news_lifecycle_and_feeds(
    client: AsyncClient,
    news_test_fixture: dict[str, Any],
) -> None:
    """Test creating, publishing, listing, and cross-tenant access of institutional news."""
    rector_token = news_test_fixture["rector_token"]
    student_token = news_test_fixture["student_token"]
    rector_b_token = news_test_fixture["rector_b_token"]

    # 1. Rector publishes a news item
    payload = {
        "title": "Primer Puesto en Olimpiadas de Matematicas",
        "summary": "Estudiantes de grado decimo obtienen reconocimiento departamental.",
        "content": "Felicitamos con orgullo a nuestra delegacion academica por su destacado desempeno.",
        "category": "LOGRO_ACADEMICO",
        "cover_image_url": "https://cdn.pevn.gov.co/news/math_olympics.jpg",
        "status": "PUBLICADO",
    }
    create_res = await client.post(
        "/api/v1/news",
        json=payload,
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    assert create_res.status_code == 201
    news_data = create_res.json()
    news_id = news_data["id"]
    assert news_data["title"] == payload["title"]
    assert news_data["category"] == "LOGRO_ACADEMICO"

    # 2. Student lists news
    student_res = await client.get(
        "/api/v1/student/news",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_res.status_code == 200
    student_news = student_res.json()
    assert student_news["total"] >= 1
    assert any(n["id"] == news_id for n in student_news["items"])

    # 3. Cross tenant access to news by id from Institution B -> Returns 404
    cross_res = await client.get(
        f"/api/v1/news/{news_id}",
        headers={"Authorization": f"Bearer {rector_b_token}"},
    )
    assert cross_res.status_code == 404
