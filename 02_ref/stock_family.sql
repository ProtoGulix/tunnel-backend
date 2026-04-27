-- ============================================================================
-- stock_family.sql - Familles d'articles stock
-- ============================================================================
-- Classification haut niveau articles (ex: VIS, ROUL, COURR, HUIL)
--
-- @see stock_item.sql (01_core)
-- @see stock_sub_family.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.stock_family (
    code VARCHAR(255) PRIMARY KEY,
    
    -- Nom famille
    name TEXT NOT NULL
);

-- Commentaires
COMMENT ON TABLE public.stock_family IS 'Familles d''articles stock (niveau 1)';

-- Données de référence exemples
-- INSERT INTO stock_family (code, name) VALUES
--   ('VIS', 'Visserie'),
--   ('ROUL', 'Roulements'),
--   ('COURR', 'Courroies'),
--   ('HUIL', 'Huiles et lubrifiants'),
--   ('ELEC', 'Électrique');
