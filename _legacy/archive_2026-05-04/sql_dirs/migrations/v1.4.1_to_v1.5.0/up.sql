-- Migration v1.4.1 -> v1.5.0 (UP)
-- Liens fabricants : manufacturer_name NOT NULL + FK stock_item_supplier -> manufacturer_item

-- ============================================================================
-- 1. Nettoyer les valeurs NULL existantes avant d'ajouter la contrainte
-- ============================================================================
-- Les lignes sans nom de fabricant reçoivent 'Inconnu' par défaut
UPDATE public.manufacturer_item
SET
    manufacturer_name = 'Inconnu'
WHERE
    manufacturer_name IS NULL;

-- ============================================================================
-- 2. Contrainte NOT NULL sur manufacturer_item.manufacturer_name
-- ============================================================================
ALTER TABLE public.manufacturer_item
ALTER COLUMN manufacturer_name
SET NOT NULL;

-- ============================================================================
-- 3. FK stock_item_supplier.manufacturer_item_id -> manufacturer_item
-- ============================================================================
ALTER TABLE public.stock_item_supplier
ADD CONSTRAINT stock_item_supplier_manufacturer_item_id_fkey FOREIGN KEY (manufacturer_item_id) REFERENCES public.manufacturer_item (id) ON DELETE SET NULL;