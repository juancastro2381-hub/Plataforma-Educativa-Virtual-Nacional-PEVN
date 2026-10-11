"""
PEVN Backend — Department Admin Creation CLI Command

Creates a dedicated platform Department Admin account interactively
or via environment variables for manual certification and territorial inspection.

SECURITY:
  - Passwords are never hardcoded or seeded in source control
  - Uses Argon2id password hashing (RFC 9106)
  - Assigns departmental scope with SystemRole.DEPARTMENT_ADMIN (level 80)
  - Explicitly does NOT grant superadmin wildcard (*:*)

Usage:
  Interactive:
    python -m app.cli.create_department_admin

  Environment variables (automated / testing):
    DEPARTMENT_ADMIN_EMAIL="department_admin@pevn.edu.co" \
    DEPARTMENT_ADMIN_USERNAME="department_admin" \
    DEPARTMENT_ADMIN_PASSWORD="<SECURE_ENV_PASSWORD>" \
    python -m app.cli.create_department_admin
"""

from __future__ import annotations

import asyncio
import getpass
import os
import sys

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.logging import configure_logging, get_logger
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.db.session import get_session_factory
from app.models.role import Role, UserRole
from app.models.territory import Department
from app.models.user import DocumentType, User

configure_logging(log_level="INFO", log_format="console")
_logger = get_logger("app.cli.create_department_admin")
_MIN_PASSWORD_LENGTH = 8


async def async_create_department_admin() -> int:
    """Async execution of department admin creation."""
    email = os.getenv("DEPARTMENT_ADMIN_EMAIL")
    username = os.getenv("DEPARTMENT_ADMIN_USERNAME")
    password = os.getenv("DEPARTMENT_ADMIN_PASSWORD")
    first_name = os.getenv("DEPARTMENT_ADMIN_FIRST_NAME", "Administrador")
    last_name = os.getenv("DEPARTMENT_ADMIN_LAST_NAME", "Departamental — Manual Test")
    document_number = os.getenv("DEPARTMENT_ADMIN_DOCUMENT_NUMBER", "1000000003")
    department_code = os.getenv("DEPARTMENT_ADMIN_DEPT_CODE", "11")

    # Interactive prompts if not supplied via environment
    if not email:
        email = input("Ingrese correo electrónico del Department Admin: ").strip()
    if not username:
        username = input("Ingrese nombre de usuario (username): ").strip()
    if not password:
        password = getpass.getpass("Ingrese contraseña segura: ")
        password_confirm = getpass.getpass("Confirme la contraseña: ")
        if password != password_confirm:
            print("ERROR: Las contraseñas no coinciden.", file=sys.stderr)
            return 1

    if not email or not username or not password:
        print("ERROR: Todos los campos son obligatorios.", file=sys.stderr)
        return 1

    if len(password) < _MIN_PASSWORD_LENGTH:
        print(
            "ERROR: La contraseña debe tener al menos "
            f"{_MIN_PASSWORD_LENGTH} caracteres.",
            file=sys.stderr,
        )
        return 1

    session_maker = get_session_factory()
    async with session_maker() as db:
        # Validate that department code exists in territory catalog
        dept_query = select(Department).where(Department.code == department_code)
        dept_res = await db.execute(dept_query)
        dept = dept_res.scalar_one_or_none()
        if not dept:
            print(
                f"ERROR: Código de departamento {department_code!r} no encontrado.",
                file=sys.stderr,
            )
            return 1
        dept_name = dept.name

        # Resolve department_admin role (must exist as a canonical role)
        role_query = select(Role).where(Role.name == SystemRole.DEPARTMENT_ADMIN.value)
        role_res = await db.execute(role_query)
        department_admin_role = role_res.scalar_one_or_none()

        if not department_admin_role:
            print(
                f"ERROR: El rol canónico {SystemRole.DEPARTMENT_ADMIN.value!r} "
                "no existe en la base de datos.",
                file=sys.stderr,
            )
            return 1

        hashed_password = password_hasher.hash(password)

        # Check collision or existing account on username or email
        query = (
            select(User)
            .where((User.email == email) | (User.username == username))
            .options(selectinload(User.user_roles))
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Idempotent update: ensure user is active, password updated, and department_id is bound
            existing_user.hashed_password = hashed_password
            existing_user.is_active = True
            existing_user.is_verified = True
            existing_user.institution_id = None

            found_role = False
            for ur in existing_user.user_roles:
                if ur.role_id == department_admin_role.id:
                    ur.department_id = dept.id
                    ur.institution_id = None
                    ur.campus_id = None
                    ur.is_active = True
                    found_role = True
                    break

            if not found_role:
                new_ur = UserRole(
                    user_id=existing_user.id,
                    role_id=department_admin_role.id,
                    institution_id=None,
                    campus_id=None,
                    department_id=dept.id,
                    is_active=True,
                )
                db.add(new_ur)

            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_UPDATED,
                    actor_id=str(existing_user.id),
                    actor_ip="127.0.0.1",
                    target_id=str(existing_user.id),
                    target_type="user",
                    institution_id=None,
                    success=True,
                    metadata={
                        "role": SystemRole.DEPARTMENT_ADMIN.value,
                        "department_code": department_code,
                        "department_id": str(dept.id),
                        "department_name": dept_name,
                        "source": "cli_idempotent",
                    },
                ),
                session=db,
            )

            await db.commit()
            print(
                f"ÉXITO: Department Admin {username!r} ({email!r}) actualizado satisfactoriamente "
                f"con alcance departamental {department_code} ({dept_name}) y department_id={dept.id}."
            )
            return 0

        # Create new user
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            document_type=DocumentType.CC,
            document_number=document_number,
            institution_id=None,  # Territorial scope (institution_id is NULL)
            is_active=True,
            is_verified=True,
            must_change_password=False,
        )
        db.add(new_user)
        await db.flush()

        # Assign Department Admin role with territorial department_id
        user_role = UserRole(
            user_id=new_user.id,
            role_id=department_admin_role.id,
            institution_id=None,
            campus_id=None,
            department_id=dept.id,
            is_active=True,
        )
        db.add(user_role)

        # Audit creation event
        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.USER_CREATED,
                actor_id=str(new_user.id),
                actor_ip="127.0.0.1",
                target_id=str(new_user.id),
                target_type="user",
                institution_id=None,
                success=True,
                metadata={
                    "role": SystemRole.DEPARTMENT_ADMIN.value,
                    "department_code": department_code,
                    "department_id": str(dept.id),
                    "department_name": dept_name,
                    "source": "cli",
                },
            ),
            session=db,
        )

        await db.commit()
        print(
            f"ÉXITO: Department Admin {username!r} ({email!r}) creado satisfactoriamente "
            f"para departamento {department_code} ({dept_name}) con department_id={dept.id}."
        )
        return 0


def main() -> None:
    """CLI entry point."""
    code = asyncio.run(async_create_department_admin())
    sys.exit(code)


if __name__ == "__main__":
    main()
