-- ============================================================================
-- gamme_step_validation.sql - Validation des étapes de gamme
-- ============================================================================
-- Trace la validation (ou le saut) de chaque étape de gamme pour une
-- intervention préventive. Générée automatiquement par trigger à la
-- création d'une action de sous-catégorie PREV_.
--
-- @see preventive_plan_gamme_step.sql (02_ref)
-- @see intervention.sql               (01_core)
-- @see intervention_action.sql        (01_core)
-- @see trg_preventive_v2.sql          (05_triggers)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.gamme_step_validation (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_id         UUID        NOT NULL REFERENCES public.preventive_plan_gamme_step (id) ON DELETE RESTRICT,
    intervention_id UUID        NOT NULL REFERENCES public.intervention (id) ON DELETE RESTRICT,
    action_id       UUID        REFERENCES public.intervention_action (id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    skip_reason     TEXT,
    validated_at    TIMESTAMPTZ,
    validated_by    UUID,   -- référence utilisateur externe, pas de FK

    CONSTRAINT gamme_step_validation_step_interv_key UNIQUE (step_id, intervention_id),
    CONSTRAINT gamme_step_validation_skip_reason_check CHECK (
        (status != 'skipped') OR (skip_reason IS NOT NULL)
    )
);

-- Index
CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_intervention_id
    ON public.gamme_step_validation (intervention_id);

CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_action_id
    ON public.gamme_step_validation (action_id);

CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_status
    ON public.gamme_step_validation (status);

-- Commentaires
COMMENT ON TABLE  public.gamme_step_validation              IS 'Validation de chaque étape de gamme pour une intervention préventive.';
COMMENT ON COLUMN public.gamme_step_validation.action_id    IS 'Action d''intervention liée à cette étape (nullable).';
COMMENT ON COLUMN public.gamme_step_validation.validated_by IS 'UUID de l''utilisateur ayant validé (référence externe, sans FK).';
COMMENT ON COLUMN public.gamme_step_validation.skip_reason  IS 'Obligatoire si status = ''skipped''.';
