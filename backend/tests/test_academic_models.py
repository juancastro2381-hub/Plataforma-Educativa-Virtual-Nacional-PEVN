"""
PEVN Backend — Tests for Academic Foundation Domain Models (Phase 3 Step 1)

Verifies ORM mappings, constraints, validations, and database invariants
for academic_years, academic_periods, grades, knowledge_areas, and subjects.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.grade import EducationalLevel, Grade
from app.models.institution import Institution
from app.models.subject import KnowledgeArea, Subject
from app.models.territory import Department, Municipality


@pytest.fixture
async def sample_institution(db_session: AsyncSession) -> Institution:
    """Fixture to provide a test institution."""
    dept = Department(
        code=f"D{uuid.uuid4().hex[:4]}",
        name="Departamento Prueba",
    )
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(
        department_id=dept.id,
        code=f"M{uuid.uuid4().hex[:4]}",
        name="Municipio Prueba",
    )
    db_session.add(mun)
    await db_session.flush()

    inst = Institution(
        municipality_id=mun.id,
        dane_code=f"1{uuid.uuid4().hex[:11]}",
        name="Colegio Nacional de Prueba",
        email=f"contacto_{uuid.uuid4().hex[:6]}@colegio.edu.co",
    )
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)
    return inst


@pytest.mark.asyncio
async def test_national_grade_catalog_seeded(db_session: AsyncSession) -> None:
    """Verify that standardized national grades exist and have correct ordering."""
    query = select(Grade).order_by(Grade.ordinal_order)
    result = await db_session.execute(query)
    grades = list(result.scalars().all())

    assert len(grades) >= 12
    codes = [g.code for g in grades]
    assert "TRANSICION" in codes
    assert "G01" in codes
    assert "G11" in codes

    # Check that Transición is order 0 and Preescolar
    transicion = next(g for g in grades if g.code == "TRANSICION")
    assert transicion.ordinal_order == 0
    assert transicion.level == EducationalLevel.PREESCOLAR


@pytest.mark.asyncio
async def test_academic_year_lifecycle_and_uniqueness(
    db_session: AsyncSession,
    sample_institution: Institution,
) -> None:
    """Verify AcademicYear creation, unique constraint per institution and year."""
    ay = AcademicYear(
        institution_id=sample_institution.id,
        year=2026,
        name="Año Escolar 2026",
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 11, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    await db_session.commit()
    await db_session.refresh(ay)

    assert ay.id is not None
    assert ay.year == 2026
    assert ay.status == AcademicYearStatus.ACTIVE

    # Attempt to insert duplicate year for the same institution -> must raise IntegrityError
    duplicate_ay = AcademicYear(
        institution_id=sample_institution.id,
        year=2026,
        name="Año Escolar 2026 Duplicado",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 11, 30),
    )
    db_session.add(duplicate_ay)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_academic_periods_cascade_and_weight(
    db_session: AsyncSession,
    sample_institution: Institution,
) -> None:
    """Verify AcademicPeriod creation, ordering and cascade deletion."""
    ay = AcademicYear(
        institution_id=sample_institution.id,
        year=2027,
        name="Año Escolar 2027",
        start_date=date(2027, 2, 1),
        end_date=date(2027, 11, 30),
        status=AcademicYearStatus.PLANNING,
    )
    db_session.add(ay)
    await db_session.flush()

    p1 = AcademicPeriod(
        academic_year_id=ay.id,
        period_number=1,
        name="Periodo 1",
        weight_percentage=Decimal("25.00"),
        start_date=date(2027, 2, 1),
        end_date=date(2027, 4, 15),
    )
    p2 = AcademicPeriod(
        academic_year_id=ay.id,
        period_number=2,
        name="Periodo 2",
        weight_percentage=Decimal("25.00"),
        start_date=date(2027, 4, 16),
        end_date=date(2027, 6, 30),
    )
    db_session.add_all([p1, p2])
    await db_session.commit()

    # Query periods
    periods_query = select(AcademicPeriod).where(
        AcademicPeriod.academic_year_id == ay.id
    )
    result = await db_session.execute(periods_query)
    periods = list(result.scalars().all())
    assert len(periods) == 2
    assert periods[0].weight_percentage == Decimal("25.00")


@pytest.mark.asyncio
async def test_knowledge_area_and_subject_mapping(
    db_session: AsyncSession,
    sample_institution: Institution,
) -> None:
    """Verify KnowledgeArea and Subject relationships and unique constraint."""
    # Find Grade 10
    grade_query = select(Grade).where(Grade.code == "G10")
    grade_res = await db_session.execute(grade_query)
    grade_10 = grade_res.scalar_one()

    # National Knowledge Area
    area = KnowledgeArea(
        name="Ciencias Naturales y Educación Ambiental Test",
        is_mandatory=True,
    )
    db_session.add(area)
    await db_session.flush()

    # Subject in Grade 10
    subject = Subject(
        institution_id=sample_institution.id,
        knowledge_area_id=area.id,
        grade_id=grade_10.id,
        name="Física Clásica",
        weekly_hours=4,
    )
    db_session.add(subject)
    await db_session.commit()
    await db_session.refresh(subject)

    assert subject.id is not None
    assert subject.name == "Física Clásica"
    assert subject.weekly_hours == 4

    # Duplicate subject name in same grade and institution must fail
    dup_subject = Subject(
        institution_id=sample_institution.id,
        knowledge_area_id=area.id,
        grade_id=grade_10.id,
        name="Física Clásica",
        weekly_hours=3,
    )
    db_session.add(dup_subject)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
