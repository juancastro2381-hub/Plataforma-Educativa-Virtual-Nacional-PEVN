"""
PEVN Backend — Guardian Onboarding Domain Service (Phase 7 - Step 2)

Handles secure self-activation of legal guardians linked to enrolled students.
Preserves [OPEN-DECISION-3A-01] so offline/rural guardians remain valid in the domain
model without being forced to have an application login account.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import hash_token
from app.exceptions.errors import (
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)
from app.models.guardian import Guardian, StudentGuardian
from app.models.institution import Institution
from app.models.invitation import GuardianInvitation
from app.models.role import Role, UserRole
from app.models.student import Student
from app.models.token import PasswordResetToken
from app.models.user import DocumentType, User

GUARDIAN_ACTIVATION_EXPIRY_HOURS = 24


class GuardianOnboardingService:
    """
    Manages the lifecycle of Guardian tokenized self-onboarding.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit_svc: audit_service.__class__ = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit_svc

    async def request_activation(
        self,
        *,
        student_code_simat: str,
        guardian_document_type: DocumentType,
        guardian_document_number: str,
        email: str,
        client_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> tuple[GuardianInvitation, str]:
        """
        Validates the student enrollment relationship and guardian civil identity,
        generating a cryptographically secure 48-byte single-use onboarding token.
        """
        cleaned_simat = student_code_simat.strip()
        cleaned_guardian_doc = guardian_document_number.strip()
        cleaned_email = email.strip().lower()

        # 1. Locate student by SIMAT code or student document number
        student_stmt = (
            select(Student)
            .where(
                (Student.code_simat == cleaned_simat)
                | (Student.id.in_(
                    select(Student.id)
                    .join(User, Student.user_id == User.id)
                    .where(User.document_number == cleaned_simat)
                ))
            )
            .options(
                selectinload(Student.user),
                selectinload(Student.institution),
            )
        )
        student = (await self._session.execute(student_stmt)).scalar_one_or_none()
        if not student:
            raise NotFoundError(
                "No se encontró ningún estudiante matriculado con el código o documento suministrado.",
                code="STUDENT_NOT_FOUND",
            )

        # 2. Locate civil guardian record
        guardian_stmt = (
            select(Guardian)
            .where(
                Guardian.document_type == guardian_document_type,
                Guardian.document_number == cleaned_guardian_doc,
            )
            .options(selectinload(Guardian.user))
        )
        guardian = (await self._session.execute(guardian_stmt)).scalar_one_or_none()
        if not guardian:
            raise NotFoundError(
                "No se encontró un registro de acudiente registrado con el documento especificado.",
                code="GUARDIAN_NOT_FOUND",
            )

        # 3. Verify that the legal guardian-student relationship is registered
        link_stmt = select(StudentGuardian).where(
            StudentGuardian.student_id == student.id,
            StudentGuardian.guardian_id == guardian.id,
        )
        link = (await self._session.execute(link_stmt)).scalar_one_or_none()
        if not link:
            raise NotFoundError(
                "El acudiente no se encuentra vinculado legalmente como tutor del estudiante indicado.",
                code="GUARDIAN_RELATION_NOT_FOUND",
            )

        # 4. Check if guardian already has an active User account
        if guardian.user_id is not None:
            user_stmt = select(User).where(User.id == guardian.user_id)
            existing_user = (await self._session.execute(user_stmt)).scalar_one_or_none()
            if existing_user and existing_user.is_active:
                raise ConflictError(
                    "El acudiente ya cuenta con una cuenta de usuario activa en la plataforma.",
                    code="ACCOUNT_ALREADY_ACTIVATED",
                )

        # 5. Revoke any prior unredeemed invitations for this guardian
        await self._session.execute(
            update(GuardianInvitation)
            .where(
                GuardianInvitation.guardian_id == guardian.id,
                GuardianInvitation.is_used == False,  # noqa: E712
                GuardianInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # 6. Generate unforgeable 48-byte URL-safe cryptographic token
        raw_token = secrets.token_urlsafe(48)
        token_digest = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(hours=GUARDIAN_ACTIVATION_EXPIRY_HOURS)

        # 7. Create activation record
        invitation = GuardianInvitation(
            guardian_id=guardian.id,
            student_id=student.id,
            institution_id=student.institution_id,
            token_hash=token_digest,
            email=cleaned_email,
            expires_at=expires_at,
        )
        self._session.add(invitation)

        # Update guardian email if empty
        if not guardian.email:
            guardian.email = cleaned_email

        await self._session.flush()

        # 8. Record audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GUARDIAN_ACTIVATION_REQUESTED,
                actor_id=str(guardian.id),
                actor_ip=client_ip,
                target_id=str(guardian.id),
                target_type="Guardian",
                institution_id=str(student.institution_id),
                correlation_id=correlation_id,
                metadata={
                    "guardian_document": f"{guardian.document_type.value}:{guardian.document_number}",
                    "student_code_simat": student.code_simat,
                    "email": cleaned_email,
                    "expires_at": expires_at.isoformat(),
                },
            ),
            session=self._session,
        )

        return invitation, raw_token

    async def verify_token(self, *, token: str) -> dict[str, str | bool | datetime]:
        """
        Validates the integrity, non-expiration, and unredeemed status of an activation token.
        """
        token_digest = hash_token(token)

        stmt = (
            select(GuardianInvitation)
            .where(GuardianInvitation.token_hash == token_digest)
            .options(
                selectinload(GuardianInvitation.guardian),
                selectinload(GuardianInvitation.student).selectinload(Student.user),
                selectinload(GuardianInvitation.institution),
            )
        )
        invitation = (await self._session.execute(stmt)).scalar_one_or_none()

        if not invitation:
            # Fallback: check if this is an administrative PasswordResetToken (e.g. provisioned guardian account)
            reset_stmt = (
                select(PasswordResetToken)
                .where(PasswordResetToken.token_hash == token_digest)
                .options(selectinload(PasswordResetToken.user).selectinload(User.institution))
            )
            reset_token_rec = (await self._session.execute(reset_stmt)).scalar_one_or_none()
            if reset_token_rec:
                if reset_token_rec.is_used:
                    raise ConflictError(
                        "El token de activación ya ha sido redimido previamente.",
                        code="TOKEN_ALREADY_USED",
                    )
                if reset_token_rec.is_expired:
                    raise ConflictError(
                        "El enlace de activación ha expirado.",
                        code="TOKEN_EXPIRED",
                    )
                user = reset_token_rec.user
                g_stmt = select(Guardian).where(Guardian.user_id == user.id)
                guardian = (await self._session.execute(g_stmt)).scalar_one_or_none()
                guardian_name = f"{user.first_name} {user.last_name}" if user else "Acudiente"
                institution_name = user.institution.name if (user and user.institution) else "Institución Educativa"
                student_name = "Estudiante a cargo"
                if guardian:
                    sg_stmt = (
                        select(StudentGuardian)
                        .where(StudentGuardian.guardian_id == guardian.id)
                        .options(selectinload(StudentGuardian.student).selectinload(Student.user))
                    )
                    sg = (await self._session.execute(sg_stmt)).scalars().first()
                    if sg and sg.student:
                        if sg.student.user:
                            student_name = f"{sg.student.user.first_name} {sg.student.user.last_name}"
                        else:
                            student_name = f"Estudiante SIMAT {sg.student.code_simat}"

                return {
                    "valid": True,
                    "guardian_name": guardian_name,
                    "student_name": student_name,
                    "institution_name": institution_name,
                    "email": user.email if user else "",
                    "expires_at": reset_token_rec.expires_at,
                }

            raise NotFoundError(
                "El token de activación no es válido o no existe.",
                code="INVALID_TOKEN",
            )

        if invitation.is_used:
            raise ConflictError(
                "El token de activación ya ha sido redimido previamente.",
                code="TOKEN_ALREADY_USED",
            )

        if invitation.is_revoked:
            raise ConflictError(
                "El token de activación ha sido revocado o sustituido por una solicitud más reciente.",
                code="TOKEN_REVOKED",
            )

        if invitation.is_expired:
            raise ConflictError(
                "El enlace de activación ha expirado (vigencia máxima de 24 horas).",
                code="TOKEN_EXPIRED",
            )

        guardian = invitation.guardian
        student = invitation.student
        institution = invitation.institution
        guardian_name = f"{guardian.first_name} {guardian.last_name}" if guardian else "Acudiente"
        institution_name = institution.name if institution else "Institución Educativa"

        if student:
            student_user = student.user
            if student_user is not None:
                student_name = f"{student_user.first_name} {student_user.last_name}"
            else:
                student_name = f"Estudiante SIMAT {student.code_simat}"
        else:
            student_name = "Estudiante a cargo"

        return {
            "valid": True,
            "guardian_name": guardian_name,
            "student_name": student_name,
            "institution_name": institution_name,
            "email": invitation.email,
            "expires_at": invitation.expires_at,
        }

    async def accept_activation(
        self,
        *,
        token: str,
        password: str,
        password_confirmation: str,
        client_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> User:
        """
        Redeems the activation token, securely creates the User identity with Argon2id,
        assigns the canonical guardian role, links the Guardian domain entity, and activates login access.
        """
        if password != password_confirmation:
            raise UnprocessableEntityError(
                "La confirmación de contraseña no coincide con la clave ingresada.",
                code="PASSWORD_MISMATCH",
            )

        if len(password) < 8:
            raise UnprocessableEntityError(
                "La contraseña debe contener un mínimo de 8 caracteres.",
                code="PASSWORD_TOO_SHORT",
            )

        token_digest = hash_token(token)

        stmt = (
            select(GuardianInvitation)
            .where(GuardianInvitation.token_hash == token_digest)
            .options(
                selectinload(GuardianInvitation.guardian),
                selectinload(GuardianInvitation.student).selectinload(Student.user),
                selectinload(GuardianInvitation.institution),
            )
        )
        invitation = (await self._session.execute(stmt)).scalar_one_or_none()

        if not invitation or not invitation.is_valid:
            # Fallback: check if this is an administrative PasswordResetToken
            reset_stmt = (
                select(PasswordResetToken)
                .where(PasswordResetToken.token_hash == token_digest)
                .options(selectinload(PasswordResetToken.user))
            )
            reset_token_rec = (await self._session.execute(reset_stmt)).scalar_one_or_none()
            if reset_token_rec and reset_token_rec.is_valid:
                from app.services.auth_service import auth_service
                await auth_service.confirm_password_reset(
                    db=self._session,
                    raw_reset_token=token,
                    new_password=password,
                    client_ip=client_ip,
                    correlation_id=correlation_id,
                )
                user = reset_token_rec.user
                user.is_active = True
                user.must_change_password = False
                await self._session.flush()
                return user

            # Re-run verify to throw precise conflict/not-found error
            await self.verify_token(token=token)

        guardian = invitation.guardian
        institution = invitation.institution

        # Check if guardian already has an active user account
        if guardian.user_id is not None:
            raise ConflictError(
                "El acudiente ya cuenta con una cuenta de usuario activa en el sistema.",
                code="ACCOUNT_ALREADY_ACTIVATED",
            )

        # Check if email is already taken by another User
        email_stmt = select(User).where(User.email == invitation.email)
        existing_user = (await self._session.execute(email_stmt)).scalar_one_or_none()

        # Check if canonical 'guardian' role exists
        role_stmt = select(Role).where(Role.name == "guardian")
        guardian_role = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not guardian_role:
            raise NotFoundError(
                "Rol canónico 'guardian' no encontrado en el catálogo del sistema.",
                code="ROLE_NOT_FOUND",
            )

        hashed_pw = password_hasher.hash(password)

        if existing_user:
            user = existing_user
            user.hashed_password = hashed_pw
            user.is_active = True
            user.is_verified = True
        else:
            user = User(
                email=invitation.email,
                username=invitation.email,
                hashed_password=hashed_pw,
                first_name=guardian.first_name,
                last_name=guardian.last_name,
                document_type=guardian.document_type,
                document_number=guardian.document_number,
                institution_id=institution.id,
                is_active=True,
                is_verified=True,
            )
            self._session.add(user)
            await self._session.flush()

        # Link Guardian entity to User
        guardian.user_id = user.id

        # Assign canonical guardian UserRole
        ur_stmt = select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == guardian_role.id,
            UserRole.institution_id == institution.id,
        )
        existing_ur = (await self._session.execute(ur_stmt)).scalar_one_or_none()
        if existing_ur:
            existing_ur.is_active = True
        else:
            self._session.add(
                UserRole(
                    user_id=user.id,
                    role_id=guardian_role.id,
                    institution_id=institution.id,
                    is_active=True,
                )
            )

        # Mark invitation as redeemed
        invitation.is_used = True
        invitation.used_at = datetime.now(UTC)

        # Invalidate any other pending invitations for this guardian
        await self._session.execute(
            update(GuardianInvitation)
            .where(
                GuardianInvitation.guardian_id == guardian.id,
                GuardianInvitation.id != invitation.id,
                GuardianInvitation.is_used == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        await self._session.flush()

        # Record audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GUARDIAN_ONBOARDING_COMPLETED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                target_id=str(guardian.id),
                target_type="Guardian",
                institution_id=str(institution.id),
                correlation_id=correlation_id,
                metadata={
                    "guardian_id": str(guardian.id),
                    "user_id": str(user.id),
                    "email": user.email,
                    "institution_name": institution.name,
                },
            ),
            session=self._session,
        )

        return user
