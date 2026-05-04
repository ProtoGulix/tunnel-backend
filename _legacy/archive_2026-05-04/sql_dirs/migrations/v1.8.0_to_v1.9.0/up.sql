-- Migration v1.8.0 -> v1.9.0 (UP)
-- Suppression de la contrainte FK dupliquée sur stock_item_supplier.manufacturer_item_id
--
-- La table possède deux FK identiques sur manufacturer_item_id :
--   - stock_item_supplier_manufacturer_item_id_fkey   (ajoutée en v1.5.0)
--   - stock_item_supplier_manufacturer_item_id_foreign (créée par Directus à l'origine)
-- On conserve la forme _fkey (convention PostgreSQL) et on supprime la _foreign.

ALTER TABLE public.stock_item_supplier
    DROP CONSTRAINT IF EXISTS stock_item_supplier_manufacturer_item_id_foreign;
