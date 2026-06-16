"""Créer la séquence supplier_order_seq manquante

Le trigger generate_supplier_order_number() référence supplier_order_seq
pour générer les numéros CMD-YYYYMMDD-XXXX, mais la séquence n'existait pas.

Revision ID: 013_supplier_order_seq
Revises: 012_sol_nullable
Create Date: 2026-06-16
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "013_supplier_order_seq"
down_revision: Union[str, None] = "012_sol_nullable"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        DECLARE
            n INTEGER;
        BEGIN
            SELECT COUNT(*) INTO n FROM supplier_order;
            EXECUTE format('CREATE SEQUENCE IF NOT EXISTS supplier_order_seq START %s', n + 1);
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS supplier_order_seq")
