"""
PEVN Backend — SQLAlchemy Declarative Base

All ORM models must inherit from Base defined here.
This module also serves as the central import point for Alembic,
which reads Base.metadata to detect schema changes.

Usage:
    from app.db.base import Base

    class MyModel(Base):
        __tablename__ = "my_table"
        ...

Note for Alembic autogenerate:
    All model modules must be imported in migrations/env.py
    (or imported here via the model registry below) so that
    Alembic can discover them through Base.metadata.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all PEVN domain models.

    Provides common audit columns (created_at, updated_at) that
    will be inherited by all domain entity tables.
    """

    # ---- Common audit columns --------------------------------------------
    # These are defined here so ALL domain tables automatically get them.
    # No domain model should need to redeclare these.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created (set by the database).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of the last update (updated by the database on each write).",
    )

    def __repr__(self) -> str:
        """Provide a safe, useful repr for all models."""
        # Avoid exposing sensitive column values in repr
        try:
            table = getattr(self, "__table__", None)
            pk = getattr(table, "primary_key", None)
            cols = getattr(pk, "columns", [])
            pk_cols = [getattr(col, "name", str(col)) for col in cols]
            pk_vals = {col: getattr(self, col, "?") for col in pk_cols}
            pk_str = ", ".join(f"{k}={v!r}" for k, v in pk_vals.items())
            return (
                f"<{self.__class__.__name__} {pk_str}>"
                if pk_str
                else f"<{self.__class__.__name__}>"
            )
        except Exception:
            return f"<{self.__class__.__name__}>"


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
# Import all domain models here so Alembic's autogenerate can discover them.
# When a new model is created in Phase 2+, add its import here.
#
# Example (DO NOT add until Phase 2 domain models exist):
#   from app.models.user import User
#   from app.models.institution import Institution
#
# Currently empty — Phase 1 establishes the infrastructure only.
