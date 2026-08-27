"""
PEVN Backend — Phase 4 Step 4: Virtual Classroom & Recordings REST API Integration Tests

Validates all Virtual Classroom endpoints, authentication, RBAC, student active enrollment
gating, join URL generation, attendance telemetry, recording management, and Blind 404 isolation.
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
async def vc_api_fixture(  # noqa: PLR0915
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Sets up institutional hierarchy, assignments, enrolled students, and bearer tokens."""
    dept = Department(code="25", name="Cundinamarca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="25001", name="Agua de Dios")
    db_session.add(mun)
    await db_session.flush()

    # Inst 1
    inst1 = Institution(
        municipality_id=mun.id,
        dane_code="22500100001",
        name="Colegio Virtual Central",
        email="rector@central.edu.co",
        is_active=True,
    )
    # Inst 2 (Cross-tenant)
    inst2 = Institution(
        municipality_id=mun.id,
        dane_code="22500100002",
        name="Colegio Virtual Periferico",
        email="rector@periferico.edu.co",
        is_active=True,
    )
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    campus1 = Campus(
        institution_id=inst1.id,
        dane_sede_code="22500100001-01",
        name="Sede Central",
        is_active=True,
    )
    db_session.add(campus1)
    await db_session.flush()

    # Academic Structure
    year1 = AcademicYear(
        institution_id=inst1.id,
        year=2026,
        name="2026 Regular",
        start_date=datetime(2026, 2, 1, tzinfo=UTC).date(),
        end_date=datetime(2026, 11, 30, tzinfo=UTC).date(),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    grade11 = Grade(
        code="11-VC",
        name="Grado Once VC",
        level=EducationalLevel.MEDIA,
        ordinal_order=11,
    )
    db_session.add_all([year1, grade11])
    await db_session.flush()

    group_11a = Group(
        campus_id=campus1.id,
        academic_year_id=year1.id,
        grade_id=grade11.id,
        name="11-A Virtual",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    group_11b = Group(
        campus_id=campus1.id,
        academic_year_id=year1.id,
        grade_id=grade11.id,
        name="11-B Virtual",
        shift=ShiftEnum.TARDE,
        capacity_limit=35,
    )
    area = KnowledgeArea(
        institution_id=inst1.id,
        name="Matemáticas",
        is_mandatory=True,
    )
    db_session.add_all([group_11a, group_11b, area])
    await db_session.flush()

    subject_calc = Subject(
        institution_id=inst1.id,
        knowledge_area_id=area.id,
        grade_id=grade11.id,
        name="Cálculo Diferencial",
        weekly_hours=4,
    )
    db_session.add(subject_calc)
    await db_session.flush()

    # Users
    pwd = password_hasher.hash("SecurePass1234*!")
    teacher_user = User(
        email="prof.calc@central.edu.co",
        username="prof_calc",
        hashed_password=pwd,
        first_name="Leonardo",
        last_name="Euler",
        document_type=DocumentType.CC,
        document_number="88100200",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    student_enrolled_user = User(
        email="est.enr@central.edu.co",
        username="est_enr",
        hashed_password=pwd,
        first_name="Isaac",
        last_name="Newton",
        document_type=DocumentType.TI,
        document_number="1002003001",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    student_unenrolled_user = User(
        email="est.unenr@central.edu.co",
        username="est_unenr",
        hashed_password=pwd,
        first_name="Gottfried",
        last_name="Leibniz",
        document_type=DocumentType.TI,
        document_number="1002003002",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    tenant2_user = User(
        email="rector@periferico.edu.co",
        username="rector_t2",
        hashed_password=pwd,
        first_name="Rector",
        last_name="Tenant2",
        document_type=DocumentType.CC,
        document_number="88100999",
        institution_id=inst2.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all(
        [
            teacher_user,
            student_enrolled_user,
            student_unenrolled_user,
            tenant2_user,
        ]
    )
    await db_session.flush()

    # Domain Entities
    teacher = Teacher(
        user_id=teacher_user.id,
        institution_id=inst1.id,
        specialty_area="Matemáticas",
        contract_type=TeacherContractType.PROPIEDAD,
        escalafon_grade="14",
    )
    student_enr = Student(
        user_id=student_enrolled_user.id,
        institution_id=inst1.id,
        code_simat="SIMAT-1101",
        birth_date=datetime(2009, 1, 1, tzinfo=UTC).date(),
        gender="M",
    )
    student_unenr = Student(
        user_id=student_unenrolled_user.id,
        institution_id=inst1.id,
        code_simat="SIMAT-1102",
        birth_date=datetime(2009, 3, 1, tzinfo=UTC).date(),
        gender="M",
    )
    db_session.add_all([teacher, student_enr, student_unenr])
    await db_session.flush()

    # Enrollments
    # student_enr in 11-A (ACTIVE)
    enr_11a = Enrollment(
        student_id=student_enr.id,
        group_id=group_11a.id,
        academic_year_id=year1.id,
        status=EnrollmentStatus.ACTIVE,
    )
    # student_unenr in 11-B (ACTIVE in another group)
    enr_11b = Enrollment(
        student_id=student_unenr.id,
        group_id=group_11b.id,
        academic_year_id=year1.id,
        status=EnrollmentStatus.ACTIVE,
    )
    # Academic assignment for 11-A
    assignment_11a = AcademicAssignment(
        teacher_id=teacher.id,
        subject_id=subject_calc.id,
        group_id=group_11a.id,
        academic_year_id=year1.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add_all([enr_11a, enr_11b, assignment_11a])
    await db_session.flush()

    # Roles
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
                institution_id=inst1.id,
                is_active=True,
            ),
            UserRole(
                user_id=student_enrolled_user.id,
                role_id=student_role.id,
                institution_id=inst1.id,
                is_active=True,
            ),
            UserRole(
                user_id=student_unenrolled_user.id,
                role_id=student_role.id,
                institution_id=inst1.id,
                is_active=True,
            ),
            UserRole(
                user_id=tenant2_user.id,
                role_id=rector_role.id,
                institution_id=inst2.id,
                is_active=True,
            ),
        ]
    )
    await db_session.commit()

    # Generate JWT Tokens
    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={
            "roles": [SystemRole.TEACHER.value],
            "institution_id": str(inst1.id),
        },
    )
    student_enr_token = await token_service.create_access_token(
        subject=str(student_enrolled_user.id),
        additional_claims={
            "roles": [SystemRole.STUDENT.value],
            "institution_id": str(inst1.id),
        },
    )
    student_unenr_token = await token_service.create_access_token(
        subject=str(student_unenrolled_user.id),
        additional_claims={
            "roles": [SystemRole.STUDENT.value],
            "institution_id": str(inst1.id),
        },
    )
    tenant2_token = await token_service.create_access_token(
        subject=str(tenant2_user.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst2.id),
        },
    )

    return {
        "inst1": inst1,
        "inst2": inst2,
        "assignment_11a": assignment_11a,
        "teacher_headers": {"Authorization": f"Bearer {teacher_token}"},
        "student_enr_headers": {"Authorization": f"Bearer {student_enr_token}"},
        "student_unenr_headers": {"Authorization": f"Bearer {student_unenr_token}"},
        "tenant2_headers": {"Authorization": f"Bearer {tenant2_token}"},
    }


# =============================================================================
# 1. Authentication & Security Gate Tests
# =============================================================================


@pytest.mark.asyncio
async def test_virtual_classrooms_unauthenticated_rejected(
    client: AsyncClient,
) -> None:
    """Verifies all endpoints reject unauthenticated requests with HTTP 401."""
    fake_id = uuid.uuid4()

    res_post = await client.post(
        "/api/v1/virtual-classrooms",
        json={"title": "Test Classroom"},
    )
    assert res_post.status_code == 401

    res_get = await client.get("/api/v1/virtual-classrooms")
    assert res_get.status_code == 401

    res_join = await client.post(f"/api/v1/virtual-classrooms/{fake_id}/join")
    assert res_join.status_code == 401

    res_rec = await client.get(f"/api/v1/recordings/classroom/{fake_id}")
    assert res_rec.status_code == 401


# =============================================================================
# 2. Virtual Classroom Lifecycle & Enrollment Access Tests
# =============================================================================


@pytest.mark.asyncio
async def test_virtual_classroom_full_lifecycle_and_join_authorization(
    client: AsyncClient,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Tests creation, launch, moderator/enrolled/unenrolled join, attendances, and end."""
    teacher_hdr = vc_api_fixture["teacher_headers"]
    student_enr_hdr = vc_api_fixture["student_enr_headers"]
    student_unenr_hdr = vc_api_fixture["student_unenr_headers"]
    tenant2_hdr = vc_api_fixture["tenant2_headers"]

    # 1. Teacher creates Virtual Classroom
    create_payload = {
        "title": "Cálculo Diferencial: Límites y Continuidad",
        "description": "Introducción intuitiva al concepto de límite",
        "academic_assignment_id": str(vc_api_fixture["assignment_11a"].id),
        "is_recording_enabled": True,
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
    assert classroom_data["title"] == "Cálculo Diferencial: Límites y Continuidad"
    assert classroom_data["status"] == "SCHEDULED"
    assert "moderator_password" not in classroom_data  # No secret leakage

    # 2. List Classrooms
    res_list = await client.get("/api/v1/virtual-classrooms", headers=teacher_hdr)
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 1

    # 3. Get Classroom by ID
    res_get = await client.get(
        f"/api/v1/virtual-classrooms/{classroom_id}",
        headers=teacher_hdr,
    )
    assert res_get.status_code == 200
    assert res_get.json()["id"] == classroom_id

    # 4. Launch Classroom
    res_launch = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/launch",
        headers=teacher_hdr,
    )
    assert res_launch.status_code == 200
    assert res_launch.json()["status"] == "RUNNING"

    # 5. Host Teacher joins -> MODERATOR
    res_teacher_join = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/join",
        headers=teacher_hdr,
    )
    assert res_teacher_join.status_code == 200
    teacher_join_data = res_teacher_join.json()
    assert teacher_join_data["role"] == "MODERATOR"
    assert "join_url" in teacher_join_data
    assert "pevn" in teacher_join_data["join_url"]

    # 6. Enrolled Student (in 11-A) joins -> VIEWER
    res_student_join = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/join",
        headers=student_enr_hdr,
    )
    assert res_student_join.status_code == 200
    assert res_student_join.json()["role"] == "VIEWER"

    # 7. Unenrolled Student (in 11-B) tries to join -> MUST BE BLOCKED (403)
    res_unenr_join = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/join",
        headers=student_unenr_hdr,
    )
    assert res_unenr_join.status_code == 403
    assert "no cuenta con matrícula activa" in res_unenr_join.json()["error"]["message"]

    # 8. Student leaves meeting
    res_leave = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/leave",
        headers=student_enr_hdr,
    )
    assert res_leave.status_code == 200

    # 9. List Attendances
    res_att = await client.get(
        f"/api/v1/virtual-classrooms/{classroom_id}/attendances",
        headers=teacher_hdr,
    )
    assert res_att.status_code == 200
    assert res_att.json()["total"] >= 1

    # 10. End Classroom
    res_end = await client.post(
        f"/api/v1/virtual-classrooms/{classroom_id}/end",
        headers=teacher_hdr,
    )
    assert res_end.status_code == 200
    assert res_end.json()["status"] == "ENDED"

    # 11. Cross-Tenant Classroom Access -> BLIND 404
    res_cross = await client.get(
        f"/api/v1/virtual-classrooms/{classroom_id}",
        headers=tenant2_hdr,
    )
    assert res_cross.status_code == 404
    assert res_cross.json()["error"]["code"] == "VIRTUAL_CLASSROOM_NOT_FOUND"


# =============================================================================
# 3. Recordings REST API Tests
# =============================================================================


@pytest.mark.asyncio
async def test_recordings_api_sync_publish_and_permissions(
    client: AsyncClient,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Tests recording synchronization, publication visibility toggle, and deletion."""
    teacher_hdr = vc_api_fixture["teacher_headers"]
    student_enr_hdr = vc_api_fixture["student_enr_headers"]
    tenant2_hdr = vc_api_fixture["tenant2_headers"]

    # 1. Create a classroom
    res_create = await client.post(
        "/api/v1/virtual-classrooms",
        json={"title": "Sesión con Grabación", "is_recording_enabled": True},
        headers=teacher_hdr,
    )
    classroom_id = res_create.json()["id"]

    # 2. Sync Recordings from provider
    res_sync = await client.post(
        f"/api/v1/recordings/classroom/{classroom_id}/sync",
        headers=teacher_hdr,
    )
    assert res_sync.status_code == 200
    recordings_list = res_sync.json()["items"]
    assert len(recordings_list) >= 1
    recording_id = recordings_list[0]["id"]
    assert recordings_list[0]["is_published"] is True

    # 3. Publish Toggle: Unpublish recording
    res_unpub = await client.patch(
        f"/api/v1/recordings/{recording_id}/publish",
        json={"is_published": False},
        headers=teacher_hdr,
    )
    assert res_unpub.status_code == 200
    assert res_unpub.json()["is_published"] is False

    # 4. Student queries recordings -> should NOT see unpublished recordings (total = 0)
    res_student_list = await client.get(
        f"/api/v1/recordings/classroom/{classroom_id}",
        headers=student_enr_hdr,
    )
    assert res_student_list.status_code == 200
    assert res_student_list.json()["total"] == 0

    # Staff queries recordings -> sees all (total >= 1)
    res_staff_list = await client.get(
        f"/api/v1/recordings/classroom/{classroom_id}",
        headers=teacher_hdr,
    )
    assert res_staff_list.status_code == 200
    assert res_staff_list.json()["total"] >= 1

    # 5. Cross-Tenant Recording Access -> BLIND 404
    res_cross_rec = await client.get(
        f"/api/v1/recordings/classroom/{classroom_id}",
        headers=tenant2_hdr,
    )
    assert res_cross_rec.status_code == 404

    # 6. Delete Recording
    res_del = await client.delete(
        f"/api/v1/recordings/{recording_id}",
        headers=teacher_hdr,
    )
    assert res_del.status_code == 204

    # Confirm deletion
    res_pub_again = await client.patch(
        f"/api/v1/recordings/{recording_id}/publish",
        json={"is_published": True},
        headers=teacher_hdr,
    )
    assert res_pub_again.status_code == 404
