"""
PEVN Backend — Student Submissions API Test Suite (Phase B3-H13)

Comprehensive tests covering:
1. Delivery Modalities Validation (TEXT, FILE, TEXT_AND_FILE).
2. Attachment Constraints (max 3 files, size limits, whitelist validation, dangerous extension blocking).
3. On-Time vs Late Submission based on UTC Server due_date and CLOSED activity protection.
4. Multi-Attempt Lifecycle & SIEE / ActivityGrade Synchronization:
   - Initial submission sets ActivityGrade.status to SUBMITTED
   - Teacher return sets submission to RETURNED and ActivityGrade.status to PENDING
   - Student next fetch automatically spawns Attempt #2 DRAFT with previous attempt in history
   - Resubmission sets ActivityGrade.status to SUBMITTED
   - Unique student count for total_submissions metric
5. Multi-Tenant Isolation & Anti-IDOR Protection:
   - Student A cannot download Student B's attachments
   - Teacher of the group can download submission attachments
"""

from __future__ import annotations

import io
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.academic_activity import (
    AcademicActivity,
    ActivityDeliveryType,
    ActivityGrade,
    ActivityStatus,
    ActivitySubmissionStatus,
    ActivityType,
    StudentSubmission,
    SubmissionAttachment,
    SubmissionStatus,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


# ===========================================================================
# Fixture: Multi-Student, Teacher, Group & Activity Environment
# ===========================================================================

@pytest.fixture
async def submissions_test_context(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Sets up a complete multi-tenant environment with Teacher, 2 Students, RBAC and Activities."""
    dept = Department(code=f"D{uuid.uuid4().hex[:4]}", name="Antioquia Submissions")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code=f"M{uuid.uuid4().hex[:4]}", name="Medellin Submissions")
    db_session.add(mun)
    await db_session.flush()

    inst = Institution(
        municipality_id=mun.id,
        dane_code=f"DANE-{uuid.uuid4().hex[:8]}",
        name="Colegio B3-H13 Entregas",
        email=f"rectoria_{uuid.uuid4().hex[:6]}@h13.edu.co",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code=f"SEDE-{uuid.uuid4().hex[:8]}",
        name="Sede Principal Entregas",
        is_active=True,
    )
    db_session.add(campus)

    ay = AcademicYear(
        institution_id=inst.id,
        name="Año 2026 Entregas",
        year=2026,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 11, 30),
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
    )
    db_session.add(ay)
    await db_session.flush()

    period = AcademicPeriod(
        academic_year_id=ay.id,
        period_number=1,
        name="Primer Periodo",
        start_date=date(2026, 1, 15),
        end_date=date(2026, 4, 15),
        weight_percentage=Decimal("25.0"),
    )
    db_session.add(period)

    grade = Grade(
        code=f"G09-{uuid.uuid4().hex[:4]}",
        name="Noveno Submissions",
        level=EducationalLevel.SECUNDARIA,
        ordinal_order=9,
    )
    db_session.add(grade)
    await db_session.flush()

    group = Group(
        academic_year_id=ay.id,
        grade_id=grade.id,
        campus_id=campus.id,
        name="9-1",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    db_session.add(group)

    ka = KnowledgeArea(id=uuid.uuid4(), institution_id=inst.id, name="Matemáticas Avanzadas")
    db_session.add(ka)
    await db_session.flush()

    subj = Subject(
        id=uuid.uuid4(),
        institution_id=inst.id,
        knowledge_area_id=ka.id,
        grade_id=grade.id,
        name="Álgebra Lineal",
        weekly_hours=4,
    )
    db_session.add(subj)

    # Teacher User & Model
    pwd_hash = password_hasher.hash("Teacher123*")
    teacher_user = User(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"docente_{uuid.uuid4().hex[:6]}@h13.edu.co",
        username=f"docente_{uuid.uuid4().hex[:6]}",
        first_name="Profesor",
        last_name="Gauss",
        document_type=DocumentType.CC,
        document_number=f"CC-{uuid.uuid4().hex[:8]}",
        hashed_password=pwd_hash,
        is_active=True,
    )
    db_session.add(teacher_user)
    await db_session.flush()

    teacher = Teacher(
        id=uuid.uuid4(),
        institution_id=inst.id,
        user_id=teacher_user.id,
        contract_type=TeacherContractType.PROPIEDAD,
        specialty_area="Matemáticas",
    )
    db_session.add(teacher)

    # Student 1 (Primary)
    st_pwd_hash = password_hasher.hash("Student123*")
    student1_user = User(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"estudiante1_{uuid.uuid4().hex[:6]}@h13.edu.co",
        username=f"estudiante1_{uuid.uuid4().hex[:6]}",
        first_name="Ada",
        last_name="Lovelace",
        document_type=DocumentType.TI,
        document_number=f"TI-1-{uuid.uuid4().hex[:6]}",
        hashed_password=st_pwd_hash,
        is_active=True,
    )
    db_session.add(student1_user)
    await db_session.flush()

    student1 = Student(
        id=uuid.uuid4(),
        institution_id=inst.id,
        user_id=student1_user.id,
        birth_date=date(2010, 12, 10),
        gender=StudentGender.F,
        code_simat=f"SIM1-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(student1)
    await db_session.flush()

    enrollment1 = Enrollment(
        id=uuid.uuid4(),
        student_id=student1.id,
        group_id=group.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=date(2026, 1, 20),
    )
    db_session.add(enrollment1)

    # Student 2 (Peer / Anti-IDOR target)
    student2_user = User(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"estudiante2_{uuid.uuid4().hex[:6]}@h13.edu.co",
        username=f"estudiante2_{uuid.uuid4().hex[:6]}",
        first_name="Alan",
        last_name="Turing",
        document_type=DocumentType.TI,
        document_number=f"TI-2-{uuid.uuid4().hex[:6]}",
        hashed_password=st_pwd_hash,
        is_active=True,
    )
    db_session.add(student2_user)
    await db_session.flush()

    student2 = Student(
        id=uuid.uuid4(),
        institution_id=inst.id,
        user_id=student2_user.id,
        birth_date=date(2010, 6, 23),
        gender=StudentGender.M,
        code_simat=f"SIM2-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(student2)
    await db_session.flush()

    enrollment2 = Enrollment(
        id=uuid.uuid4(),
        student_id=student2.id,
        group_id=group.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=date(2026, 1, 20),
    )
    db_session.add(enrollment2)

    # Academic Assignment
    assignment = AcademicAssignment(
        id=uuid.uuid4(),
        teacher_id=teacher.id,
        subject_id=subj.id,
        group_id=group.id,
        academic_year_id=ay.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assignment)

    # Activity 1: TEXT_AND_FILE modality, future due date (on-time)
    activity_future = AcademicActivity(
        id=uuid.uuid4(),
        institution_id=inst.id,
        teacher_id=teacher.id,
        academic_assignment_id=assignment.id,
        subject_id=subj.id,
        group_id=group.id,
        academic_year_id=ay.id,
        title="Taller 1: Matrices y Determinantes",
        description="Resolver ejercicios y subir memoria de cálculo",
        activity_type=ActivityType.WORKSHOP,
        status=ActivityStatus.PUBLISHED,
        delivery_type=ActivityDeliveryType.TEXT_AND_FILE,
        publication_date=datetime.now(UTC) - timedelta(days=2),
        due_date=datetime.now(UTC) + timedelta(days=5),
        max_score=Decimal("5.0"),
        instructions="Completar los ejercicios justificando cada paso.",
    )
    db_session.add(activity_future)

    # Activity 2: Past due date (Late submission test)
    activity_past = AcademicActivity(
        id=uuid.uuid4(),
        institution_id=inst.id,
        teacher_id=teacher.id,
        academic_assignment_id=assignment.id,
        subject_id=subj.id,
        group_id=group.id,
        academic_year_id=ay.id,
        title="Taller 2: Sistemas de Ecuaciones (Vencido)",
        description="Actividad con fecha límite vencida",
        activity_type=ActivityType.TASK,
        status=ActivityStatus.PUBLISHED,
        delivery_type=ActivityDeliveryType.TEXT,
        publication_date=datetime.now(UTC) - timedelta(days=10),
        due_date=datetime.now(UTC) - timedelta(days=2),
        max_score=Decimal("5.0"),
        instructions="Entregar análisis textual.",
    )
    db_session.add(activity_past)

    # Activity 3: CLOSED Activity
    activity_closed = AcademicActivity(
        id=uuid.uuid4(),
        institution_id=inst.id,
        teacher_id=teacher.id,
        academic_assignment_id=assignment.id,
        subject_id=subj.id,
        group_id=group.id,
        academic_year_id=ay.id,
        title="Taller 3: Actividad Cerrada",
        description="Actividad ya clausurada",
        activity_type=ActivityType.TASK,
        status=ActivityStatus.CLOSED,
        delivery_type=ActivityDeliveryType.FILE,
        publication_date=datetime.now(UTC) - timedelta(days=20),
        due_date=datetime.now(UTC) - timedelta(days=10),
        max_score=Decimal("5.0"),
        instructions="Ya finalizada.",
    )
    db_session.add(activity_closed)

    # RBAC Setup
    teacher_role_stmt = select(Role).where(Role.name == SystemRole.TEACHER.value)
    teacher_role = (await db_session.execute(teacher_role_stmt)).scalar_one()

    student_role_stmt = select(Role).where(Role.name == SystemRole.STUDENT.value)
    student_role = (await db_session.execute(student_role_stmt)).scalar_one()

    perms_to_ensure = [
        (teacher_role, "activities", "read"),
        (teacher_role, "activities", "create"),
        (teacher_role, "activities", "update"),
        (teacher_role, "submissions", "read"),
        (teacher_role, "submissions", "return"),
        (teacher_role, "grades", "read"),
        (teacher_role, "grades", "create"),
        (teacher_role, "grades", "update"),
        (student_role, "activities", "read"),
        (student_role, "students", "read"),
        (student_role, "submissions", "read"),
        (student_role, "submissions", "create"),
        (student_role, "submissions", "update"),
    ]

    for role_obj, res, act in perms_to_ensure:
        p_stmt = select(Permission).where(Permission.resource == res, Permission.action == act)
        p = (await db_session.execute(p_stmt)).scalar_one_or_none()
        if not p:
            p = Permission(resource=res, action=act, description=f"{res}:{act}")
            db_session.add(p)
            await db_session.flush()

        rp_exists = (
            await db_session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_obj.id,
                    RolePermission.permission_id == p.id,
                )
            )
        ).scalar_one_or_none()
        if not rp_exists:
            db_session.add(RolePermission(role_id=role_obj.id, permission_id=p.id))

    db_session.add(UserRole(user_id=teacher_user.id, role_id=teacher_role.id, institution_id=inst.id, is_active=True))
    db_session.add(UserRole(user_id=student1_user.id, role_id=student_role.id, institution_id=inst.id, is_active=True))
    db_session.add(UserRole(user_id=student2_user.id, role_id=student_role.id, institution_id=inst.id, is_active=True))

    await db_session.commit()

    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={"roles": [SystemRole.TEACHER.value], "institution_id": str(inst.id)},
    )
    student1_token = await token_service.create_access_token(
        subject=str(student1_user.id),
        additional_claims={"roles": [SystemRole.STUDENT.value], "institution_id": str(inst.id)},
    )
    student2_token = await token_service.create_access_token(
        subject=str(student2_user.id),
        additional_claims={"roles": [SystemRole.STUDENT.value], "institution_id": str(inst.id)},
    )

    return {
        "institution": inst,
        "teacher": teacher,
        "student1": student1,
        "student2": student2,
        "activity_future": activity_future,
        "activity_past": activity_past,
        "activity_closed": activity_closed,
        "teacher_token": teacher_token,
        "student1_token": student1_token,
        "student2_token": student2_token,
    }


# ===========================================================================
# 1. Tests: Modalities & Validation Rules
# ===========================================================================

@pytest.mark.asyncio
async def test_student_fetch_or_create_draft(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    """Student fetching submission for the first time gets an automatically created attempt #1 DRAFT."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_future"].id)

    resp = await client.get(
        f"/api/v1/student/activities/{activity_id}/submission",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["can_submit"] is True
    assert data["current_attempt"] is not None
    assert data["current_attempt"]["attempt_number"] == 1
    assert data["current_attempt"]["status"] == SubmissionStatus.DRAFT.value
    assert data["current_attempt"]["student_response"] is None
    assert data["current_attempt"]["attachments"] == []
    assert data["history"] == []


@pytest.mark.asyncio
async def test_student_save_draft(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    """Student can incrementally update their draft text without submitting."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_future"].id)

    draft_resp = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/draft",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        json={"student_response": "Borrador preliminar de la memoria técnica"},
    )
    assert draft_resp.status_code == 200, draft_resp.text
    draft_data = draft_resp.json()
    assert draft_data["student_response"] == "Borrador preliminar de la memoria técnica"
    assert draft_data["status"] == SubmissionStatus.DRAFT.value


@pytest.mark.asyncio
async def test_attachment_validation_and_limits(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    """Tests file upload constraints: max 3 attachments, blocked extensions, valid upload and deletion."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_future"].id)

    # 1. Dangerous extension (.exe) must be blocked (HTTP 400 AcademicDomainError)
    fake_exe = io.BytesIO(b"MZ\x90\x00executable content")
    resp_exe = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("malware.exe", fake_exe, "application/octet-stream")},
    )
    assert resp_exe.status_code == 400
    assert "no permitido" in resp_exe.text or "ejecutable" in resp_exe.text

    # 2. Valid PDF upload #1
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    resp1 = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("archivo1.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert resp1.status_code == 201, resp1.text
    att1 = resp1.json()
    assert att1["original_filename"] == "archivo1.pdf"

    # 3. Valid file upload #2 (png)
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    resp2 = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("grafico2.png", io.BytesIO(png_content), "image/png")},
    )
    assert resp2.status_code == 201, resp2.text
    att2 = resp2.json()

    # 4. Valid file upload #3 (zip file)
    zip_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00" + b"desarrollo anexo 3"
    resp3 = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("anexo3.zip", io.BytesIO(zip_content), "application/zip")},
    )
    assert resp3.status_code == 201, resp3.text

    # 5. 4th file upload must be rejected (max 3 files limit)
    resp4 = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("archivo4.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert resp4.status_code == 400
    assert "3 archivos" in resp4.text

    # 6. Delete file #2 (HTTP 204 No Content)
    del_resp = await client.delete(
        f"/api/v1/student/activities/{activity_id}/submission/files/{att2['id']}",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert del_resp.status_code == 204, del_resp.text

    # 7. Check current files count is now 2
    sub_resp = await client.get(
        f"/api/v1/student/activities/{activity_id}/submission",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    att_list = sub_resp.json()["current_attempt"]["attachments"]
    assert len(att_list) == 2


@pytest.mark.asyncio
async def test_modality_validation_on_submit(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    """Tests TEXT_AND_FILE modality: missing text should fail, missing files should fail."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_future"].id)

    # 1. Missing both files and text -> should fail with 400
    fail_resp1 = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/submit",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert fail_resp1.status_code == 400
    assert "texto" in fail_resp1.text.lower() or "archivo" in fail_resp1.text.lower()

    # 2. Upload a file, but keep text empty -> should fail because TEXT is required
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("solucion.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )

    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/draft",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        json={"student_response": "   "},
    )

    fail_resp2 = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/submit",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert fail_resp2.status_code == 400
    assert "texto" in fail_resp2.text.lower()


# ===========================================================================
# 2. Tests: Submission Deadlines (On-Time, Late, Closed)
# ===========================================================================

@pytest.mark.asyncio
async def test_on_time_submission_and_activity_grade_sync(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """On-time submission sets is_late=False, status=SUBMITTED, and updates ActivityGrade."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_future"].id)

    # 1. Upload required file
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("memoria.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )

    # 2. Set valid text
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/draft",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        json={"student_response": "Respuesta completa a la actividad de matrices."},
    )

    # 3. Submit
    submit_resp = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/submit",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert submit_resp.status_code == 200, submit_resp.text
    data = submit_resp.json()
    assert data["current_attempt"]["status"] == SubmissionStatus.SUBMITTED.value
    assert data["current_attempt"]["is_late"] is False
    assert data["current_attempt"]["submitted_at"] is not None
    assert data["can_submit"] is False  # Cannot submit again while pending review

    # 4. Check ActivityGrade status
    grade_stmt = select(ActivityGrade).where(
        ActivityGrade.activity_id == ctx["activity_future"].id,
        ActivityGrade.student_id == ctx["student1"].id,
    )
    grade = (await db_session.execute(grade_stmt)).scalar_one_or_none()
    assert grade is not None
    assert grade.status == ActivitySubmissionStatus.SUBMITTED
    assert grade.score is None


@pytest.mark.asyncio
async def test_late_submission_flow(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    """Late submission (now_utc > due_date) sets is_late=True and status=LATE."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_past"].id)

    # Fetch draft
    await client.get(
        f"/api/v1/student/activities/{activity_id}/submission",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )

    # Save draft text (TEXT modality)
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/draft",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        json={"student_response": "Entrega extemporánea justificando el retraso."},
    )

    # Submit
    submit_resp = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/submit",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert submit_resp.status_code == 200, submit_resp.text
    data = submit_resp.json()
    assert data["current_attempt"]["status"] == SubmissionStatus.LATE.value
    assert data["current_attempt"]["is_late"] is True


@pytest.mark.asyncio
async def test_submission_blocked_when_activity_closed(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    """Submissions to a CLOSED activity are strictly blocked with 400 Bad Request."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_closed"].id)

    submit_resp = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/submit",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert submit_resp.status_code == 400
    assert "cerrada" in submit_resp.text


# ===========================================================================
# 3. Tests: Multi-Attempt Lifecycle & Teacher Review / Return
# ===========================================================================

@pytest.mark.asyncio
async def test_teacher_list_and_detail_submissions(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    """Teacher lists all group students with submission summary and views detail."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_future"].id)
    student1_id = str(ctx["student1"].id)

    # 1. Student 1 submits
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("solucion1.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/draft",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        json={"student_response": "Respuesta completa a la actividad de matrices."},
    )
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/submit",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )

    # 2. Teacher views submissions list
    list_resp = await client.get(
        f"/api/v1/teacher/activities/{activity_id}/submissions",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
    )
    assert list_resp.status_code == 200, list_resp.text
    list_data = list_resp.json()
    assert list_data["total"] == 2  # Total 2 students enrolled in 9-1

    # Verify student rows
    st1_row = next(r for r in list_data["items"] if r["student_id"] == student1_id)
    assert st1_row["status"] == SubmissionStatus.SUBMITTED.value
    assert st1_row["attempt_number"] == 1
    assert st1_row["is_late"] is False

    # 3. Teacher views detail of Student 1
    detail_resp = await client.get(
        f"/api/v1/teacher/activities/{activity_id}/submissions/{student1_id}",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
    )
    assert detail_resp.status_code == 200, detail_resp.text
    detail_data = detail_resp.json()
    assert detail_data["student_id"] == student1_id
    assert detail_data["current_attempt"]["student_response"] == "Respuesta completa a la actividad de matrices."
    assert len(detail_data["current_attempt"]["attachments"]) == 1


@pytest.mark.asyncio
async def test_teacher_return_and_multi_attempt_flow(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Full lifecycle: Teacher returns -> Student sees Attempt 1 in history -> Student submits Attempt 2 -> Teacher grades."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_future"].id)
    student1_id = str(ctx["student1"].id)
    # Capture assignment_id before any session expiry to avoid MissingGreenlet lazy-load
    assignment_id = str(ctx["activity_future"].academic_assignment_id)

    # 1. Student 1 submits attempt #1
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("intento1.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/draft",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        json={"student_response": "Primer intento incompleto."},
    )
    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/submit",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )

    # 2. Teacher returns submission with feedback
    return_resp = await client.post(
        f"/api/v1/teacher/activities/{activity_id}/submissions/{student1_id}/return",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
        json={"return_feedback": "Falta adjuntar la matriz inversa en el ejercicio 4. Por favor corregir."},
    )
    assert return_resp.status_code == 200, return_resp.text
    return_data = return_resp.json()
    assert return_data["current_attempt"]["status"] == SubmissionStatus.RETURNED.value
    assert return_data["current_attempt"]["return_feedback"] == "Falta adjuntar la matriz inversa en el ejercicio 4. Por favor corregir."

    # Verify ActivityGrade reverted to PENDING and score is None
    grade_stmt = select(ActivityGrade).where(
        ActivityGrade.activity_id == ctx["activity_future"].id,
        ActivityGrade.student_id == ctx["student1"].id,
    )
    grade = (await db_session.execute(grade_stmt)).scalar_one()
    assert grade.status == ActivitySubmissionStatus.PENDING
    assert grade.score is None

    # 3. Student fetches submission -> automatically spawns Attempt #2 as DRAFT
    student_fetch = await client.get(
        f"/api/v1/student/activities/{activity_id}/submission",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert student_fetch.status_code == 200, student_fetch.text
    s_data = student_fetch.json()
    assert s_data["can_submit"] is True
    assert s_data["current_attempt"]["attempt_number"] == 2
    assert s_data["current_attempt"]["status"] == SubmissionStatus.DRAFT.value
    assert len(s_data["history"]) == 1
    assert s_data["history"][0]["attempt_number"] == 1
    assert s_data["history"][0]["status"] == SubmissionStatus.RETURNED.value
    assert s_data["history"][0]["return_feedback"] == "Falta adjuntar la matriz inversa en el ejercicio 4. Por favor corregir."

    # 4. Student uploads corrected file for Attempt #2 and updates text
    new_pdf = b"%PDF-1.4\nCorrecion ejercicio 4 con matriz inversa\n%%EOF"
    file_resp = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("solucion_v2.pdf", io.BytesIO(new_pdf), "application/pdf")},
    )
    assert file_resp.status_code == 201, file_resp.text

    await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/draft",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        json={"student_response": "Entrega corregida con la matriz inversa en la página 2."},
    )

    # 5. Student resubmits Attempt #2
    resubmit_resp = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/submit",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert resubmit_resp.status_code == 200, resubmit_resp.text
    resubmit_data = resubmit_resp.json()
    assert resubmit_data["current_attempt"]["attempt_number"] == 2
    assert resubmit_data["current_attempt"]["status"] == SubmissionStatus.SUBMITTED.value

    # ActivityGrade is back to SUBMITTED
    db_session.expire_all()
    grade = (await db_session.execute(grade_stmt)).scalar_one()
    assert grade.status == ActivitySubmissionStatus.SUBMITTED

    # 6. Teacher lists activities and checks total_submissions metric
    # total_submissions MUST equal 1 (1 unique student), even with multiple attempts
    activities_resp = await client.get(
        "/api/v1/teacher/activities",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
    )
    assert activities_resp.status_code == 200, activities_resp.text
    act_list = activities_resp.json()
    target_act = next(a for a in act_list["items"] if a["id"] == activity_id)
    assert target_act["total_submissions"] == 1


# ===========================================================================
# 4. Tests: Anti-IDOR & Multi-Tenant Isolation
# ===========================================================================

@pytest.mark.asyncio
async def test_anti_idor_attachment_download(
    submissions_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    """Student 2 cannot download Student 1's submission attachment."""
    ctx = submissions_test_context
    activity_id = str(ctx["activity_future"].id)

    # 1. Student 1 uploads a file
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    upload_resp = await client.post(
        f"/api/v1/student/activities/{activity_id}/submission/files",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
        files={"file": ("tarea_privada.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert upload_resp.status_code == 201, upload_resp.text
    att_id = upload_resp.json()["id"]

    # 2. Student 1 can download their own attachment
    s1_dl = await client.get(
        f"/api/v1/student/activities/{activity_id}/submission/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {ctx['student1_token']}"},
    )
    assert s1_dl.status_code == 200
    assert len(s1_dl.content) == len(pdf_content)

    # 3. Student 2 attempting to download Student 1's attachment receives 404
    s2_dl = await client.get(
        f"/api/v1/student/activities/{activity_id}/submission/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {ctx['student2_token']}"},
    )
    assert s2_dl.status_code == 404

    # 4. Teacher of the group can download Student 1's attachment
    student1_id = str(ctx["student1"].id)
    teacher_dl = await client.get(
        f"/api/v1/teacher/activities/{activity_id}/submissions/{student1_id}/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
    )
    assert teacher_dl.status_code == 200
    assert len(teacher_dl.content) == len(pdf_content)
