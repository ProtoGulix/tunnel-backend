"""merge_branch_i4d5_et_q2r3

Merge des deux têtes divergentes :
- i4d5e6f7a8b9  (drop_redundant_trg_sync_status_from_log — 2026-04-15)
- q2r3s4t5u6v7  (add_tech_id_to_intervention — 2026-04-28)

Revision ID: r3s4t5u6v7w8
Revises: i4d5e6f7a8b9, q2r3s4t5u6v7
Create Date: 2026-04-30

"""
from alembic import op

revision = 'r3s4t5u6v7w8'
down_revision = ('i4d5e6f7a8b9', 'q2r3s4t5u6v7')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
