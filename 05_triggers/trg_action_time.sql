-- ============================================================================
-- trg_action_time.sql - Validation et calcul du temps d'action
-- ============================================================================
-- Deux modes exclusifs pour renseigner le temps d'une action :
--
--   Mode bornes  : action_start + action_end fournis
--                  → time_spent calculé automatiquement
--                  → Les deux bornes doivent être des multiples de 15 min
--                  → action_end doit être postérieur à action_start
--
--   Mode direct  : time_spent fourni directement
--                  → Doit être un multiple de 0.25h (quart d'heure)
--                  → Minimum 0.25h
--
-- Les deux modes sont mutuellement exclusifs.
--
-- @see intervention_action.sql (01_core)
-- ============================================================================

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