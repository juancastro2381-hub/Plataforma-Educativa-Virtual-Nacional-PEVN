"""
PEVN Backend — Comprehensive Domain Services Test Suite (Step 4)

Tests all authoritative domain services:
- AcademicYearService
- GroupService
- StudentService
- TeacherService
- GuardianService
- EnrollmentService
- TransferService
- AcademicAssignmentService
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AcademicDomainError,
    AcademicYearLifecycleError,
    CrossTenantMismatchError,
    DuplicateActiveAssignmentError,
    GroupCapacityExceededError,
    StudentAlreadyEnrolledActiveError,
)
from app.models.academic_year import (
    AcademicYearStatus,
)
from app.models.enrollment import (
    EnrollmentStatus,
)
from app.models.grade import Grade
from app.models.group import ShiftEnum
from app.models.guardian import GuardianRelationshipType
from app.models.institution import Campus, Institution
from app.models.student import StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.academic_assignment_service import AcademicAssignmentService
from app.services.academic_year_service import AcademicYearService
from app.services.enrollment_service import EnrollmentService
from app.services.group_service import GroupService
from app.services.guardian_service import GuardianService
from app.services.student_service import StudentService
from app.services.teacher_service import TeacherService
from app.services.transfer_service import TransferService


@pytest.fixture
async def service_fixture(
    db_session: AsyncSession,
) -> dict[str, object]:
    """Provides two separate institutions with campuses and users for multi-tenant service testing."""
    dept = Department(code=f"D{uuid.uuid4().hex[:4]}", name="Valle")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(
        department_id=dept.id, code=f"M{uuid.uuid4().hex[:4]}", name="Cali"
    )
    db_session.add(mun)
    await db_session.flush()

    # Institution 1
    inst1 = Institution(
        municipality_id=mun.id,
        dane_code=f"1{uuid.uuid4().hex[:11]}",
        name="I.E. Santa Librada",
        email=f"librada_{uuid.uuid4().hex[:6]}@colegio.edu.co",
    )
    # Institution 2 (for cross-tenant checks)
    inst2 = Institution(
        municipality_id=mun.id,
        dane_code=f"2{uuid.uuid4().hex[:11]}",
        name="I.E. Eustaquio Palacios",
        email=f"eustaquio_{uuid.uuid4().hex[:6]}@colegio.edu.co",
    )
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    campus1 = Campus(
        institution_id=inst1.id,
        dane_sede_code=f"3{uuid.uuid4().hex[:11]}",
        name="Sede Principal Librada",
    )
    campus2 = Campus(
        institution_id=inst2.id,
        dane_sede_code=f"4{uuid.uuid4().hex[:11]}",
        name="Sede Principal Eustaquio",
    )
    db_session.add_all([campus1, campus2])
    await db_session.flush()

    # Grade (Shared national)
    grade = (
        await db_session.execute(select(Grade).where(Grade.code == "G11"))
    ).scalar_one()

    area = KnowledgeArea(name="Ciencias Naturales", is_mandatory=True)
    db_session.add(area)
    await db_session.flush()

    subject1 = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area.id,
        grade_id=grade.id,
        name="Física Clásica",
        weekly_hours=3,
    )
    db_session.add(subject1)
    await db_session.flush()

    # Admin User for Inst 1
    admin_user = User(
        email=f"admin_{uuid.uuid4().hex[:6]}@librada.edu.co",
        username=f"adm_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Carlos",
        last_name="Rector",
        document_type=DocumentType.CC,
        document_number=f"16{uuid.uuid4().hex[:6]}",
        institution_id=inst1.id,
    )
    # Teacher User for Inst 1
    t_user1 = User(
        email=f"doc1_{uuid.uuid4().hex[:6]}@librada.edu.co",
        username=f"t1_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Alberto",
        last_name="Lleras",
        document_type=DocumentType.CC,
        document_number=f"31{uuid.uuid4().hex[:6]}",
        institution_id=inst1.id,
    )
    # Teacher User for Inst 2
    t_user2 = User(
        email=f"doc2_{uuid.uuid4().hex[:6]}@eustaquio.edu.co",
        username=f"t2_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Rodrigo",
        last_name="Lara",
        document_type=DocumentType.CC,
        document_number=f"32{uuid.uuid4().hex[:6]}",
        institution_id=inst2.id,
    )
    # Student User for Inst 1
    s_user1 = User(
        email=f"stu1_{uuid.uuid4().hex[:6]}@librada.edu.co",
        username=f"s1_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Daniel",
        last_name="Marín",
        document_type=DocumentType.TI,
        document_number=f"110{uuid.uuid4().hex[:6]}",
        institution_id=inst1.id,
    )
    db_session.add_all([admin_user, t_user1, t_user2, s_user1])
    await db_session.commit()

    return {
        "inst1": inst1,
        "inst2": inst2,
        "campus1": campus1,
        "campus2": campus2,
        "grade": grade,
        "subject1": subject1,
        "admin_user": admin_user,
        "t_user1": t_user1,
        "t_user2": t_user2,
        "s_user1": s_user1,
    }


@pytest.mark.asyncio
async def test_academic_year_service_lifecycle_and_invariants(
    db_session: AsyncSession,
    service_fixture: dict[str, object],
) -> None:
    """Test AcademicYearService creation, validation, activation and closure."""
    inst1: Institution = service_fixture["inst1"]  # type: ignore[assignment]
    inst2: Institution = service_fixture["inst2"]  # type: ignore[assignment]
    ay_service = AcademicYearService(session=db_session)

    # 1. Prevent invalid start/end dates
    with pytest.raises(
        AcademicDomainError, match="anterior a la fecha de finalización"
    ):
        await ay_service.create_academic_year(
            institution_id=inst1.id,
            year=2026,
            name="Año 2026",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 2, 1),
        )

    # 2. Create valid academic year in PLANNING state
    ay1 = await ay_service.create_academic_year(
        institution_id=inst1.id,
        year=2026,
        name="Año Lectivo 2026",
        start_date=date(2026, 1, 15),
        end_date=date(2026, 11, 30),
    )
    await db_session.commit()
    assert ay1.id is not None
    assert ay1.status == AcademicYearStatus.PLANNING

    # 3. Prevent duplicate year in same institution
    with pytest.raises(AcademicDomainError, match="Ya existe un año lectivo"):
        await ay_service.create_academic_year(
            institution_id=inst1.id,
            year=2026,
            name="Año Lectivo 2026 Duplicado",
            start_date=date(2026, 1, 15),
            end_date=date(2026, 11, 30),
        )

    # 4. Activate Academic Year
    ay_active = await ay_service.activate_academic_year(
        year_id=ay1.id,
        institution_id=inst1.id,
    )
    await db_session.commit()
    assert ay_active.status == AcademicYearStatus.ACTIVE

    # 5. Prevent activating an already active or non-planning year
    with pytest.raises(AcademicYearLifecycleError):
        await ay_service.activate_academic_year(
            year_id=ay1.id,
            institution_id=inst1.id,
        )

    # 6. Close Academic Year
    ay_closed = await ay_service.close_academic_year(
        year_id=ay1.id,
        institution_id=inst1.id,
    )
    await db_session.commit()
    assert ay_closed.status == AcademicYearStatus.CLOSED

    # 7. Cross-tenant isolation verification
    with pytest.raises(AcademicDomainError):
        await ay_service.get_academic_year_by_id(
            year_id=ay1.id,
            institution_id=inst2.id,
        )


@pytest.mark.asyncio
async def test_teacher_and_group_service_operations(
    db_session: AsyncSession,
    service_fixture: dict[str, object],
) -> None:
    """Test TeacherService and GroupService domain rules and tenant isolation."""
    inst1: Institution = service_fixture["inst1"]  # type: ignore[assignment]
    campus1: Campus = service_fixture["campus1"]  # type: ignore[assignment]
    campus2: Campus = service_fixture["campus2"]  # type: ignore[assignment]
    grade: Grade = service_fixture["grade"]  # type: ignore[assignment]
    t_user1: User = service_fixture["t_user1"]  # type: ignore[assignment]
    t_user2: User = service_fixture["t_user2"]  # type: ignore[assignment]

    ay_service = AcademicYearService(session=db_session)
    teacher_service = TeacherService(session=db_session)
    group_service = GroupService(session=db_session)

    # 1. Create Academic Year
    ay = await ay_service.create_academic_year(
        institution_id=inst1.id,
        year=2027,
        name="Año 2027",
        start_date=date(2027, 2, 1),
        end_date=date(2027, 11, 30),
    )
    await db_session.commit()

    # 2. Create Teacher in Inst 1
    teacher1 = await teacher_service.create_teacher(
        institution_id=inst1.id,
        user_id=t_user1.id,
        specialty_area="Física y Matemáticas",
        contract_type=TeacherContractType.PROPIEDAD,
    )
    await db_session.commit()
    assert teacher1.id is not None

    # 3. Prevent duplicate teacher profile on same User
    with pytest.raises(AcademicDomainError, match="ya posee un perfil docente"):
        await teacher_service.create_teacher(
            institution_id=inst1.id,
            user_id=t_user1.id,
        )

    # 4. Prevent creating teacher with user from different institution
    with pytest.raises(CrossTenantMismatchError):
        await teacher_service.create_teacher(
            institution_id=inst1.id,
            user_id=t_user2.id,  # t_user2 belongs to inst2
        )

    # 5. Create Group in Inst 1
    group = await group_service.create_group(
        institution_id=inst1.id,
        campus_id=campus1.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="11-A",
        shift=ShiftEnum.MANANA,
        capacity_limit=2,
        director_teacher_id=teacher1.id,
    )
    await db_session.commit()
    assert group.id is not None
    assert group.group_director_teacher_id == teacher1.id

    # 6. Reject cross-tenant group creation (campus2 belongs to inst2)
    with pytest.raises(CrossTenantMismatchError):
        await group_service.create_group(
            institution_id=inst1.id,
            campus_id=campus2.id,
            academic_year_id=ay.id,
            grade_id=grade.id,
            name="11-B",
        )


@pytest.mark.asyncio
async def test_student_and_guardian_service_operations(
    db_session: AsyncSession,
    service_fixture: dict[str, object],
) -> None:
    """Test StudentService and GuardianService with [OPEN-DECISION-3A-01] decoupled identity."""
    inst1: Institution = service_fixture["inst1"]  # type: ignore[assignment]
    inst2: Institution = service_fixture["inst2"]  # type: ignore[assignment]
    s_user1: User = service_fixture["s_user1"]  # type: ignore[assignment]

    student_service = StudentService(session=db_session)
    guardian_service = GuardianService(session=db_session)

    # 1. Create Student
    student = await student_service.create_student(
        institution_id=inst1.id,
        user_id=s_user1.id,
        code_simat="SIMAT-CALI-2026-001",
        birth_date=date(2009, 5, 20),
        gender=StudentGender.M,
        stratum=3,
        eps_health_provider="Emssanar",
    )
    await db_session.commit()
    assert student.id is not None

    # 2. Reject duplicate student profile on same User
    with pytest.raises(AcademicDomainError, match="ya posee un perfil de estudiante"):
        await student_service.create_student(
            institution_id=inst1.id,
            user_id=s_user1.id,
            code_simat="SIMAT-CALI-2026-DIFF",
            birth_date=date(2009, 5, 20),
        )

    # 3. Reject duplicate SIMAT on another user
    s_user_dup = User(
        email=f"studup_{uuid.uuid4().hex[:6]}@librada.edu.co",
        username=f"sdup_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Estudiante",
        last_name="Duplicado",
        document_type=DocumentType.TI,
        document_number=f"119{uuid.uuid4().hex[:6]}",
        institution_id=inst1.id,
    )
    db_session.add(s_user_dup)
    await db_session.flush()

    with pytest.raises(AcademicDomainError, match="SIMAT"):
        await student_service.create_student(
            institution_id=inst1.id,
            user_id=s_user_dup.id,
            code_simat="SIMAT-CALI-2026-001",
            birth_date=date(2009, 5, 20),
        )

    # 4. Create Guardian without mandatory email (per OPEN-DECISION-3A-01)
    guardian = await guardian_service.create_guardian(
        first_name="Patricia",
        last_name="Gómez",
        document_type=DocumentType.CC,
        document_number=f"66{uuid.uuid4().hex[:6]}",
        phone="3155550199",
        email=None,  # Decoupled email
        address="Calle 5 # 34-12",
    )
    await db_session.commit()
    assert guardian.id is not None
    assert guardian.email is None

    # 4. Associate Guardian with Student
    assoc = await guardian_service.associate_guardian_to_student(
        student_id=student.id,
        guardian_id=guardian.id,
        institution_id=inst1.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
        is_authorized_pickup=True,
    )
    await db_session.commit()
    assert assoc.id is not None
    assert assoc.is_primary_contact is True

    # 5. Prevent cross-tenant association
    with pytest.raises(AcademicDomainError):
        await guardian_service.associate_guardian_to_student(
            student_id=student.id,
            guardian_id=guardian.id,
            institution_id=inst2.id,  # inst2 does not own student
        )


@pytest.mark.asyncio
async def test_enrollment_service_and_transfer_service_atomicity(
    db_session: AsyncSession,
    service_fixture: dict[str, object],
) -> None:
    """Test EnrollmentService, TransferService with capacity locking and transfer history."""
    inst1: Institution = service_fixture["inst1"]  # type: ignore[assignment]
    campus1: Campus = service_fixture["campus1"]  # type: ignore[assignment]
    grade: Grade = service_fixture["grade"]  # type: ignore[assignment]
    admin_user: User = service_fixture["admin_user"]  # type: ignore[assignment]
    s_user1: User = service_fixture["s_user1"]  # type: ignore[assignment]

    ay_service = AcademicYearService(session=db_session)
    group_service = GroupService(session=db_session)
    student_service = StudentService(session=db_session)
    enrollment_service = EnrollmentService(session=db_session)
    transfer_service = TransferService(session=db_session)

    # Setup Year, Groups and Student
    ay = await ay_service.create_academic_year(
        institution_id=inst1.id,
        year=2028,
        name="Año 2028",
        start_date=date(2028, 2, 1),
        end_date=date(2028, 11, 30),
    )
    await db_session.flush()

    group_a = await group_service.create_group(
        institution_id=inst1.id,
        campus_id=campus1.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="11-1",
        capacity_limit=1,  # Capacity = 1 for capacity testing
    )
    group_b = await group_service.create_group(
        institution_id=inst1.id,
        campus_id=campus1.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="11-2",
        capacity_limit=30,
    )
    await db_session.flush()

    student1 = await student_service.create_student(
        institution_id=inst1.id,
        user_id=s_user1.id,
        code_simat="SIMAT-2028-001",
        birth_date=date(2010, 8, 14),
    )
    await db_session.commit()

    # 1. Create Active Enrollment in Group A
    enrollment1 = await enrollment_service.create_enrollment(
        institution_id=inst1.id,
        student_id=student1.id,
        group_id=group_a.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
    )
    await db_session.commit()
    assert enrollment1.id is not None
    assert enrollment1.status == EnrollmentStatus.ACTIVE

    # 2. Attempt duplicate active enrollment for same student and year -> StudentAlreadyEnrolledActiveError
    with pytest.raises(StudentAlreadyEnrolledActiveError):
        await enrollment_service.create_enrollment(
            institution_id=inst1.id,
            student_id=student1.id,
            group_id=group_b.id,
            academic_year_id=ay.id,
            status=EnrollmentStatus.ACTIVE,
        )

    # 3. Create Student 2 and attempt enrolling in Group A -> Exceeds capacity limit 1 -> GroupCapacityExceededError
    s_user2 = User(
        email=f"stu2_{uuid.uuid4().hex[:6]}@librada.edu.co",
        username=f"s2_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Felipe",
        last_name="Pérez",
        document_type=DocumentType.TI,
        document_number=f"111{uuid.uuid4().hex[:6]}",
        institution_id=inst1.id,
    )
    db_session.add(s_user2)
    await db_session.flush()
    student2 = await student_service.create_student(
        institution_id=inst1.id,
        user_id=s_user2.id,
        code_simat="SIMAT-2028-002",
        birth_date=date(2010, 9, 15),
    )
    await db_session.commit()

    with pytest.raises(GroupCapacityExceededError):
        await enrollment_service.create_enrollment(
            institution_id=inst1.id,
            student_id=student2.id,
            group_id=group_a.id,  # Group A full (1/1)
            academic_year_id=ay.id,
            status=EnrollmentStatus.ACTIVE,
        )

    # 4. Atomic Transfer of Student 1 from Group A to Group B
    enr_transferred, transfer_log = await transfer_service.transfer_student_group(
        enrollment_id=enrollment1.id,
        target_group_id=group_b.id,
        institution_id=inst1.id,
        transferred_by_user_id=admin_user.id,
        reason="Solicitud familiar por jornada escolar",
    )
    await db_session.commit()

    assert enr_transferred.group_id == group_b.id
    assert transfer_log.previous_group_id == group_a.id
    assert transfer_log.new_group_id == group_b.id
    assert transfer_log.reason == "Solicitud familiar por jornada escolar"

    # 5. Now that Group A is freed, Student 2 can enroll in Group A!
    enr2 = await enrollment_service.create_enrollment(
        institution_id=inst1.id,
        student_id=student2.id,
        group_id=group_a.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
    )
    await db_session.commit()
    assert enr2.id is not None
    assert enr2.group_id == group_a.id

    # 6. Withdraw Student 2 preserving history
    enr2_withdrawn = await enrollment_service.withdraw_enrollment(
        enrollment_id=enr2.id,
        institution_id=inst1.id,
        reason="Cambio de ciudad",
    )
    await db_session.commit()
    assert enr2_withdrawn.status == EnrollmentStatus.WITHDRAWN

    # 7. Query history: All enrollments preserved
    history = await enrollment_service.get_enrollment_history(
        student_id=student2.id,
        institution_id=inst1.id,
    )
    assert len(history) == 1
    assert history[0].status == EnrollmentStatus.WITHDRAWN


@pytest.mark.asyncio
async def test_academic_assignment_service_and_teacher_replacement(
    db_session: AsyncSession,
    service_fixture: dict[str, object],
) -> None:
    """Test AcademicAssignmentService, single active assignment invariant and atomic replacement."""
    inst1: Institution = service_fixture["inst1"]  # type: ignore[assignment]
    campus1: Campus = service_fixture["campus1"]  # type: ignore[assignment]
    grade: Grade = service_fixture["grade"]  # type: ignore[assignment]
    subject1: Subject = service_fixture["subject1"]  # type: ignore[assignment]
    t_user1: User = service_fixture["t_user1"]  # type: ignore[assignment]

    ay_service = AcademicYearService(session=db_session)
    group_service = GroupService(session=db_session)
    teacher_service = TeacherService(session=db_session)
    assign_service = AcademicAssignmentService(session=db_session)

    # Setup
    ay = await ay_service.create_academic_year(
        institution_id=inst1.id,
        year=2029,
        name="Año 2029",
        start_date=date(2029, 2, 1),
        end_date=date(2029, 11, 30),
    )
    group = await group_service.create_group(
        institution_id=inst1.id,
        campus_id=campus1.id,
        academic_year_id=ay.id,
        grade_id=grade.id,
        name="11-03",
    )
    teacher1 = await teacher_service.create_teacher(
        institution_id=inst1.id,
        user_id=t_user1.id,
        specialty_area="Física",
    )
    await db_session.commit()

    # 1. Create Active Assignment for Teacher 1
    assign1 = await assign_service.create_assignment(
        institution_id=inst1.id,
        teacher_id=teacher1.id,
        subject_id=subject1.id,
        group_id=group.id,
        academic_year_id=ay.id,
        weekly_hours=4,
        is_active=True,
    )
    await db_session.commit()
    assert assign1.id is not None
    assert assign1.is_active is True

    # 2. Create Teacher 2 in Inst 1
    t_user3 = User(
        email=f"doc3_{uuid.uuid4().hex[:6]}@librada.edu.co",
        username=f"t3_{uuid.uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="Gloria",
        last_name="Valencia",
        document_type=DocumentType.CC,
        document_number=f"41{uuid.uuid4().hex[:6]}",
        institution_id=inst1.id,
    )
    db_session.add(t_user3)
    await db_session.flush()
    teacher2 = await teacher_service.create_teacher(
        institution_id=inst1.id,
        user_id=t_user3.id,
        specialty_area="Física Cuántica",
    )
    await db_session.commit()

    # 3. Attempt duplicate active assignment without replacement -> DuplicateActiveAssignmentError
    with pytest.raises(DuplicateActiveAssignmentError):
        await assign_service.create_assignment(
            institution_id=inst1.id,
            teacher_id=teacher2.id,
            subject_id=subject1.id,
            group_id=group.id,
            academic_year_id=ay.id,
            weekly_hours=4,
            is_active=True,
        )

    # 4. Atomic Teacher Replacement
    old_assign, new_assign = await assign_service.replace_teacher(
        assignment_id=assign1.id,
        new_teacher_id=teacher2.id,
        institution_id=inst1.id,
    )
    await db_session.commit()

    assert old_assign.is_active is False
    assert new_assign.is_active is True
    assert new_assign.teacher_id == teacher2.id
    assert new_assign.subject_id == subject1.id
