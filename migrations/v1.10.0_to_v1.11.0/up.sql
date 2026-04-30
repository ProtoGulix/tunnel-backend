-- Migration v1.10.0 -> v1.11.0 (UP)
-- intervention_action : ajout bornes horaires + trigger de calcul/validation time_spent

-- ═══════════════════════════════════════════════════════════════
-- 1. NOUVELLES COLONNES
-- ═══════════════════════════════════════════════════════════════

ALTER TABLE public.intervention_action
ADD COLUMN IF NOT EXISTS action_start TIME DEFAULT NULL,
ADD COLUMN IF NOT EXISTS action_end TIME DEFAULT NULL;

COMMENT ON COLUMN public.intervention_action.action_start IS 'Heure de début (multiple de 15 min) ; exclusif avec time_spent direct';

COMMENT ON COLUMN public.intervention_action.action_end IS 'Heure de fin (multiple de 15 min) ; exclusif avec time_spent direct';

-- ═══════════════════════════════════════════════════════════════
-- 2. time_spent : retrait du NOT NULL (les deux modes sont acceptés)
-- ═══════════════════════════════════════════════════════════════

ALTER TABLE public.intervention_action
ALTER COLUMN time_spent
DROP NOT NULL;

-- ═══════════════════════════════════════════════════════════════
-- 3. FONCTION + TRIGGER fn_compute_action_time
-- ═══════════════════════════════════════════════════════════════
-- Deux modes exclusifs :
--   Mode bornes  : action_start + action_end → time_spent calculé automatiquement
--   Mode direct  : time_spent fourni, doit être un multiple de 0.25h

CREATE OR REPLACE FUNCTION public.fn_compute_action_time()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    has_bounds BOOLEAN := (NEW.action_start IS NOT NULL AND NEW.action_end IS NOT NULL);
    has_time   BOOLEAN := (NEW.time_spent IS NOT NULL);
BEGIN
    -- Ambiguïté : les deux modes fournis ensemble
    IF has_bounds AND has_time THEN
        RAISE EXCEPTION 'Ambiguïté : fournir soit les bornes horaires soit time_spent, pas les deux';
    END IF;

    -- Aucun mode fourni
    IF NOT has_bounds AND NOT has_time THEN
        RAISE EXCEPTION 'time_spent ou les bornes action_start/action_end sont requis';
    END IF;

    -- Mode bornes : validation + calcul time_spent
    IF has_bounds THEN
        IF EXTRACT(MINUTE FROM NEW.action_start) NOT IN (0, 15, 30, 45) THEN
            RAISE EXCEPTION 'action_start doit être un multiple de 15 minutes';
        END IF;
        IF EXTRACT(MINUTE FROM NEW.action_end) NOT IN (0, 15, 30, 45) THEN
            RAISE EXCEPTION 'action_end doit être un multiple de 15 minutes';
        END IF;
        IF NEW.action_end <= NEW.action_start THEN
            RAISE EXCEPTION 'action_end doit être postérieur à action_start';
        END IF;
        NEW.time_spent := EXTRACT(EPOCH FROM (NEW.action_end - NEW.action_start)) / 3600.0;
    END IF;

    -- Mode direct : validation multiple de 0.25h
    IF has_time THEN
        IF (NEW.time_spent * 4) <> FLOOR(NEW.time_spent * 4) THEN
            RAISE EXCEPTION 'time_spent doit être un multiple de 0.25';
        END IF;
        IF NEW.time_spent < 0.25 THEN
            RAISE EXCEPTION 'time_spent minimum est 0.25h';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_compute_action_time
    BEFORE INSERT OR UPDATE ON public.intervention_action
    FOR EACH ROW EXECUTE FUNCTION public.fn_compute_action_time();