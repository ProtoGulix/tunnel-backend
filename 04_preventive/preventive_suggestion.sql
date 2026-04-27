-- ═══════════════════════════════════════════════════════════════════════════════
-- 07_preventive_suggestion.sql - Table des préconisations détectées
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- Trace factuelle : chaque préconisation détectée est gelée ici avec son statut.
-- Aucun calcul, aucune réesaturation : c'est l'historique vrai.
--
-- Cycle de vie :
--   NEW      → détecté par le trigger, en attente de validation
--   REVIEWED → superviseur a regardé (futur : peut être dans une UI intermédiaire)
--   ACCEPTED → pris en compte, déclenchera création DI_PREV + action préventive
--   REJECTED → refusé par superviseur, conservé pour trace
--
-- @author Tunnel GMAO
-- @version 1.0
-- @created 2026-01-05

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. Création de la table
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS preventive_suggestion (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- ─────────────────────────────────────────────────────────────────
  -- Traçabilité de l'origine (immuable après création)
  -- ─────────────────────────────────────────────────────────────────
  
  -- FK vers intervention_action qui a déclenché la détection
  intervention_action_id UUID NOT NULL UNIQUE,
  
  -- FK vers machine (dénormalisation pour requêtes rapides)
  machine_id UUID NOT NULL,
  
  -- ─────────────────────────────────────────────────────────────────
  -- Contenu de la préconisation (copie de preventive_rule)
  -- ─────────────────────────────────────────────────────────────────
  
  -- Code standardisé (ex: PREV_COURROIE)
  preventive_code TEXT NOT NULL,
  
  -- Label lisible
  preventive_label TEXT NOT NULL,
  
  -- Score de pertinence (poids de la règle déclenchée)
  score INT NOT NULL,
  
  -- ─────────────────────────────────────────────────────────────────
  -- Cycle de vie métier (signature)
  -- ─────────────────────────────────────────────────────────────────
  
  -- État : NEW | REVIEWED | ACCEPTED | REJECTED
  status TEXT NOT NULL DEFAULT 'NEW',
  
  -- Audit : quand détectée
  detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Audit : quand actée (ACCEPTED/REJECTED)
  handled_at TIMESTAMP,
  
  -- Audit : qui a actée
  handled_by UUID,
  
  -- ─────────────────────────────────────────────────────────────────
  -- Contraintes de cohérence
  -- ─────────────────────────────────────────────────────────────────
  
  -- Une machine ne peut avoir qu'une préco par type
  UNIQUE (machine_id, preventive_code),
  
  -- FK : action_intervention (à adapter si ta colonne s'appelle différemment)
  CONSTRAINT fk_preventive_suggestion_action 
    FOREIGN KEY (intervention_action_id) 
    REFERENCES intervention_action(id) 
    ON DELETE RESTRICT,
  
  -- FK : machine
  CONSTRAINT fk_preventive_suggestion_machine 
    FOREIGN KEY (machine_id) 
    REFERENCES machine(id) 
    ON DELETE RESTRICT,
  
  -- Validation : si handled_at, alors status doit être REVIEWED/ACCEPTED/REJECTED
  CONSTRAINT check_handled_at_with_status 
    CHECK (
      (handled_at IS NULL AND status = 'NEW')
      OR (handled_at IS NOT NULL AND status IN ('REVIEWED', 'ACCEPTED', 'REJECTED'))
    )
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. Index (performances des requêtes API)
-- ═══════════════════════════════════════════════════════════════════════════════

-- Requête API principale : précos par machine + statut
CREATE INDEX IF NOT EXISTS idx_preventive_suggestion_machine_status 
  ON preventive_suggestion(machine_id, status);

-- Pour recherche par machine uniquement
CREATE INDEX IF NOT EXISTS idx_preventive_suggestion_machine 
  ON preventive_suggestion(machine_id);

-- Pour recherche par statut
CREATE INDEX IF NOT EXISTS idx_preventive_suggestion_status 
  ON preventive_suggestion(status);

-- Pour recherche par code préconisation
CREATE INDEX IF NOT EXISTS idx_preventive_suggestion_code 
  ON preventive_suggestion(preventive_code);

-- Pour audit/historique
CREATE INDEX IF NOT EXISTS idx_preventive_suggestion_detected_at 
  ON preventive_suggestion(detected_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. Vue pour requêtes courantes (optionnel, pour faciliter API Directus)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW preventive_suggestion_by_status AS
SELECT 
  ps.id,
  ps.intervention_action_id,
  ps.machine_id,
  ps.preventive_code,
  ps.preventive_label,
  ps.score,
  ps.status,
  ps.detected_at,
  ps.handled_at,
  ps.handled_by,
  -- Dénormalisation pour lisibilité (optionnel, à confirmer si tables existent)
  m.code AS machine_code,
  m.name AS machine_name
FROM preventive_suggestion ps
LEFT JOIN machine m ON ps.machine_id = m.id
ORDER BY ps.detected_at DESC;

-- ═══════════════════════════════════════════════════════════════════════════════
-- Notes de maintenance
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- ⚠️ Contrats Directus (à déclarer dans Directus après ce script) :
--
-- Collection : preventive_suggestion
--   Fields:
--     - id (UUID, primary, read-only)
--     - intervention_action_id (UUID, relation to intervention_action)
--     - machine_id (UUID, relation to machine)
--     - preventive_code (Text)
--     - preventive_label (Text)
--     - score (Integer)
--     - status (Dropdown: NEW | REVIEWED | ACCEPTED | REJECTED)
--     - detected_at (Datetime, read-only)
--     - handled_at (Datetime, nullable)
--     - handled_by (UUID, relation to directus_users, nullable)
--
-- Permissions :
--   Role "Technician":
--     - read (filter: own machines)
--   Role "Team Leader":
--     - read (all)
--     - update (status, handled_at, handled_by)
--   Role "Admin":
--     - full CRUD
--
-- ⚠️ Jamais permettre DELETE (conservation trace)
--
-- Requêtes API type :
--
--   GET /items/preventive_suggestion
--   ?filter[machine_id][_eq]=XXX
--   &filter[status][_eq]=NEW
--   &sort=-detected_at
--
--   PATCH /items/preventive_suggestion/{id}
--   { "status": "ACCEPTED", "handled_at": "now()", "handled_by": "..." }
--
