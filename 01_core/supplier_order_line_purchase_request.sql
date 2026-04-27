-- ============================================================================
-- supplier_order_line_purchase_request.sql - Lien commandes/demandes achat
-- ============================================================================
-- Table jonction : quelle ligne commande répond à quelle(s) demande(s) achat
--
-- @see supplier_order_line.sql
-- @see purchase_request.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.supplier_order_line_purchase_request (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relations
    supplier_order_line_id UUID, -- FK vers supplier_order_line
    purchase_request_id UUID, -- FK vers purchase_request
    
    -- Quantité couverte par cette ligne
    quantity_fulfilled INTEGER NOT NULL,
    
    -- Métadonnées
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Contrainte unicité
    CONSTRAINT uq_line_request UNIQUE (supplier_order_line_id, purchase_request_id)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_sol_pr_line ON public.supplier_order_line_purchase_request(supplier_order_line_id);
CREATE INDEX IF NOT EXISTS idx_sol_pr_request ON public.supplier_order_line_purchase_request(purchase_request_id);

-- Commentaires
COMMENT ON TABLE public.supplier_order_line_purchase_request IS 'Lien lignes commandes avec demandes achat';
COMMENT ON COLUMN public.supplier_order_line_purchase_request.quantity_fulfilled IS 'Quantité de la demande couverte par cette ligne';
