-- ============================================================================
-- stock_sub_family.sql - Sous-familles d'articles stock
-- ============================================================================
-- Classification niveau 2 articles (ex: VIS-CHC, VIS-TH, ROUL-BIL)
--
-- @see stock_family.sql
-- @see stock_item.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.stock_sub_family (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relation famille parent
    family_code VARCHAR(255), -- FK vers stock_family
    
    -- Code sous-famille
    code VARCHAR(255) NOT NULL,
    
    -- Nom sous-famille
    name TEXT NOT NULL,
    
    -- Contrainte unicité (family_code + code)
    CONSTRAINT uq_stock_sub_family UNIQUE (family_code, code)
);

-- Commentaires
COMMENT ON TABLE public.stock_sub_family IS 'Sous-familles d''articles stock (niveau 2)';

-- Données de référence exemples
-- INSERT INTO stock_sub_family (family_code, code, name) VALUES
--   ('VIS', 'CHC', 'Vis à tête cylindrique hexagonale creuse'),
--   ('VIS', 'TH', 'Vis à tête hexagonale'),
--   ('ROUL', 'BIL', 'Roulements à billes'),
--   ('ROUL', 'ROUL', 'Roulements à rouleaux');
