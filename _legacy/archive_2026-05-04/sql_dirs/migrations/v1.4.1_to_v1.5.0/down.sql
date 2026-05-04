-- Migration v1.5.0 -> v1.4.1 (DOWN)
-- Rollback : suppression FK stock_item_supplier -> manufacturer_item + retrait NOT NULL

-- ============================================================================
-- 1. Suppression de la FK stock_item_supplier -> manufacturer_item
-- ============================================================================
ALTER TABLE public.stock_item_supplier
DROP CONSTRAINT IF EXISTS stock_item_supplier_manufacturer_item_id_fkey;

-- ============================================================================
-- 2. Retrait de la contrainte NOT NULL sur manufacturer_item.manufacturer_name
-- ============================================================================
ALTER TABLE public.manufacturer_item
ALTER COLUMN manufacturer_name
DROP NOT NULL;