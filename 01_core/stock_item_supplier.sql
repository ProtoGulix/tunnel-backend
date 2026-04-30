-- ============================================================================
-- stock_item_supplier.sql - Relations articles/fournisseurs
-- ============================================================================
-- Catalogues fournisseurs : quels articles disponibles chez quels fournisseurs
-- Prix, délais, quantités minimum
--
-- @see stock_item.sql
-- @see supplier.sql
-- @see manufacturer_item.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.stock_item_supplier (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),

    -- Relations
    stock_item_id UUID NOT NULL,       -- FK vers stock_item
    supplier_id   UUID NOT NULL,       -- FK vers supplier
    manufacturer_item_id UUID,         -- FK vers manufacturer_item (référence fabricant)

    -- Référence fournisseur
    supplier_ref TEXT NOT NULL,        -- Référence catalogue fournisseur

    -- Tarification
    unit_price         NUMERIC(10,2),
    min_order_quantity INTEGER DEFAULT 1, -- Quantité minimum commande
    delivery_time_days INTEGER,           -- Délai livraison (jours)

    -- Fournisseur préféré
    is_preferred BOOLEAN DEFAULT FALSE,

    -- Lien produit
    product_url TEXT,                  -- URL fiche produit chez le fournisseur (ex: Amazon, AliExpress)

    -- Métadonnées
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Contraintes
    CONSTRAINT stock_item_supplier_pkey PRIMARY KEY (id),
    CONSTRAINT uq_stock_item_supplier UNIQUE (stock_item_id, supplier_id),
    CONSTRAINT stock_item_supplier_manufacturer_item_id_fkey FOREIGN KEY (manufacturer_item_id)
        REFERENCES public.manufacturer_item (id) ON DELETE SET NULL,
    CONSTRAINT stock_item_supplier_stock_item_id_fkey FOREIGN KEY (stock_item_id)
        REFERENCES public.stock_item (id) ON DELETE SET NULL,
    CONSTRAINT stock_item_supplier_supplier_id_fkey FOREIGN KEY (supplier_id)
        REFERENCES public.supplier (id) ON DELETE CASCADE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_stock_item_supplier_preferred
    ON public.stock_item_supplier(stock_item_id, is_preferred)
    WHERE is_preferred = TRUE;

CREATE INDEX IF NOT EXISTS stock_item_supplier_manufacturer_item_id_index
    ON public.stock_item_supplier(manufacturer_item_id);

-- Triggers (définis dans 05_triggers/trg_update_supplier_refs_count.sql)
-- trg_stock_item_supplier_refs_count_insert  → fn_update_supplier_refs_count() AFTER INSERT
-- trg_stock_item_supplier_refs_count_delete  → fn_update_supplier_refs_count() AFTER DELETE
-- trg_stock_item_supplier_refs_count_update  → fn_update_supplier_refs_count() AFTER UPDATE (si stock_item_id change)
-- trg_stock_item_supplier_updated_at         → update_updated_at_column()      BEFORE UPDATE

-- Commentaires
COMMENT ON TABLE  public.stock_item_supplier IS 'Catalogues fournisseurs (articles disponibles)';
COMMENT ON COLUMN public.stock_item_supplier.supplier_ref IS 'Référence catalogue du fournisseur';
COMMENT ON COLUMN public.stock_item_supplier.delivery_time_days IS 'Délai de livraison en jours';
COMMENT ON COLUMN public.stock_item_supplier.is_preferred IS 'Fournisseur préféré pour cet article';
COMMENT ON COLUMN public.stock_item_supplier.product_url IS 'URL de la fiche produit chez le fournisseur';
