"""Mettre à jour la vue purchase_request_derived_status pour supporter part_id (V4)

Deux corrections :
1. La règle TO_QUALIFY doit tenir compte de part_id : une DA qualifiée via part_id
   (sans stock_item_id legacy) ne doit plus être vue comme TO_QUALIFY.
2. supplier_refs_count : priorité aux refs part_supplier_ref quand part_id est renseigné,
   sinon fallback sur stock_item_supplier (legacy).

Revision ID: 010_fix_pr_derived_status_view_part_id
Revises: 009_parts_schema
Create Date: 2026-06-16
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "010_pr_view_part_id"
down_revision: Union[str, None] = "009_parts_schema"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


_VIEW_SQL = """
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
            -- Règle 1 : ni stock_item_id (legacy) ni part_id (V4) → à qualifier
            WHEN pr.stock_item_id IS NULL AND pr.part_id IS NULL
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
            -- supplier_refs_count : part V4 en priorité, stock_item legacy en fallback
            CASE
                WHEN pr.part_id IS NOT NULL THEN (
                    SELECT COUNT(*)
                    FROM part_supplier_ref psr
                    JOIN part_manufacturer_ref pmr ON pmr.id = psr.part_manufacturer_ref_id
                    WHERE pmr.part_id = pr.part_id
                )
                ELSE (
                    SELECT COUNT(*) FROM stock_item_supplier WHERE stock_item_id = pr.stock_item_id
                )
            END AS supplier_refs_count,
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
        'Supporte stock_item_id (legacy) et part_id (V4). '
        'Ne pas dupliquer la logique CASE WHEN en Python ou dans d''autres requêtes SQL.';
"""

_VIEW_DOWNGRADE_SQL = """
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
"""


def upgrade() -> None:
    op.execute(_VIEW_SQL)


def downgrade() -> None:
    op.execute(_VIEW_DOWNGRADE_SQL)
