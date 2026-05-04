-- ============================================================================
-- seed_meta_configuration.sql - Données d'initialisation configuration métier
-- ============================================================================
-- Insère les données initiales basées sur anomalyConfig.js
-- À exécuter après création des tables 03_meta/
-- ============================================================================

-- ============================================================================
-- 1. Métadonnées des catégories (action_category_meta)
-- ============================================================================

INSERT INTO action_category_meta (category_code, is_simple, is_low_value, typical_duration_min, typical_duration_max) VALUES
  ('BAT', true, true, 0.5, 2.0),   -- Bâtiment/Nettoyage : simple et faible valeur (ex: BAT_NET)
  ('SUP', true, true, 0.5, 3.0),   -- Support/Admin : simple et faible valeur (ex: SUP_INV, SUP_ACH, SUP_GES)
  ('DEP', false, false, 1.0, 6.0), -- Dépannage : valeur élevée, technique
  ('PREV', false, false, 1.0, 4.0), -- Préventif : valeur élevée, planifié
  ('FAB', false, false, 2.0, 8.0)  -- Fabrication : valeur élevée, complexe
ON CONFLICT (category_code) DO UPDATE SET
  is_simple = EXCLUDED.is_simple,
  is_low_value = EXCLUDED.is_low_value,
  typical_duration_min = EXCLUDED.typical_duration_min,
  typical_duration_max = EXCLUDED.typical_duration_max,
  updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- 2. Sondes de classification NLP (action_classification_probe)
-- ============================================================================

INSERT INTO action_classification_probe (keyword, suggested_category, severity, description, detection_type) VALUES
  -- Mots-clés administratifs → SUP
  ('identif', 'SUP', 'warning', 'Action d''identification potentiellement administrative', 'keyword'),
  ('tableur', 'SUP', 'warning', 'Travail sur tableur = tâche administrative', 'keyword'),
  ('référence', 'SUP', 'warning', 'Recherche de référence = support', 'keyword'),
  ('classement', 'SUP', 'warning', 'Classement = administratif', 'keyword'),
  ('inventaire', 'SUP', 'warning', 'Inventaire = support/gestion', 'keyword'),
  ('commande', 'SUP', 'warning', 'Commande = achat/administratif', 'keyword'),
  
  -- Mots-clés rangement/nettoyage → BAT
  ('rangement', 'BAT', 'warning', 'Rangement = bâtiment/nettoyage', 'keyword'),
  ('tri', 'BAT', 'warning', 'Tri = bâtiment/organisation', 'keyword'),
  ('nettoyage', 'BAT', 'info', 'Nettoyage = bâtiment', 'keyword'),
  
  -- Mots-clés techniques → DEP
  ('pneuma', 'DEP', 'warning', 'Pneumatique = dépannage probable', 'keyword'),
  ('vis', 'DEP', 'info', 'Visserie = opération mécanique', 'keyword'),
  ('fuite', 'DEP', 'warning', 'Fuite = dépannage urgent', 'keyword'),
  ('panne', 'DEP', 'error', 'Panne = dépannage critique', 'keyword')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 3. Seuils de détection d'anomalies (anomaly_threshold)
-- ============================================================================

INSERT INTO anomaly_threshold (anomaly_type, threshold_value, threshold_unit, high_severity_value, description, config_json, is_active) VALUES
  (
    'repetitive',
    3,
    'count',
    6,
    'Actions répétitives sur même machine par mois (A)',
    '{"monthlyCount": 3, "highSeverityCount": 6}'::jsonb,
    true
  ),
  (
    'fragmented',
    1,
    'hours',
    5,
    'Actions fragmentées : courtes (<1h) et fréquentes (>5 occurrences) (B)',
    '{"maxDuration": 1, "minOccurrences": 5, "highSeverityCount": 10}'::jsonb,
    true
  ),
  (
    'too_long',
    4,
    'hours',
    8,
    'Actions trop longues pour catégorie simple (>4h, sévère >8h) (C)',
    '{"maxDuration": 4, "highSeverityDuration": 8}'::jsonb,
    true
  ),
  (
    'bad_classification',
    1,
    'keywords',
    2,
    'Mauvaise classification détectée par mots-clés suspects (D)',
    '{"minKeywords": 1, "highSeverityKeywords": 2}'::jsonb,
    true
  ),
  (
    'back_to_back',
    1,
    'days',
    0.5,
    'Retours back-to-back : réintervention rapide (<1 jour, sévère <0.5 jour) (E)',
    '{"maxDaysDiff": 1, "highSeverityDays": 0.5}'::jsonb,
    true
  ),
  (
    'low_value_high_load',
    30,
    'hours',
    60,
    'Faible valeur ajoutée + charge élevée (>30h cumulées, sévère >60h) (F)',
    '{"minTotalHours": 30, "highSeverityHours": 60}'::jsonb,
    true
  )
ON CONFLICT (anomaly_type) DO UPDATE SET
  threshold_value = EXCLUDED.threshold_value,
  high_severity_value = EXCLUDED.high_severity_value,
  description = EXCLUDED.description,
  config_json = EXCLUDED.config_json,
  is_active = EXCLUDED.is_active,
  updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- Vérification
-- ============================================================================

-- Afficher les données insérées
SELECT 'action_category_meta' as table_name, count(*) as count FROM action_category_meta
UNION ALL
SELECT 'action_classification_probe', count(*) FROM action_classification_probe
UNION ALL
SELECT 'anomaly_threshold', count(*) FROM anomaly_threshold;
