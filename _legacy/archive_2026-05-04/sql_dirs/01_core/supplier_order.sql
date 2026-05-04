-- ============================================================================
-- supplier_order.sql - Commandes fournisseurs
-- ============================================================================
-- Commandes passées aux fournisseurs
-- Numéro auto-généré par trigger : CMD-YYYYMMDD-NNNN
--
-- @see supplier.sql
-- @see supplier_order_line.sql
-- @see trigger trg_generate_supplier_order_number
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.supplier_order (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Numéro commande auto-généré
    order_number TEXT UNIQUE,
    
    -- Relations
    supplier_id UUID, -- FK vers supplier
    
    -- Dates
    ordered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- Date de commande
    expected_delivery_date DATE, -- Date livraison prévue
    received_at TIMESTAMPTZ, -- Date réception réelle
    
    -- Statut
    status VARCHAR(255) DEFAULT 'brouillon', -- brouillon, envoyé, reçu, annulé
    
    -- Montants
    total_amount NUMERIC(10,2), -- Montant total calculé
    currency REAL, -- Devise (ex: EUR, USD)
    
    -- Notes
    notes TEXT,
    
    -- Métadonnées
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Séquence pour numérotation
CREATE SEQUENCE IF NOT EXISTS public.supplier_order_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

-- Index
CREATE INDEX IF NOT EXISTS idx_supplier_order_supplier ON public.supplier_order(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_order_status ON public.supplier_order(status);

-- Commentaires
COMMENT ON TABLE public.supplier_order IS 'Commandes fournisseurs';
COMMENT ON COLUMN public.supplier_order.order_number IS 'Numéro auto-généré CMD-YYYYMMDD-NNNN';
