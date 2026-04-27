-- ============================================================================
-- intervention_status_log.sql - Historique changements statut interventions
-- ============================================================================
-- Log de tous les changements de statut (ouvert → en cours → fermé, etc.)
-- Alimenté automatiquement par triggers
--
-- @see intervention.sql
-- @see intervention_status_ref.sql (02_ref)
-- @see trigger trg_init_status_log
-- @see trigger trg_log_status_change
-- @see trigger trg_sync_status_from_log
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.intervention_status_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relations
    intervention_id UUID,
    technician_id UUID, -- Technicien ayant effectué le changement
    
    -- Transition
    status_from VARCHAR(255), -- Statut précédent (NULL si création)
    status_to VARCHAR(255), -- Nouveau statut
    
    -- Date transition
    date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Notes optionnelles
    notes TEXT
);

-- Commentaires
COMMENT ON TABLE public.intervention_status_log IS 'Historique changements statut interventions';
COMMENT ON COLUMN public.intervention_status_log.status_from IS 'Statut précédent (NULL si création initiale)';
COMMENT ON COLUMN public.intervention_status_log.date IS 'Date/heure du changement de statut';
