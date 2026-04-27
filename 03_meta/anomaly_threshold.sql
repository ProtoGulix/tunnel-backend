-- ============================================================================
-- anomaly_threshold.sql - Seuils de détection d'anomalies
-- ============================================================================
-- Configuration des seuils pour 6 types d'anomalies détectées
-- Permet ajustement sans redéploiement
--
-- Types d'anomalies :
-- - repetitive       : Actions répétitives (même machine/mois)
-- - fragmented       : Actions fragmentées (courtes et fréquentes)
-- - too_long         : Actions trop longues (catégorie simple)
-- - bad_classification : Mauvaise classification (mots-clés suspects)
-- - back_to_back     : Retours back-to-back (réinterventions rapides)
-- - low_value_high_load : Faible valeur + charge élevée
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.anomaly_threshold (
    id SERIAL PRIMARY KEY,
    
    -- Type d'anomalie
    anomaly_type VARCHAR(50) UNIQUE NOT NULL,   -- Clé unique du type
    
    -- Seuils de détection
    threshold_value NUMERIC,                    -- Valeur seuil principal
    threshold_unit VARCHAR(50),                 -- Unité : hours, count, days, keywords
    high_severity_value NUMERIC,                -- Seuil pour sévérité élevée
    
    -- Configuration additionnelle (JSON pour flexibilité)
    config_json JSONB,                          -- Paramètres supplémentaires
    
    -- Métadonnées
    description TEXT,                           -- Explication du type d'anomalie
    is_active BOOLEAN DEFAULT true,             -- Actif/inactif
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Trigger pour updated_at
CREATE TRIGGER update_anomaly_threshold_updated_at
    BEFORE UPDATE ON public.anomaly_threshold
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Index
CREATE INDEX IF NOT EXISTS anomaly_threshold_type_index ON public.anomaly_threshold(anomaly_type);
CREATE INDEX IF NOT EXISTS anomaly_threshold_active_index ON public.anomaly_threshold(is_active);

-- Commentaires
COMMENT ON TABLE public.anomaly_threshold IS 'Seuils de détection d''anomalies dans les actions';
COMMENT ON COLUMN public.anomaly_threshold.anomaly_type IS 'Type d''anomalie (clé unique)';
COMMENT ON COLUMN public.anomaly_threshold.threshold_value IS 'Valeur seuil de détection principale';
COMMENT ON COLUMN public.anomaly_threshold.threshold_unit IS 'Unité du seuil : hours, count, days, keywords';
COMMENT ON COLUMN public.anomaly_threshold.high_severity_value IS 'Valeur seuil pour sévérité élevée';
COMMENT ON COLUMN public.anomaly_threshold.config_json IS 'Configuration JSON additionnelle (paramètres spécifiques)';

-- Données de référence (basées sur anomalyConfig.js)
-- INSERT INTO anomaly_threshold (anomaly_type, threshold_value, threshold_unit, high_severity_value, description, config_json) VALUES
--   ('repetitive', 3, 'count', 6, 'Actions répétitives sur même machine par mois', '{"monthlyCount": 3, "highSeverityCount": 6}'::jsonb),
--   ('fragmented', 1, 'hours', 5, 'Actions fragmentées (courtes et fréquentes)', '{"maxDuration": 1, "minOccurrences": 5, "highSeverityCount": 10}'::jsonb),
--   ('too_long', 4, 'hours', 8, 'Actions trop longues pour catégorie simple', '{"maxDuration": 4, "highSeverityDuration": 8}'::jsonb),
--   ('bad_classification', 1, 'keywords', 2, 'Mauvaise classification (mots-clés suspects)', '{"minKeywords": 1, "highSeverityKeywords": 2}'::jsonb),
--   ('back_to_back', 1, 'days', 0.5, 'Retours back-to-back (réintervention rapide)', '{"maxDaysDiff": 1, "highSeverityDays": 0.5}'::jsonb),
--   ('low_value_high_load', 30, 'hours', 60, 'Faible valeur ajoutée + charge élevée', '{"minTotalHours": 30, "highSeverityHours": 60}'::jsonb);
