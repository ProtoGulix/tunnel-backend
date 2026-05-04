-- ============================================================================
-- trg_log_status.sql - Historisation changements statut interventions
-- ============================================================================
-- Enregistre automatiquement tous les changements de statut
-- 2 triggers :
--   - trg_init_status_log : Création initiale (statut "ouvert")
--   - trg_log_status_change : Changements statut ultérieurs
--
-- @see intervention.sql (01_core)
-- @see intervention_status_log.sql (01_core)
-- ============================================================================

-- ============================================================================
-- 1. Trigger initialisation statut (INSERT intervention)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.trg_init_status_log()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    new_log_id UUID := uuid_generate_v4();
BEGIN
    -- Initialise statut à "ouvert"
    UPDATE public.intervention
    SET status_actual = 'ouvert'
    WHERE id = NEW.id;

    -- Crée log initial
    INSERT INTO public.intervention_status_log (
        id,
        intervention_id,
        status_from,
        status_to,
        date,
        technician_id,
        notes
    )
    VALUES (
        new_log_id,
        NEW.id,
        NULL, -- Pas de statut précédent
        'ouvert',
        NOW(),
        NULL,
        'Création intervention'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_init_status_log
  AFTER INSERT ON public.intervention
  FOR EACH ROW
  EXECUTE FUNCTION public.trg_init_status_log();

-- ============================================================================
-- 2. Trigger changement statut (UPDATE intervention)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.trg_log_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    new_log_id UUID := uuid_generate_v4();
BEGIN
    -- ⚠️ Ignore les créations (OLD.status_actual IS NULL)
    IF OLD.status_actual IS NOT NULL AND NEW.status_actual IS DISTINCT FROM OLD.status_actual THEN
        INSERT INTO public.intervention_status_log (
            id,
            intervention_id,
            status_from,
            status_to,
            date,
            technician_id,
            notes
        )
        VALUES (
            new_log_id,
            NEW.id,
            OLD.status_actual,
            NEW.status_actual,
            NOW(),
            NEW.updated_by,
            'Changement statut automatique'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_log_status_change
  AFTER UPDATE ON public.intervention
  FOR EACH ROW
  WHEN (OLD.status_actual IS DISTINCT FROM NEW.status_actual)
  EXECUTE FUNCTION public.trg_log_status_change();

-- Commentaires
COMMENT ON FUNCTION public.trg_init_status_log() IS 'Initialise log statut à la création intervention';
COMMENT ON FUNCTION public.trg_log_status_change() IS 'Enregistre changements statut intervention';
