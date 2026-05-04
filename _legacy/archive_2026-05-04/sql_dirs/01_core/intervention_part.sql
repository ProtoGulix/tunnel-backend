-- ============================================================================
-- intervention_part.sql - Pièces consommées durant interventions
-- ============================================================================
-- Lien entre interventions et pièces/articles stock utilisés
--
-- @see intervention.sql
-- @see stock_item.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.intervention_part (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relations
    intervention_id UUID,
    stock_item_id UUID, -- FK vers stock_item
    
    -- Quantité consommée
    quantity INTEGER,
    
    -- Notes optionnelles
    notes TEXT
);

-- Commentaires
COMMENT ON TABLE public.intervention_part IS 'Pièces/articles consommés durant interventions';
COMMENT ON COLUMN public.intervention_part.quantity IS 'Quantité consommée (décrémente stock)';
