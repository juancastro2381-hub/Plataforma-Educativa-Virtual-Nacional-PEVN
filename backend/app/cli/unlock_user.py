"""
PEVN Backend — Account Unlock & Maintenance CLI Utility
Framework: AI Software Factory Standard v1.2 — Phase NTA-05 Hardening

Unlocks user accounts that were administratively locked or affected by
brute-force abuse, resets velocity state in Redis, and optionally performs
interactive password resets.

SECURITY GUARANTEES:
  - Passwords are NEVER accepted through command-line arguments or environment variables
  - Password inputs are securely gathered via getpass.getpass()
  - Uses Argon2id password hashing (RFC 9106)
  - Records USER_ACCOUNT_UNLOCKED audit event with SYSTEM_CLI_MAINTENANCE actor
  - Clears all Redis Tier 3 and velocity state keys for the account
  - Zero plaintext secrets logged, displayed, or persisted in process tables

Usage:
  Interactive unlock:
    python -m app.cli.unlock_user --username department_admin

  Unlock with interactive password reset:
    python -m app.cli.unlock_user --username department_admin --reset-password
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import socket
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.logging import configure_logging, get_logger
from app.core.security.password import password_hasher
from app.core.security.rate_limiter import rate_limiter
from app.db.session import get_session_factory
from app.models.user import User

configure_logging(log_level="INFO", log_format="console")
_logger = get_logger("app.cli.unlock_user")
_MIN_PASSWORD_LENGTH = 8


async def async_unlock_user(
    target_identifier: str,
    reset_password: bool = False,
    db_session: AsyncSession | None = None,
) -> int:
    """
    Safely unlock target user, reset failure counters, clear Redis keys,
    optionally reset password, and record administrative audit trail.
    """
    target = target_identifier.strip()
    if not target:
        print("ERROR: Debe especificar un nombre de usuario o correo.", file=sys.stderr)
        return 1

    new_password: str | None = None
    if reset_password:
        p1 = getpass.getpass("Ingrese la nueva contraseña: ")
        if len(p1) < _MIN_PASSWORD_LENGTH:
            print(f"ERROR: La contraseña debe tener al menos {_MIN_PASSWORD_LENGTH} caracteres.", file=sys.stderr)
            return 1
        p2 = getpass.getpass("Confirme la nueva contraseña: ")
        if p1 != p2:
            print("ERROR: Las contraseñas no coinciden.", file=sys.stderr)
            return 1
        new_password = p1

    async def _execute_unlock(db: AsyncSession) -> int:
        query = select(User).where(
            (User.username == target) | (User.email == target.lower())
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            print(f"ERROR: Usuario {target!r} no encontrado en la base de datos.", file=sys.stderr)
            return 1

        print(f"Usuario localizado: {user.username} ({user.email})")
        print(f" - Estado actual: {'Activo' if user.is_active else 'Inactivo'}")
        print(f" - Intentos fallidos previos: {user.failed_login_attempts}")
        print(f" - Bloqueado hasta: {user.locked_until}")

        # 1. Atomically reset database lockout state
        user.failed_login_attempts = 0
        user.locked_until = None
        user.is_active = True

        # 2. Update password if requested
        if new_password:
            user.hashed_password = password_hasher.hash(new_password)
            print(" - Contraseña actualizada con Argon2id.")

        # 3. Clear Redis velocity and rate limit keys
        await rate_limiter.reset_all_for_account(user.username)
        await rate_limiter.reset_all_for_account(user.email)
        print(" - Estado de velocidad y limitadores Redis reiniciados.")

        # 4. Record certified maintenance audit event
        try:
            operator_name = getpass.getuser()
        except Exception:
            operator_name = os.getenv("USERNAME") or os.getenv("USER") or "unknown_operator"

        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = "localhost"

        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.USER_ACCOUNT_UNLOCKED,
                actor_id="SYSTEM_CLI_MAINTENANCE",
                actor_ip="127.0.0.1",
                target_id=str(user.id),
                target_type="user",
                institution_id=str(user.institution_id) if user.institution_id else None,
                success=True,
                metadata={
                    "action": "account_unlocked",
                    "source": "cli_unlock_utility",
                    "operator": operator_name,
                    "hostname": hostname,
                    "password_reset": bool(new_password),
                },
            ),
            session=db,
        )

        await db.commit()
        print(f"ÉXITO: La cuenta {user.username!r} ha sido desbloqueada satisfactoriamente.")
        return 0

    if db_session is not None:
        return await _execute_unlock(db_session)

    session_maker = get_session_factory()
    async with session_maker() as db:
        return await _execute_unlock(db)


def main() -> None:
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="PEVN Account Unlock & Maintenance Utility (NTA-05)"
    )
    parser.add_argument(
        "-u",
        "--username",
        dest="username",
        help="Nombre de usuario o correo electrónico a desbloquear",
        default=None,
    )
    parser.add_argument(
        "--reset-password",
        dest="reset_password",
        action="store_true",
        help="Solicitar interactivamente una nueva contraseña",
    )

    args = parser.parse_args()
    target = args.username
    if not target:
        target = input("Ingrese nombre de usuario o correo electrónico a desbloquear: ").strip()

    code = asyncio.run(async_unlock_user(target, reset_password=args.reset_password))
    sys.exit(code)


if __name__ == "__main__":
    main()
