"""
PEVN Backend — Student Domain Service

Authoritative business logic for student profiles, SIMAT uniqueness,
socio-demographic inclusion metadata, and guardian associations.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    StudentNotFoundError,
)
from app.core.logging import get_logger
from app.models.guardian import StudentGuardian
from app.models.student import Student, StudentGender
from app.models.user import User

_logger = get_logger(__name__)

_MIN_STRATUM = 1
_MAX_STRATUM = 6


class StudentService:
    """
    Domain service for Student profile management.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_student(
        self,
        *,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
        code_simat: str,
        birth_date: date,
        gender: StudentGender = StudentGender.M,
        blood_type: str | None = None,
        stratum: int | None = None,
        eps_health_provider: str | None = None,
        has_disability: bool = False,
        disability_type: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Student:
        """
        Create a student profile 1:1 linked to a User account within an institution.
        """
        # 1. Validate Stratum Range
        if stratum is not None and not (_MIN_STRATUM <= stratum <= _MAX_STRATUM):
            raise AcademicDomainError(
                "El estrato socioeconómico debe estar entre 1 y 6."
            )

        # 2. Validate User Tenant Ownership
        user = (
            await self._session.execute(
                select(User).where(
                    User.id == user_id,
                    User.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not user:
            raise CrossTenantMismatchError(
                "La cuenta de usuario no pertenece a la institución especificada."
            )

        # 3. Check 1:1 User to Student Uniqueness
        existing_profile = (
            await self._session.execute(
                select(Student).where(Student.user_id == user_id)
            )
        ).scalar_one_or_none()
        if existing_profile:
            raise AcademicDomainError(
                "El usuario ya posee un perfil de estudiante asignado."
            )

        # 4. Check SIMAT Uniqueness
        dup_simat = (
            await self._session.execute(
                select(Student).where(Student.code_simat == code_simat)
            )
        ).scalar_one_or_none()
        if dup_simat:
            raise AcademicDomainError(
                f"El código SIMAT '{code_simat}' ya se encuentra registrado."
            )

        student = Student(
            user_id=user_id,
            institution_id=institution_id,
            code_simat=code_simat,
            birth_date=birth_date,
            gender=gender,
            blood_type=blood_type,
            stratum=stratum,
            eps_health_provider=eps_health_provider,
            has_disability=has_disability,
            disability_type=disability_type,
        )
        self._session.add(student)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.STUDENT_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(student.id),
                target_type="Student",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"code_simat": code_simat, "user_id": str(user_id)},
            ),
            session=self._session,
        )

        return student

    async def get_student_by_id(
        self,
        *,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> Student:
        """
        Retrieve a student validating tenant isolation.
        """
        stmt = (
            select(Student)
            .options(selectinload(Student.user))
            .where(
                Student.id == student_id,
                Student.institution_id == institution_id,
            )
        )
        student = (await self._session.execute(stmt)).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError(
                f"Estudiante {student_id} no encontrado en la institución."
            )
        return student

    async def get_student_by_simat(
        self,
        *,
        code_simat: str,
        institution_id: uuid.UUID,
    ) -> Student:
        """
        Retrieve a student by national SIMAT code validating tenant isolation.
        """
        stmt = (
            select(Student)
            .options(selectinload(Student.user))
            .where(
                Student.code_simat == code_simat,
                Student.institution_id == institution_id,
            )
        )
        student = (await self._session.execute(stmt)).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError(
                f"Estudiante con SIMAT '{code_simat}' no encontrado."
            )
        return student

    async def get_student_guardians(
        self,
        *,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> list[StudentGuardian]:
        """
        Retrieve all guardian associations for a student.
        """
        # Ensure student belongs to institution
        await self.get_student_by_id(
            student_id=student_id,
            institution_id=institution_id,
        )

        stmt = (
            select(StudentGuardian)
            .options(selectinload(StudentGuardian.guardian))
            .where(StudentGuardian.student_id == student_id)
        )
        return list((await self._session.execute(stmt)).scalars().all())
