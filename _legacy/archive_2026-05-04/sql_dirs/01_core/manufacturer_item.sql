-- ============================================================================
-- manufacturer_item.sql - Références fabricants
-- ============================================================================
-- Liens articles avec références fabricants/constructeurs
--
-- @see stock_item.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.manufacturer_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

-- Fabricant
manufacturer_name TEXT NOT NULL,
manufacturer_ref TEXT, -- Référence catalogue fabricant

-- Notes
notes TEXT );

-- Commentaires
COMMENT ON TABLE public.manufacturer_item IS 'Références fabricants pour articles stock';

COMMENT ON COLUMN public.manufacturer_item.manufacturer_name IS 'Nom du fabricant/constructeur';

COMMENT ON COLUMN public.manufacturer_item.manufacturer_ref IS 'Référence catalogue fabricant';