-- ============================================================================
-- supplier.sql - Fournisseurs
-- ============================================================================
-- Annuaire fournisseurs pour commandes
--
-- @see supplier_order.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.supplier (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identification
    name TEXT NOT NULL,
    
    -- Contact
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(255),
    address TEXT,
    
    -- État
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Notes
    notes TEXT,
    
    -- Métadonnées
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Commentaires
COMMENT ON TABLE public.supplier IS 'Annuaire fournisseurs';
COMMENT ON COLUMN public.supplier.is_active IS 'Fournisseur actif (FALSE = archivé)';
