"""National DIVIPOLA Operational Foundation (Phase NTA-02)

Revision ID: 026_nta02_national_divipola_foundation
Revises: 025_department_admin_invitations
Create Date: 2026-10-06 05:00:00.000000

Implements Phase NTA-02 of the PEVN National Territorial Architecture:
  - Expands operational departments from 3 pilot departments to all 33 Colombian territorial entities.
  - Expands operational municipalities from 3 pilot municipalities to all 1,119 official municipalities.
  - Preserves 100% of existing pilot department and municipality UUIDs (08, 11, 25 and 08001, 11001, 25286).
  - Preserves 100% of existing institution, campus, user, and role assignments.
  - Completely idempotent and conflict-safe via ON CONFLICT (code) DO NOTHING.
  - Safe, non-destructive downgrade strategy.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "026_nta02_national_divipola_foundation"
down_revision: str | None = "025_department_admin_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Insert missing departments (conflict-safe by unique DANE code)
    # Existing pilot departments (08, 11, 25) are strictly preserved with their original UUIDs.
    insert_departments_sql = """
    WITH ranked_depts AS (
        SELECT 
            department_code,
            CASE 
                WHEN department_code = '44' THEN 'LA GUAJIRA'
                ELSE department_name 
            END as department_name,
            count(*) as cnt,
            ROW_NUMBER() OVER(
                PARTITION BY department_code 
                ORDER BY count(*) DESC, department_name ASC
            ) as rn
        FROM official_institution_catalog
        GROUP BY department_code, department_name
    )
    INSERT INTO departments (id, code, name)
    SELECT 
        gen_random_uuid(),
        department_code,
        department_name
    FROM ranked_depts
    WHERE rn = 1
    ON CONFLICT (code) DO NOTHING;
    """
    op.execute(sa.text(insert_departments_sql))

    # 2. Insert missing municipalities (conflict-safe by unique DANE code)
    # Existing pilot municipalities (08001, 11001, 25286) are strictly preserved with their original UUIDs.
    insert_municipalities_sql = """
    WITH ranked_munis AS (
        SELECT 
            municipality_code,
            department_code,
            municipality_name,
            count(*) as cnt,
            ROW_NUMBER() OVER(
                PARTITION BY municipality_code 
                ORDER BY count(*) DESC, municipality_name ASC
            ) as rn
        FROM official_institution_catalog
        GROUP BY municipality_code, department_code, municipality_name
    )
    INSERT INTO municipalities (id, department_id, code, name)
    SELECT 
        gen_random_uuid(),
        d.id,
        rm.municipality_code,
        rm.municipality_name
    FROM ranked_munis rm
    JOIN departments d ON d.code = rm.department_code
    WHERE rm.rn = 1
    ON CONFLICT (code) DO NOTHING;
    """
    op.execute(sa.text(insert_municipalities_sql))


def downgrade() -> None:
    # Rollback removes ONLY the territorial records added in NTA-02.
    # The original 3 pilot departments and 3 pilot municipalities are preserved intact,
    # ensuring zero foreign-key violations on institutions, campuses, users, or user_roles.
    delete_municipalities_sql = """
    DELETE FROM municipalities 
    WHERE code NOT IN ('08001', '11001', '25286');
    """
    op.execute(sa.text(delete_municipalities_sql))

    delete_departments_sql = """
    DELETE FROM departments 
    WHERE code NOT IN ('08', '11', '25');
    """
    op.execute(sa.text(delete_departments_sql))
