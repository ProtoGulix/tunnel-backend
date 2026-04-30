-- ============================================================================
-- trg_interv_code.sql - Génération automatique code intervention
-- ============================================================================
-- Génère code unique intervention : MACHINE-TYPE-YYYYMMDD-INITIALES
-- Exemple : CONV01-PREV-20241228-JD
--
-- @see intervention.sql (01_core)
-- @see machine.sql (01_core)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.generate_intervention_code()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
DECLARE
  machine_code TEXT;
  today TEXT := to_char(current_date, 'YYYYMMDD');
BEGIN
  SELECT code INTO machine_code
  FROM machine
  WHERE id = NEW.machine_id;

  IF machine_code IS NULL THEN
    RAISE EXCEPTION 'Machine % inconnue', NEW.machine_id;
  END IF;

  IF NEW.type_inter IS NULL THEN
    RAISE EXCEPTION 'type_inter est requis pour générer le code intervention';
  END IF;

  IF NEW.tech_initials IS NULL THEN
    RAISE EXCEPTION 'tech_initials est requis pour générer le code intervention';
  END IF;

  NEW.code := machine_code || '-' || NEW.type_inter || '-' || today || '-' || NEW.tech_initials;

  RETURN NEW;
END;
$BODY$;

ALTER FUNCTION public.generate_intervention_code() OWNER TO directus;

DROP TRIGGER IF EXISTS trg_interv_code ON public.intervention;

CREATE TRIGGER trg_interv_code
  BEFORE INSERT ON public.intervention
  FOR EACH ROW
  EXECUTE FUNCTION public.generate_intervention_code();

-- Commentaires
COMMENT ON FUNCTION public.generate_intervention_code() IS 'Génère code intervention automatiquement (valide machine, type_inter et tech_initials)';
