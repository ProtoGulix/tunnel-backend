-- ============================================================================
-- preventive_v2.sql - Module Maintenance Préventive v2
-- ============================================================================
-- Nouvelles tables référentielles, transactionnelles et triggers pour la
-- gestion des plans de maintenance préventive avec gammes d'intervention.
--
-- @see machine.sql            (01_core)
-- @see intervention.sql       (01_core)
-- @see intervention_action.sql(01_core)
-- @see intervention_request.sql (01_core)
-- @see equipment_class.sql    (02_ref)
-- @see action_subcategory.sql (02_ref)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 02_ref — Table référentielle preventive_plan
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.preventive_plan (
    id                  UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    code                VARCHAR(50)  UNIQUE NOT NULL,   -- immuable, ex: PREV_CONV_MENS
    label               TEXT         NOT NULL,
    equipement_class_id UUID         REFERENCES public.equipement_class (id) ON DELETE RESTRICT,
    trigger_type        VARCHAR(20)  NOT NULL,          -- 'periodicity' ou 'hours'
    periodicity_days    INTEGER,                        -- NULL si trigger_type = 'hours'
    hours_threshold     INTEGER,                        -- NULL si trigger_type = 'periodicity'
    auto_accept         BOOLEAN      NOT NULL DEFAULT FALSE,
    active              BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT preventive_plan_trigger_type_check CHECK (
        (trigger_type = 'periodicity' AND periodicity_days IS NOT NULL)
        OR
        (trigger_type = 'hours' AND hours_threshold IS NOT NULL)
    )
);

COMMENT ON TABLE  public.preventive_plan                  IS 'Plans de maintenance préventive référentiels (périodicité ou seuil heures).';
COMMENT ON COLUMN public.preventive_plan.code             IS 'Code technique immuable du plan (ex : PREV_CONV_MENS).';
COMMENT ON COLUMN public.preventive_plan.trigger_type     IS 'Mode de déclenchement : ''periodicity'' (jours) ou ''hours'' (compteur heures).';
COMMENT ON COLUMN public.preventive_plan.periodicity_days IS 'Intervalle en jours — renseigné uniquement si trigger_type = ''periodicity''.';
COMMENT ON COLUMN public.preventive_plan.hours_threshold  IS 'Seuil compteur heures — renseigné uniquement si trigger_type = ''hours''.';
COMMENT ON COLUMN public.preventive_plan.auto_accept      IS 'Si TRUE, la génération d''occurrence crée directement une DI sans validation manuelle.';

-- ============================================================================
-- 02_ref — Table référentielle preventive_plan_gamme_step
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.preventive_plan_gamme_step (
    id          UUID     PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id     UUID     NOT NULL REFERENCES public.preventive_plan (id) ON DELETE CASCADE,
    label       TEXT     NOT NULL,
    sort_order  INTEGER  NOT NULL,
    optional    BOOLEAN  NOT NULL DEFAULT FALSE,

    CONSTRAINT preventive_plan_gamme_step_plan_sort_key UNIQUE (plan_id, sort_order)
);

COMMENT ON TABLE  public.preventive_plan_gamme_step             IS 'Étapes de la gamme d''un plan préventif (checklist ordonnée).';
COMMENT ON COLUMN public.preventive_plan_gamme_step.sort_order  IS 'Ordre d''affichage — unique par plan.';
COMMENT ON COLUMN public.preventive_plan_gamme_step.optional    IS 'Si TRUE, l''étape peut être ignorée sans bloquer la clôture.';

-- ============================================================================
-- 01_core — Table transactionnelle preventive_occurrence
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.preventive_occurrence (
    id               UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id          UUID          NOT NULL REFERENCES public.preventive_plan (id) ON DELETE RESTRICT,
    machine_id       UUID          NOT NULL REFERENCES public.machine (id) ON DELETE RESTRICT,
    scheduled_date   DATE          NOT NULL,
    triggered_at     TIMESTAMPTZ,
    hours_at_trigger NUMERIC(10,2),                 -- snapshot compteur heures au déclenchement
    di_id            UUID          REFERENCES public.intervention_request (id) ON DELETE SET NULL,
    intervention_id  UUID          REFERENCES public.intervention (id) ON DELETE SET NULL,
    status           VARCHAR(20)   NOT NULL DEFAULT 'pending', -- 'pending','generated','done','skipped'
    skip_reason      TEXT,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT preventive_occurrence_plan_machine_date_key UNIQUE (plan_id, machine_id, scheduled_date),
    CONSTRAINT preventive_occurrence_skip_reason_check CHECK (
        (status != 'skipped') OR (skip_reason IS NOT NULL)
    )
);

COMMENT ON TABLE  public.preventive_occurrence                  IS 'Occurrences planifiées d''un plan préventif pour une machine donnée.';
COMMENT ON COLUMN public.preventive_occurrence.hours_at_trigger IS 'Snapshot du compteur heures machine au moment du déclenchement.';
COMMENT ON COLUMN public.preventive_occurrence.di_id            IS 'Demande d''intervention générée pour cette occurrence (nullable).';
COMMENT ON COLUMN public.preventive_occurrence.status           IS 'État de l''occurrence : pending | generated | done | skipped.';
COMMENT ON COLUMN public.preventive_occurrence.skip_reason      IS 'Obligatoire si status = ''skipped''.';

-- ============================================================================
-- 01_core — Table transactionnelle gamme_step_validation
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.gamme_step_validation (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_id         UUID        NOT NULL REFERENCES public.preventive_plan_gamme_step (id) ON DELETE RESTRICT,
    intervention_id UUID        NOT NULL REFERENCES public.intervention (id) ON DELETE RESTRICT,
    action_id       UUID        REFERENCES public.intervention_action (id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending','validated','skipped'
    skip_reason     TEXT,
    validated_at    TIMESTAMPTZ,
    validated_by    UUID,   -- référence utilisateur externe, pas de FK

    CONSTRAINT gamme_step_validation_step_interv_key UNIQUE (step_id, intervention_id),
    CONSTRAINT gamme_step_validation_skip_reason_check CHECK (
        (status != 'skipped') OR (skip_reason IS NOT NULL)
    )
);

COMMENT ON TABLE  public.gamme_step_validation              IS 'Validation de chaque étape de gamme pour une intervention préventive.';
COMMENT ON COLUMN public.gamme_step_validation.action_id    IS 'Action d''intervention liée à cette étape (nullable).';
COMMENT ON COLUMN public.gamme_step_validation.validated_by IS 'UUID de l''utilisateur ayant validé (référence externe, sans FK).';
COMMENT ON COLUMN public.gamme_step_validation.skip_reason  IS 'Obligatoire si status = ''skipped''.';

-- ============================================================================
-- 01_core — Table transactionnelle machine_hours
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.machine_hours (
    machine_id  UUID          PRIMARY KEY REFERENCES public.machine (id) ON DELETE CASCADE,
    hours_total NUMERIC(10,2) NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.machine_hours             IS 'Compteur total heures par machine, mis à jour par trigger depuis intervention_action.';
COMMENT ON COLUMN public.machine_hours.hours_total IS 'Cumul des time_spent de toutes les actions liées à la machine.';

-- ============================================================================
-- 01_core — ALTER TABLE intervention : ajout plan_id
-- ============================================================================

ALTER TABLE public.intervention
    ADD COLUMN IF NOT EXISTS plan_id UUID
        REFERENCES public.preventive_plan (id) ON DELETE SET NULL;

COMMENT ON COLUMN public.intervention.plan_id IS 'Plan préventif associé à l''intervention (NULL pour interventions correctives).';

-- ============================================================================
-- Index
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_prev_occurrence_plan_id
    ON public.preventive_occurrence (plan_id);

CREATE INDEX IF NOT EXISTS idx_prev_occurrence_machine_id
    ON public.preventive_occurrence (machine_id);

CREATE INDEX IF NOT EXISTS idx_prev_occurrence_status
    ON public.preventive_occurrence (status);

CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_intervention_id
    ON public.gamme_step_validation (intervention_id);

CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_action_id
    ON public.gamme_step_validation (action_id);

CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_status
    ON public.gamme_step_validation (status);

-- ============================================================================
-- 05_triggers — fn_machine_hours_update / trg_machine_hours_update
-- AFTER INSERT OR UPDATE OF time_spent ON intervention_action
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
-- 05_triggers — fn_generate_gamme_validations / trg_generate_gamme_validations
-- AFTER INSERT ON intervention_action
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
    -- Vérifie que la sous-catégorie de l'action commence par PREV_
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

    -- Pas de plan → rien à faire
    IF v_plan_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Génère une entrée de validation pour chaque étape de la gamme
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
-- 05_triggers — fn_check_intervention_closable / trg_check_intervention_closable
-- BEFORE UPDATE ON intervention
-- ============================================================================

CREATE OR REPLACE FUNCTION public.fn_check_intervention_closable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_pending_count INT;
BEGIN
    -- Se déclenche uniquement lors de la fermeture
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
-- 05_triggers — fn_updated_at_preventive_plan / trg_updated_at_preventive_plan
-- BEFORE UPDATE ON preventive_plan
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

-- ============================================================================

COMMIT;
