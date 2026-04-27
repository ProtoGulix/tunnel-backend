-- ============================================================================
-- trg_intervention_request.sql - Triggers module Demandes d'Intervention
-- ============================================================================
-- Fonctions et triggers pour :
--   - Génération du code DI-YYYY-NNNN
--   - Initialisation du statut via request_status_log
--   - Synchronisation statut ← log
--   - Traçage des transitions applicatives
--   - updated_at (convention Tunnel)
--
-- @see intervention_request.sql (01_core)
-- @see request_status_log.sql   (01_core)
-- @see request_status_ref.sql   (02_ref)
-- ============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- fn_generate_request_code : code DI-YYYY-NNNN (BEFORE INSERT)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.fn_generate_request_code()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_year TEXT := to_char(now(), 'YYYY');
    v_seq  INT;
BEGIN
    SELECT COUNT(*) + 1
    INTO v_seq
    FROM public.intervention_request
    WHERE code LIKE 'DI-' || v_year || '-%';

    NEW.code := 'DI-' || v_year || '-' || lpad(v_seq::TEXT, 4, '0');
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_request_code
    BEFORE INSERT ON public.intervention_request
    FOR EACH ROW EXECUTE FUNCTION public.fn_generate_request_code();

-- ─────────────────────────────────────────────────────────────────────────────
-- fn_init_request_status_log : init log statut (AFTER INSERT request)
-- ─────────────────────────────────────────────────────────────────────────────
-- Insère la première ligne du log {NULL → 'nouvelle'}.
-- Le flag app.skip_request_status_log empêche la boucle avec
-- trg_log_request_status_change pendant la mise à jour interne du statut.

CREATE OR REPLACE FUNCTION public.fn_init_request_status_log()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    PERFORM set_config('app.skip_request_status_log', 'true', true);

    INSERT INTO public.request_status_log (request_id, status_from, status_to, notes)
    VALUES (NEW.id, NULL, 'nouvelle', 'Création demande');

    PERFORM set_config('app.skip_request_status_log', 'false', true);
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_init_request_status_log
    AFTER INSERT ON public.intervention_request
    FOR EACH ROW EXECUTE FUNCTION public.fn_init_request_status_log();

-- ─────────────────────────────────────────────────────────────────────────────
-- fn_apply_request_status : synchronise statut depuis log (AFTER INSERT log)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.fn_apply_request_status()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    UPDATE public.intervention_request
    SET statut = NEW.status_to
    WHERE id = NEW.request_id;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_apply_request_status
    AFTER INSERT ON public.request_status_log
    FOR EACH ROW EXECUTE FUNCTION public.fn_apply_request_status();

-- ─────────────────────────────────────────────────────────────────────────────
-- fn_log_request_status_change : trace transitions (AFTER UPDATE statut)
-- ─────────────────────────────────────────────────────────────────────────────
-- Court-circuité via flag de session pendant l'initialisation interne.
-- Vérifie la cohérence status_from avant d'insérer dans le log.

CREATE OR REPLACE FUNCTION public.fn_log_request_status_change()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF current_setting('app.skip_request_status_log', true) = 'true' THEN
        RETURN NEW;
    END IF;

    IF NEW.statut IS DISTINCT FROM OLD.statut THEN
        IF OLD.statut IS DISTINCT FROM (
            SELECT status_to FROM public.request_status_log
            WHERE request_id = NEW.id
            ORDER BY date DESC
            LIMIT 1
        ) THEN
            RAISE EXCEPTION
                'Incohérence statut : statut actuel "%" ne correspond pas à la dernière entrée du log',
                OLD.statut;
        END IF;

        INSERT INTO public.request_status_log (request_id, status_from, status_to)
        VALUES (NEW.id, OLD.statut, NEW.statut);
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_log_request_status_change
    AFTER UPDATE OF statut ON public.intervention_request
    FOR EACH ROW EXECUTE FUNCTION public.fn_log_request_status_change();

-- ─────────────────────────────────────────────────────────────────────────────
-- updated_at — convention Tunnel (update_updated_at_column déjà définie dans le schéma)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_request_updated_at
    BEFORE UPDATE ON public.intervention_request
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();