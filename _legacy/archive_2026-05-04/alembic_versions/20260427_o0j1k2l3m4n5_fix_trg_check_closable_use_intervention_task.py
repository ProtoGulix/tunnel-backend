"""fix_trg_check_closable_use_intervention_task

Le trigger check_intervention_closable référençait public.gamme_step_validation
qui n'existe plus. La validation des tâches bloquantes se fait désormais via
intervention_task (colonnes : intervention_id, status, optional), en cohérence
avec _check_closable() côté Python.

Revision ID: o0j1k2l3m4n5
Revises: n9i0j1k2l3m4
Create Date: 2026-04-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op


revision: str = "o0j1k2l3m4n5"
down_revision: Union[str, None] = "n9i0j1k2l3m4"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION public.check_intervention_closable()
        RETURNS TRIGGER AS $$
        DECLARE
            blocking_count INTEGER;
        BEGIN
            IF NEW.status_actual != 'ferme' OR OLD.status_actual = 'ferme' THEN
                RETURN NEW;
            END IF;

            IF NEW.plan_id IS NULL THEN
                RETURN NEW;
            END IF;

            SELECT COUNT(*) INTO blocking_count
            FROM public.intervention_task
            WHERE intervention_id = NEW.id
              AND status IN ('todo', 'in_progress')
              AND optional = FALSE;

            IF blocking_count > 0 THEN
                RAISE EXCEPTION 'GAMME_INCOMPLETE: % tache(s) obligatoire(s) en attente', blocking_count;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)


def downgrade() -> None:
    # Restaure la version précédente (référençait gamme_step_validation, table supprimée)
    op.execute("""
        CREATE OR REPLACE FUNCTION public.check_intervention_closable()
        RETURNS TRIGGER AS $$
        DECLARE
            blocking_count INTEGER;
        BEGIN
            IF NEW.status_actual != 'ferme' OR OLD.status_actual = 'ferme' THEN
                RETURN NEW;
            END IF;

            IF NEW.plan_id IS NULL THEN
                RETURN NEW;
            END IF;

            SELECT COUNT(*) INTO blocking_count
            FROM public.gamme_step_validation gsv
            JOIN public.preventive_plan_gamme_step pgs ON pgs.id = gsv.step_id
            WHERE gsv.intervention_id = NEW.id
              AND gsv.status = 'pending'
              AND pgs.optional = FALSE;

            IF blocking_count > 0 THEN
                RAISE EXCEPTION 'GAMME_INCOMPLETE: % etape(s) obligatoire(s) en attente de validation', blocking_count;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
