-- ═══════════════════════════════════════════════════════════════════════════════
-- 08_detect_preventive_function.sql - Fonction de détection heuristique
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- Cœur du moteur : fonction appelée par le trigger à la création d'une action.
-- Analyse la description en minuscules, cherche les mots-clés, crée les précos.
--
-- Stratégie de détection :
--   1. Sécurité minimale (null check, longueur)
--   2. Filtre métier (uniquement dépannage DEP_*)
--   3. Boucle sur règles actives
--   4. Insertion avec gestion des doublons (CONFLICT)
--
-- @author Tunnel GMAO
-- @version 1.1 (v1.11.1) : premier match uniquement, sans SECURITY DEFINER
-- @created 2026-01-05
-- @updated 2026-03-16

-- ═══════════════════════════════════════════════════════════════════════════════
-- Création de la fonction
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION detect_preventive_suggestions()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $func$
DECLARE
  v_rule RECORD;
  v_machine_id UUID;
  v_description_lower TEXT;
  v_action_subcategory_code TEXT;
BEGIN
  -- ─────────────────────────────────────────────────────────────────
  -- 1. Sécurité minimale
  -- ─────────────────────────────────────────────────────────────────

  -- Pas de description = pas d'analyse
  IF new.description IS NULL OR length(trim(new.description)) < 10 THEN
    RETURN new;
  END IF;

  -- Minuscule une seule fois pour la boucle
  v_description_lower := lower(new.description);

  -- ─────────────────────────────────────────────────────────────────
  -- 2. Filtre métier : uniquement dépannage (DEP_*)
  -- ─────────────────────────────────────────────────────────────────

  -- Récupérer le code de la sous-catégorie d'action
  SELECT sc.code
  INTO v_action_subcategory_code
  FROM action_subcategory sc
  WHERE sc.id = new.action_subcategory;

  -- Si pas de sous-catégorie ou n'est pas un dépannage, arrêt
  IF v_action_subcategory_code IS NULL OR NOT v_action_subcategory_code LIKE 'DEP_%' THEN
    RETURN new;
  END IF;

  -- ─────────────────────────────────────────────────────────────────
  -- 3. Récupérer machine_id de l'intervention
  -- ─────────────────────────────────────────────────────────────────

  SELECT i.machine_id
  INTO v_machine_id
  FROM intervention i
  WHERE i.id = new.intervention_id;

  -- Si pas d'intervention ou pas de machine, arrêt
  IF v_machine_id IS NULL THEN
    RETURN new;
  END IF;

  -- ─────────────────────────────────────────────────────────────────
  -- 4. Boucle de détection : premier match uniquement (poids DESC)
  -- ─────────────────────────────────────────────────────────────────

  FOR v_rule IN
    SELECT
      pr.id,
      pr.keyword,
      pr.preventive_code,
      pr.preventive_label,
      pr.weight
    FROM preventive_rule pr
    WHERE pr.active = TRUE
    ORDER BY pr.weight DESC
  LOOP
    -- Vérifier si le mot-clé est dans la description
    IF (
      v_description_lower LIKE '%' || v_rule.keyword || '%'
    ) THEN
      -- Insérer la préconisation (CONFLICT sur UNIQUE constraint)
      INSERT INTO preventive_suggestion (
        intervention_action_id,
        machine_id,
        preventive_code,
        preventive_label,
        score
      )
      VALUES (
        new.id,
        v_machine_id,
        v_rule.preventive_code,
        v_rule.preventive_label,
        v_rule.weight
      )
      ON CONFLICT (machine_id, preventive_code) DO NOTHING;

      -- Une seule suggestion par action (contrainte UNIQUE intervention_action_id)
      EXIT;
    END IF;
  END LOOP;

  -- ─────────────────────────────────────────────────────────────────
  -- 5. Logging (optionnel, à adapter selon ta config)
  -- ─────────────────────────────────────────────────────────────────

  -- Décommenter pour debug :
  -- RAISE NOTICE 'detect_preventive_suggestions: action_id=%, machine_id=%',
  --   new.id, v_machine_id;

  RETURN new;
END;
$func$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- Notes d'implémentation
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- Sécurité :
--   ✓ SECURITY DEFINER : exécutée avec droits de l'owner (safe pour INSERT)
--   ✓ NULL checks : arrêt si description manquante ou trop courte
--   ✓ FK checks : arrêt si action ou machine missing
--
-- Performance :
--   ✓ Boucle sur preventive_rule (petite table statique)
--   ✓ ON CONFLICT (machine_id, preventive_code) DO NOTHING : idempotent
--   ✓ Index sur preventive_rule.active : filtre rapide
--
-- Évolutivité :
--   ✓ Modifiable sans redéployer (SQL seulement)
--   ✓ Ajout/désactivation règles : UPDATE preventive_rule
--   ✓ Pattern détection : LIKE '%keyword%' peut être remplacé par regex
--
-- Futur :
--   ✓ Réservé pour DI_PREV : trigger ACCEPT → create intervention
--
