"""Fix supplier_order_line : stock_item_id nullable + index partiels pour part_id V4

La contrainte NOT NULL sur stock_item_id bloquait le dispatch des DAs qualifiées
via part_id (V4) qui n'ont pas de stock_item_id. La contrainte unique était aussi
sur (supplier_order_id, stock_item_id) uniquement, sans couvrir part_id.

Corrections :
1. stock_item_id devient nullable (les lignes V4 ont part_id à la place)
2. Suppression de l'unique constraint globale
3. Deux index uniques partiels : un pour stock_item_id, un pour part_id

Revision ID: 012_sol_nullable
Revises: 011_pr_stock_to_part
Create Date: 2026-06-16
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "012_sol_nullable"
down_revision: Union[str, None] = "011_pr_stock_to_part"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE supplier_order_line ALTER COLUMN stock_item_id DROP NOT NULL")
    op.execute("ALTER TABLE supplier_order_line DROP CONSTRAINT IF EXISTS uq_supplier_order_line")
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_sol_stock_item
            ON supplier_order_line (supplier_order_id, stock_item_id)
            WHERE stock_item_id IS NOT NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_sol_part
            ON supplier_order_line (supplier_order_id, part_id)
            WHERE part_id IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_sol_stock_item")
    op.execute("DROP INDEX IF EXISTS uq_sol_part")
    op.execute("""
        ALTER TABLE supplier_order_line
        ADD CONSTRAINT uq_supplier_order_line UNIQUE (supplier_order_id, stock_item_id)
    """)
    op.execute("ALTER TABLE supplier_order_line ALTER COLUMN stock_item_id SET NOT NULL")
