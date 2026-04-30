-- ============================================================================
-- intervention.sql - Table principale des interventions
-- ============================================================================
-- Interventions de maintenance sur machines/équipements
-- Code généré automatiquement par trigger : MACHINE-TYPE-YYYYMMDD-INITIALES
--
-- @see machine.sql
-- @see intervention_status_ref.sql
-- @see trigger trg_interv_code
-- @see trigger trg_init_status_log
-- @see trigger trg_log_status_change
-- @see preventive_plan.sql (02_ref)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.intervention (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Code unique auto-généré (trigger)
    code VARCHAR(255) UNIQUE,
    
    -- Relations
    machine_id UUID,
    updated_by UUID, -- Référence utilisateur (gestion externe)
    
    -- Informations intervention
    type_inter VARCHAR(255), -- Type: 'PREV', 'COR', 'INST', etc.
    tech_initials VARCHAR(255), -- Initiales technicien (pour code)
    description TEXT,
    
    -- Dates
    date_debut TIMESTAMPTZ,
    date_fin TIMESTAMPTZ,
    
    -- Statut actuel (synchronisé avec intervention_status_log)
    status_actual VARCHAR(255),

    -- Plan préventif associé (NULL pour interventions correctives)
    plan_id UUID, -- FK ajoutée après création de preventive_plan (02_ref)

    -- Métadonnées
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index
CREATE INDEX IF NOT EXISTS intervention_machine_id_index ON public.intervention(machine_id);

-- Commentaires
COMMENT ON TABLE public.intervention IS 'Interventions maintenance sur équipements';
COMMENT ON COLUMN public.intervention.code IS 'Code unique auto-généré (MACHINE-TYPE-DATE-INITIALES)';
COMMENT ON COLUMN public.intervention.status_actual IS 'Statut actuel synchronisé depuis intervention_status_log';
COMMENT ON COLUMN public.intervention.plan_id IS 'Plan préventif associé à l''intervention (NULL pour interventions correctives).';
