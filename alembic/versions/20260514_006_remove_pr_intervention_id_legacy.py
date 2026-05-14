"""Supprimer purchase_request.intervention_id — migration vers M2M exclusif

Toutes les DA liées via intervention_id direct sont rattachées à la première
action de leur intervention dans intervention_action_purchase_request, puis
la colonne legacy est supprimée.

Revision ID: 006_remove_pr_legacy_fk
Revises: 005_pr_derived_status_view
Create Date: 2026-05-14
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "006_remove_pr_legacy_fk"
down_revision: Union[str, None] = "005_pr_derived_status_view"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # 1. Rattacher les DA legacy (intervention_id direct) sans lien M2M existant
    #    à la première action de leur intervention.
    op.execute("""
        INSERT INTO intervention_action_purchase_request (intervention_action_id, purchase_request_id)
        SELECT DISTINCT ON (pr.id)
            first_action.id AS intervention_action_id,
            pr.id           AS purchase_request_id
        FROM purchase_request pr
        INNER JOIN LATERAL (
            SELECT id FROM intervention_action
            WHERE intervention_id = pr.intervention_id
            ORDER BY created_at
            LIMIT 1
        ) first_action ON TRUE
        WHERE pr.intervention_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM intervention_action_purchase_request iapr
              INNER JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
              WHERE iapr.purchase_request_id = pr.id
                AND ia.intervention_id = pr.intervention_id
          )
        ON CONFLICT DO NOTHING;
    """)

    # 2. Supprimer la vue qui dépend de intervention_id (sera recrée sans la colonne)
    op.execute("DROP VIEW IF EXISTS purchase_request_derived_status;")

    # 3. Supprimer la contrainte FK si elle existe, puis la colonne
    op.execute("""
        DO $$
        DECLARE
            fk_name text;
        BEGIN
            SELECT tc.constraint_name INTO fk_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'purchase_request'
              AND tc.constraint_type = 'FOREIGN KEY'
              AND kcu.column_name = 'intervention_id';

            IF fk_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE purchase_request DROP CONSTRAINT ' || quote_ident(fk_name);
            END IF;
        END $$;
    """)
    op.execute("ALTER TABLE purchase_request DROP COLUMN IF EXISTS intervention_id;")

    # 4. Recréer la vue sans intervention_id
    op.execute("""
        CREATE OR REPLACE VIEW purchase_request_derived_status AS
        SELECT
            pr.id,
            pr.stock_item_id,
            pr.item_label,
            pr.quantity,
            pr.unit,
            pr.urgency,
            pr.requested_by,
            pr.created_at,
            pr.updated_at,

            sol_agg.supplier_refs_count,
            sol_agg.quotes_count,
            sol_agg.selected_count,
            sol_agg.total_allocated,
            sol_agg.total_received,
            sol_agg.has_locked_order,
            sol_agg.all_terminal,
            sol_agg.has_order_lines,

            CASE
                WHEN pr.stock_item_id IS NULL
                    THEN 'TO_QUALIFY'
                WHEN COALESCE(sol_agg.supplier_refs_count, 0) = 0
                    THEN 'NO_SUPPLIER_REF'
                WHEN NOT COALESCE(sol_agg.has_order_lines, FALSE)
                    THEN 'PENDING_DISPATCH'
                WHEN COALESCE(sol_agg.all_terminal, FALSE) AND COALESCE(sol_agg.selected_count, 0) = 0
                    THEN 'REJECTED'
                WHEN COALESCE(sol_agg.all_terminal, FALSE) AND COALESCE(sol_agg.selected_count, 0) > 0
                    THEN 'RECEIVED'
                WHEN COALESCE(sol_agg.total_received, 0) >= COALESCE(sol_agg.total_allocated, 1)
                     AND COALESCE(sol_agg.total_allocated, 0) > 0
                    THEN 'RECEIVED'
                WHEN COALESCE(sol_agg.has_locked_order, FALSE)
                     AND COALESCE(sol_agg.selected_count, 0) = 0
                     AND COALESCE(sol_agg.quotes_count, 0) = 0
                    THEN 'CONSULTATION'
                WHEN COALESCE(sol_agg.total_received, 0) > 0
                    THEN 'PARTIAL'
                WHEN COALESCE(sol_agg.selected_count, 0) > 0
                    THEN 'ORDERED'
                WHEN COALESCE(sol_agg.quotes_count, 0) > 0
                    THEN 'QUOTED'
                ELSE 'OPEN'
            END AS derived_status

        FROM purchase_request pr
        LEFT JOIN LATERAL (
            SELECT
                (SELECT COUNT(*) FROM stock_item_supplier WHERE stock_item_id = pr.stock_item_id) AS supplier_refs_count,
                COUNT(DISTINCT CASE WHEN sol.quote_received  THEN sol.id END)  AS quotes_count,
                COUNT(DISTINCT CASE WHEN sol.is_selected     THEN sol.id END)  AS selected_count,
                COALESCE(SUM(solpr.quantity), 0)                               AS total_allocated,
                COALESCE(SUM(sol.quantity_received), 0)                        AS total_received,
                BOOL_OR(so.status IN ('SENT', 'ACK'))                          AS has_locked_order,
                BOOL_AND(so.status IN ('CANCELLED', 'CLOSED'))                 AS all_terminal,
                COUNT(sol.id) > 0                                              AS has_order_lines
            FROM supplier_order_line_purchase_request solpr
            JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
            JOIN supplier_order so       ON sol.supplier_order_id = so.id
            WHERE solpr.purchase_request_id = pr.id
        ) sol_agg ON TRUE;

        COMMENT ON VIEW purchase_request_derived_status IS
            'Source de vérité unique du statut dérivé des demandes d''achat. '
            'Ne pas dupliquer la logique CASE WHEN en Python ou dans d''autres requêtes SQL.';
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE purchase_request
        ADD COLUMN IF NOT EXISTS intervention_id uuid;
    """)
    # Note : les données legacy ne sont pas restaurées — downgrade structurel uniquement.
