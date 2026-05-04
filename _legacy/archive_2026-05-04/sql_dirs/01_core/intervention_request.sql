-- ============================================================================
-- intervention_request.sql - Table principale des demandes d'intervention
-- ============================================================================
-- Demande d'intervention soumise par un acteur externe (opérateur, service).
-- Code DI-YYYY-NNNN généré automatiquement par trigger BEFORE INSERT.
-- Le statut est positionné exclusivement via request_status_log (trigger).
--
-- @see request_status_ref.sql     (02_ref)
-- @see request_status_log.sql     (01_core)
-- @see machine.sql                (01_core)
-- @see intervention.sql           (01_core)
-- @see fn_generate_request_code   (05_triggers)
-- @see fn_init_request_status_log (05_triggers)
-- @see fn_log_request_status_change (05_triggers)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.intervention_request (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),

-- Code unique auto-généré (trigger BEFORE INSERT : trg_request_code)
code VARCHAR(255) UNIQUE NOT NULL,

-- Relations
machine_id UUID NOT NULL REFERENCES public.machine (id) ON DELETE RESTRICT,
-- Lien vers l'intervention créée depuis la demande (NULL tant qu'aucune)
intervention_id UUID UNIQUE REFERENCES public.intervention (id) ON DELETE SET NULL,

-- Demandeur
demandeur_nom TEXT NOT NULL,
demandeur_service TEXT,

-- Contenu
description TEXT NOT NULL,

-- Statut courant — synchronisé par trigger depuis request_status_log
-- Pas de DEFAULT : positionné exclusivement via le log à la création
statut VARCHAR(50) NOT NULL REFERENCES public.request_status_ref (code),

-- Horodatage
created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.intervention_request IS 'Demandes d''intervention soumises par des acteurs externes';

COMMENT ON COLUMN public.intervention_request.code IS 'Code unique DI-YYYY-NNNN généré par trigger';

COMMENT ON COLUMN public.intervention_request.statut IS 'Statut courant, synchronisé par trigger depuis request_status_log';

COMMENT ON COLUMN public.intervention_request.intervention_id IS 'Intervention GMAO créée depuis cette demande (NULL si pas encore créée)';

COMMENT ON COLUMN public.intervention_request.demandeur_service IS 'Service émetteur de la demande (nullable pour demandes publiques)';