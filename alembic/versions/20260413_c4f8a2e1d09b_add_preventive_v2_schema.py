"""add_preventive_v2_schema

Cree les tables du module Maintenance Preventive v2 :
  - preventive_plan          (referentiel)
  - preventive_plan_gamme_step (referentiel)
  - preventive_occurrence    (transactionnel)
  - gamme_step_validation    (transactionnel)
  - machine_hours            (transactionnel)
  - intervention.plan_id     (nouvelle colonne)
  - 4 triggers associes

Revision ID: c4f8a2e1d09b
Revises: b3e7f1a09c42
Create Date: 2026-04-13 00:00:00.000000
"""
from __future__ import annotations
from typing import Union
from alembic import op

revision: str = "c4f8a2e1d09b"
down_revision: Union[str, None] = "b3e7f1a09c42"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Table référentielle preventive_plan
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.preventive_plan (
            id                  UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
            code                VARCHAR(50)  UNIQUE NOT NULL,
            label               TEXT         NOT NULL,
            equipement_class_id UUID         REFERENCES public.equipement_class (id) ON DELETE RESTRICT,
            trigger_type        VARCHAR(20)  NOT NULL,
            periodicity_days    INTEGER,
            hours_threshold     INTEGER,
            auto_accept         BOOLEAN      NOT NULL DEFAULT FALSE,
            active              BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            CONSTRAINT preventive_plan_trigger_type_check CHECK (
                (trigger_type = 'periodicity' AND periodicity_days IS NOT NULL)
                OR
                (trigger_type = 'hours' AND hours_threshold IS NOT NULL)
            )
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_preventive_plan_equipment_class
            ON public.preventive_plan (equipement_class_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_preventive_plan_active
            ON public.preventive_plan (active) WHERE active = TRUE
    """)

    # -------------------------------------------------------------------------
    # 2. Table référentielle preventive_plan_gamme_step
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.preventive_plan_gamme_step (
            id          UUID     PRIMARY KEY DEFAULT uuid_generate_v4(),
            plan_id     UUID     NOT NULL REFERENCES public.preventive_plan (id) ON DELETE CASCADE,
            label       TEXT     NOT NULL,
            sort_order  INTEGER  NOT NULL,
            optional    BOOLEAN  NOT NULL DEFAULT FALSE,
            CONSTRAINT preventive_plan_gamme_step_plan_sort_key UNIQUE (plan_id, sort_order)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_gamme_step_plan_id
            ON public.preventive_plan_gamme_step (plan_id)
    """)

    # -------------------------------------------------------------------------
    # 3. Colonne plan_id sur intervention
    # -------------------------------------------------------------------------
    op.execute("""
        ALTER TABLE public.intervention
            ADD COLUMN IF NOT EXISTS plan_id UUID
                REFERENCES public.preventive_plan (id) ON DELETE SET NULL
    """)

    # -------------------------------------------------------------------------
    # 4. Table transactionnelle preventive_occurrence
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.preventive_occurrence (
            id               UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
            plan_id          UUID          NOT NULL REFERENCES public.preventive_plan (id) ON DELETE RESTRICT,
            machine_id       UUID          NOT NULL REFERENCES public.machine (id) ON DELETE RESTRICT,
            scheduled_date   DATE          NOT NULL,
            triggered_at     TIMESTAMPTZ,
            hours_at_trigger NUMERIC(10,2),
            di_id            UUID          REFERENCES public.intervention_request (id) ON DELETE SET NULL,
            intervention_id  UUID          REFERENCES public.intervention (id) ON DELETE SET NULL,
            status           VARCHAR(20)   NOT NULL DEFAULT 'pending',
            skip_reason      TEXT,
            created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            CONSTRAINT preventive_occurrence_plan_machine_date_key UNIQUE (plan_id, machine_id, scheduled_date),
            CONSTRAINT preventive_occurrence_skip_reason_check CHECK (
                (status != 'skipped') OR (skip_reason IS NOT NULL)
            )
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_prev_occurrence_plan_id ON public.preventive_occurrence (plan_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_prev_occurrence_machine_id ON public.preventive_occurrence (machine_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_prev_occurrence_status ON public.preventive_occurrence (status)")

    # -------------------------------------------------------------------------
    # 5. Table transactionnelle machine_hours
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.machine_hours (
            machine_id  UUID          PRIMARY KEY REFERENCES public.machine (id) ON DELETE CASCADE,
            hours_total NUMERIC(10,2) NOT NULL DEFAULT 0,
            updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        )
    """)

    # -------------------------------------------------------------------------
    # 6. Table transactionnelle gamme_step_validation
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.gamme_step_validation (
            id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
            step_id         UUID        NOT NULL REFERENCES public.preventive_plan_gamme_step (id) ON DELETE RESTRICT,
            intervention_id UUID        NOT NULL REFERENCES public.intervention (id) ON DELETE RESTRICT,
            action_id       UUID        REFERENCES public.intervention_action (id) ON DELETE SET NULL,
            status          VARCHAR(20) NOT NULL DEFAULT 'pending',
            skip_reason     TEXT,
            validated_at    TIMESTAMPTZ,
            validated_by    UUID,
            CONSTRAINT gamme_step_validation_step_interv_key UNIQUE (step_id, intervention_id),
            CONSTRAINT gamme_step_validation_skip_reason_check CHECK (
                (status != 'skipped') OR (skip_reason IS NOT NULL)
            )
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_intervention_id ON public.gamme_step_validation (intervention_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_action_id ON public.gamme_step_validation (action_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_status ON public.gamme_step_validation (status)")

    # -------------------------------------------------------------------------
    # 7. Trigger : fn_machine_hours_update
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_machine_hours_update()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE
            v_machine_id UUID;
            v_delta      NUMERIC(10,2);
        BEGIN
            SELECT i.machine_id INTO v_machine_id
            FROM public.intervention i
            WHERE i.id = NEW.intervention_id;

            IF v_machine_id IS NULL THEN RETURN NEW; END IF;

            IF TG_OP = 'INSERT' THEN
                v_delta := COALESCE(NEW.time_spent, 0);
            ELSE
                v_delta := COALESCE(NEW.time_spent, 0) - COALESCE(OLD.time_spent, 0);
            END IF;

            INSERT INTO public.machine_hours (machine_id, hours_total, updated_at)
            VALUES (v_machine_id, GREATEST(0, v_delta), NOW())
            ON CONFLICT (machine_id) DO UPDATE
                SET hours_total = GREATEST(0, public.machine_hours.hours_total + v_delta),
                    updated_at  = NOW();

            RETURN NEW;
        END;
        $$
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_machine_hours_update ON public.intervention_action")
    op.execute("""
        CREATE TRIGGER trg_machine_hours_update
            AFTER INSERT OR UPDATE OF time_spent ON public.intervention_action
            FOR EACH ROW
            EXECUTE FUNCTION public.fn_machine_hours_update()
    """)

    # -------------------------------------------------------------------------
    # 8. Trigger : fn_generate_gamme_validations
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_generate_gamme_validations()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
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

            IF v_plan_id IS NULL THEN RETURN NEW; END IF;

            FOR v_step IN
                SELECT id FROM public.preventive_plan_gamme_step
                WHERE plan_id = v_plan_id ORDER BY sort_order
            LOOP
                INSERT INTO public.gamme_step_validation (step_id, intervention_id, action_id, status)
                VALUES (v_step.id, NEW.intervention_id, NEW.id, 'pending')
                ON CONFLICT (step_id, intervention_id) DO NOTHING;
            END LOOP;

            RETURN NEW;
        END;
        $$
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_generate_gamme_validations ON public.intervention_action")
    op.execute("""
        CREATE TRIGGER trg_generate_gamme_validations
            AFTER INSERT ON public.intervention_action
            FOR EACH ROW
            EXECUTE FUNCTION public.fn_generate_gamme_validations()
    """)

    # -------------------------------------------------------------------------
    # 9. Trigger : fn_check_intervention_closable
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_check_intervention_closable()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        DECLARE
            v_pending_count INT;
        BEGIN
            IF NEW.status_actual = 'ferme' AND OLD.status_actual IS DISTINCT FROM 'ferme' THEN
                IF NEW.plan_id IS NOT NULL THEN
                    SELECT COUNT(*) INTO v_pending_count
                    FROM public.gamme_step_validation
                    WHERE intervention_id = NEW.id AND status = 'pending';

                    IF v_pending_count > 0 THEN
                        RAISE EXCEPTION 'GAMME_INCOMPLETE: % etape(s) en attente de validation', v_pending_count;
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_check_intervention_closable ON public.intervention")
    op.execute("""
        CREATE TRIGGER trg_check_intervention_closable
            BEFORE UPDATE ON public.intervention
            FOR EACH ROW
            EXECUTE FUNCTION public.fn_check_intervention_closable()
    """)

    # -------------------------------------------------------------------------
    # 10. Trigger : fn_updated_at_preventive_plan
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_updated_at_preventive_plan()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at := NOW();
            RETURN NEW;
        END;
        $$
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_updated_at_preventive_plan ON public.preventive_plan")
    op.execute("""
        CREATE TRIGGER trg_updated_at_preventive_plan
            BEFORE UPDATE ON public.preventive_plan
            FOR EACH ROW
            EXECUTE FUNCTION public.fn_updated_at_preventive_plan()
    """)


def downgrade() -> None:
    # Triggers
    op.execute("DROP TRIGGER IF EXISTS trg_updated_at_preventive_plan ON public.preventive_plan")
    op.execute("DROP FUNCTION IF EXISTS public.fn_updated_at_preventive_plan()")
    op.execute("DROP TRIGGER IF EXISTS trg_check_intervention_closable ON public.intervention")
    op.execute("DROP FUNCTION IF EXISTS public.fn_check_intervention_closable()")
    op.execute("DROP TRIGGER IF EXISTS trg_generate_gamme_validations ON public.intervention_action")
    op.execute("DROP FUNCTION IF EXISTS public.fn_generate_gamme_validations()")
    op.execute("DROP TRIGGER IF EXISTS trg_machine_hours_update ON public.intervention_action")
    op.execute("DROP FUNCTION IF EXISTS public.fn_machine_hours_update()")

    # Tables transactionnelles
    op.execute("DROP TABLE IF EXISTS public.gamme_step_validation")
    op.execute("DROP TABLE IF EXISTS public.machine_hours")
    op.execute("DROP TABLE IF EXISTS public.preventive_occurrence")

    # Colonne plan_id sur intervention
    op.execute("ALTER TABLE public.intervention DROP COLUMN IF EXISTS plan_id")

    # Tables référentielles
    op.execute("DROP TABLE IF EXISTS public.preventive_plan_gamme_step")
    op.execute("DROP TABLE IF EXISTS public.preventive_plan")
