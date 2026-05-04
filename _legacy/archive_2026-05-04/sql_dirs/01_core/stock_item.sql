-- ============================================================================
-- stock_item.sql - Articles en stock
-- ============================================================================
-- Pièces détachées, consommables, outillage
-- Référence auto-générée par trigger basée sur famille/spéc/dimension
--
-- @see stock_family.sql (02_ref)
-- @see stock_sub_family.sql
-- @see manufacturer_item.sql
-- @see stock_item_standard_spec.sql
-- @see trigger trg_generate_stock_item_ref
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.stock_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Référence auto-générée (FAM-SFAM-SPEC-DIM)
    ref TEXT UNIQUE,
    
    -- Désignation (name en DB)
    name TEXT NOT NULL,
    
    -- Classification
    family_code VARCHAR(20) NOT NULL, -- FK vers stock_family
    sub_family_code VARCHAR(20) NOT NULL, -- FK vers stock_sub_family
    spec VARCHAR(50), -- Spécification (ex: M8, Ø20mm)
    dimension TEXT NOT NULL, -- Dimension physique
    
    -- Unité
    unit VARCHAR(50), -- ex: pièce, mètre, litre, kg
    
    -- Stock (quantity en DB)
    quantity INTEGER DEFAULT 0,
    
    -- Localisation
    location TEXT,
    
    -- Relations
    manufacturer_item_id UUID, -- FK vers manufacturer_item
    standars_spec UUID, -- FK vers stock_item_standard_spec (Note: typo historique dans la DB)
    
    -- Compteur de références fournisseurs (géré par trigger)
    supplier_refs_count INTEGER,
    
    -- Contrainte CHECK stock >= 0
    CONSTRAINT check_stock_positive CHECK (quantity >= 0)
);

-- Commentaires
COMMENT ON TABLE public.stock_item IS 'Articles en stock (pièces, consommables, outillage)';
COMMENT ON COLUMN public.stock_item.ref IS 'Référence auto-générée (trigger)';
COMMENT ON COLUMN public.stock_item.name IS 'Désignation de l''article';
COMMENT ON COLUMN public.stock_item.quantity IS 'Quantité en stock';
COMMENT ON COLUMN public.stock_item.supplier_refs_count IS 'Nombre de références fournisseurs (géré par trigger)';
