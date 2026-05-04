-- ============================================================================
-- subtask.sql - Sous-tâches interventions
-- ============================================================================
-- Découpage intervention en sous-tâches assignables
--
-- @see intervention.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.subtask (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relations
    intervention_id UUID,
    assigned_to UUID, -- Technicien assigné
    
    -- Détails sous-tâche
    description TEXT,
    status VARCHAR(255) -- Statut: todo, in_progress, done, blocked
);

-- Commentaires
COMMENT ON TABLE public.subtask IS 'Sous-tâches décomposition interventions';
