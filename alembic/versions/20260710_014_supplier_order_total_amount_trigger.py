"""Recalculer total_amount du panier fournisseur à chaque changement de ligne

total_price est déjà recalculé par trigger sur supplier_order_line
(trg_calculate_line_total), mais rien ne répercutait la somme sur
supplier_order.total_amount : le montant total du panier restait figé
(souvent à 0) après une modification de ligne (PATCH quantité/prix côté
négociation, ajout ou suppression de ligne).

Revision ID: 014_supplier_order_total_trigger
Revises: 013_supplier_order_seq
Create Date: 2026-07-10
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "014_supplier_order_total_trigger"
down_revision: Union[str, None] = "013_supplier_order_seq"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION public.recalculate_supplier_order_total()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        DECLARE
          affected_order_id uuid;
        BEGIN
          affected_order_id := COALESCE(NEW.supplier_order_id, OLD.supplier_order_id);

          UPDATE supplier_order
          SET total_amount = COALESCE(
            (SELECT SUM(total_price) FROM supplier_order_line WHERE supplier_order_id = affected_order_id),
            0
          )
          WHERE id = affected_order_id;

          RETURN NULL;
        END;
        $function$;
    """)

    op.execute("""
        CREATE TRIGGER trg_recalculate_supplier_order_total
        AFTER INSERT OR UPDATE OF unit_price, quantity, total_price OR DELETE
        ON public.supplier_order_line
        FOR EACH ROW EXECUTE FUNCTION recalculate_supplier_order_total();
    """)

    # Backfill : corrige les paniers existants dont total_amount est désynchronisé des lignes
    op.execute("""
        UPDATE supplier_order so
        SET total_amount = COALESCE(
            (SELECT SUM(sol.total_price) FROM supplier_order_line sol WHERE sol.supplier_order_id = so.id),
            0
        );
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_recalculate_supplier_order_total ON public.supplier_order_line")
    op.execute("DROP FUNCTION IF EXISTS public.recalculate_supplier_order_total()")
