-- Migration v1.11.0 → v1.11.1 (DOWN)
-- Restaure detect_preventive_suggestions dans sa version v1.11.0 :
--   - SECURITY DEFINER réactivé
--   - Compteur v_count_inserted rétabli
--   - Boucle complète (tous les matchs, pas de EXIT)
--   - Délimiteur $$

CREATE OR REPLACE FUNCTION detect_preventive_suggestions()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_rule RECORD;
  v_machine_id UUID;
  v_description_lower TEXT;
  v_action_subcategory_code TEXT;
  v_count_inserted INT := 0;
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

  SELECT sc.code
  INTO v_action_subcategory_code
  FROM action_subcategory sc
  WHERE sc.id = new.action_subcategory;

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

  IF v_machine_id IS NULL THEN
    RETURN new;
  END IF;

  -- ─────────────────────────────────────────────────────────────────
  -- 4. Boucle de détection : tous les matchs
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
    IF (
      v_description_lower LIKE '%' || v_rule.keyword || '%'
    ) THEN
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

      v_count_inserted := v_count_inserted + 1;
    END IF;
  END LOOP;

  RETURN new;
END;
$$;
