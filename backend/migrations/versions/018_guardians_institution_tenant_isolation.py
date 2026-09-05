"""Guardian Institutional Multi-Tenant Isolation Schema (Phase 13E.4)

Revision ID: 018_guardian_tenant_isolation
Revises: 017_teacher_portal_schema
Create Date: 2026-09-01 09:45:00.000000

Guarantees complete multi-tenant server-side isolation for Legal Guardians (Acudientes):
  - Adds `institution_id` (UUID NOT NULL) to the `guardians` table.
  - Adds foreign key constraint to `institutions.id` with ON DELETE RESTRICT.
  - Adds index on `institution_id` for tenant-scoped query optimization.
  - Validates and backfills existing Guardian ownership deterministically from
    `student_guardians -> students.institution_id`.
  - Replaces global document unique constraint with institutional composite
    uniqueness `(institution_id, document_type, document_number)`.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "018_guardian_tenant_isolation"
down_revision: str | None = "017_teacher_portal_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add institution_id column as nullable initially for safe backfill
    op.add_column(
        "guardians",
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 2. Safety check: Detect any ambiguous guardians linked to students across multiple institutions
    conn = op.get_bind()
    multi_inst_check = conn.execute(
        sa.text("""
            SELECT sg.guardian_id, COUNT(DISTINCT s.institution_id) as inst_count
            FROM student_guardians sg
            JOIN students s ON s.id = sg.student_id
            GROUP BY sg.guardian_id
            HAVING COUNT(DISTINCT s.institution_id) > 1
        """)
    ).fetchall()

    if multi_inst_check:
        raise RuntimeError(
            f"Migration halted: Detected {len(multi_inst_check)} guardian(s) associated with students "
            "from multiple different institutions. Cannot determine unambiguous ownership."
        )

    # 3. Deterministic backfill from student_guardians -> students.institution_id
    op.execute("""
        UPDATE guardians
        SET institution_id = subquery.institution_id
        FROM (
            SELECT DISTINCT sg.guardian_id, s.institution_id
            FROM student_guardians sg
            JOIN students s ON s.id = sg.student_id
        ) AS subquery
        WHERE guardians.id = subquery.guardian_id
    """)

    # 4. Safety check: Detect any orphan guardians that could not be mapped to any institution
    orphan_check = conn.execute(
        sa.text("SELECT id, document_type, document_number, first_name, last_name FROM guardians WHERE institution_id IS NULL")
    ).fetchall()

    if orphan_check:
        orphan_details = ", ".join(f"[{r[0]}: {r[1]} {r[2]} - {r[3]} {r[4]}]" for r in orphan_check)
        raise RuntimeError(
            f"Migration halted: Detected {len(orphan_check)} orphan guardian(s) with no student links: {orphan_details}. "
            "Cannot infer institution_id without manual assignment."
        )

    # 5. Enforce NOT NULL on institution_id
    op.alter_column("guardians", "institution_id", nullable=False)

    # 6. Add foreign key constraint to institutions.id
    op.create_foreign_key(
        "fk_guardians_institution_id",
        "guardians",
        "institutions",
        ["institution_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 7. Create index on institution_id
    op.create_index(
        op.f("ix_guardians_institution_id"),
        "guardians",
        ["institution_id"],
        unique=False,
    )

    # 8. Drop legacy global document uniqueness constraint
    op.drop_constraint("uq_guardians_document", "guardians", type_="unique")

    # 9. Create composite tenant-scoped uniqueness constraint (institution_id, document_type, document_number)
    op.create_unique_constraint(
        "uq_guardians_institution_document",
        "guardians",
        ["institution_id", "document_type", "document_number"],
    )


def downgrade() -> None:
    # 1. Drop composite tenant uniqueness constraint
    op.drop_constraint("uq_guardians_institution_document", "guardians", type_="unique")

    # 2. Re-create legacy global document uniqueness constraint
    op.create_unique_constraint(
        "uq_guardians_document",
        "guardians",
        ["document_type", "document_number"],
    )

    # 3. Drop index on institution_id
    op.drop_index(op.f("ix_guardians_institution_id"), table_name="guardians")

    # 4. Drop foreign key constraint
    op.drop_constraint("fk_guardians_institution_id", "guardians", type_="foreignkey")

    # 5. Drop institution_id column
    op.drop_column("guardians", "institution_id")
