"""add_preventive_v2_addendum_02

Corrige le flux de validations preventives :
- gamme_step_validation.intervention_id devient nullable
- ajout occurrence_id + nouvelle unique (step_id, occurrence_id)
- suppression trigger legacy trg_generate_gamme_validations
- correction check_intervention_closable (pending non-optionnels seulement)

Revision ID: e91c4a7b2f16
Revises: d2a7b3c0e15f
Create Date: 2026-04-13 00:00:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op


revision: str = "e91c4a7b2f16"
down_revision: Union[str, None] = "d2a7b3c0e15f"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # 1) intervention_id nullable
    op.execute("""
        ALTER TABLE public.gamme_step_validation
            ALTER COLUMN intervention_id DROP NOT NULL
    """)

    # 2) occurrence_id + commentaire
    op.execute("""
        ALTER TABLE public.gamme_step_validation
            ADD COLUMN IF NOT EXISTS occurrence_id UUID
                REFERENCES public.preventive_occurrence (id) ON DELETE RESTRICT
    """)
    op.execute("""
        COMMENT ON COLUMN public.gamme_step_validation.occurrence_id IS
            'Occurrence preventive a l''origine de cette validation. Renseignee a la generation de l''occurrence, avant meme la creation de l''intervention.'
    """)

    # 3) UNIQUE(step_id, occurrence_id)
    op.execute("""
        ALTER TABLE public.gamme_step_validation
            DROP CONSTRAINT IF EXISTS gamme_step_validation_step_interv_key
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'gamme_step_validation_step_occurrence_key'
                  AND conrelid = 'public.gamme_step_validation'::regclass
            ) THEN
                ALTER TABLE public.gamme_step_validation
                    ADD CONSTRAINT gamme_step_validation_step_occurrence_key
                    UNIQUE (step_id, occurrence_id);
            END IF;
        END
        $$
    """)

    # 4) Index occurrence_id
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_occurrence_id
            ON public.gamme_step_validation (occurrence_id)
    """)

    # 5) Suppression trigger legacy
    op.execute("""
        DROP TRIGGER IF EXISTS trg_generate_gamme_validations
            ON public.intervention_action
    """)
    op.execute("DROP FUNCTION IF EXISTS public.fn_generate_gamme_validations()")
    op.execute("DROP FUNCTION IF EXISTS public.generate_gamme_validations()")

    # 6) Correction trigger de cloture
    op.execute("""
        DROP TRIGGER IF EXISTS trg_check_intervention_closable
            ON public.intervention
    """)
    op.execute("DROP FUNCTION IF EXISTS public.fn_check_intervention_closable()")
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
    op.execute("""
        CREATE TRIGGER trg_check_intervention_closable
            BEFORE UPDATE ON public.intervention
            FOR EACH ROW
            EXECUTE FUNCTION public.check_intervention_closable()
    """)

    # 7) Commentaire final intervention_id
    op.execute("""
        COMMENT ON COLUMN public.gamme_step_validation.intervention_id IS
            'Intervention liee a cette validation. NULL a la generation de l''occurrence, renseignee lors de l''acceptation de la DI.'
    """)


def downgrade() -> None:
    # Revenir a la logique pre-addendum_02
    op.execute("""
        DROP TRIGGER IF EXISTS trg_check_intervention_closable
            ON public.intervention
    """)
    op.execute("DROP FUNCTION IF EXISTS public.check_intervention_closable()")

    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_check_intervention_closable()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_pending_count INT;
        BEGIN
            IF NEW.status_actual = 'ferme' AND OLD.status_actual IS DISTINCT FROM 'ferme' THEN
                IF NEW.plan_id IS NOT NULL THEN
                    SELECT COUNT(*) INTO v_pending_count
                    FROM public.gamme_step_validation
                    WHERE intervention_id = NEW.id
                      AND status = 'pending';

                    IF v_pending_count > 0 THEN
                        RAISE EXCEPTION 'GAMME_INCOMPLETE: % etape(s) en attente de validation', v_pending_count;
                    END IF;
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_check_intervention_closable
            BEFORE UPDATE ON public.intervention
            FOR EACH ROW
            EXECUTE FUNCTION public.fn_check_intervention_closable()
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_generate_gamme_validations()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_subcategory_code TEXT;
            v_plan_id          UUID;
            v_step             RECORD;
        BEGIN
            SELECT sc.code INTO v_subcategory_code
            FROM public.action_subcategory sc
            WHERE sc.id = NEW.action_subcategory;

            IF v_subcategory_code IS NULL OR v_subcategory_code NOT LIKE 'PREV_%' THEN
                RETURN NEW;
            END IF;

            SELECT i.plan_id INTO v_plan_id
            FROM public.intervention i
            WHERE i.id = NEW.intervention_id;

            IF v_plan_id IS NULL THEN
                RETURN NEW;
            END IF;

            FOR v_step IN
                SELECT id
                FROM public.preventive_plan_gamme_step
                WHERE plan_id = v_plan_id
                ORDER BY sort_order
            LOOP
                INSERT INTO public.gamme_step_validation (
                    step_id,
                    intervention_id,
                    action_id,
                    status
                )
                VALUES (
                    v_step.id,
                    NEW.intervention_id,
                    NEW.id,
                    'pending'
                )
                ON CONFLICT (step_id, intervention_id) DO NOTHING;
            END LOOP;

            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_generate_gamme_validations
            AFTER INSERT ON public.intervention_action
            FOR EACH ROW
            EXECUTE FUNCTION public.fn_generate_gamme_validations()
    """)

    op.execute("DROP INDEX IF EXISTS idx_gamme_step_validation_occurrence_id")

    op.execute("""
        ALTER TABLE public.gamme_step_validation
            DROP CONSTRAINT IF EXISTS gamme_step_validation_step_occurrence_key
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'gamme_step_validation_step_interv_key'
                  AND conrelid = 'public.gamme_step_validation'::regclass
            ) THEN
                ALTER TABLE public.gamme_step_validation
                    ADD CONSTRAINT gamme_step_validation_step_interv_key
                    UNIQUE (step_id, intervention_id);
            END IF;
        END
        $$
    """)

    op.execute("""
        ALTER TABLE public.gamme_step_validation
            DROP COLUMN IF EXISTS occurrence_id
    """)

    op.execute("""
        ALTER TABLE public.gamme_step_validation
            ALTER COLUMN intervention_id SET NOT NULL
    """)
