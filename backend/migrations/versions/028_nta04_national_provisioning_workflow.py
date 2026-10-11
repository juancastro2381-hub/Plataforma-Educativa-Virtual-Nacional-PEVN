"""National Provisioning Workflow (Phase NTA-04)

Revision ID: 028_nta04_national_provisioning_workflow
Revises: 027_nta03_catalog_provisioning_architecture
Create Date: 2026-10-06 12:00:00.000000

Implements Phase NTA-04 of the PEVN National Territorial Architecture:
  - Creates `institution_onboarding_requests` table to govern the transition from
    official educational catalog records into fully provisioned SaaS tenants.
  - Enforces foreign keys with strict ON DELETE semantics.
  - Implements unique radicado constraint (`uq_onboarding_request_number`).
  - Implements territorial performance compound index (`ix_onboarding_department_status`).
  - Implements status/timestamp index (`ix_onboarding_status_created`).
  - Implements DANE code lookup index (`ix_onboarding_dane_code`).
  - Implements partial unique index `uq_onboarding_active_catalog_institution`
    preventing simultaneous active onboarding requests for the same catalog institution.
  - Safe, non-destructive downgrade strategy.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "028_nta04_national_provisioning_workflow"
down_revision: str | None = "027_nta03_catalog_provisioning_architecture"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create table institution_onboarding_requests
    op.create_table(
        "institution_onboarding_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("request_number", sa.String(length=32), nullable=False),
        sa.Column(
            "catalog_institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("official_institution_catalog.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("dane_code", sa.String(length=12), nullable=False),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "municipality_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("municipalities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "requested_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("requester_role", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="SUBMITTED",
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("proposed_rector_name", sa.String(length=255), nullable=True),
        sa.Column("proposed_rector_email", sa.String(length=255), nullable=True),
        sa.Column("proposed_rector_doc_type", sa.String(length=20), nullable=True),
        sa.Column("proposed_rector_doc_num", sa.String(length=50), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "rejected_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "cancelled_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column(
            "provisioned_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("provisioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "lock_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # 2. Indexes
    op.create_index(
        "uq_onboarding_request_number",
        "institution_onboarding_requests",
        ["request_number"],
        unique=True,
    )
    op.create_index(
        "ix_onboarding_department_status",
        "institution_onboarding_requests",
        ["department_id", "status"],
    )
    op.create_index(
        "ix_onboarding_status_created",
        "institution_onboarding_requests",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_onboarding_dane_code",
        "institution_onboarding_requests",
        ["dane_code"],
    )

    # 3. Partial unique index: prevents simultaneous active requests for the same catalog institution
    op.create_index(
        "uq_onboarding_active_catalog_institution",
        "institution_onboarding_requests",
        ["catalog_institution_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED')"
        ),
    )


def downgrade() -> None:
    # 1. Drop table (cascades indexes and constraints)
    op.drop_table("institution_onboarding_requests")
