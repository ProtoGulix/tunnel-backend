-- ============================================================================
-- complexity_factor.sql - Facteurs de complexité
-- ============================================================================
-- Référentiel niveaux complexité actions
--
-- @see intervention_action.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.complexity_factor (
    code VARCHAR(255) PRIMARY KEY,
    
    -- Libellé
    label TEXT,
    
    -- Catégorie (ex: technique, organisationnel)
    category VARCHAR(255)
);

-- Commentaires
COMMENT ON TABLE public.complexity_factor IS 'Facteurs de complexité des actions';

-- Données de référence
-- INSERT INTO complexity_factor (code, label, category) VALUES
--   ('simple', 'Simple', 'technique'),
--   ('moyen', 'Moyen', 'technique'),
--   ('eleve', 'Élevé', 'technique'),
--   ('critique', 'Critique', 'technique');
