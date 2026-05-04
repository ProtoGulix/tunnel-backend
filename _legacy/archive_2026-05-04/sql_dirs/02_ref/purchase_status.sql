-- ============================================================================
-- purchase_status.sql - Statuts demandes d'achat
-- ============================================================================
-- Référentiel statuts demandes achat
--
-- @see purchase_request.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.purchase_status (
    code VARCHAR(255) PRIMARY KEY,
    
    -- Libellé
    label TEXT,
    
    -- Ordre affichage
    order_index INTEGER
);

-- Commentaires
COMMENT ON TABLE public.purchase_status IS 'Référentiel statuts demandes achat';

-- Données de référence
-- INSERT INTO purchase_status (code, label, order_index) VALUES
--   ('en_attente', 'En attente', 1),
--   ('approuve', 'Approuvé', 2),
--   ('commande', 'Commandé', 3),
--   ('recu', 'Reçu', 4),
--   ('refuse', 'Refusé', 99);
