-- ============================================================================
-- stock_item_standard_spec.sql - Spécifications normées articles
-- ============================================================================
-- Standards techniques (ISO, DIN, AFNOR, etc.) pour articles stock
--
-- @see stock_item.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.stock_item_standard_spec (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relation
    stock_item_id UUID, -- FK vers stock_item
    
    -- Norme
    standard_name VARCHAR(255), -- ex: ISO 4762, DIN 912
    standard_value TEXT, -- Valeur nominale
    unit VARCHAR(255), -- Unité mesure
    tolerance VARCHAR(255), -- Tolérance (ex: ±0.1mm)
    
    -- Notes
    notes TEXT
);

-- Commentaires
COMMENT ON TABLE public.stock_item_standard_spec IS 'Spécifications normées pour articles stock';
COMMENT ON COLUMN public.stock_item_standard_spec.standard_name IS 'Nom de la norme (ISO, DIN, AFNOR, etc.)';
