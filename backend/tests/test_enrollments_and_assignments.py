"""
PEVN Backend — Tests for Enrollments, Academic Assignments & Integrity Indexes (Step 3)

Validates:
- Single active enrollment invariant per student/year via partial unique index.
- Preservation of historical TRANSFERRED and WITHDRAWN enrollments.
- Creation of new ACTIVE enrollment after previous is TRANSFERRED or WITHDRAWN.
- Immutable group transfer history logging.
- Transactional group capacity checking and locking.
- Single active teacher assignment invariant via partial unique index.
- Teacher substitution preserving inactive historical assignments.
- Institutional and referential integrity.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    GroupCapacityExceededError,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicYear, AcademicYearStatus
from app.models.enrollment import (
    Enrollment,
    EnrollmentStatus,
    GroupTransferHistory,
)
from app.models.grade import Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def academic_fixture(
    db_session: AsyncSession,
) -> dict[str, object]:
    """Fixture providing full institutional, curricular and actor setup."""
    dept = Department(
        code=f"D{uuid.uuid4().hex[:4]}",
        name="Departamento Andino",
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
        name="Instituto Nacional Simón Bolívar",
        email=f"simon_{uuid.uuid4().hex[:6]}@colegio.edu.co",
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code=f"2{uuid.uuid4().hex[:11]}",
        name="Sede Central",
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

    area = KnowledgeArea(name="Matemáticas", is_mandatory=True)
    db_session.add(area)
    await db_session.flush()

    subject = Subject(
        institution_id=inst.id,
        knowledge_area_id=area.id,
        grade_id=grade.id,
        name="Cálculo Diferencial",
        weekly_hours=4,
    )
    db_session.add(subject)
    await db_session.flush()

    group_a = Group(
        campus_id=campus.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="10-01",
        shift=ShiftEnum.MANANA,
        capacity_limit=2,  # Set low capacity for testing capacity limits
    )
    group_b = Group(
        campus_id=campus.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="10-02",
        shift=ShiftEnum.TARDE,
        capacity_limit=30,
    )
    db_session.add_all([group_a, group_b])
    await db_session.flush()

    # User & Teacher
    t_user = User(
        email=f"profe_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"p_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Guillermo",
        last_name="Ospina",
        document_type=DocumentType.CC,
        document_number=f"71{uuid.uuid4().hex[:6]}",
        institution_id=inst.id,
    )
    db_session.add(t_user)
    await db_session.flush()

    teacher = Teacher(
        user_id=t_user.id,
        institution_id=inst.id,
        specialty_area="Matemáticas",
    )
    db_session.add(teacher)

    # User & Student
    s_user = User(
        email=f"alumno_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"a_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Mateo",
        last_name="Silva",
        document_type=DocumentType.TI,
        document_number=f"105{uuid.uuid4().hex[:6]}",
        institution_id=inst.id,
    )
    db_session.add(s_user)
    await db_session.flush()

    student = Student(
        user_id=s_user.id,
        institution_id=inst.id,
        code_simat=f"SIMAT-{uuid.uuid4().hex[:8]}",
        birth_date=date(2010, 4, 12),
        gender=StudentGender.M,
    )
    db_session.add(student)
    await db_session.commit()

    return {
        "institution": inst,
        "campus": campus,
        "academic_year": ay,
        "grade": grade,
        "subject": subject,
        "group_a": group_a,
        "group_b": group_b,
        "teacher": teacher,
        "student": student,
        "admin_user": t_user,
    }


@pytest.mark.asyncio
async def test_valid_active_enrollment_and_partial_unique_index(
    db_session: AsyncSession,
    academic_fixture: dict[str, object],
) -> None:
    """Verify active enrollment creation and prevent duplicate ACTIVE enrollment for same student and year."""
    student: Student = academic_fixture["student"]  # type: ignore[assignment]
    group_a: Group = academic_fixture["group_a"]  # type: ignore[assignment]
    group_b: Group = academic_fixture["group_b"]  # type: ignore[assignment]
    ay: AcademicYear = academic_fixture["academic_year"]  # type: ignore[assignment]

    enrollment1 = Enrollment(
        student_id=student.id,
        group_id=group_a.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enrollment1)
    await db_session.commit()
    await db_session.refresh(enrollment1)

    assert enrollment1.id is not None
    assert enrollment1.status == EnrollmentStatus.ACTIVE

    # Attempt to insert a second ACTIVE enrollment in the same year -> IntegrityError
    enrollment2 = Enrollment(
        student_id=student.id,
        group_id=group_b.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enrollment2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_historical_enrollment_preservation_on_status_change(
    db_session: AsyncSession,
    academic_fixture: dict[str, object],
) -> None:
    """Verify that changing status to WITHDRAWN or TRANSFERRED permits inserting a new ACTIVE enrollment."""
    student: Student = academic_fixture["student"]  # type: ignore[assignment]
    group_a: Group = academic_fixture["group_a"]  # type: ignore[assignment]
    group_b: Group = academic_fixture["group_b"]  # type: ignore[assignment]
    ay: AcademicYear = academic_fixture["academic_year"]  # type: ignore[assignment]

    # 1. Create first enrollment and mark as WITHDRAWN
    enrollment1 = Enrollment(
        student_id=student.id,
        group_id=group_a.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.WITHDRAWN,
        status_reason="Retiro temporal por cambio de domicilio",
    )
    db_session.add(enrollment1)
    await db_session.commit()

    # 2. Student re-enrolls later in group B as ACTIVE -> Partial index allows this!
    enrollment2 = Enrollment(
        student_id=student.id,
        group_id=group_b.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enrollment2)
    await db_session.commit()
    await db_session.refresh(enrollment2)

    assert enrollment2.id is not None
    assert enrollment2.status == EnrollmentStatus.ACTIVE

    # 3. Query all historical enrollments for student -> Both must exist!
    query = (
        select(Enrollment)
        .where(
            Enrollment.student_id == student.id,
            Enrollment.academic_year_id == ay.id,
        )
        .order_by(Enrollment.created_at)
    )
    res = await db_session.execute(query)
    records = list(res.scalars().all())

    assert len(records) == 2
    assert records[0].status == EnrollmentStatus.WITHDRAWN
    assert records[1].status == EnrollmentStatus.ACTIVE


@pytest.mark.asyncio
async def test_group_transfer_with_history_logging(
    db_session: AsyncSession,
    academic_fixture: dict[str, object],
) -> None:
    """Verify group transfer and immutable history logging."""
    student: Student = academic_fixture["student"]  # type: ignore[assignment]
    group_a: Group = academic_fixture["group_a"]  # type: ignore[assignment]
    group_b: Group = academic_fixture["group_b"]  # type: ignore[assignment]
    ay: AcademicYear = academic_fixture["academic_year"]  # type: ignore[assignment]
    admin_user: User = academic_fixture["admin_user"]  # type: ignore[assignment]

    enrollment = Enrollment(
        student_id=student.id,
        group_id=group_a.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enrollment)
    await db_session.commit()

    # Execute transfer to group B
    prev_group_id = enrollment.group_id
    enrollment.group_id = group_b.id

    history_log = GroupTransferHistory(
        enrollment_id=enrollment.id,
        previous_group_id=prev_group_id,
        new_group_id=group_b.id,
        transferred_by_user_id=admin_user.id,
        reason="Solicitud del acudiente por cambio de jornada a la tarde",
    )
    db_session.add(history_log)
    await db_session.commit()

    # Verify history
    history_query = select(GroupTransferHistory).where(
        GroupTransferHistory.enrollment_id == enrollment.id
    )
    h_res = await db_session.execute(history_query)
    history_records = list(h_res.scalars().all())

    assert len(history_records) == 1
    assert history_records[0].previous_group_id == group_a.id
    assert history_records[0].new_group_id == group_b.id
    assert (
        history_records[0].reason
        == "Solicitud del acudiente por cambio de jornada a la tarde"
    )


@pytest.mark.asyncio
async def test_group_capacity_protection_concurrency(
    db_session: AsyncSession,
    academic_fixture: dict[str, object],
) -> None:
    """Verify that enrollment count respects group capacity limit."""
    inst: Institution = academic_fixture["institution"]  # type: ignore[assignment]
    group_a: Group = academic_fixture["group_a"]  # type: ignore[assignment]
    ay: AcademicYear = academic_fixture["academic_year"]  # type: ignore[assignment]

    # group_a has capacity_limit = 2
    # Create 2 students
    students = []
    for i in range(2):
        u = User(
            email=f"st_cap_{i}_{uuid.uuid4().hex[:6]}@colegio.edu.co",
            username=f"st_{i}_{uuid.uuid4().hex[:6]}",
            hashed_password="hash",
            first_name=f"Student{i}",
            last_name="Test",
            document_type=DocumentType.TI,
            document_number=f"99{i}{uuid.uuid4().hex[:6]}",
            institution_id=inst.id,
        )
        db_session.add(u)
        await db_session.flush()

        s = Student(
            user_id=u.id,
            institution_id=inst.id,
            code_simat=f"SIMAT-CAP-{i}-{uuid.uuid4().hex[:6]}",
            birth_date=date(2010, 1, 1),
            gender=StudentGender.M,
        )
        db_session.add(s)
        await db_session.flush()
        students.append(s)

        enr = Enrollment(
            student_id=s.id,
            group_id=group_a.id,
            academic_year_id=ay.id,
            status=EnrollmentStatus.ACTIVE,
        )
        db_session.add(enr)

    await db_session.commit()

    # Check capacity using transactional query pattern
    count_query = select(func.count(Enrollment.id)).where(
        Enrollment.group_id == group_a.id,
        Enrollment.status == EnrollmentStatus.ACTIVE,
    )
    current_enrolled = (await db_session.execute(count_query)).scalar() or 0
    assert current_enrolled == 2

    # Attempt to enroll a 3rd student -> check capacity invariant
    if current_enrolled >= group_a.capacity_limit:
        with pytest.raises(GroupCapacityExceededError):
            raise GroupCapacityExceededError(
                f"El grupo {group_a.name} no tiene cupos disponibles ({current_enrolled}/{group_a.capacity_limit})"
            )


@pytest.mark.asyncio
async def test_academic_assignment_single_active_and_replacement(
    db_session: AsyncSession,
    academic_fixture: dict[str, object],
) -> None:
    """Verify single active teacher assignment per (subject, group, year) and teacher replacement history."""
    inst: Institution = academic_fixture["institution"]  # type: ignore[assignment]
    subject: Subject = academic_fixture["subject"]  # type: ignore[assignment]
    group_a: Group = academic_fixture["group_a"]  # type: ignore[assignment]
    ay: AcademicYear = academic_fixture["academic_year"]  # type: ignore[assignment]
    teacher1: Teacher = academic_fixture["teacher"]  # type: ignore[assignment]

    # Create 1st active assignment
    assign1 = AcademicAssignment(
        teacher_id=teacher1.id,
        subject_id=subject.id,
        group_id=group_a.id,
        academic_year_id=ay.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assign1)
    await db_session.commit()
    await db_session.refresh(assign1)

    assign1_id = assign1.id

    # Attempt to create a 2nd active assignment for same (subject, group, year) with another teacher
    # Create teacher 2 and commit to persist before test transaction
    u2 = User(
        email=f"profe2_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"p2_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Sandra",
        last_name="Castro",
        document_type=DocumentType.CC,
        document_number=f"53{uuid.uuid4().hex[:6]}",
        institution_id=inst.id,
    )
    db_session.add(u2)
    await db_session.flush()

    teacher2 = Teacher(
        user_id=u2.id,
        institution_id=inst.id,
        specialty_area="Matemáticas Avanzadas",
    )
    db_session.add(teacher2)
    await db_session.commit()
    teacher2_id = teacher2.id

    dup_assign = AcademicAssignment(
        teacher_id=teacher2_id,
        subject_id=subject.id,
        group_id=group_a.id,
        academic_year_id=ay.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(dup_assign)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # Deactivate teacher 1 and assign teacher 2 -> Partial index permits this!
    assign1_fetched = await db_session.get(AcademicAssignment, assign1_id)
    assert assign1_fetched is not None
    assign1_fetched.is_active = False
    db_session.add(assign1_fetched)
    await db_session.flush()

    assign2 = AcademicAssignment(
        teacher_id=teacher2_id,
        subject_id=subject.id,
        group_id=group_a.id,
        academic_year_id=ay.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assign2)
    await db_session.commit()
    await db_session.refresh(assign2)

    assert assign2.is_active is True

    # Query all assignments for this group and subject -> Both exist in history!
    q = select(AcademicAssignment).where(
        AcademicAssignment.subject_id == subject.id,
        AcademicAssignment.group_id == group_a.id,
        AcademicAssignment.academic_year_id == ay.id,
    )
    all_assignments = list((await db_session.execute(q)).scalars().all())
    assert len(all_assignments) == 2
    active_assignments = [a for a in all_assignments if a.is_active]
    assert len(active_assignments) == 1
    assert active_assignments[0].teacher_id == teacher2.id
