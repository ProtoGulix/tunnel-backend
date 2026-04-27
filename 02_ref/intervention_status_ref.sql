-- ============================================================================
-- intervention_status_ref.sql - Statuts interventions
-- ============================================================================
-- Référentiel statuts interventions (ouvert, en_cours, fermé, etc.)
--
-- @see intervention.sql (01_core)
-- @see intervention_status_log.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.intervention_status_ref (
    code VARCHAR(255) PRIMARY KEY,
    
    -- Libellé
    label TEXT,
    
    -- Couleur hexadécimale pour UI
    color VARCHAR(255)
);

-- Commentaires
COMMENT ON TABLE public.intervention_status_ref IS 'Référentiel statuts interventions';

-- Données de référence
-- INSERT INTO intervention_status_ref (code, label, color) VALUES
--   ('ouvert', 'Ouvert', '#3b82f6'),
--   ('en_cours', 'En cours', '#f59e0b'),
--   ('ferme', 'Fermé', '#10b981'),
--   ('annule', 'Annulé', '#ef4444');
