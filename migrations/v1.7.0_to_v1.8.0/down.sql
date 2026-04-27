-- Migration v1.7.0 -> v1.8.0 (DOWN)
-- Suppression de product_url dans stock_item_supplier

ALTER TABLE public.stock_item_supplier
    DROP COLUMN IF EXISTS product_url;
