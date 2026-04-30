-- ============================================================================
-- request_status_log.sql - Historique des transitions de statut des demandes
-- ============================================================================
-- Log immuable de toutes les transitions de statut d'une demande d'intervention.
-- Alimenté automatiquement par triggers.
-- Le motif de rejet est stocké dans la colonne notes lors de la transition → rejetee.
--
-- @see intervention_request.sql     (01_core)
-- @see request_status_ref.sql       (02_ref)
-- @see fn_init_request_status_log   (05_triggers)
-- @see fn_apply_request_status      (05_triggers)
-- @see fn_log_request_status_change (05_triggers)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.request_status_log (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

-- Relations
request_id UUID NOT NULL REFERENCES public.intervention_request (id) ON DELETE CASCADE,

-- Transition
status_from VARCHAR(50) REFERENCES public.request_status_ref (code), -- NULL à la création
status_to VARCHAR(50) NOT NULL REFERENCES public.request_status_ref (code),

-- Auteur du changement (UUID Directus ; nullable = demande publique sans auth)
changed_by UUID,

-- Commentaire libre (ex : motif de rejet pour transition → rejetee)
notes       TEXT,

    date        TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.request_status_log IS 'Historique des transitions de statut des demandes d''intervention';

COMMENT ON COLUMN public.request_status_log.status_from IS 'Statut précédent (NULL pour la ligne initiale à la création)';

COMMENT ON COLUMN public.request_status_log.changed_by IS 'UUID Directus de l''utilisateur ayant effectué la transition (nullable)';

COMMENT ON COLUMN public.request_status_log.notes IS 'Commentaire libre : motif de rejet, observations, etc.';