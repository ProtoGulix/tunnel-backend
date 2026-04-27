-- ============================================================================
-- intervention_action.sql - Actions réalisées durant interventions
-- ============================================================================
-- Détail des actions/tâches effectuées lors d'une intervention
-- Lien avec sous-catégories d'actions pour classification
--
-- @see intervention.sql
-- @see action_subcategory.sql (02_ref)
-- @see complexity_factor.sql  (02_ref)
-- @see trg_action_time.sql    (05_triggers)
-- @see trigger_detect_preventive.sql (05_triggers)
-- @see intervention_action_purchase_request.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.intervention_action (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

-- Relations
intervention_id UUID REFERENCES public.intervention (id) ON DELETE CASCADE,
action_subcategory INTEGER REFERENCES public.action_subcategory (id) ON DELETE SET NULL,
tech UUID REFERENCES public.directus_users (id) ON DELETE NO ACTION,

-- Détails action
description TEXT,
-- Temps passé (heures, multiple de 0.25). Calculé par trigger si bornes fournies. Nullable.
time_spent NUMERIC(6, 2) DEFAULT 0,
-- Bornes horaires (mode alternatif à time_spent direct, multiples de 15 min)
action_start TIME DEFAULT NULL,
action_end TIME DEFAULT NULL,

-- Complexité
complexity_score INTEGER,
complexity_anotation JSON,
-- Facteur de complexité (remplace complexity_anotation après migration v1.2.1→v1.3.0)
complexity_factor VARCHAR(255) REFERENCES public.complexity_factor (code) ON DELETE SET NULL,

-- Métadonnées
created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index
CREATE INDEX IF NOT EXISTS intervention_action_created_at_index ON public.intervention_action (created_at);

CREATE INDEX IF NOT EXISTS idx_intervention_action_complexity_factor ON public.intervention_action (complexity_factor);

-- Commentaires
COMMENT ON TABLE public.intervention_action IS 'Actions réalisées durant interventions';

COMMENT ON COLUMN public.intervention_action.action_subcategory IS 'Sous-catégorie d''action (classification métier)';

COMMENT ON COLUMN public.intervention_action.time_spent IS 'Temps passé en heures, multiple de 0.25. Calculé automatiquement si bornes fournies.';

COMMENT ON COLUMN public.intervention_action.action_start IS 'Heure de début (multiple de 15 min) ; exclusif avec time_spent direct';

COMMENT ON COLUMN public.intervention_action.action_end IS 'Heure de fin (multiple de 15 min) ; exclusif avec time_spent direct';

COMMENT ON COLUMN public.intervention_action.complexity_score IS 'Score de complexité calculé (somme des facteurs)';

COMMENT ON COLUMN public.intervention_action.complexity_anotation IS 'Détail JSON des facteurs de complexité appliqués';

COMMENT ON COLUMN public.intervention_action.complexity_factor IS 'Référence vers le facteur de complexité (remplace complexity_anotation)';