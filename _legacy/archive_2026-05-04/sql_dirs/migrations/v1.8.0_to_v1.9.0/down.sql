-- Migration v1.8.0 -> v1.9.0 (DOWN)
-- Restauration de la contrainte FK dupliquée (Directus)

ALTER TABLE public.stock_item_supplier
    ADD CONSTRAINT stock_item_supplier_manufacturer_item_id_foreign FOREIGN KEY (manufacturer_item_id)
        REFERENCES public.manufacturer_item (id) ON DELETE SET NULL;
