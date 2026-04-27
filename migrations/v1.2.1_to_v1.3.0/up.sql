-- Migration v1.2.1 -> v1.3.0 (UP)
-- Remplacement de complexity_anotation (JSON) par complexity_factor (FK)
-- ============================================================================
-- Cette migration remplace le champ JSON complexity_anotation par une FK
-- directe vers complexity_factor.
-- ============================================================================

-- 1. Ajouter la nouvelle colonne FK
ALTER TABLE public.intervention_action
ADD COLUMN IF NOT EXISTS complexity_factor VARCHAR(255);

-- 2. Ajouter la contrainte FK
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_intervention_action_complexity_factor'
    ) THEN
        ALTER TABLE public.intervention_action
            ADD CONSTRAINT fk_intervention_action_complexity_factor
            FOREIGN KEY (complexity_factor)
            REFERENCES public.complexity_factor(code)
            ON DELETE SET NULL;
    END IF;
END $$;

-- 3. Index pour les requêtes
CREATE INDEX IF NOT EXISTS idx_intervention_action_complexity_factor ON public.intervention_action (complexity_factor);

-- 4. Commentaire
COMMENT ON COLUMN public.intervention_action.complexity_factor IS 'Référence vers le facteur de complexité (remplace complexity_anotation)';

-- Note: La migration des données JSON vers FK est effectuée par migrate.py
-- La suppression de complexity_anotation sera faite dans une migration ultérieure