-- ============================================================================
-- action_classification_probe.sql - Sondes de classification des actions
-- ============================================================================
-- Mots-clés et patterns pour détecter les anomalies de classification
-- Basé sur NLP/keywords pour suggérer des recatégorisations
--
-- @see action_category.sql (02_ref)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.action_classification_probe (
    id SERIAL PRIMARY KEY,
    
    -- Pattern de détection
    keyword VARCHAR(255) NOT NULL,                    -- Mot-clé ou pattern à détecter
    detection_type VARCHAR(50) DEFAULT 'keyword',     -- keyword, regex, nlp
    
    -- Suggestion
    suggested_category VARCHAR(255),                  -- Catégorie suggérée (peut être NULL pour alertes)
    
    -- Sévérité
    severity VARCHAR(20) DEFAULT 'warning',           -- info, warning, error
    
    -- Métadonnées
    description TEXT,                                 -- Explication de la détection
    is_active BOOLEAN DEFAULT true,                   -- Actif/inactif
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Trigger pour updated_at
CREATE TRIGGER update_action_classification_probe_updated_at
    BEFORE UPDATE ON public.action_classification_probe
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Index
CREATE INDEX IF NOT EXISTS action_classification_probe_keyword_index ON public.action_classification_probe(keyword);
CREATE INDEX IF NOT EXISTS action_classification_probe_active_index ON public.action_classification_probe(is_active);
CREATE INDEX IF NOT EXISTS action_classification_probe_severity_index ON public.action_classification_probe(severity);

-- Commentaires
COMMENT ON TABLE public.action_classification_probe IS 'Sondes NLP pour détection anomalies de classification';
COMMENT ON COLUMN public.action_classification_probe.keyword IS 'Mot-clé ou pattern à détecter dans descriptions';
COMMENT ON COLUMN public.action_classification_probe.detection_type IS 'Type de détection : keyword (exact), regex (pattern), nlp (sémantique)';
COMMENT ON COLUMN public.action_classification_probe.suggested_category IS 'Catégorie suggérée (NULL = alerte sans suggestion)';
COMMENT ON COLUMN public.action_classification_probe.severity IS 'Sévérité : info, warning, error';

-- Données de référence (basées sur anomalyConfig.js - suspiciousKeywords)
-- INSERT INTO action_classification_probe (keyword, suggested_category, severity, description) VALUES
--   ('identif', 'SUP', 'warning', 'Action d''identification potentiellement administrative'),
--   ('tableur', 'SUP', 'warning', 'Travail sur tableur = tâche administrative'),
--   ('référence', 'SUP', 'warning', 'Recherche de référence = support'),
--   ('pneuma', 'DEP', 'warning', 'Pneumatique = dépannage probable'),
--   ('vis', 'DEP', 'info', 'Visserie = opération mécanique'),
--   ('rangement', 'BAT', 'warning', 'Rangement = bâtiment/nettoyage'),
--   ('tri', 'BAT', 'warning', 'Tri = bâtiment/organisation'),
--   ('classement', 'SUP', 'warning', 'Classement = administratif'),
--   ('inventaire', 'SUP', 'warning', 'Inventaire = support/gestion'),
--   ('commande', 'SUP', 'warning', 'Commande = achat/administratif');
