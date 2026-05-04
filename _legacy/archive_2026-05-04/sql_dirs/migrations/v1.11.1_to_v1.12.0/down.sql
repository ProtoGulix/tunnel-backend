-- Migration v1.11.1 → v1.12.0 (DOWN)
-- Rollback : suppression de statut_id sur equipements + suppression equipement_statuts

-- ═══════════════════════════════════════════════════════════════
-- 1. SUPPRESSION DE LA COLONNE statut_id SUR equipements
-- ═══════════════════════════════════════════════════════════════

ALTER TABLE public.machine
    DROP COLUMN IF EXISTS statut_id;

-- ═══════════════════════════════════════════════════════════════
-- 2. SUPPRESSION DE LA TABLE DE RÉFÉRENCE
-- ═══════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS public.equipement_statuts;
