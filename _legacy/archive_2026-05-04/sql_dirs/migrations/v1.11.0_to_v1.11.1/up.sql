-- Migration v1.11.0 → v1.11.1 (UP)
-- detect_preventive_suggestions : passage à la logique "premier match only" + suppression SECURITY DEFINER
--
-- Changements :
--   - Suppression de SECURITY DEFINER (droit owner non requis)
--   - Suppression du compteur v_count_inserted (inutile sans multi-insert)
--   - Ajout EXIT après le premier match → une seule suggestion par action (contrainte UNIQUE intervention_action_id)
--   - Délimiteur $func$ pour cohérence interne

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
  -- Pas de description = pas d'analyse
  IF new.description IS NULL OR length(trim(new.description)) < 10 THEN
    RETURN new;
  END IF;

  v_description_lower := lower(new.description);

  -- Uniquement dépannage (DEP_*)
  SELECT sc.code
  INTO v_action_subcategory_code
  FROM action_subcategory sc
  WHERE sc.id = new.action_subcategory;

  IF v_action_subcategory_code IS NULL OR NOT v_action_subcategory_code LIKE 'DEP_%' THEN
    RETURN new;
  END IF;

  SELECT i.machine_id
  INTO v_machine_id
  FROM intervention i
  WHERE i.id = new.intervention_id;

  IF v_machine_id IS NULL THEN
    RETURN new;
  END IF;

  -- Boucle triée par poids DESC : on insère le premier match uniquement
  FOR v_rule IN
    SELECT pr.id, pr.keyword, pr.preventive_code, pr.preventive_label, pr.weight
    FROM preventive_rule pr
    WHERE pr.active = TRUE
    ORDER BY pr.weight DESC
  LOOP
    IF v_description_lower LIKE '%' || v_rule.keyword || '%' THEN
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

  RETURN new;
END;
$func$;
