-- ============================================================================
-- intervention_action_purchase_request.sql - Table de liaison action ↔ demande d'achat
-- ============================================================================
-- Liaison N-N entre les actions d'intervention et les demandes d'achat.
-- Une action peut générer plusieurs demandes d'achat (pièces différentes),
-- et une demande d'achat peut être liée à plusieurs actions.
--
-- Table créée initialement par Directus ; rapatriée dans le schéma versionné.
--
-- @see intervention_action.sql (01_core)
-- @see purchase_request.sql    (01_core)
-- ============================================================================

CREATE SEQUENCE IF NOT EXISTS public.intervention_action_purchase_request_id_seq;

CREATE TABLE IF NOT EXISTS public.intervention_action_purchase_request (
    id INTEGER NOT NULL DEFAULT nextval(
        'intervention_action_purchase_request_id_seq'::regclass
    ),
    intervention_action_id UUID REFERENCES public.intervention_action (id) ON DELETE SET NULL,
    purchase_request_id UUID REFERENCES public.purchase_request (id) ON DELETE SET NULL,
    CONSTRAINT intervention_action_purchase_request_pkey PRIMARY KEY (id)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_iapr_action ON public.intervention_action_purchase_request (intervention_action_id);

CREATE INDEX IF NOT EXISTS idx_iapr_purchase ON public.intervention_action_purchase_request (purchase_request_id);

-- Commentaires
COMMENT ON TABLE public.intervention_action_purchase_request IS 'Liaison N-N entre actions d''intervention et demandes d''achat';

COMMENT ON COLUMN public.intervention_action_purchase_request.intervention_action_id IS 'Action d''intervention concernée (SET NULL si supprimée)';

COMMENT ON COLUMN public.intervention_action_purchase_request.purchase_request_id IS 'Demande d''achat associée (SET NULL si supprimée)';