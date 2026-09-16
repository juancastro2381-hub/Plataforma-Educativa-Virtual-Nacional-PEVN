"""
PEVN Backend — Activity Resources and Secure Storage Test Suite (Phase B3-H11)

Comprehensive tests covering:
1. LocalStorageDriver: Path resolution, directory traversal protection, file operations.
2. StorageService: Size validation (20MB limit), extension whitelist, dangerous extension blocking, magic bytes validation.
3. Teacher Portal Activity Resources API: URL resource creation, multipart file upload, listing, downloading, deletion.
4. Student Portal Activity Resources API: Resource discovery, detail loading, authenticated download.
5. Anti-IDOR & Multi-tenant Isolation: Unauthorized student and teacher 404 protection.
"""

from __future__ import annotations

import io
import shutil
import tempfile
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.core.storage.local import LocalStorageDriver, StorageSecurityError
from app.core.storage.service import FileValidationError, StorageService
from app.models.academic_activity import (
    AcademicActivity,
    ActivityResource,
    ActivityResourceType,
    ActivityStatus,
    ActivityType,
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
# 1. Unit Tests: LocalStorageDriver & StorageService
# ===========================================================================

@pytest.mark.asyncio
async def test_local_storage_driver_crud_and_security() -> None:
    temp_dir = tempfile.mkdtemp(prefix="pevn_storage_test_")
    try:
        driver = LocalStorageDriver(base_path=temp_dir)

        # 1. Write and read
        test_data = b"Hello PEVN Storage World!"
        path = "inst_1/activities/act_1/resources/test.txt"
        written_path = await driver.save(path, test_data)
        assert written_path == path
        assert await driver.exists(path) is True

        read_bytes = await driver.read(path)
        assert read_bytes == test_data

        # 2. Directory traversal attempts must raise StorageSecurityError
        with pytest.raises(StorageSecurityError):
            await driver.save("../../../evil.txt", b"evil payload")

        with pytest.raises(StorageSecurityError):
            await driver.read("../../../etc/passwd")

        with pytest.raises(StorageSecurityError):
            await driver.delete("../../../evil.txt")

        # 3. Delete
        deleted = await driver.delete(path)
        assert deleted is True
        assert await driver.exists(path) is False

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_storage_service_validation_rules() -> None:
    temp_dir = tempfile.mkdtemp(prefix="pevn_service_test_")
    try:
        driver = LocalStorageDriver(base_path=temp_dir)
        service = StorageService(driver=driver)

        inst_id = uuid.uuid4()
        act_id = uuid.uuid4()
        res_id = uuid.uuid4()

        # 1. Dangerous extension rejection
        with pytest.raises(FileValidationError, match="tipo de archivo ejecutable no permitido"):
            await service.save_activity_resource(
                institution_id=inst_id,
                activity_id=act_id,
                resource_id=res_id,
                original_filename="malware.exe",
                content=b"MZ\x90\x00\x03\x00\x00\x00",
            )

        with pytest.raises(FileValidationError, match="tipo de archivo ejecutable no permitido"):
            await service.save_activity_resource(
                institution_id=inst_id,
                activity_id=act_id,
                resource_id=res_id,
                original_filename="script.sh",
                content=b"#!/bin/bash\necho hello",
            )

        # 2. File size limit exceeded (> 20 MB)
        huge_content = b"0" * (20 * 1024 * 1024 + 1)
        with pytest.raises(FileValidationError, match="El archivo excede el tamaño máximo permitido"):
            await service.save_activity_resource(
                institution_id=inst_id,
                activity_id=act_id,
                resource_id=res_id,
                original_filename="large.pdf",
                content=huge_content,
            )

        # 3. Disallowed extension (e.g. .xyz)
        with pytest.raises(FileValidationError, match="no permitida"):
            await service.save_activity_resource(
                institution_id=inst_id,
                activity_id=act_id,
                resource_id=res_id,
                original_filename="custom.xyz",
                content=b"some custom format",
            )

        # 4. Valid PDF magic bytes
        valid_pdf = b"%PDF-1.4\n%test pdf content"
        path, mime, stored_size = await service.save_activity_resource(
            institution_id=inst_id,
            activity_id=act_id,
            resource_id=res_id,
            original_filename="guia_matematicas.pdf",
            content=valid_pdf,
        )
        assert stored_size == len(valid_pdf)
        assert mime == "application/pdf"
        assert path == f"{inst_id}/activities/{act_id}/resources/{res_id}.pdf"

        # 5. Invalid PDF magic bytes
        invalid_pdf = b"NOT A PDF HEADER JUNK CONTENT"
        with pytest.raises(FileValidationError, match="El contenido binario del archivo no coincide"):
            await service.save_activity_resource(
                institution_id=inst_id,
                activity_id=act_id,
                resource_id=uuid.uuid4(),
                original_filename="fake.pdf",
                content=invalid_pdf,
            )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ===========================================================================
# 2. Integration Tests: Teacher & Student Portals Resources Endpoints
# ===========================================================================

@pytest.fixture
async def resources_test_context(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Sets up a complete multi-tenant environment with Teacher, Student, RBAC and Activity."""
    dept = Department(code="76", name="Valle del Cauca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="76001", name="Cali")
    db_session.add(mun)
    await db_session.flush()

    inst = Institution(
        municipality_id=mun.id,
        dane_code="17600100999",
        name="Colegio B3-H11 Materiales",
        email="rectoria@h11.edu.co",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code="17600100999-01",
        name="Sede Principal",
        is_active=True,
    )
    db_session.add(campus)

    ay = AcademicYear(
        institution_id=inst.id,
        name="Año Escolar 2026",
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
        code=f"G08-{uuid.uuid4().hex[:4]}",
        name="Octavo Especial",
        level=EducationalLevel.SECUNDARIA,
        ordinal_order=8,
    )
    db_session.add(grade)
    await db_session.flush()

    group = Group(
        academic_year_id=ay.id,
        grade_id=grade.id,
        campus_id=campus.id,
        name="8-1",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    db_session.add(group)

    ka = KnowledgeArea(id=uuid.uuid4(), institution_id=inst.id, name="Ciencias Exactas")
    db_session.add(ka)
    await db_session.flush()

    subj = Subject(
        id=uuid.uuid4(),
        institution_id=inst.id,
        knowledge_area_id=ka.id,
        grade_id=grade.id,
        name="Física General",
        weekly_hours=4,
    )
    db_session.add(subj)

    # Teacher User & Model
    pwd_hash = password_hasher.hash("Teacher123*")
    teacher_user = User(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"profe_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"profe_{uuid.uuid4().hex[:6]}",
        first_name="Profesor",
        last_name="Newton",
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
        specialty_area="Física",
    )
    db_session.add(teacher)

    # Student User & Model & Enrollment
    st_pwd_hash = password_hasher.hash("Student123*")
    student_user = User(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"alumno_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"alumno_{uuid.uuid4().hex[:6]}",
        first_name="Estudiante",
        last_name="Curie",
        document_type=DocumentType.TI,
        document_number=f"TI-{uuid.uuid4().hex[:8]}",
        hashed_password=st_pwd_hash,
        is_active=True,
    )
    db_session.add(student_user)
    await db_session.flush()

    student = Student(
        id=uuid.uuid4(),
        institution_id=inst.id,
        user_id=student_user.id,
        birth_date=date(2010, 5, 10),
        gender=StudentGender.F,
        code_simat=f"SIM-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(student)
    await db_session.flush()

    enrollment = Enrollment(
        id=uuid.uuid4(),
        student_id=student.id,
        group_id=group.id,
        academic_year_id=ay.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=date(2026, 1, 20),
    )
    db_session.add(enrollment)

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

    # Academic Activity
    activity = AcademicActivity(
        id=uuid.uuid4(),
        institution_id=inst.id,
        teacher_id=teacher.id,
        academic_assignment_id=assignment.id,
        subject_id=subj.id,
        group_id=group.id,
        academic_year_id=ay.id,
        title="Taller de Dinámica y Leyes de Newton",
        description="Resolver ejercicios prácticos",
        activity_type=ActivityType.WORKSHOP,
        status=ActivityStatus.PUBLISHED,
        publication_date=datetime.now(UTC),
        due_date=datetime(2026, 10, 20, 23, 59, tzinfo=UTC),
        max_score=Decimal("5.0"),
        instructions="Descargar la guía adjunta y resolver los ejercicios.",
        resource_url="https://ejemplo.edu.co/guia-general.pdf",
    )
    db_session.add(activity)

    # RBAC Setup: Teacher & Student roles and permissions
    teacher_role_stmt = select(Role).where(Role.name == SystemRole.TEACHER.value)
    teacher_role = (await db_session.execute(teacher_role_stmt)).scalar_one()

    student_role_stmt = select(Role).where(Role.name == SystemRole.STUDENT.value)
    student_role = (await db_session.execute(student_role_stmt)).scalar_one()

    perms_to_ensure = [
        (teacher_role, "activities", "read"),
        (teacher_role, "activities", "create"),
        (teacher_role, "activities", "update"),
        (teacher_role, "activities", "delete"),
        (student_role, "activities", "read"),
        (student_role, "students", "read"),
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

    db_session.add(
        UserRole(
            user_id=teacher_user.id,
            role_id=teacher_role.id,
            institution_id=inst.id,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=student_user.id,
            role_id=student_role.id,
            institution_id=inst.id,
            is_active=True,
        )
    )

    await db_session.commit()

    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={"roles": [SystemRole.TEACHER.value], "institution_id": str(inst.id)},
    )
    student_token = await token_service.create_access_token(
        subject=str(student_user.id),
        additional_claims={"roles": [SystemRole.STUDENT.value], "institution_id": str(inst.id)},
    )

    return {
        "institution": inst,
        "teacher_user": teacher_user,
        "teacher": teacher,
        "student_user": student_user,
        "student": student,
        "activity": activity,
        "teacher_token": teacher_token,
        "student_token": student_token,
    }


@pytest.mark.asyncio
async def test_teacher_create_url_resource_and_student_view(
    resources_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    ctx = resources_test_context
    activity_id = str(ctx["activity"].id)

    # 1. Teacher creates a URL resource via JSON endpoint
    create_resp = await client.post(
        f"/api/v1/teacher/activities/{activity_id}/resources/url",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
        json={
            "title": "Video Explicativo de Leyes de Newton",
            "url": "https://www.youtube.com/watch?v=kKKM8Y-u7ds",
            "description": "Explicación visual del concepto de inercia y fuerza",
        },
    )
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["title"] == "Video Explicativo de Leyes de Newton"
    assert created_data["resource_type"] == "URL"
    assert created_data["url"] == "https://www.youtube.com/watch?v=kKKM8Y-u7ds"
    resource_id = created_data["id"]

    # 2. Teacher lists resources
    list_resp = await client.get(
        f"/api/v1/teacher/activities/{activity_id}/resources",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == resource_id

    # 3. Student views activity details -> sees the attached resource
    student_act_resp = await client.get(
        f"/api/v1/student/activities/{activity_id}",
        headers={"Authorization": f"Bearer {ctx['student_token']}"},
    )
    assert student_act_resp.status_code == 200
    student_data = student_act_resp.json()
    assert "resources" in student_data
    assert len(student_data["resources"]) == 1
    assert student_data["resources"][0]["title"] == "Video Explicativo de Leyes de Newton"

    # 4. Student lists resources endpoint
    student_res_list = await client.get(
        f"/api/v1/student/activities/{activity_id}/resources",
        headers={"Authorization": f"Bearer {ctx['student_token']}"},
    )
    assert student_res_list.status_code == 200
    assert len(student_res_list.json()["items"]) == 1


@pytest.mark.asyncio
async def test_teacher_file_upload_download_and_student_download(
    resources_test_context: dict[str, Any],
    client: AsyncClient,
) -> None:
    ctx = resources_test_context
    activity_id = str(ctx["activity"].id)

    valid_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Guia de Fisica) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

    # 1. Teacher uploads file resource via multipart/form-data
    files = {
        "file": ("guia_taller_newton.pdf", io.BytesIO(valid_pdf_content), "application/pdf")
    }
    data = {
        "title": "Guía Oficial de Ejercicios N° 1",
        "resource_type": "FILE",
        "description": "Documento con 10 ejercicios para resolver en clase",
    }

    upload_resp = await client.post(
        f"/api/v1/teacher/activities/{activity_id}/resources",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
        data=data,
        files=files,
    )
    assert upload_resp.status_code == 201
    res_data = upload_resp.json()
    assert res_data["title"] == "Guía Oficial de Ejercicios N° 1"
    assert res_data["resource_type"] == "FILE"
    assert res_data["original_filename"] == "guia_taller_newton.pdf"
    assert res_data["file_size_bytes"] == len(valid_pdf_content)
    assert res_data["mime_type"] == "application/pdf"
    resource_id = res_data["id"]

    # 2. Teacher downloads file
    teacher_dl_resp = await client.get(
        f"/api/v1/teacher/activities/{activity_id}/resources/{resource_id}/download",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
    )
    assert teacher_dl_resp.status_code == 200
    assert teacher_dl_resp.content == valid_pdf_content
    assert "attachment" in teacher_dl_resp.headers["content-disposition"]
    assert "guia_taller_newton.pdf" in teacher_dl_resp.headers["content-disposition"]

    # 3. Student downloads file
    student_dl_resp = await client.get(
        f"/api/v1/student/activities/{activity_id}/resources/{resource_id}/download",
        headers={"Authorization": f"Bearer {ctx['student_token']}"},
    )
    assert student_dl_resp.status_code == 200
    assert student_dl_resp.content == valid_pdf_content
    assert student_dl_resp.headers["content-type"] == "application/pdf"

    # 4. Teacher deletes resource
    del_resp = await client.delete(
        f"/api/v1/teacher/activities/{activity_id}/resources/{resource_id}",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
    )
    assert del_resp.status_code == 204

    # 5. Subsequent download returns 404
    dl_after_del = await client.get(
        f"/api/v1/student/activities/{activity_id}/resources/{resource_id}/download",
        headers={"Authorization": f"Bearer {ctx['student_token']}"},
    )
    assert dl_after_del.status_code == 404


@pytest.mark.asyncio
async def test_anti_idor_and_tenant_isolation(
    resources_test_context: dict[str, Any],
    db_session: AsyncSession,
    client: AsyncClient,
) -> None:
    ctx = resources_test_context
    activity_id = str(ctx["activity"].id)

    # Create an external student in another institution
    other_inst = Institution(
        municipality_id=ctx["institution"].municipality_id,
        dane_code="17600100888",
        name="Otro Colegio Foráneo",
        email="otro@colegio.edu.co",
        is_active=True,
    )
    db_session.add(other_inst)
    await db_session.flush()

    other_user = User(
        id=uuid.uuid4(),
        institution_id=other_inst.id,
        email=f"otro_{uuid.uuid4().hex[:6]}@colegio.edu.co",
        username=f"otro_{uuid.uuid4().hex[:6]}",
        first_name="Intruso",
        last_name="Foráneo",
        document_type=DocumentType.TI,
        document_number=f"TI-{uuid.uuid4().hex[:8]}",
        hashed_password=password_hasher.hash("Pass123*"),
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()

    other_student = Student(
        id=uuid.uuid4(),
        institution_id=other_inst.id,
        user_id=other_user.id,
        birth_date=date(2010, 1, 1),
        gender=StudentGender.M,
        code_simat=f"SIM-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(other_student)

    # Assign student role to other_user
    student_role = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.STUDENT.value)
        )
    ).scalar_one()

    db_session.add(
        UserRole(
            user_id=other_user.id,
            role_id=student_role.id,
            institution_id=other_inst.id,
            is_active=True,
        )
    )
    await db_session.commit()

    other_student_token = await token_service.create_access_token(
        subject=str(other_user.id),
        additional_claims={"roles": [SystemRole.STUDENT.value], "institution_id": str(other_inst.id)},
    )

    valid_pdf_content = b"%PDF-1.4\n%test pdf content"

    # Create resource by teacher
    files = {
        "file": ("guia_privada.pdf", io.BytesIO(valid_pdf_content), "application/pdf")
    }
    data = {
        "title": "Guía Privada del Curso",
        "resource_type": "FILE",
    }
    upload_resp = await client.post(
        f"/api/v1/teacher/activities/{activity_id}/resources",
        headers={"Authorization": f"Bearer {ctx['teacher_token']}"},
        data=data,
        files=files,
    )
    assert upload_resp.status_code == 201
    res_id = upload_resp.json()["id"]

    # External student tries to list resources -> 404
    idor_list = await client.get(
        f"/api/v1/student/activities/{activity_id}/resources",
        headers={"Authorization": f"Bearer {other_student_token}"},
    )
    assert idor_list.status_code == 404

    # External student tries to download resource -> 404
    idor_dl = await client.get(
        f"/api/v1/student/activities/{activity_id}/resources/{res_id}/download",
        headers={"Authorization": f"Bearer {other_student_token}"},
    )
    assert idor_dl.status_code == 404

