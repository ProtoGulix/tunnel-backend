-- Migration v1.5.0 -> v1.6.0 (UP)
-- Suppression des colonnes redondantes dans purchase_request

-- ============================================================================
-- Contexte
-- La table purchase_request contient trois doublons issus d'itérations
-- successives du schéma :
--   • requester_name  → doublon de requested_by  (requested_by est utilisé)
--   • quantity_requested → doublon de quantity    (quantity porte le NOT NULL + CHECK)
--   • urgent (boolean) → doublon de urgency       (urgency est plus précis)
-- ============================================================================

-- ============================================================================
-- 1. Sécurité : récupérer les données de requester_name vers requested_by
--    au cas où certaines lignes auraient été créées via l'ancien champ.
-- ============================================================================
UPDATE public.purchase_request
SET requested_by = requester_name
WHERE requested_by IS NULL
  AND requester_name IS NOT NULL;

-- ============================================================================
-- 2. Suppression des colonnes redondantes
-- ============================================================================
ALTER TABLE public.purchase_request
    DROP COLUMN IF EXISTS requester_name,
    DROP COLUMN IF EXISTS quantity_requested,
    DROP COLUMN IF EXISTS urgent;
