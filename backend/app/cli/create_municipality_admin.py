"""
PEVN Backend — Municipality Admin Creation CLI Command

Creates a dedicated platform Municipality Admin account interactively
or via environment variables for manual certification and municipal territorial inspection.

SECURITY:
  - Passwords are never hardcoded or seeded in source control
  - Uses Argon2id password hashing (RFC 9106)
  - Assigns municipal scope with SystemRole.MUNICIPALITY_ADMIN (level 70)
  - Derives parent department strictly from the canonical municipality record
  - Explicitly does NOT grant superadmin wildcard (*:*) or department-wide authority

Usage:
  Interactive:
    python -m app.cli.create_municipality_admin

  Environment variables (automated / testing):
    MUNICIPALITY_ADMIN_EMAIL="municipality_admin@pevn.edu.co" \
    MUNICIPALITY_ADMIN_USERNAME="municipality_admin" \
    MUNICIPALITY_ADMIN_PASSWORD="<SECURE_ENV_PASSWORD>" \
    MUNICIPALITY_ADMIN_MUNI_CODE="11001" \
    python -m app.cli.create_municipality_admin
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
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User

configure_logging(log_level="INFO", log_format="console")
_logger = get_logger("app.cli.create_municipality_admin")
_MIN_PASSWORD_LENGTH = 8


async def async_create_municipality_admin() -> int:
    """Async execution of municipality admin creation."""
    email = os.getenv("MUNICIPALITY_ADMIN_EMAIL")
    username = os.getenv("MUNICIPALITY_ADMIN_USERNAME")
    password = os.getenv("MUNICIPALITY_ADMIN_PASSWORD")
    first_name = os.getenv("MUNICIPALITY_ADMIN_FIRST_NAME", "Administrador")
    last_name = os.getenv("MUNICIPALITY_ADMIN_LAST_NAME", "Municipal — Test")
    document_number = os.getenv("MUNICIPALITY_ADMIN_DOCUMENT_NUMBER", "1000000004")
    municipality_code = os.getenv("MUNICIPALITY_ADMIN_MUNI_CODE", "11001")

    # Interactive prompts if not supplied via environment
    if not email:
        email = input("Ingrese correo electrónico del Municipality Admin: ").strip()
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
        # 1. Validate that municipality code exists in territory catalog
        muni_query = (
            select(Municipality)
            .where(Municipality.code == municipality_code)
            .options(selectinload(Municipality.department))
        )
        muni_res = await db.execute(muni_query)
        municipality = muni_res.scalar_one_or_none()
        if not municipality:
            print(
                f"ERROR: Código de municipio {municipality_code!r} no encontrado en la base de datos.",
                file=sys.stderr,
            )
            return 1

        # Derive parent department strictly from the canonical municipality record
        department_id = municipality.department_id
        dept_name = municipality.department.name if municipality.department else "N/A"
        dept_code = municipality.department.code if municipality.department else "N/A"

        # 2. Resolve municipality_admin canonical role
        role_query = select(Role).where(Role.name == SystemRole.MUNICIPALITY_ADMIN.value)
        role_res = await db.execute(role_query)
        muni_admin_role = role_res.scalar_one_or_none()

        if not muni_admin_role:
            print(
                f"ERROR: El rol canónico {SystemRole.MUNICIPALITY_ADMIN.value!r} "
                "no existe en la base de datos.",
                file=sys.stderr,
            )
            return 1

        hashed_password = password_hasher.hash(password)

        # 3. Check existing user account by email or username
        query = (
            select(User)
            .where((User.email == email) | (User.username == username))
            .options(selectinload(User.user_roles))
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        action = "create"
        if existing_user:
            action = "update"
            # Idempotent update: ensure user is active, password updated, and bound to municipality
            existing_user.hashed_password = hashed_password
            existing_user.is_active = True
            existing_user.is_verified = True
            existing_user.institution_id = None
            existing_user.first_name = first_name
            existing_user.last_name = last_name

            found_role = False
            for ur in existing_user.user_roles:
                if ur.role_id == muni_admin_role.id:
                    ur.municipality_id = municipality.id
                    ur.department_id = department_id
                    ur.institution_id = None
                    ur.campus_id = None
                    ur.is_active = True
                    found_role = True
                    break

            if not found_role:
                new_ur = UserRole(
                    user_id=existing_user.id,
                    role_id=muni_admin_role.id,
                    municipality_id=municipality.id,
                    department_id=department_id,
                    institution_id=None,
                    campus_id=None,
                    is_active=True,
                )
                db.add(new_ur)

            user_id = str(existing_user.id)
            print(f"Cuenta de Municipality Admin {username!r} actualizada idempotentemente.")
        else:
            new_user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                document_type=DocumentType.CC,
                document_number=document_number,
                institution_id=None,
                is_active=True,
                is_verified=True,
                must_change_password=False,
            )
            db.add(new_user)
            await db.flush()

            new_ur = UserRole(
                user_id=new_user.id,
                role_id=muni_admin_role.id,
                municipality_id=municipality.id,
                department_id=department_id,
                institution_id=None,
                campus_id=None,
                is_active=True,
            )
            db.add(new_ur)
            user_id = str(new_user.id)
            print(f"Cuenta de Municipality Admin {username!r} creada exitosamente.")

        await db.commit()

        # Audit log entry
        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.USER_ROLE_ASSIGNED,
                actor_id=user_id,
                actor_ip="127.0.0.1",
                target_id=user_id,
                target_type="User",
                institution_id=None,
                metadata={
                    "action": f"cli.{action}_municipality_admin",
                    "role": SystemRole.MUNICIPALITY_ADMIN.value,
                    "municipality_code": municipality.code,
                    "municipality_name": municipality.name,
                    "municipality_id": str(municipality.id),
                    "department_code": dept_code,
                    "department_name": dept_name,
                    "department_id": str(department_id),
                },
                success=True,
            )
        )

        print(
            f"Asignación territorial: Municipio {municipality.code} - {municipality.name} "
            f"(Departamento {dept_code} - {dept_name})"
        )
        return 0


def main() -> None:
    """CLI entrypoint."""
    exit_code = asyncio.run(async_create_municipality_admin())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
