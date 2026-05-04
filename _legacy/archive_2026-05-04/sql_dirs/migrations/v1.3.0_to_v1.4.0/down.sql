-- ============================================================================
-- Migration v1.3.0 -> v1.4.0 (DOWN)
-- Rollback du système de caractérisation des pièces
-- ============================================================================
-- Supprime toutes les tables et colonnes ajoutées par la migration v1.4.0
-- dans l'ordre inverse des dépendances
-- ============================================================================

-- ============================================================================
-- 1. Suppression de la table stock_item_characteristic
-- ============================================================================

DROP TABLE IF EXISTS stock_item_characteristic CASCADE;

-- ============================================================================
-- 2. Suppression des colonnes ajoutées à stock_item
-- ============================================================================

ALTER TABLE stock_item
DROP CONSTRAINT IF EXISTS stock_item_template_fk;

ALTER TABLE stock_item
DROP CONSTRAINT IF EXISTS stock_item_template_version_positive;

DROP INDEX IF EXISTS idx_stock_item_template_id;

DROP INDEX IF EXISTS idx_stock_item_template_version;

ALTER TABLE stock_item DROP COLUMN IF EXISTS template_id;

ALTER TABLE stock_item DROP COLUMN IF EXISTS template_version;

-- ============================================================================
-- 3. Suppression de la colonne ajoutée à stock_sub_family
-- ============================================================================

ALTER TABLE stock_sub_family
DROP CONSTRAINT IF EXISTS stock_sub_family_template_fk;

DROP INDEX IF EXISTS idx_stock_sub_family_template_id;

ALTER TABLE stock_sub_family DROP COLUMN IF EXISTS template_id;

-- ============================================================================
-- 4. Suppression de la table part_template_field_enum
-- ============================================================================

DROP TABLE IF EXISTS part_template_field_enum CASCADE;

-- ============================================================================
-- 5. Suppression de la table part_template_field
-- ============================================================================

DROP TABLE IF EXISTS part_template_field CASCADE;

-- ============================================================================
-- 6. Suppression de la table part_template
-- ============================================================================

DROP TABLE IF EXISTS part_template CASCADE;

-- ============================================================================
-- FIN DU ROLLBACK
-- ============================================================================
-- Note: Les données créées par l'utilisateur dans ces tables sont perdues
-- après ce rollback. Assurez-vous d'avoir une sauvegarde si nécessaire.
-- ============================================================================