"""fix_trg_sync_status_log_use_id_not_code

Le trigger fn_sync_status_log_to_intervention comparait intervention_status_ref.code
à 'ferme', mais cette colonne est vide en base. Le vrai identifiant est la colonne id
(qui vaut directement 'ferme', 'ouvert', etc.). On corrige en lisant l'id du statut_to
via intervention_status_log.status_to directement, sans passer par la colonne code.

Revision ID: n9i0j1k2l3m4
Revises: m8h9i0j1k2l3
Create Date: 2026-04-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op


revision: str = "n9i0j1k2l3m4"
down_revision: Union[str, None] = "m8h9i0j1k2l3"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # intervention_status_ref.id contient directement le code ('ferme', 'ouvert'…)
    # et intervention_status_log.status_to stocke cet id texte.
    # On n'a plus besoin du SELECT code — on compare status_to directement à 'ferme'.
    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_sync_status_log_to_intervention()
        RETURNS TRIGGER AS $$
        DECLARE
            v_occurrence_id UUID;
            v_request_id UUID;
            v_request_statut TEXT;
        BEGIN
            -- 1. Mettre à jour intervention.status_actual avec le nouveau statut
            UPDATE public.intervention
            SET status_actual = NEW.status_to
            WHERE id = NEW.intervention_id;

            -- 2. Si fermeture : propager sur l'occurrence préventive + la demande
            --    NEW.status_to est le code texte direct (ex: 'ferme')
            IF NEW.status_to = 'ferme' THEN

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


def downgrade() -> None:
    # Restaure la version précédente avec la résolution via colonne code (comportement buggé)
    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_sync_status_log_to_intervention()
        RETURNS TRIGGER AS $$
        DECLARE
            v_status_code TEXT;
            v_occurrence_id UUID;
            v_request_id UUID;
            v_request_statut TEXT;
        BEGIN
            UPDATE public.intervention
            SET status_actual = NEW.status_to
            WHERE id = NEW.intervention_id;

            SELECT code INTO v_status_code
            FROM public.intervention_status_ref
            WHERE id = NEW.status_to;

            IF v_status_code = 'ferme' THEN

                SELECT id INTO v_occurrence_id
                FROM public.preventive_occurrence
                WHERE intervention_id = NEW.intervention_id
                LIMIT 1;

                IF v_occurrence_id IS NOT NULL THEN
                    UPDATE public.preventive_occurrence
                    SET status = 'completed'
                    WHERE id = v_occurrence_id;
                END IF;

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
