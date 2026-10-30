"""SIEE Evaluation and Promotion Audit Timestamps Alignment Schema

Revision ID: 033_siee_evaluations_audit_timestamps
Revises: 032_coordinator_invitations
Create Date: 2026-10-30 03:00:00.000000

Aligns physical PostgreSQL SIEE evaluation and promotion tables with canonical
SQLAlchemy Base models inheriting standard audit timestamp columns:
  - period_subject_grades: adds created_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
  - academic_achievements: adds updated_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
  - recovery_grades: adds updated_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
  - student_promotions: adds updated_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "033_siee_evaluations_audit_timestamps"
down_revision: str | None = "032_coordinator_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. period_subject_grades table: add created_at
    op.add_column(
        "period_subject_grades",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 2. academic_achievements table: add updated_at
    op.add_column(
        "academic_achievements",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 3. recovery_grades table: add updated_at
    op.add_column(
        "recovery_grades",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 4. student_promotions table: add updated_at
    op.add_column(
        "student_promotions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("student_promotions", "updated_at")
    op.drop_column("recovery_grades", "updated_at")
    op.drop_column("academic_achievements", "updated_at")
    op.drop_column("period_subject_grades", "created_at")

