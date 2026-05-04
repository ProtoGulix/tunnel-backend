-- Migration v1.11.0 -> v1.10.0 (DOWN)
-- Rollback : suppression trigger + colonnes horaires + restauration NOT NULL time_spent

-- ═══════════════════════════════════════════════════════════════
-- 1. TRIGGER & FONCTION
-- ═══════════════════════════════════════════════════════════════

DROP TRIGGER IF EXISTS trg_compute_action_time ON public.intervention_action;

DROP FUNCTION IF EXISTS public.fn_compute_action_time ();

-- ═══════════════════════════════════════════════════════════════
-- 2. COLONNES HORAIRES
-- ═══════════════════════════════════════════════════════════════

ALTER TABLE public.intervention_action
DROP COLUMN IF EXISTS action_start,
DROP COLUMN IF EXISTS action_end;

-- ═══════════════════════════════════════════════════════════════
-- 3. Restauration NOT NULL sur time_spent
-- ═══════════════════════════════════════════════════════════════

UPDATE public.intervention_action
SET
    time_spent = 0
WHERE
    time_spent IS NULL;

ALTER TABLE public.intervention_action
ALTER COLUMN time_spent
SET NOT NULL;