"""
PEVN Backend — SuperAdmin Creation CLI Command

Creates the initial platform SuperAdmin account interactively
or via environment variables.

SECURITY:
  - Passwords are never hardcoded or seeded in migrations
  - Uses Argon2id password hashing
  - Assigns national scope with SystemRole.SUPERADMIN (level 100)

Usage:
  Interactive:
    python -m app.cli.create_superadmin

  Environment variables (automated deployment):
    SUPERADMIN_EMAIL="admin@pevn.edu.co" \
    SUPERADMIN_USERNAME="superadmin" \
    SUPERADMIN_PASSWORD="StrongSecurePassword123!" \
    SUPERADMIN_FIRST_NAME="Administrador" \
    SUPERADMIN_LAST_NAME="Nacional" \
    SUPERADMIN_DOCUMENT_NUMBER="1234567890" \
    python -m app.cli.create_superadmin
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
_logger = get_logger("app.cli.create_superadmin")
_MIN_PASSWORD_LENGTH = 8


async def async_create_superadmin() -> int:
    """Async execution of superadmin creation."""
    email = os.getenv("SUPERADMIN_EMAIL")
    username = os.getenv("SUPERADMIN_USERNAME")
    password = os.getenv("SUPERADMIN_PASSWORD")
    first_name = os.getenv("SUPERADMIN_FIRST_NAME", "Administrador")
    last_name = os.getenv("SUPERADMIN_LAST_NAME", "Nacional")
    document_number = os.getenv("SUPERADMIN_DOCUMENT_NUMBER", "1000000000")

    # Interactive prompts if not supplied via environment
    if not email:
        email = input("Ingrese correo electrónico del SuperAdmin: ").strip()
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
        # Check if username or email already exists
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

        # Ensure superadmin role exists
        role_query = select(Role).where(Role.name == SystemRole.SUPERADMIN.value)
        role_res = await db.execute(role_query)
        superadmin_role = role_res.scalar_one_or_none()

        if not superadmin_role:
            superadmin_role = Role(
                name=SystemRole.SUPERADMIN.value,
                display_name="Super Administrador Nacional",
                description="Acceso global completo a toda la plataforma PEVN.",
                level=100,
            )
            db.add(superadmin_role)
            await db.flush()

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
            institution_id=None,  # National scope
            is_active=True,
            is_verified=True,
            must_change_password=False,
        )
        db.add(new_user)
        await db.flush()

        # Assign SuperAdmin role with national scope
        user_role = UserRole(
            user_id=new_user.id,
            role_id=superadmin_role.id,
            institution_id=None,
            campus_id=None,
            is_active=True,
        )
        db.add(user_role)

        # Audit creation
        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.USER_CREATED,
                actor_id=str(new_user.id),
                actor_ip="127.0.0.1",
                target_id=str(new_user.id),
                target_type="user",
                institution_id=None,
                success=True,
                metadata={"role": SystemRole.SUPERADMIN.value, "source": "cli"},
            ),
            session=db,
        )

        await db.commit()
        print(f"ÉXITO: SuperAdmin {username!r} ({email!r}) creado satisfactoriamente.")
        return 0


def main() -> None:
    """CLI entry point."""
    code = asyncio.run(async_create_superadmin())
    sys.exit(code)


if __name__ == "__main__":
    main()
