-- ============================================================================
-- trg_sync_status.sql - Synchronisation statut depuis log + cascade préventive
-- ============================================================================
-- AFTER INSERT ON intervention_status_log :
--   1. Synchronise intervention.status_actual depuis le status_to du log
--   2. Si fermeture (code = 'ferme') :
--      - passe preventive_occurrence.status à 'completed'
--      - passe intervention_request.statut à 'cloturee' si encore 'acceptee'
--
-- Remplace l'ancien trigger trg_sync_status_from_log (supprimé — migration i4d5e6f7a8b9)
-- qui ne faisait que (1) sans la cascade préventive.
--
-- @see intervention.sql              (01_core)
-- @see intervention_status_log.sql   (01_core)
-- @see preventive_occurrence.sql     (01_core)
-- @see intervention_request.sql      (01_core)
-- ============================================================================

-- Supprimer l'ancien trigger redondant si encore présent
DROP TRIGGER IF EXISTS trg_sync_status_from_log ON public.intervention_status_log;
DROP FUNCTION IF EXISTS public.trg_sync_status_from_log();

CREATE OR REPLACE FUNCTION public.fn_sync_status_log_to_intervention()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_status_code    TEXT;
    v_occurrence_id  UUID;
    v_request_id     UUID;
    v_request_statut TEXT;
BEGIN
    -- 1. Mettre à jour intervention.status_actual avec le nouveau statut
    UPDATE public.intervention
    SET status_actual = NEW.status_to
    WHERE id = NEW.intervention_id;

    -- 2. Résoudre le code du statut cible
    SELECT code INTO v_status_code
    FROM public.intervention_status_ref
    WHERE id = NEW.status_to;

    -- 3. Si fermeture : propager sur l'occurrence préventive + la demande
    IF v_status_code = 'ferme' THEN

        SELECT id INTO v_occurrence_id
        FROM public.preventive_occurrence
        WHERE intervention_id = NEW.intervention_id
        LIMIT 1;

        IF v_occurrence_id IS NOT NULL THEN
            UPDATE public.preventive_occurrence
            SET status = 'completed'
            WHERE id = v_occurrence_id;
        END IF;

        SELECT id, statut INTO v_request_id, v_request_statut
        FROM public.intervention_request
        WHERE intervention_id = NEW.intervention_id
          AND statut = 'acceptee'
        LIMIT 1;

        IF v_request_id IS NOT NULL THEN
            UPDATE public.intervention_request
            SET statut = 'cloturee'
            WHERE id = v_request_id;

            INSERT INTO public.request_status_log
                (request_id, status_from, status_to, changed_by, notes)
            VALUES (
                v_request_id,
                v_request_statut,
                'cloturee',
                NULL,
                'Clôture automatique suite à la fermeture de l''intervention (via log de statut)'
            );
        END IF;

    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.fn_sync_status_log_to_intervention() IS
    'Synchronise status_actual depuis le log ET propage la clôture sur l''occurrence préventive et la demande liée.';

DROP TRIGGER IF EXISTS trg_sync_status_log_to_intervention ON public.intervention_status_log;

CREATE TRIGGER trg_sync_status_log_to_intervention
    AFTER INSERT ON public.intervention_status_log
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_sync_status_log_to_intervention();

