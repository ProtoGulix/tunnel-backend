"""Migrer les purchase_request : stock_item_id → part_id (UUID reuse)

La migration 009 a créé les parts avec les mêmes UUIDs que les stock_items.
Cette migration met à jour toutes les DAs existantes pour utiliser part_id
à la place de stock_item_id, en exploitant la réutilisation d'UUID.

Revision ID: 011_pr_stock_to_part
Revises: 010_pr_view_part_id
Create Date: 2026-06-16
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "011_pr_stock_to_part"
down_revision: Union[str, None] = "010_pr_view_part_id"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # Étape 1 : DAs avec stock_item_id seulement, dont le stock_item
    #           a été migré en part avec le même UUID (UUID reuse strategy)
    op.execute("""
        UPDATE purchase_request pr
        SET
            part_id = pr.stock_item_id,
            stock_item_id = NULL
        WHERE pr.stock_item_id IS NOT NULL
          AND pr.part_id IS NULL
          AND EXISTS (SELECT 1 FROM part p WHERE p.id = pr.stock_item_id)
    """)

    # Étape 2 : DAs qui ont les deux colonnes avec le même UUID (doublon)
    #           → vider stock_item_id, garder part_id
    op.execute("""
        UPDATE purchase_request
        SET stock_item_id = NULL
        WHERE stock_item_id IS NOT NULL
          AND part_id IS NOT NULL
          AND stock_item_id = part_id
    """)

    # Validation : aucune DA ne doit encore avoir stock_item_id = part_id
    op.execute("""
        DO $$
        DECLARE
            n_redundant INTEGER;
            n_stock_only INTEGER;
        BEGIN
            SELECT COUNT(*) INTO n_redundant
            FROM purchase_request
            WHERE stock_item_id IS NOT NULL
              AND part_id IS NOT NULL
              AND stock_item_id = part_id;

            IF n_redundant > 0 THEN
                RAISE EXCEPTION 'Migration 011 : % DA(s) ont encore stock_item_id = part_id', n_redundant;
            END IF;

            SELECT COUNT(*) INTO n_stock_only
            FROM purchase_request pr
            WHERE pr.stock_item_id IS NOT NULL
              AND pr.part_id IS NULL
              AND EXISTS (SELECT 1 FROM part p WHERE p.id = pr.stock_item_id);

            IF n_stock_only > 0 THEN
                RAISE EXCEPTION 'Migration 011 : % DA(s) ont encore un stock_item_id migreable non converti', n_stock_only;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Restaurer stock_item_id depuis part_id pour les DAs dont le part
    # correspond à un stock_item (UUID identique)
    op.execute("""
        UPDATE purchase_request pr
        SET
            stock_item_id = pr.part_id,
            part_id = NULL
        WHERE pr.part_id IS NOT NULL
          AND pr.stock_item_id IS NULL
          AND EXISTS (SELECT 1 FROM stock_item si WHERE si.id = pr.part_id)
    """)
