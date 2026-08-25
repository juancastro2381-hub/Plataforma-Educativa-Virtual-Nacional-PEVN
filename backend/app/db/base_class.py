"""
PEVN Backend — SQLAlchemy Declarative Base Class

Defines the declarative Base class and common audit columns without circular imports.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all PEVN domain models.

    Provides common audit columns (created_at, updated_at) inherited by all models.
    """

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
