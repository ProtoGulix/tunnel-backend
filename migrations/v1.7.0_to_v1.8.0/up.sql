-- Migration v1.7.0 -> v1.8.0 (UP)
-- Ajout de product_url dans stock_item_supplier

ALTER TABLE public.stock_item_supplier
    ADD COLUMN IF NOT EXISTS product_url TEXT;

COMMENT ON COLUMN public.stock_item_supplier.product_url IS 'URL de la fiche produit chez le fournisseur';
