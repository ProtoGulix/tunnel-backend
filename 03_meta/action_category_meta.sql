-- ============================================================================
-- action_category_meta.sql - Métadonnées métier des catégories d'actions
-- ============================================================================
-- Stocke les caractéristiques métier stables des catégories pour analyse
-- et détection d'anomalies (durées typiques, valeur ajoutée)
--
-- @see action_category.sql (02_ref)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.action_category_meta (
    category_code VARCHAR(255) PRIMARY KEY,
    
    -- Caractéristiques métier
    is_simple BOOLEAN DEFAULT false,           -- Catégorie "simple" (temps exécution normalement court)
    is_low_value BOOLEAN DEFAULT false,        -- Faible valeur ajoutée métier
    
    -- Durées typiques (heures)
    typical_duration_min NUMERIC(4,2),         -- Durée typique minimale
    typical_duration_max NUMERIC(4,2),         -- Durée typique maximale
    
    -- Métadonnées
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Trigger pour updated_at
CREATE TRIGGER update_action_category_meta_updated_at
    BEFORE UPDATE ON public.action_category_meta
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Index
CREATE INDEX IF NOT EXISTS action_category_meta_simple_index ON public.action_category_meta(is_simple);
CREATE INDEX IF NOT EXISTS action_category_meta_low_value_index ON public.action_category_meta(is_low_value);

-- Commentaires
COMMENT ON TABLE public.action_category_meta IS 'Métadonnées métier des catégories d''actions (caractéristiques, durées typiques)';
COMMENT ON COLUMN public.action_category_meta.is_simple IS 'Catégorie considérée comme simple (temps exécution court)';
COMMENT ON COLUMN public.action_category_meta.is_low_value IS 'Catégorie à faible valeur ajoutée métier';
COMMENT ON COLUMN public.action_category_meta.typical_duration_min IS 'Durée typique minimale en heures';
COMMENT ON COLUMN public.action_category_meta.typical_duration_max IS 'Durée typique maximale en heures';

-- Données de référence (basées sur anomalyConfig.js)
-- INSERT INTO action_category_meta (category_code, is_simple, is_low_value, typical_duration_min, typical_duration_max) VALUES
--   ('BAT', true, true, 0.5, 2.0),   -- Bâtiment/Nettoyage : simple et faible valeur
--   ('SUP', true, true, 0.5, 3.0),   -- Support/Admin : simple et faible valeur
--   ('DEP', false, false, 1.0, 6.0), -- Dépannage : valeur élevée
--   ('PREV', false, false, 1.0, 4.0), -- Préventif : valeur élevée
--   ('FAB', false, false, 2.0, 8.0); -- Fabrication : valeur élevée
