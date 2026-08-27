"""
PEVN Backend — Phase 4 Step 1: Virtual Classroom Domain Model Tests

Validates model instantiation, defaults, foreign key relationships,
lifecycle enums, and database persistence invariants.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security.password import password_hasher
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.models.virtual_classroom import (
    MeetingAttendance,
    MeetingParticipantRole,
    MeetingRecording,
    VirtualClassroom,
    VirtualClassroomStatus,
)


@pytest.mark.asyncio
async def test_virtual_classroom_models_and_relationships(  # noqa: PLR0915
    db_session: AsyncSession,
) -> None:
    """
    Validates complete lifecycle, foreign-key linkages, and attendance/recording
    persistence for VirtualClassroom, MeetingAttendance, and MeetingRecording.
    """
    # 1. Setup Territory & Institution
    dept = Department(code="11", name="Bogota D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogota")
    db_session.add(mun)
    await db_session.flush()

    inst = Institution(
        municipality_id=mun.id,
        dane_code="11100100999",
        name="Colegio Mayor de San Bartolomé",
        email="rectoria@sanbartolome.edu.co",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code="11100100999-01",
        name="Sede Principal",
        is_active=True,
    )
    db_session.add(campus)
    await db_session.flush()

    # 2. Setup Academic Year & Structure
    year = AcademicYear(
        institution_id=inst.id,
        year=2026,
        name="Año Lectivo 2026",
        start_date=datetime(2026, 2, 1, tzinfo=UTC).date(),
        end_date=datetime(2026, 11, 30, tzinfo=UTC).date(),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    grade = Grade(
        code="11-VC",
        name="Grado Once Virtual",
        level=EducationalLevel.MEDIA,
        ordinal_order=11,
    )
    db_session.add_all([year, grade])
    await db_session.flush()

    group = Group(
        campus_id=campus.id,
        academic_year_id=year.id,
        grade_id=grade.id,
        name="11-A Virtual",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    area = KnowledgeArea(
        institution_id=inst.id,
        name="Tecnología e Informática",
        is_mandatory=True,
    )
    db_session.add_all([group, area])
    await db_session.flush()

    subject = Subject(
        institution_id=inst.id,
        knowledge_area_id=area.id,
        grade_id=grade.id,
        name="Informática Avanzada",
        weekly_hours=3,
    )
    db_session.add(subject)
    await db_session.flush()

    # 3. Setup Users & Teacher
    pwd = password_hasher.hash("Seguro123456*!")
    teacher_user = User(
        email="docente.virtual@pevn.edu.co",
        username="docente_virtual",
        hashed_password=pwd,
        first_name="Profesor",
        last_name="Virtual",
        document_type=DocumentType.CC,
        document_number="79555666",
        institution_id=inst.id,
        is_active=True,
        is_verified=True,
    )
    student_user = User(
        email="alumno.virtual@pevn.edu.co",
        username="alumno_virtual",
        hashed_password=pwd,
        first_name="Estudiante",
        last_name="Online",
        document_type=DocumentType.TI,
        document_number="1099887766",
        institution_id=inst.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([teacher_user, student_user])
    await db_session.flush()

    teacher = Teacher(
        user_id=teacher_user.id,
        institution_id=inst.id,
        specialty_area="Ingeniería de Sistemas",
        contract_type=TeacherContractType.PROPIEDAD,
        escalafon_grade="14",
    )
    db_session.add(teacher)
    await db_session.flush()

    # 4. Setup Academic Assignment
    assignment = AcademicAssignment(
        teacher_id=teacher.id,
        subject_id=subject.id,
        group_id=group.id,
        academic_year_id=year.id,
        weekly_hours=3,
        is_active=True,
    )
    db_session.add(assignment)
    await db_session.flush()

    # 5. Create VirtualClassroom
    bbb_id = f"pevn-{uuid.uuid4().hex[:12]}"
    vroom = VirtualClassroom(
        institution_id=inst.id,
        academic_assignment_id=assignment.id,
        host_user_id=teacher_user.id,
        title="Clase 1: Programación Web Asíncrona",
        description="Introducción a FastAPI y PostgreSQL",
        bbb_meeting_id=bbb_id,
        moderator_password_hash="mod_pwd_hash_123",
        attendee_password_hash="att_pwd_hash_456",
        status=VirtualClassroomStatus.SCHEDULED,
        scheduled_start_time=datetime(2026, 3, 1, 8, 0, tzinfo=UTC),
        scheduled_end_time=datetime(2026, 3, 1, 10, 0, tzinfo=UTC),
        is_recording_enabled=True,
        is_breakout_enabled=False,
        max_participants=50,
        provider_metadata={"welcome_msg": "Bienvenidos al aula virtual PEVN"},
    )
    db_session.add(vroom)
    await db_session.flush()

    assert vroom.id is not None
    assert vroom.status == VirtualClassroomStatus.SCHEDULED
    assert vroom.is_recording_enabled is True
    assert vroom.max_participants == 50

    # 6. Track Meeting Attendance
    attendance = MeetingAttendance(
        virtual_classroom_id=vroom.id,
        user_id=student_user.id,
        role=MeetingParticipantRole.VIEWER,
        joined_at=datetime(2026, 3, 1, 8, 5, tzinfo=UTC),
        left_at=datetime(2026, 3, 1, 9, 55, tzinfo=UTC),
        duration_seconds=6600,
    )
    db_session.add(attendance)
    await db_session.flush()

    assert attendance.id is not None
    assert attendance.role == MeetingParticipantRole.VIEWER
    assert attendance.duration_seconds == 6600

    # 7. Track Meeting Recording
    rec_id = f"rec-{uuid.uuid4().hex[:12]}"
    recording = MeetingRecording(
        institution_id=inst.id,
        virtual_classroom_id=vroom.id,
        bbb_record_id=rec_id,
        playback_url="https://bbb.pevn.gov.co/playback/presentation/2.3/" + rec_id,
        duration_seconds=7200,
        file_size_bytes=154857600,
        is_published=True,
        recording_metadata={"resolution": "1080p", "format": "presentation"},
        recorded_at=datetime(2026, 3, 1, 10, 0, tzinfo=UTC),
    )
    db_session.add(recording)
    await db_session.commit()

    # 8. Verify Queries & Relationships
    query = (
        select(VirtualClassroom)
        .where(VirtualClassroom.id == vroom.id)
        .options(
            selectinload(VirtualClassroom.attendances).selectinload(
                MeetingAttendance.user
            ),
            selectinload(VirtualClassroom.recordings),
            selectinload(VirtualClassroom.academic_assignment).selectinload(
                AcademicAssignment.subject
            ),
        )
    )
    refreshed_room = (await db_session.execute(query)).scalar_one()
    assert refreshed_room is not None
    assert refreshed_room.academic_assignment is not None
    assert refreshed_room.academic_assignment.subject.name == "Informática Avanzada"
    assert len(refreshed_room.attendances) == 1
    assert refreshed_room.attendances[0].user.username == "alumno_virtual"
    assert len(refreshed_room.recordings) == 1
    assert refreshed_room.recordings[0].bbb_record_id == rec_id
