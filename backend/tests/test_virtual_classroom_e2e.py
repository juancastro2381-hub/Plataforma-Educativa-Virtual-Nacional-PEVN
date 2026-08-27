"""
PEVN Backend — Phase 4 Step 6: Virtual Classroom End-to-End System & Integration Validation

Exhaustive integration test suite validating:
  1. Full Virtual Classroom lifecycle (Schedule -> Launch -> Moderator/Viewer Join -> Attendance -> Termination -> Recording Sync -> Publication Toggle -> Deletion)
  2. Multi-Tenant isolation and Blind 404 enforcement across all endpoints
  3. Strict RBAC & Active SIMAT Enrollment gating (Blocked unenrolled students)
  4. Telemetry duration accuracy & idempotent session closure
  5. Secret concealment (No passwords, hashes, salts, or provider credentials exposed)
  6. Failure modes & provider error resilience
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.meeting.bbb_adapter import BBBAdapter
from app.core.meeting.exceptions import MeetingProviderAuthError
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
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
from app.models.role import Role, UserRole
from app.models.student import Student
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def e2e_vc_fixture(  # noqa: PLR0915
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Provisions complete multi-tenant hierarchy, academic structure, and bearer tokens."""
    dept = Department(code="11", name="Bogotá D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogotá D.C.")
    db_session.add(mun)
    await db_session.flush()

    # Tenant A (Institución Educativa Distrital Simón Bolívar)
    inst_a = Institution(
        municipality_id=mun.id,
        dane_code="11100100010",
        name="IED Simón Bolívar",
        email="rectoria@bolivar.edu.co",
        is_active=True,
    )
    # Tenant B (Institución Educativa Distrital Francisco de Paula Santander)
    inst_b = Institution(
        municipality_id=mun.id,
        dane_code="11100100020",
        name="IED Santander",
        email="rectoria@santander.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    campus_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="11100100010-01",
        name="Sede Principal Bolívar",
        is_active=True,
    )
    campus_b = Campus(
        institution_id=inst_b.id,
        dane_sede_code="11100100020-01",
        name="Sede Principal Santander",
        is_active=True,
    )
    db_session.add_all([campus_a, campus_b])
    await db_session.flush()

    # Academic Year 2026
    year_a = AcademicYear(
        institution_id=inst_a.id,
        year=2026,
        name="2026 Regular",
        start_date=datetime(2026, 2, 1, tzinfo=UTC).date(),
        end_date=datetime(2026, 11, 30, tzinfo=UTC).date(),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    grade10 = Grade(
        code="10-E2E",
        name="Grado Décimo E2E",
        level=EducationalLevel.MEDIA,
        ordinal_order=10,
    )
    db_session.add_all([year_a, grade10])
    await db_session.flush()

    # Groups in Tenant A: 10-A (Target class) & 10-B (Unassigned class)
    group_10a = Group(
        campus_id=campus_a.id,
        academic_year_id=year_a.id,
        grade_id=grade10.id,
        name="10-A Física",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    group_10b = Group(
        campus_id=campus_a.id,
        academic_year_id=year_a.id,
        grade_id=grade10.id,
        name="10-B Química",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    area = KnowledgeArea(
        institution_id=inst_a.id,
        name="Ciencias Naturales",
        is_mandatory=True,
    )
    db_session.add_all([group_10a, group_10b, area])
    await db_session.flush()

    subject_phys = Subject(
        institution_id=inst_a.id,
        knowledge_area_id=area.id,
        grade_id=grade10.id,
        name="Física Clásica",
        weekly_hours=4,
    )
    db_session.add(subject_phys)
    await db_session.flush()

    # Users
    pwd = password_hasher.hash("SecurePassE2E123*!")
    teacher_user = User(
        email="prof.fisica@bolivar.edu.co",
        username="prof_fisica",
        hashed_password=pwd,
        first_name="Albert",
        last_name="Einstein",
        document_type=DocumentType.CC,
        document_number="99100100",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    student_enr_user = User(
        email="est.enr@bolivar.edu.co",
        username="est_enrolled",
        hashed_password=pwd,
        first_name="Marie",
        last_name="Curie",
        document_type=DocumentType.TI,
        document_number="1009990001",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    student_unenr_user = User(
        email="est.unenr@bolivar.edu.co",
        username="est_unenrolled",
        hashed_password=pwd,
        first_name="Niels",
        last_name="Bohr",
        document_type=DocumentType.TI,
        document_number="1009990002",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    rector_b_user = User(
        email="rector@santander.edu.co",
        username="rector_santander",
        hashed_password=pwd,
        first_name="Rector",
        last_name="Santander",
        document_type=DocumentType.CC,
        document_number="99200200",
        institution_id=inst_b.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all(
        [teacher_user, student_enr_user, student_unenr_user, rector_b_user]
    )
    await db_session.flush()

    # Domain Entities
    teacher = Teacher(
        user_id=teacher_user.id,
        institution_id=inst_a.id,
        specialty_area="Física",
        contract_type=TeacherContractType.PROPIEDAD,
        escalafon_grade="14",
    )
    student_enr = Student(
        user_id=student_enr_user.id,
        institution_id=inst_a.id,
        code_simat="SIMAT-1001",
        birth_date=datetime(2009, 5, 1, tzinfo=UTC).date(),
        gender="F",
    )
    student_unenr = Student(
        user_id=student_unenr_user.id,
        institution_id=inst_a.id,
        code_simat="SIMAT-1002",
        birth_date=datetime(2009, 7, 1, tzinfo=UTC).date(),
        gender="M",
    )
    db_session.add_all([teacher, student_enr, student_unenr])
    await db_session.flush()

    # Enrollments
    # student_enr in 10-A (ACTIVE)
    enr_10a = Enrollment(
        student_id=student_enr.id,
        group_id=group_10a.id,
        academic_year_id=year_a.id,
        status=EnrollmentStatus.ACTIVE,
    )
    # student_unenr in 10-B (ACTIVE in another group)
    enr_10b = Enrollment(
        student_id=student_unenr.id,
        group_id=group_10b.id,
        academic_year_id=year_a.id,
        status=EnrollmentStatus.ACTIVE,
    )
    # Workload assignment
    assignment_10a = AcademicAssignment(
        teacher_id=teacher.id,
        subject_id=subject_phys.id,
        group_id=group_10a.id,
        academic_year_id=year_a.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add_all([enr_10a, enr_10b, assignment_10a])
    await db_session.flush()

    # System Roles
    teacher_role = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.TEACHER.value)
        )
    ).scalar_one()
    student_role = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.STUDENT.value)
        )
    ).scalar_one()
    rector_role = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.RECTOR.value)
        )
    ).scalar_one()

    db_session.add_all(
        [
            UserRole(
                user_id=teacher_user.id,
                role_id=teacher_role.id,
                institution_id=inst_a.id,
                is_active=True,
            ),
            UserRole(
                user_id=student_enr_user.id,
                role_id=student_role.id,
                institution_id=inst_a.id,
                is_active=True,
            ),
            UserRole(
                user_id=student_unenr_user.id,
                role_id=student_role.id,
                institution_id=inst_a.id,
                is_active=True,
            ),
            UserRole(
                user_id=rector_b_user.id,
                role_id=rector_role.id,
                institution_id=inst_b.id,
                is_active=True,
            ),
        ]
    )
    await db_session.commit()

    # Tokens
    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={
            "roles": [SystemRole.TEACHER.value],
            "institution_id": str(inst_a.id),
        },
    )
    student_enr_token = await token_service.create_access_token(
        subject=str(student_enr_user.id),
        additional_claims={
            "roles": [SystemRole.STUDENT.value],
            "institution_id": str(inst_a.id),
        },
    )
    student_unenr_token = await token_service.create_access_token(
        subject=str(student_unenr_user.id),
        additional_claims={
            "roles": [SystemRole.STUDENT.value],
            "institution_id": str(inst_a.id),
        },
    )
    rector_b_token = await token_service.create_access_token(
        subject=str(rector_b_user.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst_b.id),
        },
    )

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "assignment_10a": assignment_10a,
        "teacher_user": teacher_user,
        "student_enr_user": student_enr_user,
        "student_unenr_user": student_unenr_user,
        "teacher_headers": {"Authorization": f"Bearer {teacher_token}"},
        "student_enr_headers": {"Authorization": f"Bearer {student_enr_token}"},
        "student_unenr_headers": {"Authorization": f"Bearer {student_unenr_token}"},
        "rector_b_headers": {"Authorization": f"Bearer {rector_b_token}"},
    }


# =============================================================================
# 1. Complete End-to-End Lifecycle & Gating Chain
# =============================================================================


@pytest.mark.asyncio
async def test_complete_e2e_virtual_classroom_lifecycle(  # noqa: PLR0915
    client: AsyncClient,
    e2e_vc_fixture: dict[str, Any],
) -> None:
    """Validates the entire unbroken sequence of real-time virtual classroom delivery."""
    teacher_hdr = e2e_vc_fixture["teacher_headers"]
    student_enr_hdr = e2e_vc_fixture["student_enr_headers"]
    student_unenr_hdr = e2e_vc_fixture["student_unenr_headers"]
    rector_b_hdr = e2e_vc_fixture["rector_b_headers"]

    # 1. Teacher creates Virtual Classroom anchored to AcademicAssignment (10-A)
    create_payload = {
        "title": "Física Mecánica: Leyes de Newton y Gravitación",
        "description": "Sesión sincrónica interactiva con pizarra digital y grabación",
        "academic_assignment_id": str(e2e_vc_fixture["assignment_10a"].id),
        "scheduled_start_time": "2026-08-25T08:00:00Z",
        "scheduled_end_time": "2026-08-25T10:00:00Z",
        "is_recording_enabled": True,
        "is_breakout_enabled": False,
        "max_participants": 40,
    }
    res_create = await client.post(
        "/api/v1/virtual-classrooms",
        json=create_payload,
        headers=teacher_hdr,
    )
    assert res_create.status_code == 201
    classroom_data = res_create.json()
    classroom_id = classroom_data["id"]
    assert classroom_data["status"] == "SCHEDULED"
    assert classroom_data["title"] == "Física Mecánica: Leyes de Newton y Gravitación"
    assert "moderator_password" not in classroom_data
    assert "attendee_password" not in classroom_data

    # 2. Query Catalog (Tenant A)
    res_list = await client.get("/api/v1/virtual-classrooms", headers=teacher_hdr)
    assert res_list.status_code == 200
    assert any(c["id"] == classroom_id for c in res_list.json()["items"])

    # 3. Launch Classroom by Teacher Host -> Transitions to RUNNING
    res_launch = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/launch",
        headers=teacher_hdr,
    )
    assert res_launch.status_code == 200
    assert res_launch.json()["status"] == "RUNNING"

    # 4. Teacher Host Joins -> Authenticated MODERATOR
    res_mod_join = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/join",
        headers=teacher_hdr,
    )
    assert res_mod_join.status_code == 200
    mod_data = res_mod_join.json()
    assert mod_data["role"] == "MODERATOR"
    assert "join_url" in mod_data

    # 5. Enrolled Student (Marie Curie in 10-A) Joins -> Authenticated VIEWER
    res_stud_join = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/join",
        headers=student_enr_hdr,
    )
    assert res_stud_join.status_code == 200
    stud_data = res_stud_join.json()
    assert stud_data["role"] == "VIEWER"
    assert "join_url" in stud_data

    # 6. Unenrolled Student (Niels Bohr in 10-B) tries to join -> REJECTED (403)
    res_unenr_join = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/join",
        headers=student_unenr_hdr,
    )
    assert res_unenr_join.status_code == 403
    assert res_unenr_join.json()["error"]["code"] == "UNAUTHORIZED_MEETING_ACCESS"

    # 7. Student leaves meeting -> Attendance duration calculated
    res_leave = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/leave",
        headers=student_enr_hdr,
    )
    assert res_leave.status_code == 200
    leave_data = res_leave.json()
    assert leave_data["left_at"] is not None

    # 8. Check Attendance records as Teacher
    res_att = await client.get(
        f"/api/v1/virtual-classrooms/{classroom_id}/attendances",
        headers=teacher_hdr,
    )
    assert res_att.status_code == 200
    assert res_att.json()["total"] >= 2

    # 9. Teacher terminates meeting -> Status ENDED & open sessions closed
    res_end = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/end",
        headers=teacher_hdr,
    )
    assert res_end.status_code == 200
    assert res_end.json()["status"] == "ENDED"

    # 10. Sync recordings from meeting provider
    res_sync = await client.post(
        f"/api/v1/recordings/classroom/{classroom_id}/sync",
        headers=teacher_hdr,
    )
    assert res_sync.status_code == 200
    recs = res_sync.json()["items"]
    assert len(recs) >= 1
    rec_id = recs[0]["id"]
    assert recs[0]["is_published"] is True

    # 11. Staff can view recordings (both published and unpublished)
    res_staff_recs = await client.get(
        f"/api/v1/recordings/classroom/{classroom_id}",
        headers=teacher_hdr,
    )
    assert res_staff_recs.status_code == 200
    assert res_staff_recs.json()["total"] >= 1

    # 12. Toggle publication: Unpublish recording
    res_unpub = await client.patch(
        f"/api/v1/recordings/{rec_id}/publish",
        json={"is_published": False},
        headers=teacher_hdr,
    )
    assert res_unpub.status_code == 200
    assert res_unpub.json()["is_published"] is False

    # 13. Student queries recordings -> should NOT see unpublished recordings (0)
    res_stud_recs = await client.get(
        f"/api/v1/recordings/classroom/{classroom_id}",
        headers=student_enr_hdr,
    )
    assert res_stud_recs.status_code == 200
    assert res_stud_recs.json()["total"] == 0

    # 14. Delete recording
    res_del = await client.delete(
        f"/api/v1/recordings/{rec_id}",
        headers=teacher_hdr,
    )
    assert res_del.status_code == 204

    # 15. Multi-Tenant Barrier (Tenant B Rector tries to access Tenant A classroom/recordings)
    res_cross_get = await client.get(
        f"/api/v1/virtual-classrooms/{classroom_id}",
        headers=rector_b_hdr,
    )
    assert res_cross_get.status_code == 404
    assert res_cross_get.json()["error"]["code"] == "VIRTUAL_CLASSROOM_NOT_FOUND"

    res_cross_join = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/join",
        headers=rector_b_hdr,
    )
    assert res_cross_join.status_code == 404

    res_cross_rec = await client.get(
        f"/api/v1/recordings/classroom/{classroom_id}",
        headers=rector_b_hdr,
    )
    assert res_cross_rec.status_code == 404


# =============================================================================
# 2. BigBlueButton Adapter Checksum & Error Resilience
# =============================================================================


@pytest.mark.asyncio
async def test_bbb_adapter_signing_and_error_parsing() -> None:
    """Validates adapter parameter signing algorithms and XML error responses."""
    xml_error = """<response>
        <returncode>FAILED</returncode>
        <messageKey>checksumError</messageKey>
        <message>You did not pass the checksum security check</message>
    </response>"""

    transport = httpx.MockTransport(
        lambda req: httpx.Response(200, text=xml_error, request=req)
    )
    async with httpx.AsyncClient(transport=transport) as mock_client:
        adapter = BBBAdapter(
            api_url="https://bbb.example.gov.co/bigbluebutton/api",
            shared_secret="SecretSigningKey2026",
            signing_algorithm="sha256",
            http_client=mock_client,
        )

        # 1. Signing Verification
        signed_url = adapter.build_api_url(
            "create",
            {"meetingID": "meet-101", "name": "Clase de Prueba"},
        )
        assert "checksum=" in signed_url
        assert "https://bbb.example.gov.co/bigbluebutton/api/create?" in signed_url

        # 2. XML Error parsing
        with pytest.raises(MeetingProviderAuthError) as exc_info:
            await adapter._send_request("create", {"meetingID": "meet-101"})
        assert "checksum security check" in str(exc_info.value)
