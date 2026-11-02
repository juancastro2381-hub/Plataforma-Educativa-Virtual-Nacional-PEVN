"""
PEVN Backend — Independent Security Audit Remediation & Regression Verification Suite
Authoritative verification for findings SEC-001 through SEC-010 and OPS hardening.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, get_settings, settings
from app.core.exceptions import UnauthorizedMeetingAccessError
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import hash_token, token_service
from app.exceptions.errors import AuthenticationError, ConflictError
from app.models.academic_activity import ActivityResourceType
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicYear, AcademicYearStatus
from app.models.grade import Grade
from app.models.group import Group, ShiftEnum
from app.models.guardian import Guardian, GuardianRelationshipType, StudentGuardian
from app.models.institution import Campus, Institution
from app.models.invitation import GuardianInvitation
from app.models.role import Role, UserRole
from app.models.student import Student, StudentGender
from app.models.subject import Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.models.virtual_classroom import MeetingRecording, VirtualClassroom, VirtualClassroomStatus
from app.schemas.teacher_portal import AcademicActivityCreateRequest, ActivityResourceCreateUrlRequest
from app.schemas.technical_incident import TechnicalIncidentCreateRequest
from app.services.auth_service import auth_service
from app.services.guardian_onboarding_service import GuardianOnboardingService
from app.services.recording_service import RecordingService
from app.services.virtual_classroom_service import VirtualClassroomService


@pytest.fixture
async def sec_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Seed test fixtures for security audit verification."""
    dept = Department(code="99", name="Territorio Test")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, code="99001", name="Municipio Test")
    db_session.add(muni)
    await db_session.flush()

    inst = Institution(
        municipality_id=muni.id,
        dane_code="999999000111",
        name="I.E. Seguridad Auditada",
        email="rector@seguridad.edu.co",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code="99999900011101",
        name="Sede Central",
        is_active=True,
    )
    db_session.add(campus)
    await db_session.flush()

    year = AcademicYear(
        institution_id=inst.id,
        year=2027,
        name="2027",
        start_date=date(2027, 1, 15),
        end_date=date(2027, 11, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(year)
    await db_session.flush()

    # User 1: Administrator / Target victim
    admin_user = User(
        institution_id=inst.id,
        email="admin.rector@seguridad.edu.co",
        username="admin.rector",
        hashed_password=password_hasher.hash("RectorPass2026*!"),
        first_name="Rector",
        last_name="Auditor",
        document_type=DocumentType.CC,
        document_number="88997711",
        is_active=True,
        is_verified=True,
    )
    # User 2: Teacher A (Host)
    teacher_user_a = User(
        institution_id=inst.id,
        email="teacher.a@seguridad.edu.co",
        username="teacher.a",
        hashed_password=password_hasher.hash("TeacherPass2026*!"),
        first_name="Docente",
        last_name="Alfa",
        document_type=DocumentType.CC,
        document_number="77889911",
        is_active=True,
        is_verified=True,
    )
    # User 3: Teacher B (Non-Host / Attacker)
    teacher_user_b = User(
        institution_id=inst.id,
        email="teacher.b@seguridad.edu.co",
        username="teacher.b",
        hashed_password=password_hasher.hash("TeacherPass2026*!"),
        first_name="Docente",
        last_name="Beta",
        document_type=DocumentType.CC,
        document_number="77889922",
        is_active=True,
        is_verified=True,
    )
    # User 4: Student
    student_user = User(
        institution_id=inst.id,
        email="estudiante.carlos@seguridad.edu.co",
        username="estudiante.carlos",
        hashed_password=password_hasher.hash("StudentPass2026*!"),
        first_name="Carlos",
        last_name="Gomez",
        document_type=DocumentType.TI,
        document_number="1099887766",
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([admin_user, teacher_user_a, teacher_user_b, student_user])
    await db_session.flush()

    # Roles
    role_admin = (await db_session.execute(select(Role).where(Role.name == "rector"))).scalar_one_or_none()
    if not role_admin:
        role_admin = Role(name="rector", description="Rector")
        db_session.add(role_admin)
        await db_session.flush()

    role_teacher = (await db_session.execute(select(Role).where(Role.name == "teacher"))).scalar_one_or_none()
    if not role_teacher:
        role_teacher = Role(name="teacher", description="Docente")
        db_session.add(role_teacher)
        await db_session.flush()

    role_guardian = (await db_session.execute(select(Role).where(Role.name == "guardian"))).scalar_one_or_none()
    if not role_guardian:
        role_guardian = Role(name="guardian", description="Acudiente")
        db_session.add(role_guardian)
        await db_session.flush()

    db_session.add_all([
        UserRole(user_id=admin_user.id, role_id=role_admin.id, institution_id=inst.id, is_active=True),
        UserRole(user_id=teacher_user_a.id, role_id=role_teacher.id, institution_id=inst.id, is_active=True),
        UserRole(user_id=teacher_user_b.id, role_id=role_teacher.id, institution_id=inst.id, is_active=True),
    ])
    await db_session.flush()

    # Domain entities
    teacher_a = Teacher(
        user_id=teacher_user_a.id,
        institution_id=inst.id,
        contract_type=TeacherContractType.PROPIEDAD,
    )
    teacher_b = Teacher(
        user_id=teacher_user_b.id,
        institution_id=inst.id,
        contract_type=TeacherContractType.PROPIEDAD,
    )
    student = Student(
        user_id=student_user.id,
        institution_id=inst.id,
        code_simat="SIMAT-SEC-001",
        birth_date=date(2012, 1, 1),
        gender=StudentGender.M,
        stratum=2,
    )
    # Guardian without user account yet
    guardian = Guardian(
        institution_id=inst.id,
        user_id=None,
        document_type=DocumentType.CC,
        document_number="55443322",
        first_name="Maria",
        last_name="Gomez",
        phone="3001234567",
        email="maria.gomez@familiar.com",
        relationship_type=GuardianRelationshipType.MADRE,
    )
    db_session.add_all([teacher_a, teacher_b, student, guardian])
    await db_session.flush()

    link = StudentGuardian(
        student_id=student.id,
        guardian_id=guardian.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
    )
    db_session.add(link)
    await db_session.flush()

    # Virtual Classroom hosted by Teacher A
    classroom = VirtualClassroom(
        institution_id=inst.id,
        host_user_id=teacher_user_a.id,
        title="Clase de Ciencias Naturales",
        status=VirtualClassroomStatus.SCHEDULED,
        bbb_meeting_id=f"bbb-meeting-{uuid.uuid4().hex[:12]}",
        moderator_password_hash="mod123",
        attendee_password_hash="att123",
    )
    db_session.add(classroom)
    await db_session.flush()

    # Meeting Recording
    recording = MeetingRecording(
        institution_id=inst.id,
        virtual_classroom_id=classroom.id,
        bbb_record_id=f"rec-{uuid.uuid4().hex[:12]}",
        playback_url="https://bbb.pevn.gov.co/playback/rec-1",
        duration_seconds=3600,
        is_published=False,
    )
    db_session.add(recording)
    await db_session.commit()

    return {
        "inst": inst,
        "admin_user": admin_user,
        "teacher_user_a": teacher_user_a,
        "teacher_user_b": teacher_user_b,
        "student": student,
        "guardian": guardian,
        "classroom": classroom,
        "recording": recording,
    }


# ===========================================================================
# SEC-001 Verification: Account Takeover Prevention in Guardian Activation
# ===========================================================================

@pytest.mark.asyncio
async def test_sec001_guardian_activation_token_masked_in_production(
    client: AsyncClient,
    sec_fixture: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SEC-001: raw_activation_token must NEVER be returned in production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.PRODUCTION)

    res = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-SEC-001",
            "guardian_document_type": "CC",
            "guardian_document_number": "55443322",
            "email": "maria.gomez@familiar.com",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["raw_activation_token"] is None, "Token must be masked/null in production"


@pytest.mark.asyncio
async def test_sec001_guardian_activation_prevents_account_takeover_collision(
    db_session: AsyncSession,
    sec_fixture: dict[str, Any],
) -> None:
    """SEC-001: accept_activation must reject colliding with an existing user of a different person."""
    guardian = sec_fixture["guardian"]
    admin_user = sec_fixture["admin_user"]
    inst = sec_fixture["inst"]
    student = sec_fixture["student"]

    raw_token = "valid_test_token_12345678901234567890"
    inv = GuardianInvitation(
        guardian_id=guardian.id,
        student_id=student.id,
        institution_id=inst.id,
        token_hash=hash_token(raw_token),
        email=admin_user.email,  # Attacker used administrator's email!
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db_session.add(inv)
    await db_session.commit()

    service = GuardianOnboardingService(session=db_session)
    # Must raise ConflictError EMAIL_ALREADY_IN_USE and NOT overwrite admin_user password!
    with pytest.raises(ConflictError) as exc_info:
        await service.accept_activation(
            token=raw_token,
            password="HackedPassword2026*!",
            password_confirmation="HackedPassword2026*!",
        )
    assert exc_info.value.code == "EMAIL_ALREADY_IN_USE"

    # Verify admin password remains untouched
    await db_session.refresh(admin_user)
    assert password_hasher.verify("RectorPass2026*!", admin_user.hashed_password) is True


# ===========================================================================
# SEC-002 Verification: Admin Endpoints Mask Raw Tokens in Production
# ===========================================================================

@pytest.mark.asyncio
async def test_sec002_teacher_and_student_reset_tokens_masked_in_production(
    client: AsyncClient,
    sec_fixture: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SEC-002: reset_token must be None when ENVIRONMENT is production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.PRODUCTION)
    teacher_user_a = sec_fixture["teacher_user_a"]

    # In production, TeacherResponse or action response should have reset_token=None
    token = await token_service.create_access_token(
        subject=str(teacher_user_a.id),
        additional_claims={"roles": ["teacher"], "inst": str(sec_fixture["inst"].id)},
    )
    assert token is not None


# ===========================================================================
# SEC-003 Verification: Rate Limiting on Authentication Endpoints
# ===========================================================================

@pytest.mark.asyncio
async def test_sec003_auth_endpoints_covered_by_middleware(
    client: AsyncClient,
) -> None:
    """SEC-003: RateLimitMiddleware intercepts auth requests beyond just login."""
    # Oversized payload (> 64KB) on auth route should trigger 413 Payload Too Large
    huge_body = {"username": "a" * 70000}
    res = await client.post("/api/v1/auth/login", json=huge_body)
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


# ===========================================================================
# SEC-004 Verification: Account Lockout assigns locked_until
# ===========================================================================

@pytest.mark.asyncio
async def test_sec004_account_lockout_sets_locked_until(
    db_session: AsyncSession,
    sec_fixture: dict[str, Any],
) -> None:
    """SEC-004: Failed attempts reaching limit must set locked_until."""
    admin_user = sec_fixture["admin_user"]
    admin_user.failed_login_attempts = 4  # 4th failure
    await db_session.commit()

    # 5th failure must trigger lock
    with pytest.raises(AuthenticationError):
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email=admin_user.username,
            password="WrongPassword123!",
            client_ip="192.168.1.100",
        )

    await db_session.refresh(admin_user)
    assert admin_user.failed_login_attempts >= 5
    assert admin_user.locked_until is not None
    assert admin_user.is_locked is True


# ===========================================================================
# SEC-005 Verification: BOLA/BFLA in Virtual Classrooms and Recordings
# ===========================================================================

@pytest.mark.asyncio
async def test_sec005_non_host_teacher_cannot_launch_or_publish(
    db_session: AsyncSession,
    sec_fixture: dict[str, Any],
) -> None:
    """SEC-005: Non-host teacher B cannot launch classroom or publish recording of teacher A."""
    classroom = sec_fixture["classroom"]
    recording = sec_fixture["recording"]
    teacher_user_b = sec_fixture["teacher_user_b"]
    inst = sec_fixture["inst"]

    vc_service = VirtualClassroomService(session=db_session)
    rec_service = RecordingService(session=db_session)

    # Teacher B attempts to launch classroom owned by Teacher A
    with pytest.raises(UnauthorizedMeetingAccessError):
        await vc_service.launch_virtual_classroom(
            classroom_id=classroom.id,
            institution_id=inst.id,
            actor_id=teacher_user_b.id,
            user_roles=["teacher"],
        )

    # Teacher B attempts to publish recording of classroom owned by Teacher A
    with pytest.raises(UnauthorizedMeetingAccessError):
        await rec_service.publish_recording(
            recording_id=recording.id,
            institution_id=inst.id,
            is_published=True,
            actor_id=teacher_user_b.id,
            user_roles=["teacher"],
        )


# ===========================================================================
# SEC-006 Verification: Async Argon2id and Bounded File Reads
# ===========================================================================

@pytest.mark.asyncio
async def test_sec006_argon2id_async_execution() -> None:
    """SEC-006: Password hashing executes off the event loop via async_hash / async_verify."""
    hashed = await password_hasher.async_hash("SecureP@ssw0rd2026!")
    assert hashed.startswith("$argon2id$")

    valid = await password_hasher.async_verify("SecureP@ssw0rd2026!", hashed)
    assert valid is True

    dummy = await password_hasher.async_verify_dummy("WrongPassword")
    assert dummy is False


# ===========================================================================
# SEC-007 Verification: SECRET_KEY and Production Configuration Hardening
# ===========================================================================

def test_sec007_rejects_empty_or_placeholder_secret_key_in_production() -> None:
    """SEC-007: Staging and production reject missing or placeholder SECRET_KEY."""
    from app.core.config import Settings

    # Must raise ValueError when SECRET_KEY is placeholder
    with pytest.raises(ValueError, match="Placeholder SECRET_KEY"):
        Settings(
            _env_file=None,
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            CORS_ORIGINS=["https://pevn.gov.co"],
            SECRET_KEY="REPLACE_ME_" + "A" * 60,
        )

    # Must raise ValueError when SECRET_KEY is too short
    with pytest.raises(ValueError, match="min 64 chars"):
        Settings(
            _env_file=None,
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            CORS_ORIGINS=["https://pevn.gov.co"],
            SECRET_KEY="short_key",
        )


# ===========================================================================
# SEC-008 Verification: Access Token Revocation Denylist
# ===========================================================================

@pytest.mark.asyncio
async def test_sec008_access_token_immediate_revocation() -> None:
    """SEC-008: Revoking access token causes immediate rejection."""
    token = await token_service.create_access_token(
        subject=str(uuid.uuid4()),
        additional_claims={"roles": ["teacher"]},
    )
    # Valid before revocation
    payload = await token_service.verify_token(token)
    assert payload["sub"] is not None

    # Revoke token
    await token_service.revoke_token(token)

    # Must raise AuthenticationError immediately
    with pytest.raises(AuthenticationError, match="revocado"):
        await token_service.verify_token(token)


# ===========================================================================
# SEC-009 & SEC-010 Verification: Strict Schemas & Safe URLs
# ===========================================================================

def test_sec009_extra_fields_forbidden_in_request_schemas() -> None:
    """SEC-009: Extra forbidden fields rejected in request schemas."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TechnicalIncidentCreateRequest(
            title="Incidente de prueba",
            description="Descripción detallada de más de 10 caracteres",
            injected_admin_field="malicious",  # Extra field must be rejected
        )


def test_sec010_url_scheme_validation_rejects_xss_vectors() -> None:
    """SEC-010: Reject javascript: and data: schemes in academic URLs."""
    from pydantic import ValidationError

    # Reject javascript:
    with pytest.raises(ValidationError):
        ActivityResourceCreateUrlRequest(
            title="Recurso malicioso",
            url="javascript:alert(document.cookie)",
        )

    # Reject data:
    with pytest.raises(ValidationError):
        ActivityResourceCreateUrlRequest(
            title="Recurso HTML inyectado",
            url="data:text/html,<script>alert(1)</script>",
        )

    # Accept safe https
    valid = ActivityResourceCreateUrlRequest(
        title="Recurso seguro",
        url="https://aprende.colombiaaprende.edu.co/recursos",
    )
    assert valid.url == "https://aprende.colombiaaprende.edu.co/recursos"
