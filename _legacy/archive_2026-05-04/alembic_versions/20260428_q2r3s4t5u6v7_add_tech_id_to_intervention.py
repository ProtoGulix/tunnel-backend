"""add tech_id to intervention

Revision ID: q2r3s4t5u6v7
Revises: p1k2l3m4n5o6
Create Date: 2026-04-28

"""
from alembic import op

revision = 'q2r3s4t5u6v7'
down_revision = 'p1k2l3m4n5o6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE intervention
        ADD COLUMN IF NOT EXISTS tech_id UUID
            REFERENCES directus_users(id) ON DELETE SET NULL
    """)

    op.execute("""
        UPDATE intervention i
        SET tech_id = u.id
        FROM directus_users u
        WHERE u.initial = i.tech_initials
          AND i.tech_id IS NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE intervention DROP COLUMN IF EXISTS tech_id")
