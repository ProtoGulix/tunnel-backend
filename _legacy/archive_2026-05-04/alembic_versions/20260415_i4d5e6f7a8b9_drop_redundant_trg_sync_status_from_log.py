"""drop_redundant_trg_sync_status_from_log

Supprime l'ancien trigger trg_sync_status_from_log et sa fonction associée
trg_sync_status_from_log(), désormais redondants avec le nouveau trigger
trg_sync_status_log_to_intervention créé dans la migration h3c4d5e6f7a8.

L'ancien trigger synchronisait uniquement intervention.status_actual.
Le nouveau fait la même chose ET propage la clôture sur preventive_occurrence
et intervention_request. Les garder tous les deux causerait un double UPDATE
sur status_actual à chaque INSERT dans intervention_status_log.

Revision ID: i4d5e6f7a8b9
Revises: h3c4d5e6f7a8
Create Date: 2026-04-15 00:00:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op


revision: str = "i4d5e6f7a8b9"
down_revision: Union[str, None] = "h3c4d5e6f7a8"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS trg_sync_status_from_log
            ON public.intervention_status_log
    """)
    op.execute("DROP FUNCTION IF EXISTS public.trg_sync_status_from_log()")


def downgrade() -> None:
    # Recréer l'ancien trigger si besoin de rollback
    op.execute("""
        CREATE OR REPLACE FUNCTION public.trg_sync_status_from_log()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE
            last_status  VARCHAR(255);
            current_status VARCHAR(255);
        BEGIN
            SELECT status_to INTO last_status
            FROM public.intervention_status_log
            WHERE intervention_id = NEW.intervention_id
            ORDER BY date DESC
            LIMIT 1;

            SELECT status_actual INTO current_status
            FROM public.intervention
            WHERE id = NEW.intervention_id;

            IF last_status IS DISTINCT FROM current_status THEN
                UPDATE public.intervention
                SET status_actual = last_status
                WHERE id = NEW.intervention_id;
            END IF;

            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_sync_status_from_log
            AFTER INSERT OR UPDATE ON public.intervention_status_log
            FOR EACH ROW
            EXECUTE FUNCTION public.trg_sync_status_from_log()
    """)
