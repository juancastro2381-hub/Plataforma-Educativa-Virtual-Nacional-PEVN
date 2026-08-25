"""
PEVN Backend — Tests for Groups and Actors Domain Models (Phase 3 Step 2)

Validates ORM mappings, foreign key integrity, tenancy boundaries, unique
constraints, and business rules for Groups, Teachers, Students, and Guardians.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_year import AcademicYear, AcademicYearStatus
from app.models.grade import Grade
from app.models.group import Group, ShiftEnum
from app.models.guardian import (
    Guardian,
    GuardianRelationshipType,
    StudentGuardian,
)
from app.models.institution import Campus, Institution
from app.models.student import Student, StudentGender
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def sample_tenant(
    db_session: AsyncSession,
) -> tuple[Institution, Campus, AcademicYear, Grade]:
    """Fixture providing a complete institutional setup for tests."""
    dept = Department(
        code=f"D{uuid.uuid4().hex[:4]}",
        name="Departamento Central",
    )
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(
        department_id=dept.id,
        code=f"M{uuid.uuid4().hex[:4]}",
        name="Municipio Central",
    )
    db_session.add(mun)
    await db_session.flush()

    inst = Institution(
        municipality_id=mun.id,
        dane_code=f"1{uuid.uuid4().hex[:11]}",
        name="Colegio Mayor Nacional",
        email=f"rectoria_{uuid.uuid4().hex[:6]}@colegio.edu.co",
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code=f"2{uuid.uuid4().hex[:11]}",
        name="Sede Principal",
    )
    db_session.add(campus)
    await db_session.flush()

    ay = AcademicYear(
        institution_id=inst.id,
        year=2026,
        name="Año 2026",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 11, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    await db_session.flush()

    grade_res = await db_session.execute(select(Grade).where(Grade.code == "G10"))
    grade = grade_res.scalar_one()

    await db_session.commit()
    return inst, campus, ay, grade


@pytest.mark.asyncio
async def test_teacher_profile_creation_and_user_uniqueness(
    db_session: AsyncSession,
    sample_tenant: tuple[Institution, Campus, AcademicYear, Grade],
) -> None:
    """Verify Teacher profile creation, 1:1 user linkage and uniqueness."""
    inst, _, _, _ = sample_tenant

    user = User(
        email=f"docente_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"doc_{uuid.uuid4().hex[:6]}",
        hashed_password="hashed_pass_placeholder",
        first_name="Carlos",
        last_name="Pérez",
        document_type=DocumentType.CC,
        document_number=f"79{uuid.uuid4().hex[:6]}",
        institution_id=inst.id,
    )
    db_session.add(user)
    await db_session.flush()

    teacher = Teacher(
        user_id=user.id,
        institution_id=inst.id,
        specialty_area="Licenciatura en Matemáticas",
        escalafon_grade="14",
        contract_type=TeacherContractType.PROPIEDAD,
    )
    db_session.add(teacher)
    await db_session.commit()
    await db_session.refresh(teacher)

    assert teacher.id is not None
    assert teacher.user_id == user.id
    assert teacher.institution_id == inst.id
    assert teacher.contract_type == TeacherContractType.PROPIEDAD

    # Attempt to create duplicate teacher profile for same user -> IntegrityError
    dup_teacher = Teacher(
        user_id=user.id,
        institution_id=inst.id,
    )
    db_session.add(dup_teacher)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_student_profile_creation_and_simat_uniqueness(
    db_session: AsyncSession,
    sample_tenant: tuple[Institution, Campus, AcademicYear, Grade],
) -> None:
    """Verify Student profile creation, SIMAT code uniqueness and validations."""
    inst, _, _, _ = sample_tenant
    simat_code = f"SIMAT-{uuid.uuid4().hex[:8]}"

    user = User(
        email=f"estudiante_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"est_{uuid.uuid4().hex[:6]}",
        hashed_password="hashed_pass_placeholder",
        first_name="María",
        last_name="González",
        document_type=DocumentType.TI,
        document_number=f"1020{uuid.uuid4().hex[:6]}",
        institution_id=inst.id,
    )
    db_session.add(user)
    await db_session.flush()

    student = Student(
        user_id=user.id,
        institution_id=inst.id,
        code_simat=simat_code,
        birth_date=date(2010, 5, 15),
        gender=StudentGender.F,
        blood_type="O+",
        stratum=2,
        eps_health_provider="Sura EPS",
        has_disability=False,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    assert student.id is not None
    assert student.code_simat == simat_code
    assert student.gender == StudentGender.F
    assert student.stratum == 2

    # Attempt to duplicate SIMAT code -> IntegrityError
    user2 = User(
        email=f"estudiante2_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"est2_{uuid.uuid4().hex[:6]}",
        hashed_password="hashed_pass_placeholder",
        first_name="Ana",
        last_name="Rojas",
        document_type=DocumentType.TI,
        document_number=f"1030{uuid.uuid4().hex[:6]}",
        institution_id=inst.id,
    )
    db_session.add(user2)
    await db_session.flush()

    dup_student = Student(
        user_id=user2.id,
        institution_id=inst.id,
        code_simat=simat_code,
        birth_date=date(2011, 3, 20),
        gender=StudentGender.F,
    )
    db_session.add(dup_student)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_guardian_creation_without_mandatory_email(
    db_session: AsyncSession,
) -> None:
    """Verify Guardian creation without email (OPEN-DECISION-3A-01) and document uniqueness."""
    doc_num = f"52{uuid.uuid4().hex[:6]}"

    # Guardian without email and without user account
    guardian = Guardian(
        document_type=DocumentType.CC,
        document_number=doc_num,
        first_name="Esperanza",
        last_name="Gómez",
        phone="3001234567",
        email=None,
        relationship_type=GuardianRelationshipType.MADRE,
    )
    db_session.add(guardian)
    await db_session.commit()
    await db_session.refresh(guardian)

    assert guardian.id is not None
    assert guardian.email is None
    assert guardian.user_id is None
    assert guardian.document_number == doc_num

    # Duplicate document number and type -> IntegrityError
    dup_guardian = Guardian(
        document_type=DocumentType.CC,
        document_number=doc_num,
        first_name="Otra",
        last_name="Persona",
        phone="3009876543",
    )
    db_session.add(dup_guardian)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_student_guardian_association(
    db_session: AsyncSession,
    sample_tenant: tuple[Institution, Campus, AcademicYear, Grade],
) -> None:
    """Verify StudentGuardian linkage, priority contact flag, and uniqueness."""
    inst, _, _, _ = sample_tenant

    user = User(
        email=f"est_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"u_{uuid.uuid4().hex[:6]}",
        hashed_password="placeholder_hash",
        first_name="Pedro",
        last_name="Torres",
        document_type=DocumentType.TI,
        document_number=f"101{uuid.uuid4().hex[:6]}",
        institution_id=inst.id,
    )
    db_session.add(user)
    await db_session.flush()

    student = Student(
        user_id=user.id,
        institution_id=inst.id,
        code_simat=f"SIMAT-{uuid.uuid4().hex[:8]}",
        birth_date=date(2012, 8, 10),
        gender=StudentGender.M,
    )
    db_session.add(student)

    guardian = Guardian(
        document_type=DocumentType.CC,
        document_number=f"41{uuid.uuid4().hex[:6]}",
        first_name="Marta",
        last_name="Torres",
        phone="3155551234",
    )
    db_session.add(guardian)
    await db_session.flush()

    link = StudentGuardian(
        student_id=student.id,
        guardian_id=guardian.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
        is_authorized_pickup=True,
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    assert link.id is not None
    assert link.is_primary_contact is True
    assert link.is_authorized_pickup is True

    # Duplicate association -> IntegrityError
    dup_link = StudentGuardian(
        student_id=student.id,
        guardian_id=guardian.id,
        relationship_type=GuardianRelationshipType.MADRE,
    )
    db_session.add(dup_link)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_group_creation_and_capacity_constraint(
    db_session: AsyncSession,
    sample_tenant: tuple[Institution, Campus, AcademicYear, Grade],
) -> None:
    """Verify Group creation, director assignment, capacity limit and composite uniqueness."""
    inst, campus, ay, grade = sample_tenant

    # Create director teacher
    dir_user = User(
        email=f"dir_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"dir_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Laura",
        last_name="Mendoza",
        document_type=DocumentType.CC,
        document_number=f"52{uuid.uuid4().hex[:6]}",
        institution_id=inst.id,
    )
    db_session.add(dir_user)
    await db_session.flush()

    teacher = Teacher(
        user_id=dir_user.id,
        institution_id=inst.id,
        specialty_area="Ciencias Sociales",
    )
    db_session.add(teacher)
    await db_session.flush()

    group = Group(
        campus_id=campus.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="10-01",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
        group_director_teacher_id=teacher.id,
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    assert group.id is not None
    assert group.name == "10-01"
    assert group.capacity_limit == 35
    assert group.group_director_teacher_id == teacher.id

    # Duplicate group section in same campus, year and grade -> IntegrityError
    dup_group = Group(
        campus_id=campus.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="10-01",
        shift=ShiftEnum.TARDE,
    )
    db_session.add(dup_group)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
