-- ============================================================================
-- preventive_occurrence.sql - Occurrences planifiées des plans préventifs
-- ============================================================================
-- Chaque ligne représente une échéance planifiée d'un plan préventif pour
-- une machine. Le statut suit le cycle : pending → generated → done / skipped.
--
-- @see preventive_plan.sql      (02_ref)
-- @see machine.sql              (01_core)
-- @see intervention_request.sql (01_core)
-- @see intervention.sql         (01_core)
-- ============================================================================

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
);

-- Index
CREATE INDEX IF NOT EXISTS idx_prev_occurrence_plan_id
    ON public.preventive_occurrence (plan_id);

CREATE INDEX IF NOT EXISTS idx_prev_occurrence_machine_id
    ON public.preventive_occurrence (machine_id);

CREATE INDEX IF NOT EXISTS idx_prev_occurrence_status
    ON public.preventive_occurrence (status);

-- Commentaires
COMMENT ON TABLE  public.preventive_occurrence                  IS 'Occurrences planifiées d''un plan préventif pour une machine donnée.';
COMMENT ON COLUMN public.preventive_occurrence.hours_at_trigger IS 'Snapshot du compteur heures machine au moment du déclenchement.';
COMMENT ON COLUMN public.preventive_occurrence.di_id            IS 'Demande d''intervention générée pour cette occurrence (nullable).';
COMMENT ON COLUMN public.preventive_occurrence.status           IS 'État de l''occurrence : pending | generated | done | skipped.';
COMMENT ON COLUMN public.preventive_occurrence.skip_reason      IS 'Obligatoire si status = ''skipped''.';
