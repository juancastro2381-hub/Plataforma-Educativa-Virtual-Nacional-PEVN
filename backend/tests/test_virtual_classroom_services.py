"""
PEVN Backend — Phase 4 Step 3: Virtual Classroom Domain Services Tests

Validates business logic, academic anchoring, enrollment-based authority resolution,
attendance logging, recording discovery/publication, and multi-tenant isolation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AcademicAssignmentNotFoundError,
    CrossTenantMismatchError,
    RecordingNotFoundError,
    UnauthorizedMeetingAccessError,
    VirtualClassroomLifecycleError,
    VirtualClassroomNotFoundError,
)
from app.core.meeting import MockMeetingProvider
from app.core.security.password import password_hasher
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.student import Student
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.models.virtual_classroom import (
    MeetingParticipantRole,
    VirtualClassroomStatus,
)
from app.services.attendance_service import AttendanceService
from app.services.recording_service import RecordingService
from app.services.virtual_classroom_service import VirtualClassroomService


@pytest.fixture
async def vc_service_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Provides two institutions with teachers, enrolled/unenrolled students, and assignments."""
    dept = Department(code="11", name="Bogota D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogota")
    db_session.add(mun)
    await db_session.flush()

    # Institution 1
    inst1 = Institution(
        municipality_id=mun.id,
        dane_code="11100100001",
        name="Instituto Pedagógico 1",
        email="rectoria@inst1.edu.co",
        is_active=True,
    )
    # Institution 2 (Tenant 2)
    inst2 = Institution(
        municipality_id=mun.id,
        dane_code="11100100002",
        name="Liceo Distrital 2",
        email="rectoria@inst2.edu.co",
        is_active=True,
    )
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    campus1 = Campus(
        institution_id=inst1.id,
        dane_sede_code="11100100001-01",
        name="Sede Principal 1",
        is_active=True,
    )
    db_session.add(campus1)
    await db_session.flush()

    # Academic Structure
    year1 = AcademicYear(
        institution_id=inst1.id,
        year=2026,
        name="Año 2026",
        start_date=datetime(2026, 2, 1, tzinfo=UTC).date(),
        end_date=datetime(2026, 11, 30, tzinfo=UTC).date(),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    grade10 = Grade(
        code="10-VC-SRV",
        name="Grado Décimo VC",
        level=EducationalLevel.MEDIA,
        ordinal_order=10,
    )
    db_session.add_all([year1, grade10])
    await db_session.flush()

    group_a = Group(
        campus_id=campus1.id,
        academic_year_id=year1.id,
        grade_id=grade10.id,
        name="10-A Virtual",
        shift=ShiftEnum.MANANA,
        capacity_limit=30,
    )
    group_b = Group(
        campus_id=campus1.id,
        academic_year_id=year1.id,
        grade_id=grade10.id,
        name="10-B Virtual",
        shift=ShiftEnum.TARDE,
        capacity_limit=30,
    )
    area = KnowledgeArea(
        institution_id=inst1.id,
        name="Ciencias Naturales",
        is_mandatory=True,
    )
    db_session.add_all([group_a, group_b, area])
    await db_session.flush()

    subject = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area.id,
        grade_id=grade10.id,
        name="Biología Virtual",
        weekly_hours=3,
    )
    db_session.add(subject)
    await db_session.flush()

    # Users
    pwd = password_hasher.hash("Seguro123456*!")
    teacher_user = User(
        email="prof.bio@inst1.edu.co",
        username="prof_bio",
        hashed_password=pwd,
        first_name="Profesor",
        last_name="Biología",
        document_type=DocumentType.CC,
        document_number="71000111",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    student_enrolled_user = User(
        email="est.enrolled@inst1.edu.co",
        username="est_enrolled",
        hashed_password=pwd,
        first_name="Estudiante",
        last_name="Matriculado",
        document_type=DocumentType.TI,
        document_number="1000111222",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    student_other_group_user = User(
        email="est.other@inst1.edu.co",
        username="est_other",
        hashed_password=pwd,
        first_name="Estudiante",
        last_name="OtroGrupo",
        document_type=DocumentType.TI,
        document_number="1000111333",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    rector_user = User(
        email="rector@inst1.edu.co",
        username="rector_inst1",
        hashed_password=pwd,
        first_name="Rector",
        last_name="Inst1",
        document_type=DocumentType.CC,
        document_number="71000999",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all(
        [
            teacher_user,
            student_enrolled_user,
            student_other_group_user,
            rector_user,
        ]
    )
    await db_session.flush()

    teacher = Teacher(
        user_id=teacher_user.id,
        institution_id=inst1.id,
        specialty_area="Biología",
        contract_type=TeacherContractType.PROPIEDAD,
        escalafon_grade="14",
    )
    student_enrolled = Student(
        user_id=student_enrolled_user.id,
        institution_id=inst1.id,
        code_simat="SIMAT-VC-001",
        birth_date=datetime(2010, 5, 1, tzinfo=UTC).date(),
        gender="M",
    )
    student_other = Student(
        user_id=student_other_group_user.id,
        institution_id=inst1.id,
        code_simat="SIMAT-VC-002",
        birth_date=datetime(2010, 8, 1, tzinfo=UTC).date(),
        gender="F",
    )
    db_session.add_all([teacher, student_enrolled, student_other])
    await db_session.flush()

    # Enrollments
    enr_a = Enrollment(
        student_id=student_enrolled.id,
        group_id=group_a.id,
        academic_year_id=year1.id,
        status=EnrollmentStatus.ACTIVE,
    )
    enr_b = Enrollment(
        student_id=student_other.id,
        group_id=group_b.id,
        academic_year_id=year1.id,
        status=EnrollmentStatus.ACTIVE,
    )
    # Assignment in 10-A
    assignment_a = AcademicAssignment(
        teacher_id=teacher.id,
        subject_id=subject.id,
        group_id=group_a.id,
        academic_year_id=year1.id,
        weekly_hours=3,
        is_active=True,
    )
    db_session.add_all([enr_a, enr_b, assignment_a])
    await db_session.commit()

    mock_provider = MockMeetingProvider()

    return {
        "inst1": inst1,
        "inst2": inst2,
        "assignment_a": assignment_a,
        "teacher_user": teacher_user,
        "student_enrolled_user": student_enrolled_user,
        "student_other_group_user": student_other_group_user,
        "rector_user": rector_user,
        "mock_provider": mock_provider,
    }


# =============================================================================
# 1. VirtualClassroomService Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_and_launch_virtual_classroom(
    db_session: AsyncSession,
    vc_service_fixture: dict[str, Any],
) -> None:
    """Tests creating and launching a virtual classroom session."""
    provider: MockMeetingProvider = vc_service_fixture["mock_provider"]
    service = VirtualClassroomService(session=db_session, provider=provider)

    # 1. Create Classroom
    classroom = await service.create_virtual_classroom(
        institution_id=vc_service_fixture["inst1"].id,
        host_user_id=vc_service_fixture["teacher_user"].id,
        title="Sesión 1: Células Eucariotas",
        description="Estructura y organelos celulares",
        academic_assignment_id=vc_service_fixture["assignment_a"].id,
        is_recording_enabled=True,
    )

    assert classroom.id is not None
    assert classroom.status == VirtualClassroomStatus.SCHEDULED
    assert classroom.title == "Sesión 1: Células Eucariotas"
    assert classroom.bbb_meeting_id.startswith("pevn-")

    # 2. Launch Classroom
    launched = await service.launch_virtual_classroom(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
    )
    assert launched.status == VirtualClassroomStatus.RUNNING
    assert launched.actual_start_time is not None


@pytest.mark.asyncio
async def test_virtual_classroom_anchoring_and_cross_tenant_validation(
    db_session: AsyncSession,
    vc_service_fixture: dict[str, Any],
) -> None:
    """Tests assignment validation and cross-tenant isolation during classroom creation."""
    provider: MockMeetingProvider = vc_service_fixture["mock_provider"]
    service = VirtualClassroomService(session=db_session, provider=provider)

    # Non-existent assignment
    with pytest.raises(AcademicAssignmentNotFoundError):
        await service.create_virtual_classroom(
            institution_id=vc_service_fixture["inst1"].id,
            host_user_id=vc_service_fixture["teacher_user"].id,
            title="Invalida",
            academic_assignment_id=uuid.uuid4(),
        )

    # Cross-tenant assignment mismatch (Tenant 2 trying to use Tenant 1's assignment)
    with pytest.raises(CrossTenantMismatchError):
        await service.create_virtual_classroom(
            institution_id=vc_service_fixture["inst2"].id,
            host_user_id=vc_service_fixture["teacher_user"].id,
            title="Cross Tenant",
            academic_assignment_id=vc_service_fixture["assignment_a"].id,
        )


@pytest.mark.asyncio
async def test_generate_join_url_authority_and_enrollment_verification(
    db_session: AsyncSession,
    vc_service_fixture: dict[str, Any],
) -> None:
    """Tests moderator vs student viewer join URL generation and unauthorized student rejection."""
    provider: MockMeetingProvider = vc_service_fixture["mock_provider"]
    service = VirtualClassroomService(session=db_session, provider=provider)

    classroom = await service.create_virtual_classroom(
        institution_id=vc_service_fixture["inst1"].id,
        host_user_id=vc_service_fixture["teacher_user"].id,
        title="Clase de Biología",
        academic_assignment_id=vc_service_fixture["assignment_a"].id,
    )

    # 1. Teacher Host joins as MODERATOR
    teacher_url = await service.generate_join_url(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
        user=vc_service_fixture["teacher_user"],
        user_roles=["teacher"],
    )
    assert "role=MODERATOR" in teacher_url
    assert "meetingID=" in teacher_url

    # 2. Rector joins as MODERATOR (Administrative privilege)
    rector_url = await service.generate_join_url(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
        user=vc_service_fixture["rector_user"],
        user_roles=["rector"],
    )
    assert "role=MODERATOR" in rector_url

    # 3. Enrolled student in 10-A joins as VIEWER
    student_url = await service.generate_join_url(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
        user=vc_service_fixture["student_enrolled_user"],
        user_roles=["student"],
    )
    assert "role=VIEWER" in student_url

    # 4. Unenrolled student (from 10-B) tries to join -> MUST BE BLOCKED (403)
    with pytest.raises(
        UnauthorizedMeetingAccessError, match="no cuenta con matrícula activa"
    ):
        await service.generate_join_url(
            classroom_id=classroom.id,
            institution_id=vc_service_fixture["inst1"].id,
            user=vc_service_fixture["student_other_group_user"],
            user_roles=["student"],
        )

    # 5. Cross-tenant classroom access -> MUST RETURN 404 (Blind isolation)
    with pytest.raises(VirtualClassroomNotFoundError):
        await service.generate_join_url(
            classroom_id=classroom.id,
            institution_id=vc_service_fixture["inst2"].id,
            user=vc_service_fixture["student_enrolled_user"],
            user_roles=["student"],
        )


@pytest.mark.asyncio
async def test_end_virtual_classroom_lifecycle(
    db_session: AsyncSession,
    vc_service_fixture: dict[str, Any],
) -> None:
    """Tests session termination and open attendance closure."""
    provider: MockMeetingProvider = vc_service_fixture["mock_provider"]
    service = VirtualClassroomService(session=db_session, provider=provider)

    classroom = await service.create_virtual_classroom(
        institution_id=vc_service_fixture["inst1"].id,
        host_user_id=vc_service_fixture["teacher_user"].id,
        title="Clase por finalizar",
        academic_assignment_id=vc_service_fixture["assignment_a"].id,
    )
    await service.launch_virtual_classroom(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
    )

    # Student from other group attempting to end class -> 403 Forbidden
    with pytest.raises(UnauthorizedMeetingAccessError):
        await service.end_virtual_classroom(
            classroom_id=classroom.id,
            institution_id=vc_service_fixture["inst1"].id,
            user_id=vc_service_fixture["student_enrolled_user"].id,
            user_roles=["student"],
        )

    # Host ends class successfully
    ended = await service.end_virtual_classroom(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
        user_id=vc_service_fixture["teacher_user"].id,
        user_roles=["teacher"],
    )
    assert ended.status == VirtualClassroomStatus.ENDED
    assert ended.actual_end_time is not None

    # Attempting to launch or join an ENDED class -> 409 Conflict
    with pytest.raises(VirtualClassroomLifecycleError):
        await service.launch_virtual_classroom(
            classroom_id=classroom.id,
            institution_id=vc_service_fixture["inst1"].id,
        )


# =============================================================================
# 2. AttendanceService Tests
# =============================================================================


@pytest.mark.asyncio
async def test_attendance_service_join_leave_and_duration(
    db_session: AsyncSession,
    vc_service_fixture: dict[str, Any],
) -> None:
    """Tests recording join/leave events and duration calculation."""
    provider: MockMeetingProvider = vc_service_fixture["mock_provider"]
    vc_service = VirtualClassroomService(session=db_session, provider=provider)
    att_service = AttendanceService(session=db_session)

    classroom = await vc_service.create_virtual_classroom(
        institution_id=vc_service_fixture["inst1"].id,
        host_user_id=vc_service_fixture["teacher_user"].id,
        title="Clase de Asistencia",
    )

    # Join
    join_log = await att_service.record_join(
        classroom_id=classroom.id,
        user_id=vc_service_fixture["student_enrolled_user"].id,
        role=MeetingParticipantRole.VIEWER,
    )
    assert join_log.id is not None
    assert join_log.joined_at is not None
    assert join_log.left_at is None
    assert join_log.duration_seconds is None

    # Leave
    leave_log = await att_service.record_leave(
        classroom_id=classroom.id,
        user_id=vc_service_fixture["student_enrolled_user"].id,
    )
    assert leave_log is not None
    assert leave_log.left_at is not None
    assert leave_log.duration_seconds is not None
    assert leave_log.duration_seconds >= 0

    # List attendances
    items, total = await att_service.list_classroom_attendances(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
    )
    assert total == 1
    assert items[0].user.username == "est_enrolled"


# =============================================================================
# 3. RecordingService Tests
# =============================================================================


@pytest.mark.asyncio
async def test_recording_service_sync_publish_and_delete(
    db_session: AsyncSession,
    vc_service_fixture: dict[str, Any],
) -> None:
    """Tests synchronizing, publishing, and deleting session recordings."""
    provider: MockMeetingProvider = vc_service_fixture["mock_provider"]
    vc_service = VirtualClassroomService(session=db_session, provider=provider)
    rec_service = RecordingService(session=db_session, provider=provider)

    classroom = await vc_service.create_virtual_classroom(
        institution_id=vc_service_fixture["inst1"].id,
        host_user_id=vc_service_fixture["teacher_user"].id,
        title="Clase con Grabación",
        is_recording_enabled=True,
    )

    # 1. Synchronize from provider
    synced = await rec_service.sync_recordings_from_provider(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
    )
    assert len(synced) == 1
    rec = synced[0]
    assert rec.bbb_record_id.startswith("mock-rec-")
    assert rec.is_published is True

    # 2. Toggle publication visibility to unpublished
    unpub = await rec_service.publish_recording(
        recording_id=rec.id,
        institution_id=vc_service_fixture["inst1"].id,
        is_published=False,
    )
    assert unpub.is_published is False

    # 3. Student list -> should not see unpublished recording
    _student_items, student_total = await rec_service.list_recordings(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
        user_roles=["student"],
    )
    assert student_total == 0

    # Staff list -> sees all recordings
    _staff_items, staff_total = await rec_service.list_recordings(
        classroom_id=classroom.id,
        institution_id=vc_service_fixture["inst1"].id,
        user_roles=["teacher"],
    )
    assert staff_total == 1

    # 4. Delete recording
    deleted = await rec_service.delete_recording(
        recording_id=rec.id,
        institution_id=vc_service_fixture["inst1"].id,
    )
    assert deleted is True

    # Confirm deletion
    with pytest.raises(RecordingNotFoundError):
        await rec_service.publish_recording(
            recording_id=rec.id,
            institution_id=vc_service_fixture["inst1"].id,
            is_published=True,
        )
