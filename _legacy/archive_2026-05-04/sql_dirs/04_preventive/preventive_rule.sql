-- ═══════════════════════════════════════════════════════════════════════════════
-- 06_preventive_rule.sql - Table des règles de détection préventif
-- ═══════════════════════════════════════════════════════════════════════════════
-- 
-- Cœur du moteur de préconisation : chaque règle = 1 mot-clé → 1 type de maintenance
-- Statique, alimentée manuellement, utilisée par le trigger de détection.
--
-- @author Tunnel GMAO
-- @version 1.0
-- @created 2026-01-05

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. Création de la table
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS preventive_rule (
  id SERIAL PRIMARY KEY,
  
  -- Mot-clé à détecter dans la description d'action (sensible à la casse après lower())
  keyword TEXT NOT NULL UNIQUE,
  
  -- Code standardisé de la préconisation (ex: PREV_COURROIE)
  preventive_code TEXT NOT NULL,
  
  -- Label lisible (ex: "Contrôle tension & alignement courroies")
  preventive_label TEXT NOT NULL,
  
  -- Poids (score) de la règle : importance relative
  -- 1 = faible (ex: vis), 2 = moyen/standard
  weight INT DEFAULT 1,
  
  -- Permet de désactiver une règle sans la supprimer
  active BOOLEAN DEFAULT TRUE,
  
  -- Audit
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. Données initiales (MVP - basées sur historique réel)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ⚠️ Attention : ajuster selon ton domaine métier
-- Ces mots-clés doivent matcher les descriptions d'actions réelles

INSERT INTO preventive_rule (keyword, preventive_code, preventive_label, weight)
VALUES
  ('courroie', 'PREV_COURROIE', 'Contrôle tension & alignement courroies', 2),
  ('lame', 'PREV_LAME', 'Contrôle usure / réglage lames', 2),
  ('couteau', 'PREV_LAME', 'Contrôle usure couteaux', 2),
  ('roulement', 'PREV_ROULEMENT', 'Contrôle bruit / jeu roulements', 2),
  ('capteur', 'PREV_CAPTEUR', 'Nettoyage / réglage capteurs', 2),
  ('filtre', 'PREV_FILTRE', 'Nettoyage filtre / crépine', 2),
  ('cable', 'PREV_CABLE', 'Contrôle cheminement câbles', 1),
  ('vis', 'PREV_SERRAGE', 'Contrôle serrage visserie', 1),
  ('axe', 'PREV_SERRAGE', 'Contrôle axes / goupilles', 1),
  ('pompe', 'PREV_POMPE', 'Contrôle pompe / amorçage', 2)
ON CONFLICT (keyword) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. Index (performances du trigger)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_preventive_rule_active 
  ON preventive_rule(active) 
  WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS idx_preventive_rule_keyword 
  ON preventive_rule(keyword);

-- ═══════════════════════════════════════════════════════════════════════════════
-- Notes de maintenance
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- Pour ajouter une nouvelle règle :
-- INSERT INTO preventive_rule (keyword, preventive_code, preventive_label, weight)
-- VALUES ('nouveau_mot', 'PREV_CODE', 'Description', 2);
--
-- Pour désactiver temporairement :
-- UPDATE preventive_rule SET active = FALSE WHERE keyword = 'couteau';
--
-- Pour consulter les règles actives :
-- SELECT * FROM preventive_rule WHERE active = TRUE ORDER BY weight DESC;
--
