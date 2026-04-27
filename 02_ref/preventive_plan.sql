-- ============================================================================
-- preventive_plan.sql - Plans de maintenance préventive
-- ============================================================================
-- Référentiel des plans préventifs (périodicité ou seuil heures machine).
-- Chaque plan est lié à une classe d'équipement et définit le mode de
-- déclenchement ainsi que la gamme d'étapes à réaliser.
--
-- @see equipment_class.sql (02_ref)
-- @see preventive_plan_gamme_step.sql (02_ref)
-- @see preventive_occurrence.sql (01_core)
-- @see machine_hours.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.preventive_plan (
    id                  UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    code                VARCHAR(50)  UNIQUE NOT NULL,   -- immuable, ex: PREV_CONV_MENS
    label               TEXT         NOT NULL,
    equipement_class_id UUID         REFERENCES public.equipement_class (id) ON DELETE RESTRICT,
    trigger_type        VARCHAR(20)  NOT NULL,          -- 'periodicity' ou 'hours'
    periodicity_days    INTEGER,                        -- NULL si trigger_type = 'hours'
    hours_threshold     INTEGER,                        -- NULL si trigger_type = 'periodicity'
    auto_accept         BOOLEAN      NOT NULL DEFAULT FALSE,
    active              BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT preventive_plan_trigger_type_check CHECK (
        (trigger_type = 'periodicity' AND periodicity_days IS NOT NULL)
        OR
        (trigger_type = 'hours' AND hours_threshold IS NOT NULL)
    )
);

-- Index
CREATE INDEX IF NOT EXISTS idx_preventive_plan_equipment_class
    ON public.preventive_plan (equipement_class_id);

CREATE INDEX IF NOT EXISTS idx_preventive_plan_active
    ON public.preventive_plan (active)
    WHERE active = TRUE;

-- Commentaires
COMMENT ON TABLE  public.preventive_plan                  IS 'Plans de maintenance préventive référentiels (périodicité ou seuil heures).';
COMMENT ON COLUMN public.preventive_plan.code             IS 'Code technique immuable du plan (ex : PREV_CONV_MENS).';
COMMENT ON COLUMN public.preventive_plan.trigger_type     IS 'Mode de déclenchement : ''periodicity'' (jours) ou ''hours'' (compteur heures).';
COMMENT ON COLUMN public.preventive_plan.periodicity_days IS 'Intervalle en jours — renseigné uniquement si trigger_type = ''periodicity''.';
COMMENT ON COLUMN public.preventive_plan.hours_threshold  IS 'Seuil compteur heures — renseigné uniquement si trigger_type = ''hours''.';
COMMENT ON COLUMN public.preventive_plan.auto_accept      IS 'Si TRUE, la génération d''occurrence crée directement une DI sans validation manuelle.';
