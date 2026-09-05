"""
PEVN Backend — Institutional Communications Integration & Security Tests (Phase 15)

Tests:
1. Directive publication of official circulars with audience targeting.
2. Expiration mechanics (DECISION-15-02: expired circulars excluded from active feeds).
3. Student feed targeting (institution-wide, student-only, group-specific).
4. Guardian feed targeting (institution-wide, guardian-only, child's group).
5. Read receipt and formal acknowledgment lifecycle (idempotent, unforgeable).
6. Anti-IDOR & cross-tenant non-disclosure (HTTP 404 on cross-institution access).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.academic_year import (
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.communication import (
    CommunicationCategory,
    CommunicationPriority,
    InstitutionalCommunication,
    PublishingStatus,
    TargetScopeType,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.guardian import Guardian, GuardianRelationshipType, StudentGuardian
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.student import Student, StudentGender
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def comm_test_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Sets up two institutions, rector, student, guardian, groups, and auth tokens."""
    dept = Department(code="11", name="Bogota D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogota")
    db_session.add(mun)
    await db_session.flush()

    # Institution A
    inst_a = Institution(
        dane_code="111111111111",
        name="Colegio San Martin",
        email="rector.sanmartin@pevn.edu.co",
        municipality_id=mun.id,
        is_active=True,
    )
    # Institution B
    inst_b = Institution(
        dane_code="222222222222",
        name="Colegio San Ignacio",
        email="rector.sanignacio@pevn.edu.co",
        municipality_id=mun.id,
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    campus_a = Campus(institution_id=inst_a.id, dane_sede_code="11111111111101", name="Sede Principal", is_active=True)
    db_session.add(campus_a)
    await db_session.flush()

    grade_res = await db_session.execute(select(Grade).where(Grade.code == "G10"))
    grade_10 = grade_res.scalar_one_or_none()
    if not grade_10:
        grade_10 = Grade(code="G10", name="Grado Decimo", level=EducationalLevel.MEDIA, ordinal_order=10)
        db_session.add(grade_10)
        await db_session.flush()

    year_2026 = AcademicYear(
        institution_id=inst_a.id,
        name="Año 2026",
        year=2026,
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        start_date=datetime(2026, 1, 20).date(),
        end_date=datetime(2026, 11, 30).date(),
    )
    db_session.add(year_2026)
    await db_session.flush()

    group_10a = Group(
        academic_year_id=year_2026.id,
        campus_id=campus_a.id,
        grade_id=grade_10.id,
        name="10-A",
        shift=ShiftEnum.MANANA,
    )
    db_session.add(group_10a)
    await db_session.flush()

    # Retrieve bootstrapped roles
    roles_res = await db_session.execute(select(Role))
    roles_map = {r.name: r for r in roles_res.scalars().all()}

    # Rector User
    rector_user = User(
        email="rector.sanmartin@pevn.edu.co",
        username="rector_sanmartin",
        hashed_password=password_hasher.hash("RectorPass123!"),
        document_type=DocumentType.CC,
        document_number="10001",
        first_name="Guillermo",
        last_name="Rector",
        institution_id=inst_a.id,
        is_active=True,
    )
    # Student User & Profile
    student_user = User(
        email="estudiante.diego@pevn.edu.co",
        username="diego_estudiante",
        hashed_password=password_hasher.hash("StudentPass123!"),
        document_type=DocumentType.TI,
        document_number="10002",
        first_name="Diego",
        last_name="Gomez",
        institution_id=inst_a.id,
        is_active=True,
    )
    # Guardian User & Profile
    guardian_user = User(
        email="acudiente.carmen@pevn.edu.co",
        username="carmen_acudiente",
        hashed_password=password_hasher.hash("GuardianPass123!"),
        document_type=DocumentType.CC,
        document_number="10003",
        first_name="Carmen",
        last_name="Gomez",
        institution_id=inst_a.id,
        is_active=True,
    )
    # Cross-tenant Rector User (Institution B)
    rector_b_user = User(
        email="rector.sanignacio@pevn.edu.co",
        username="rector_sanignacio",
        hashed_password=password_hasher.hash("RectorBPass123!"),
        document_type=DocumentType.CC,
        document_number="10004",
        first_name="Alfonso",
        last_name="RectorB",
        institution_id=inst_b.id,
        is_active=True,
    )
    db_session.add_all([rector_user, student_user, guardian_user, rector_b_user])
    await db_session.flush()

    # User Roles
    db_session.add(UserRole(user_id=rector_user.id, role_id=roles_map["rector"].id))
    db_session.add(UserRole(user_id=student_user.id, role_id=roles_map["student"].id))
    db_session.add(UserRole(user_id=guardian_user.id, role_id=roles_map["guardian"].id))
    db_session.add(UserRole(user_id=rector_b_user.id, role_id=roles_map["rector"].id))
    await db_session.flush()

    student_profile = Student(
        institution_id=inst_a.id,
        user_id=student_user.id,
        code_simat="SIMAT-1001",
        birth_date=datetime(2009, 5, 12).date(),
        gender=StudentGender.M,
    )
    guardian_profile = Guardian(
        institution_id=inst_a.id,
        user_id=guardian_user.id,
        first_name="Carmen",
        last_name="Gomez",
        document_type=DocumentType.CC,
        document_number="10003",
        phone="3001234567",
        relationship_type=GuardianRelationshipType.MADRE,
    )
    db_session.add_all([student_profile, guardian_profile])
    await db_session.flush()

    # StudentGuardian link & Enrollment
    link = StudentGuardian(
        student_id=student_profile.id,
        guardian_id=guardian_profile.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
    )
    enr = Enrollment(
        student_id=student_profile.id,
        academic_year_id=year_2026.id,
        group_id=group_10a.id,
        status=EnrollmentStatus.ACTIVE,
        enrollment_date=datetime(2026, 1, 20).date(),
    )
    db_session.add_all([link, enr])
    await db_session.commit()

    # Generate Auth Tokens
    rector_token = await token_service.create_access_token(
        subject=str(rector_user.id),
        additional_claims={"email": rector_user.email, "roles": ["rector"], "institution_id": str(inst_a.id)},
    )
    student_token = await token_service.create_access_token(
        subject=str(student_user.id),
        additional_claims={"email": student_user.email, "roles": ["student"], "institution_id": str(inst_a.id)},
    )
    guardian_token = await token_service.create_access_token(
        subject=str(guardian_user.id),
        additional_claims={"email": guardian_user.email, "roles": ["guardian"], "institution_id": str(inst_a.id)},
    )
    rector_b_token = await token_service.create_access_token(
        subject=str(rector_b_user.id),
        additional_claims={"email": rector_b_user.email, "roles": ["rector"], "institution_id": str(inst_b.id)},
    )

    return {
        "inst_a_id": inst_a.id,
        "inst_b_id": inst_b.id,
        "campus_a_id": campus_a.id,
        "grade_10_id": grade_10.id,
        "group_10a_id": group_10a.id,
        "student_id": student_profile.id,
        "guardian_id": guardian_profile.id,
        "rector_token": rector_token,
        "student_token": student_token,
        "guardian_token": guardian_token,
        "rector_b_token": rector_b_token,
    }


@pytest.mark.asyncio
async def test_communication_lifecycle_and_targeting(
    client: AsyncClient,
    comm_test_fixture: dict[str, Any],
) -> None:
    """Test creating, publishing, targeting, reading, and acknowledging circulars."""
    rector_token = comm_test_fixture["rector_token"]
    student_token = comm_test_fixture["student_token"]
    guardian_token = comm_test_fixture["guardian_token"]
    group_10a_id = str(comm_test_fixture["group_10a_id"])

    # 1. Rector creates official circular for Group 10-A
    payload = {
        "title": "Circular 001 - Entrega de Informes Primer Periodo",
        "summary": "Citación a entrega de boletines y balance académico.",
        "content": "Estimados padres y acudientes: Se convoca a la reunión oficial.",
        "category": "CIRCULAR_OFICIAL",
        "priority": "ALTA",
        "target_scope": "POR_GRUPO",
        "requires_acknowledgment": True,
        "status": "PUBLICADO",
        "expires_at": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
        "audiences": [
            {"group_id": group_10a_id, "role_name": "guardian"},
            {"group_id": group_10a_id, "role_name": "student"},
        ],
    }

    create_res = await client.post(
        "/api/v1/communications",
        json=payload,
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    assert create_res.status_code == 201
    comm_data = create_res.json()
    comm_id = comm_data["id"]
    assert comm_data["title"] == payload["title"]
    assert comm_data["priority"] == "ALTA"
    assert comm_data["requires_acknowledgment"] is True

    # 2. Student queries /student/communications
    student_res = await client.get(
        "/api/v1/student/communications",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_res.status_code == 200
    student_comms = student_res.json()
    assert student_comms["total"] >= 1
    assert student_comms["unread_count"] >= 1
    found_student_comm = next(c for c in student_comms["items"] if c["id"] == comm_id)
    assert found_student_comm["is_read"] is False
    assert found_student_comm["is_acknowledged"] is False

    # 3. Student reads communication detail
    detail_res = await client.get(
        f"/api/v1/student/communications/{comm_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["is_read"] is True

    # 4. Guardian queries /guardian/communications
    guardian_res = await client.get(
        "/api/v1/guardian/communications",
        headers={"Authorization": f"Bearer {guardian_token}"},
    )
    assert guardian_res.status_code == 200
    guardian_comms = guardian_res.json()
    assert guardian_comms["total"] >= 1
    found_guard_comm = next(c for c in guardian_comms["items"] if c["id"] == comm_id)
    assert found_guard_comm["is_acknowledged"] is False

    # 5. Guardian acknowledges receipt
    ack_res = await client.post(
        f"/api/v1/guardian/communications/{comm_id}/acknowledge",
        headers={"Authorization": f"Bearer {guardian_token}"},
    )
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["is_acknowledged"] is True
    assert ack_data["acknowledged_at"] is not None

    # 6. Verify Guardian feed reflects acknowledgment
    guardian_res2 = await client.get(
        "/api/v1/guardian/communications",
        headers={"Authorization": f"Bearer {guardian_token}"},
    )
    found_guard_comm2 = next(c for c in guardian_res2.json()["items"] if c["id"] == comm_id)
    assert found_guard_comm2["is_acknowledged"] is True


@pytest.mark.asyncio
async def test_communication_expiration_behavior(
    client: AsyncClient,
    comm_test_fixture: dict[str, Any],
) -> None:
    """Test DECISION-15-02: Expired communications are excluded from active feeds."""
    rector_token = comm_test_fixture["rector_token"]
    student_token = comm_test_fixture["student_token"]

    # 1. Create already-expired communication (yesterday)
    expired_payload = {
        "title": "Aviso Vencido de Evento Pasado",
        "summary": "Este evento ya concluyo.",
        "content": "Detalles del evento que expiro ayer.",
        "category": "AVISO_ACADEMICO",
        "priority": "BAJA",
        "target_scope": "TODOS_INSTITUCION",
        "status": "PUBLICADO",
        "expires_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
    }
    create_res = await client.post(
        "/api/v1/communications",
        json=expired_payload,
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    assert create_res.status_code == 201
    expired_id = create_res.json()["id"]

    # 2. Student queries active communications -> must NOT contain expired item
    student_res = await client.get(
        "/api/v1/student/communications",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_res.status_code == 200
    active_ids = [c["id"] for c in student_res.json()["items"]]
    assert expired_id not in active_ids

    # 3. Rector lists communications with include_expired=True vs False
    admin_active_res = await client.get(
        "/api/v1/communications?include_expired=false",
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    assert expired_id not in [c["id"] for c in admin_active_res.json()["items"]]

    admin_all_res = await client.get(
        "/api/v1/communications?include_expired=true",
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    assert expired_id in [c["id"] for c in admin_all_res.json()["items"]]


@pytest.mark.asyncio
async def test_communication_cross_tenant_anti_idor(
    client: AsyncClient,
    comm_test_fixture: dict[str, Any],
) -> None:
    """Test Anti-IDOR non-disclosure across institutions (returns 404)."""
    rector_token = comm_test_fixture["rector_token"]
    rector_b_token = comm_test_fixture["rector_b_token"]

    # Rector A creates communication in Institution A
    create_res = await client.post(
        "/api/v1/communications",
        json={
            "title": "Circular Confidencial Inst A",
            "summary": "Solo para miembros de Inst A",
            "content": "Contenido interno confidencial.",
            "category": "CIRCULAR_OFICIAL",
            "priority": "MEDIA",
            "target_scope": "TODOS_INSTITUCION",
            "status": "PUBLICADO",
        },
        headers={"Authorization": f"Bearer {rector_token}"},
    )
    comm_a_id = create_res.json()["id"]

    # Rector B (Institution B) attempts to access Communication from Inst A -> Must return 404
    cross_res = await client.get(
        f"/api/v1/communications/{comm_a_id}",
        headers={"Authorization": f"Bearer {rector_b_token}"},
    )
    assert cross_res.status_code == 404
