-- ============================================================================
-- trg_preventive_v2.sql - Triggers module Maintenance Préventive v2
-- ============================================================================
-- 4 triggers pour le module préventif v2 :
--   1. trg_machine_hours_update        — AFTER INSERT OR UPDATE OF time_spent
--                                        ON intervention_action
--   2. trg_generate_gamme_validations  — AFTER INSERT ON intervention_action
--   3. trg_check_intervention_closable — BEFORE UPDATE ON intervention
--   4. trg_updated_at_preventive_plan  — BEFORE UPDATE ON preventive_plan
--
-- @see machine_hours.sql              (01_core)
-- @see gamme_step_validation.sql      (01_core)
-- @see preventive_plan.sql            (02_ref)
-- @see preventive_plan_gamme_step.sql (02_ref)
-- @see intervention_action.sql        (01_core)
-- @see intervention.sql               (01_core)
-- ============================================================================

-- ============================================================================
-- 1. fn_machine_hours_update / trg_machine_hours_update
--    Maintient le compteur heures machine (INSERT ou UPDATE de time_spent)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.fn_machine_hours_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_machine_id UUID;
    v_delta      NUMERIC(10,2);
BEGIN
    -- Récupère la machine via l'intervention parente
    SELECT i.machine_id INTO v_machine_id
    FROM public.intervention i
    WHERE i.id = NEW.intervention_id;

    IF v_machine_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Delta : INSERT → delta = nouveau time_spent ; UPDATE → delta = différence
    IF TG_OP = 'INSERT' THEN
        v_delta := COALESCE(NEW.time_spent, 0);
    ELSE
        v_delta := COALESCE(NEW.time_spent, 0) - COALESCE(OLD.time_spent, 0);
    END IF;

    -- Upsert du compteur — jamais inférieur à 0
    INSERT INTO public.machine_hours (machine_id, hours_total, updated_at)
    VALUES (v_machine_id, GREATEST(0, v_delta), NOW())
    ON CONFLICT (machine_id) DO UPDATE
        SET hours_total = GREATEST(0, public.machine_hours.hours_total + v_delta),
            updated_at  = NOW();

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.fn_machine_hours_update() IS 'Met à jour le compteur heures machine après chaque action (INSERT ou UPDATE de time_spent).';

DROP TRIGGER IF EXISTS trg_machine_hours_update ON public.intervention_action;

CREATE TRIGGER trg_machine_hours_update
    AFTER INSERT OR UPDATE OF time_spent ON public.intervention_action
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_machine_hours_update();

-- ============================================================================
-- 2. fn_generate_gamme_validations / trg_generate_gamme_validations
--    Génère les entrées gamme_step_validation à la création d'une action PREV_
-- ============================================================================

CREATE OR REPLACE FUNCTION public.fn_generate_gamme_validations()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_subcategory_code TEXT;
    v_plan_id          UUID;
    v_step             RECORD;
BEGIN
    -- Vérifie que la sous-catégorie commence par PREV_
    SELECT sc.code INTO v_subcategory_code
    FROM public.action_subcategory sc
    WHERE sc.id = NEW.action_subcategory;

    IF v_subcategory_code IS NULL OR v_subcategory_code NOT LIKE 'PREV_%' THEN
        RETURN NEW;
    END IF;

    -- Récupère le plan préventif de l'intervention parente
    SELECT i.plan_id INTO v_plan_id
    FROM public.intervention i
    WHERE i.id = NEW.intervention_id;

    IF v_plan_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Génère une validation pour chaque étape de la gamme (idempotent)
    FOR v_step IN
        SELECT id
        FROM public.preventive_plan_gamme_step
        WHERE plan_id = v_plan_id
        ORDER BY sort_order
    LOOP
        INSERT INTO public.gamme_step_validation (
            step_id,
            intervention_id,
            action_id,
            status
        )
        VALUES (
            v_step.id,
            NEW.intervention_id,
            NEW.id,
            'pending'
        )
        ON CONFLICT (step_id, intervention_id) DO NOTHING;
    END LOOP;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.fn_generate_gamme_validations() IS 'Génère automatiquement les validations de gamme lors de la création d''une action PREV_.';

DROP TRIGGER IF EXISTS trg_generate_gamme_validations ON public.intervention_action;

CREATE TRIGGER trg_generate_gamme_validations
    AFTER INSERT ON public.intervention_action
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_generate_gamme_validations();

-- ============================================================================
-- 3. fn_check_intervention_closable / trg_check_intervention_closable
--    Bloque la fermeture si des étapes de gamme sont en attente
-- ============================================================================

CREATE OR REPLACE FUNCTION public.fn_check_intervention_closable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_pending_count INT;
BEGIN
    -- Se déclenche uniquement lors du passage au statut 'ferme'
    IF NEW.status_actual = 'ferme' AND OLD.status_actual IS DISTINCT FROM 'ferme' THEN

        -- Vérifie seulement les interventions liées à un plan préventif
        IF NEW.plan_id IS NOT NULL THEN
            SELECT COUNT(*) INTO v_pending_count
            FROM public.gamme_step_validation
            WHERE intervention_id = NEW.id
              AND status = 'pending';

            IF v_pending_count > 0 THEN
                RAISE EXCEPTION 'GAMME_INCOMPLETE: % étape(s) en attente de validation', v_pending_count;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.fn_check_intervention_closable() IS 'Bloque la fermeture d''une intervention préventive si des étapes de gamme sont en attente (GAMME_INCOMPLETE).';

DROP TRIGGER IF EXISTS trg_check_intervention_closable ON public.intervention;

CREATE TRIGGER trg_check_intervention_closable
    BEFORE UPDATE ON public.intervention
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_check_intervention_closable();

-- ============================================================================
-- 4. fn_updated_at_preventive_plan / trg_updated_at_preventive_plan
--    Met à jour updated_at automatiquement sur preventive_plan
-- ============================================================================

CREATE OR REPLACE FUNCTION public.fn_updated_at_preventive_plan()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.fn_updated_at_preventive_plan() IS 'Met à jour automatiquement updated_at sur preventive_plan.';

DROP TRIGGER IF EXISTS trg_updated_at_preventive_plan ON public.preventive_plan;

CREATE TRIGGER trg_updated_at_preventive_plan
    BEFORE UPDATE ON public.preventive_plan
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_updated_at_preventive_plan();
