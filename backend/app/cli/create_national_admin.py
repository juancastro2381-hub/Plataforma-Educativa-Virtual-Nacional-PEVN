"""
PEVN Backend — National Admin Creation CLI Command

Creates a dedicated platform National Admin account interactively
or via environment variables for manual certification and operational inspection.

SECURITY:
  - Passwords are never hardcoded or seeded in source control
  - Uses Argon2id password hashing (RFC 9106)
  - Assigns national scope with SystemRole.NATIONAL_ADMIN (level 90)
  - Explicitly does NOT grant superadmin wildcard (*:*)

Usage:
  Interactive:
    python -m app.cli.create_national_admin

  Environment variables (automated / testing):
    NATIONAL_ADMIN_EMAIL="national_admin@pevn.edu.co" \
    NATIONAL_ADMIN_USERNAME="national_admin" \
    NATIONAL_ADMIN_PASSWORD="StrongSecurePassword123!" \
    python -m app.cli.create_national_admin
"""

from __future__ import annotations

import asyncio
import getpass
import os
import sys

from sqlalchemy import select

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.logging import configure_logging, get_logger
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.db.session import get_session_factory
from app.models.role import Role, UserRole
from app.models.user import DocumentType, User

configure_logging(log_level="INFO", log_format="console")
_logger = get_logger("app.cli.create_national_admin")
_MIN_PASSWORD_LENGTH = 8


async def async_create_national_admin() -> int:
    """Async execution of national admin creation."""
    email = os.getenv("NATIONAL_ADMIN_EMAIL")
    username = os.getenv("NATIONAL_ADMIN_USERNAME")
    password = os.getenv("NATIONAL_ADMIN_PASSWORD")
    first_name = os.getenv("NATIONAL_ADMIN_FIRST_NAME", "Administrador")
    last_name = os.getenv("NATIONAL_ADMIN_LAST_NAME", "Nacional")
    document_number = os.getenv("NATIONAL_ADMIN_DOCUMENT_NUMBER", "1000000001")

    # Interactive prompts if not supplied via environment
    if not email:
        email = input("Ingrese correo electrónico del National Admin: ").strip()
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
        # Check collision on username or email
        query = select(User).where((User.email == email) | (User.username == username))
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            print(
                f"ERROR: Ya existe un usuario con correo {email!r} "
                f"o usuario {username!r}.",
                file=sys.stderr,
            )
            return 1

        # Resolve national_admin role (must exist as a canonical role)
        role_query = select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value)
        role_res = await db.execute(role_query)
        national_admin_role = role_res.scalar_one_or_none()

        if not national_admin_role:
            print(
                f"ERROR: El rol canónico {SystemRole.NATIONAL_ADMIN.value!r} "
                "no existe en la base de datos.",
                file=sys.stderr,
            )
            return 1

        # Hash password with Argon2id
        hashed_password = password_hasher.hash(password)

        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            document_type=DocumentType.CC,
            document_number=document_number,
            institution_id=None,  # Strictly national scope
            is_active=True,
            is_verified=True,
            must_change_password=False,
        )
        db.add(new_user)
        await db.flush()

        # Assign National Admin role with national scope
        user_role = UserRole(
            user_id=new_user.id,
            role_id=national_admin_role.id,
            institution_id=None,
            campus_id=None,
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
                metadata={"role": SystemRole.NATIONAL_ADMIN.value, "source": "cli"},
            ),
            session=db,
        )

        await db.commit()
        print(f"ÉXITO: National Admin {username!r} ({email!r}) creado satisfactoriamente.")
        return 0


def main() -> None:
    """CLI entry point."""
    code = asyncio.run(async_create_national_admin())
    sys.exit(code)


if __name__ == "__main__":
    main()
