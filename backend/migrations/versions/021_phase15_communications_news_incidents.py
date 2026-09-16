"""Phase 15: Communications, News and Student Coexistence Schema

Revision ID: 021_phase15_communications_news_incidents
Revises: 020_guardian_invitations
Create Date: 2026-09-07 10:00:00.000000

Implements the Phase 15 relational tables and PostgreSQL ENUMs:
  - communication_category_enum, communication_priority_enum, target_scope_type_enum, publishing_status_enum
  - news_category_enum
  - coexistence_situation_type_enum, incident_status_enum
  - institutional_communications
  - communication_audiences
  - communication_receipts
  - institutional_news
  - student_incidents
  - incident_follow_ups
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "021_phase15_communications_news_incidents"
down_revision: str | None = "020_guardian_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Create Enums safely using PostgreSQL DO $$ BEGIN ... END $$;
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'communication_category_enum') THEN
                CREATE TYPE communication_category_enum AS ENUM (
                    'CIRCULAR_OFICIAL',
                    'CONVOCATORIA_REUNION',
                    'AVISO_ACADEMICO',
                    'AVISO_ADMINISTRATIVO',
                    'RECORDATORIO',
                    'EMERGENCIA_INSTITUCIONAL'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'communication_priority_enum') THEN
                CREATE TYPE communication_priority_enum AS ENUM (
                    'BAJA',
                    'MEDIA',
                    'ALTA',
                    'URGENTE'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'target_scope_type_enum') THEN
                CREATE TYPE target_scope_type_enum AS ENUM (
                    'TODOS_INSTITUCION',
                    'SOLO_ESTUDIANTES',
                    'SOLO_ACUDIENTES',
                    'SOLO_DOCENTES',
                    'POR_SEDE',
                    'POR_GRADO',
                    'POR_GRUPO'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'publishing_status_enum') THEN
                CREATE TYPE publishing_status_enum AS ENUM (
                    'BORRADOR',
                    'PUBLICADO',
                    'ARCHIVADO'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'news_category_enum') THEN
                CREATE TYPE news_category_enum AS ENUM (
                    'LOGRO_ACADEMICO',
                    'EVENTO_CULTURAL',
                    'EVENTO_DEPORTIVO',
                    'PROYECTO_INSTITUCIONAL',
                    'NOTICIA_GENERAL'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'coexistence_situation_type_enum') THEN
                CREATE TYPE coexistence_situation_type_enum AS ENUM (
                    'TIPO_I',
                    'TIPO_II',
                    'TIPO_III',
                    'OBSERVACION_POSITIVA'
                );
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_status_enum') THEN
                CREATE TYPE incident_status_enum AS ENUM (
                    'ABIERTO',
                    'EN_SEGUIMIENTO',
                    'CON_COMPROMISOS',
                    'CERRADO'
                );
            END IF;
        END $$;
    """))

    communication_category_enum = postgresql.ENUM(
        "CIRCULAR_OFICIAL",
        "CONVOCATORIA_REUNION",
        "AVISO_ACADEMICO",
        "AVISO_ADMINISTRATIVO",
        "RECORDATORIO",
        "EMERGENCIA_INSTITUCIONAL",
        name="communication_category_enum",
        create_type=False,
    )
    communication_priority_enum = postgresql.ENUM(
        "BAJA",
        "MEDIA",
        "ALTA",
        "URGENTE",
        name="communication_priority_enum",
        create_type=False,
    )
    target_scope_type_enum = postgresql.ENUM(
        "TODOS_INSTITUCION",
        "SOLO_ESTUDIANTES",
        "SOLO_ACUDIENTES",
        "SOLO_DOCENTES",
        "POR_SEDE",
        "POR_GRADO",
        "POR_GRUPO",
        name="target_scope_type_enum",
        create_type=False,
    )
    publishing_status_enum = postgresql.ENUM(
        "BORRADOR",
        "PUBLICADO",
        "ARCHIVADO",
        name="publishing_status_enum",
        create_type=False,
    )
    news_category_enum = postgresql.ENUM(
        "LOGRO_ACADEMICO",
        "EVENTO_CULTURAL",
        "EVENTO_DEPORTIVO",
        "PROYECTO_INSTITUCIONAL",
        "NOTICIA_GENERAL",
        name="news_category_enum",
        create_type=False,
    )
    coexistence_situation_type_enum = postgresql.ENUM(
        "TIPO_I",
        "TIPO_II",
        "TIPO_III",
        "OBSERVACION_POSITIVA",
        name="coexistence_situation_type_enum",
        create_type=False,
    )
    incident_status_enum = postgresql.ENUM(
        "ABIERTO",
        "EN_SEGUIMIENTO",
        "CON_COMPROMISOS",
        "CERRADO",
        name="incident_status_enum",
        create_type=False,
    )

    # 2. Table: institutional_communications
    op.create_table(
        "institutional_communications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", communication_category_enum, server_default="CIRCULAR_OFICIAL", nullable=False),
        sa.Column("priority", communication_priority_enum, server_default="MEDIA", nullable=False),
        sa.Column("target_scope", target_scope_type_enum, server_default="TODOS_INSTITUCION", nullable=False),
        sa.Column("attachment_url", sa.String(length=500), nullable=True),
        sa.Column("requires_acknowledgment", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", publishing_status_enum, server_default="PUBLICADO", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_institutional_communications_institution_id", "institutional_communications", ["institution_id"])
    op.create_index("ix_institutional_communications_author_user_id", "institutional_communications", ["author_user_id"])
    op.create_index("ix_institutional_communications_expires_at", "institutional_communications", ["expires_at"])

    # 3. Table: communication_audiences
    op.create_table(
        "communication_audiences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("communication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role_name", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["communication_id"], ["institutional_communications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_communication_audiences_communication_id", "communication_audiences", ["communication_id"])
    op.create_index("ix_communication_audiences_campus_id", "communication_audiences", ["campus_id"])
    op.create_index("ix_communication_audiences_grade_id", "communication_audiences", ["grade_id"])
    op.create_index("ix_communication_audiences_group_id", "communication_audiences", ["group_id"])
    op.create_index("ix_communication_audiences_role_name", "communication_audiences", ["role_name"])

    # 4. Table: communication_receipts
    op.create_table(
        "communication_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("communication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_ip", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["communication_id"], ["institutional_communications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("communication_id", "user_id", name="uq_communication_receipts_user"),
    )
    op.create_index("ix_communication_receipts_communication_id", "communication_receipts", ["communication_id"])
    op.create_index("ix_communication_receipts_user_id", "communication_receipts", ["user_id"])

    # 5. Table: institutional_news
    op.create_table(
        "institutional_news",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", news_category_enum, server_default="NOTICIA_GENERAL", nullable=False),
        sa.Column("cover_image_url", sa.String(length=500), nullable=True),
        sa.Column("status", publishing_status_enum, server_default="PUBLICADO", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_institutional_news_institution_id", "institutional_news", ["institution_id"])
    op.create_index("ix_institutional_news_author_user_id", "institutional_news", ["author_user_id"])

    # 6. Table: student_incidents
    op.create_table(
        "student_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reporter_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("situation_type", coexistence_situation_type_enum, server_default="TIPO_I", nullable=False),
        sa.Column("incident_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("student_version", sa.Text(), nullable=True),
        sa.Column("pedagogical_measures", sa.Text(), nullable=False),
        sa.Column("commitments", sa.Text(), nullable=True),
        sa.Column("status", incident_status_enum, server_default="ABIERTO", nullable=False),
        sa.Column("is_visible_to_guardian", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_visible_to_student", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_student_incidents_institution_id", "student_incidents", ["institution_id"])
    op.create_index("ix_student_incidents_student_id", "student_incidents", ["student_id"])
    op.create_index("ix_student_incidents_reporter_user_id", "student_incidents", ["reporter_user_id"])

    # 7. Table: incident_follow_ups
    op.create_table(
        "incident_follow_ups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("follow_up_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["student_incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_incident_follow_ups_incident_id", "incident_follow_ups", ["incident_id"])
    op.create_index("ix_incident_follow_ups_author_user_id", "incident_follow_ups", ["author_user_id"])


def downgrade() -> None:
    op.drop_table("incident_follow_ups")
    op.drop_table("student_incidents")
    op.drop_table("institutional_news")
    op.drop_table("communication_receipts")
    op.drop_table("communication_audiences")
    op.drop_table("institutional_communications")

    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_status_enum') THEN
                DROP TYPE incident_status_enum;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'coexistence_situation_type_enum') THEN
                DROP TYPE coexistence_situation_type_enum;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'news_category_enum') THEN
                DROP TYPE news_category_enum;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'publishing_status_enum') THEN
                DROP TYPE publishing_status_enum;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'target_scope_type_enum') THEN
                DROP TYPE target_scope_type_enum;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'communication_priority_enum') THEN
                DROP TYPE communication_priority_enum;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'communication_category_enum') THEN
                DROP TYPE communication_category_enum;
            END IF;
        END $$;
    """))
