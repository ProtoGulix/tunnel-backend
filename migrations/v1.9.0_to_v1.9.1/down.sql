-- Migration v1.9.0 -> v1.9.1 (DOWN)
-- Restauration de l'ancienne version de generate_intervention_code() (sans validations NULL)

CREATE OR REPLACE FUNCTION public.generate_intervention_code()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
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

  NEW.code := machine_code || '-' || NEW.type_inter || '-' || today || '-' || NEW.tech_initials;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_interv_code ON public.intervention;

CREATE TRIGGER trg_interv_code
  BEFORE INSERT ON public.intervention
  FOR EACH ROW
  EXECUTE FUNCTION public.generate_intervention_code();
