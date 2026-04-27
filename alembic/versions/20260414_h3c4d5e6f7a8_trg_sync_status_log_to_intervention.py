"""trg_sync_status_log_to_intervention

Trigger PostgreSQL qui synchronise automatiquement :
1. intervention.status_actual  ← status_to du nouveau log
2. preventive_occurrence.status ← 'completed' quand l'intervention est fermée

Revision ID: h3c4d5e6f7a8
Revises: g2b3c4d5e6f7
Create Date: 2026-04-14 00:00:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op


revision: str = "h3c4d5e6f7a8"
down_revision: Union[str, None] = "g2b3c4d5e6f7"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # ──────────────────────────────────────────────────────────────────────────
    # Fonction principale du trigger
    #
    # Déclenchée AFTER INSERT ON intervention_status_log.
    # Fait deux choses dans la même transaction que l'INSERT du log :
    #
    # 1. Met à jour intervention.status_actual avec le nouveau statut (status_to).
    #    Le champ status_to contient l'UUID du statut cible dans intervention_status_ref.
    #    On résout le code via un JOIN pour savoir si c'est une fermeture.
    #
    # 2. Si le code résolu est 'ferme' ET que l'intervention est liée à une
    #    occurrence préventive (via preventive_occurrence.intervention_id) :
    #    → passe preventive_occurrence.status à 'completed'
    #    → passe intervention_request.statut à 'cloturee' si elle est encore 'acceptee'
    #      (miroir de ce que fait on_intervention_closed() côté Python,
    #       mais ici déclenché uniquement via le log, pas via PATCH direct)
    #
    # Note : le PATCH /interventions/{id} continue à appeler _notify_if_closed()
    # en Python — les deux chemins coexistent sans doublon car :
    #   - PATCH met à jour status_actual directement → trg_check_intervention_closable
    #     valide la gamme, mais ce trigger NE se déclenche PAS (il écoute intervention_status_log)
    #   - POST /intervention-status-log → CE trigger se déclenche, met à jour status_actual,
    #     ce qui déclenche à son tour trg_check_intervention_closable via l'UPDATE
    # ──────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_sync_status_log_to_intervention()
        RETURNS TRIGGER AS $$
        DECLARE
            v_status_code TEXT;
            v_occurrence_id UUID;
            v_request_id UUID;
            v_request_statut TEXT;
        BEGIN
            -- 1. Mettre à jour intervention.status_actual avec le nouveau statut
            UPDATE public.intervention
            SET status_actual = NEW.status_to
            WHERE id = NEW.intervention_id;

            -- 2. Résoudre le code du statut cible
            SELECT code INTO v_status_code
            FROM public.intervention_status_ref
            WHERE id = NEW.status_to;

            -- 3. Si fermeture : propager sur l'occurrence préventive + la demande
            IF v_status_code = 'ferme' THEN

                -- Chercher l'occurrence liée à cette intervention
                SELECT id INTO v_occurrence_id
                FROM public.preventive_occurrence
                WHERE intervention_id = NEW.intervention_id
                LIMIT 1;

                IF v_occurrence_id IS NOT NULL THEN
                    UPDATE public.preventive_occurrence
                    SET status = 'completed'
                    WHERE id = v_occurrence_id;
                END IF;

                -- Clôturer la demande liée si elle est encore 'acceptee'
                SELECT id, statut INTO v_request_id, v_request_statut
                FROM public.intervention_request
                WHERE intervention_id = NEW.intervention_id
                  AND statut = 'acceptee'
                LIMIT 1;

                IF v_request_id IS NOT NULL THEN
                    UPDATE public.intervention_request
                    SET statut = 'cloturee'
                    WHERE id = v_request_id;

                    INSERT INTO public.request_status_log
                        (request_id, status_from, status_to, changed_by, notes)
                    VALUES (
                        v_request_id,
                        v_request_statut,
                        'cloturee',
                        NULL,
                        'Clôture automatique suite à la fermeture de l''intervention (via log de statut)'
                    );
                END IF;

            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trg_sync_status_log_to_intervention
            ON public.intervention_status_log
    """)
    op.execute("""
        CREATE TRIGGER trg_sync_status_log_to_intervention
            AFTER INSERT ON public.intervention_status_log
            FOR EACH ROW
            EXECUTE FUNCTION public.fn_sync_status_log_to_intervention()
    """)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS trg_sync_status_log_to_intervention
            ON public.intervention_status_log
    """)
    op.execute("DROP FUNCTION IF EXISTS public.fn_sync_status_log_to_intervention()")
