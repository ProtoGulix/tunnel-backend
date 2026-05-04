-- ============================================================================
-- preventive_v2_addendum_01.sql
-- ============================================================================
-- Addendum au module Maintenance Préventive v2 :
--   - is_system        : marque une DI créée automatiquement par le système
--   - suggested_type_inter : type d'intervention suggéré à la création de DI
--
-- Valeurs de suggested_type_inter issues de api/constants.py (INTERVENTION_TYPES) :
--   CUR, PRE, REA, BAT, PRO, COF, PIL, MES
--
-- @see intervention_request.sql (01_core)
-- @see preventive_v2.sql        (04_preventive)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. Nouvelles colonnes sur intervention_request
-- ============================================================================

ALTER TABLE public.intervention_request
    ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS suggested_type_inter VARCHAR(255);

-- ============================================================================
-- 2. Contrainte CHECK sur suggested_type_inter
--    Valeurs capturées depuis api/constants.INTERVENTION_TYPE_IDS
-- ============================================================================

ALTER TABLE public.intervention_request
    ADD CONSTRAINT IF NOT EXISTS chk_suggested_type_inter
    CHECK (
        suggested_type_inter IS NULL
        OR suggested_type_inter IN ('CUR', 'PRE', 'REA', 'BAT', 'PRO', 'COF', 'PIL', 'MES')
    );

-- ============================================================================
-- 3. Index filtré sur is_system
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_intervention_request_is_system
    ON public.intervention_request (is_system)
    WHERE is_system = TRUE;

-- ============================================================================
-- 4. Commentaires
-- ============================================================================

COMMENT ON COLUMN public.intervention_request.is_system IS
    'TRUE si la DI a été créée automatiquement par le système (scheduler préventif ou autre source non humaine). Governe les règles de transition : une DI système ne peut pas être rejetée sans rôle RESP.';

COMMENT ON COLUMN public.intervention_request.suggested_type_inter IS
    'Type d''intervention suggéré à la création. Utilisé comme valeur par défaut lors de la transition acceptee si le payload ne fournit pas de type_inter. Valeur forcée et non écrasable si is_system = TRUE et rôle insuffisant.';

COMMIT;
