"""Créer la vue purchase_request_derived_status — source de vérité du statut dérivé des DA

Revision ID: 005_view_purchase_request_derived_status
Revises: 004_audit_task_reasons
Create Date: 2026-05-14
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "005_pr_derived_status_view"
down_revision: Union[str, None] = "004_audit_task_reasons"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
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
            pr.intervention_id,
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
            'Ne pas dupliquer la logique CASE WHEN en Python ou dans d''autres requêtes SQL — '
            'toujours joindre cette vue.';
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS purchase_request_derived_status;")
