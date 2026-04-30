-- Migration v1.2.1 -> v1.3.0 (DOWN)
-- Rollback: suppression de complexity_factor
-- ============================================================================

-- 1. Supprimer la contrainte FK
ALTER TABLE public.intervention_action
DROP CONSTRAINT IF EXISTS fk_intervention_action_complexity_factor;

-- 2. Supprimer l'index
DROP INDEX IF EXISTS idx_intervention_action_complexity_factor;

-- 3. Supprimer la colonne
ALTER TABLE public.intervention_action
DROP COLUMN IF EXISTS complexity_factor;

-- Note: Les complexity_factor insérés ne sont pas supprimés (données de référence)
-- Note: complexity_anotation est conservé avec ses données d'origine