"""Ajoute une référence lisible DA-YYYY-NNNN sur purchase_request

Les demandes d'achat n'étaient identifiées que par leur UUID brut, illisible
dans les échanges (mail fournisseur, oral en atelier). intervention_request
a déjà ce pattern (code DI-YYYY-NNNN, cf. fn_generate_request_code) ainsi que
supplier_order (order_number CMD-YYYYMMDD-NNNN) : purchase_request était
l'exception sans référence humaine.

On reprend directement la version corrigée de fn_generate_request_code
(MAX(numéro extrait)+1, cf. migration 018) plutôt que l'ancien COUNT(*)+1 —
pas de raison de réintroduire le bug déjà résolu ailleurs.

Backfill : les lignes existantes sont numérotées par année de created_at,
dans l'ordre chronologique de création.

Revision ID: 019_purchase_request_code
Revises: 018_fix_request_code_sequence
Create Date: 2026-07-26
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "019_purchase_request_code"
down_revision: Union[str, None] = "018_fix_request_code_sequence"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE purchase_request ADD COLUMN code TEXT")

    op.execute("""
        WITH numbered AS (
            SELECT
                id,
                'DA-' || to_char(created_at, 'YYYY') || '-' ||
                    lpad(
                        ROW_NUMBER() OVER (
                            PARTITION BY to_char(created_at, 'YYYY')
                            ORDER BY created_at ASC
                        )::TEXT,
                        4, '0'
                    ) AS new_code
            FROM purchase_request
        )
        UPDATE purchase_request pr
        SET code = numbered.new_code
        FROM numbered
        WHERE pr.id = numbered.id
    """)

    op.execute("ALTER TABLE purchase_request ALTER COLUMN code SET NOT NULL")
    op.execute("""
        ALTER TABLE purchase_request
        ADD CONSTRAINT purchase_request_code_key UNIQUE (code)
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_generate_purchase_request_code()
         RETURNS trigger
         LANGUAGE plpgsql
        AS $function$
        DECLARE
            v_year TEXT := to_char(now(), 'YYYY');
            v_seq  INT;
        BEGIN
            IF NEW.code IS NOT NULL AND NEW.code != '' THEN
                RETURN NEW;
            END IF;

            SELECT COALESCE(MAX((regexp_match(code, 'DA-' || v_year || '-(\\d+)'))[1]::int), 0) + 1
            INTO v_seq
            FROM public.purchase_request
            WHERE code LIKE 'DA-' || v_year || '-%';

            NEW.code := 'DA-' || v_year || '-' || lpad(v_seq::TEXT, 4, '0');
            RETURN NEW;
        END;
        $function$
    """)

    op.execute("""
        CREATE TRIGGER trg_purchase_request_code
        BEFORE INSERT ON public.purchase_request
        FOR EACH ROW EXECUTE FUNCTION fn_generate_purchase_request_code()
    """)

    # La vue purchase_request_derived_status (source de vérité du statut dérivé,
    # cf. migration 016) doit exposer pr.code pour que les requêtes de liste
    # puissent l'afficher sans jointure supplémentaire sur purchase_request.
    op.execute("""
        DROP VIEW IF EXISTS purchase_request_derived_status;

        CREATE VIEW purchase_request_derived_status AS
        SELECT
            pr.id,
            pr.code,
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
            sol_agg.has_closed_selected,
            sol_agg.has_order_lines,

            CASE
                WHEN pr.stock_item_id IS NULL AND pr.part_id IS NULL
                    THEN 'TO_QUALIFY'
                WHEN COALESCE(sol_agg.supplier_refs_count, 0) = 0
                    THEN 'NO_SUPPLIER_REF'
                WHEN NOT COALESCE(sol_agg.has_order_lines, FALSE)
                    THEN 'PENDING_DISPATCH'
                WHEN COALESCE(sol_agg.all_terminal, FALSE) AND COALESCE(sol_agg.selected_count, 0) = 0
                    THEN 'REJECTED'
                WHEN COALESCE(sol_agg.has_closed_selected, FALSE)
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
                BOOL_OR(so.status = 'CLOSED' AND sol.is_selected)              AS has_closed_selected,
                COUNT(sol.id) > 0                                              AS has_order_lines
            FROM supplier_order_line_purchase_request solpr
            JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
            JOIN supplier_order so       ON sol.supplier_order_id = so.id
            WHERE solpr.purchase_request_id = pr.id
        ) sol_agg ON TRUE;

        COMMENT ON VIEW purchase_request_derived_status IS
            'Source de vérité unique du statut dérivé des demandes d''achat. '
            'Expose pr.code (référence DA-YYYY-NNNN) depuis la migration 019. '
            'Ne pas dupliquer la logique CASE WHEN en Python ou dans d''autres requêtes SQL.';
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_purchase_request_code ON public.purchase_request")
    op.execute("DROP FUNCTION IF EXISTS public.fn_generate_purchase_request_code()")
    op.execute("ALTER TABLE purchase_request DROP CONSTRAINT IF EXISTS purchase_request_code_key")
    op.execute("ALTER TABLE purchase_request DROP COLUMN IF EXISTS code")

    op.execute("""
        DROP VIEW IF EXISTS purchase_request_derived_status;

        CREATE VIEW purchase_request_derived_status AS
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
            sol_agg.has_closed_selected,
            sol_agg.has_order_lines,

            CASE
                WHEN pr.stock_item_id IS NULL AND pr.part_id IS NULL
                    THEN 'TO_QUALIFY'
                WHEN COALESCE(sol_agg.supplier_refs_count, 0) = 0
                    THEN 'NO_SUPPLIER_REF'
                WHEN NOT COALESCE(sol_agg.has_order_lines, FALSE)
                    THEN 'PENDING_DISPATCH'
                WHEN COALESCE(sol_agg.all_terminal, FALSE) AND COALESCE(sol_agg.selected_count, 0) = 0
                    THEN 'REJECTED'
                WHEN COALESCE(sol_agg.has_closed_selected, FALSE)
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
                BOOL_OR(so.status = 'CLOSED' AND sol.is_selected)              AS has_closed_selected,
                COUNT(sol.id) > 0                                              AS has_order_lines
            FROM supplier_order_line_purchase_request solpr
            JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
            JOIN supplier_order so       ON sol.supplier_order_id = so.id
            WHERE solpr.purchase_request_id = pr.id
        ) sol_agg ON TRUE;
    """)
