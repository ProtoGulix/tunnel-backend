-- ============================================================================
-- preventive_v2_addendum_02.sql
-- ============================================================================
-- Addendum au module Maintenance Preventive v2 :
--   - Generation des validations de gamme rattachee a l'occurrence
--   - Suppression du trigger legacy de generation sur intervention_action
--   - Correction du controle de cloture (seules etapes obligatoires bloquantes)
--
-- @see gamme_step_validation.sql      (01_core)
-- @see preventive_occurrence.sql      (01_core)
-- @see trg_preventive_v2.sql          (05_triggers)
-- @see preventive_v2.sql              (04_preventive)
-- @see preventive_v2_addendum_01.sql  (04_preventive)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1) intervention_id nullable sur gamme_step_validation
-- ============================================================================

ALTER TABLE public.gamme_step_validation
    ALTER COLUMN intervention_id DROP NOT NULL;

-- ============================================================================
-- 2) Ajout occurrence_id + commentaire
-- ============================================================================

ALTER TABLE public.gamme_step_validation
    ADD COLUMN IF NOT EXISTS occurrence_id UUID
        REFERENCES public.preventive_occurrence (id) ON DELETE RESTRICT;

COMMENT ON COLUMN public.gamme_step_validation.occurrence_id IS
    'Occurrence preventive a l''origine de cette validation. Renseignee a la generation de l''occurrence, avant meme la creation de l''intervention.';

-- ============================================================================
-- 3) Remplacement de la contrainte UNIQUE
-- ============================================================================

ALTER TABLE public.gamme_step_validation
    DROP CONSTRAINT IF EXISTS gamme_step_validation_step_interv_key;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'gamme_step_validation_step_occurrence_key'
          AND conrelid = 'public.gamme_step_validation'::regclass
    ) THEN
        ALTER TABLE public.gamme_step_validation
            ADD CONSTRAINT gamme_step_validation_step_occurrence_key
            UNIQUE (step_id, occurrence_id);
    END IF;
END
$$;

-- ============================================================================
-- 4) Index occurrence_id
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_gamme_step_validation_occurrence_id
    ON public.gamme_step_validation (occurrence_id);

-- ============================================================================
-- 5) Suppression du trigger legacy de generation des validations
-- ============================================================================

DROP TRIGGER IF EXISTS trg_generate_gamme_validations
    ON public.intervention_action;

DROP FUNCTION IF EXISTS public.fn_generate_gamme_validations();
DROP FUNCTION IF EXISTS public.generate_gamme_validations();

-- ============================================================================
-- 6) Correction du trigger de cloture intervention
-- ============================================================================

DROP FUNCTION IF EXISTS public.fn_check_intervention_closable();

CREATE OR REPLACE FUNCTION public.check_intervention_closable()
RETURNS TRIGGER AS $$
DECLARE
    blocking_count INTEGER;
BEGIN
    -- Ne s'applique qu'a la transition vers 'ferme'
    IF NEW.status_actual != 'ferme' OR OLD.status_actual = 'ferme' THEN
        RETURN NEW;
    END IF;

    -- Ne s'applique qu'aux interventions liees a un plan preventif
    IF NEW.plan_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Compte uniquement les steps non optionnels encore en pending
    SELECT COUNT(*) INTO blocking_count
    FROM public.gamme_step_validation gsv
    JOIN public.preventive_plan_gamme_step pgs ON pgs.id = gsv.step_id
    WHERE gsv.intervention_id = NEW.id
      AND gsv.status = 'pending'
      AND pgs.optional = FALSE;

    IF blocking_count > 0 THEN
        RAISE EXCEPTION 'GAMME_INCOMPLETE: % etape(s) obligatoire(s) en attente de validation', blocking_count;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_intervention_closable
    ON public.intervention;

CREATE TRIGGER trg_check_intervention_closable
    BEFORE UPDATE ON public.intervention
    FOR EACH ROW
    EXECUTE FUNCTION public.check_intervention_closable();

-- ============================================================================
-- 7) Commentaire final intervention_id
-- ============================================================================

COMMENT ON COLUMN public.gamme_step_validation.intervention_id IS
    'Intervention liee a cette validation. NULL a la generation de l''occurrence, renseignee lors de l''acceptation de la DI.';

COMMIT;
