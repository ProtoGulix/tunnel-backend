-- ============================================================================
-- preventive_plan_gamme_step.sql - Étapes de gamme des plans préventifs
-- ============================================================================
-- Checklist ordonnée des étapes à réaliser pour un plan préventif.
-- L'unicité (plan_id, sort_order) garantit l'ordre sans conflit.
--
-- @see preventive_plan.sql (02_ref)
-- @see gamme_step_validation.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.preventive_plan_gamme_step (
    id          UUID     PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id     UUID     NOT NULL REFERENCES public.preventive_plan (id) ON DELETE CASCADE,
    label       TEXT     NOT NULL,
    sort_order  INTEGER  NOT NULL,
    optional    BOOLEAN  NOT NULL DEFAULT FALSE,

    CONSTRAINT preventive_plan_gamme_step_plan_sort_key UNIQUE (plan_id, sort_order)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_gamme_step_plan_id
    ON public.preventive_plan_gamme_step (plan_id);

-- Commentaires
COMMENT ON TABLE  public.preventive_plan_gamme_step             IS 'Étapes de la gamme d''un plan préventif (checklist ordonnée).';
COMMENT ON COLUMN public.preventive_plan_gamme_step.sort_order  IS 'Ordre d''affichage — unique par plan.';
COMMENT ON COLUMN public.preventive_plan_gamme_step.optional    IS 'Si TRUE, l''étape peut être ignorée sans bloquer la clôture de l''intervention.';
