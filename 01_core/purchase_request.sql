-- ============================================================================
-- purchase_request.sql - Demandes d'achat
-- ============================================================================
-- Demandes d'achat articles (approvisionnement stock)
-- Cycle: open → approved → ordered → received
--
-- @see stock_item.sql
-- @see intervention.sql
-- @see intervention_action_purchase_request.sql (01_core)
-- @see trg_calculate_totals.sql (05_triggers) — trigger trg_purchase_request_updated_at
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.purchase_request (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),

-- Statut
status VARCHAR(50) NOT NULL DEFAULT 'open',

-- Relations
stock_item_id UUID, -- FK vers stock_item
intervention_id UUID, -- FK vers intervention (optionnel)

-- Article
item_label TEXT NOT NULL, -- Libellé de l'article demandé
unit VARCHAR(50), -- Unité (ex: pièce, litre, kg)

-- Quantités
quantity INTEGER NOT NULL, -- Quantité demandée
quantity_approved INTEGER, -- Quantité approuvée

-- Justification
reason TEXT,
notes TEXT,
urgency VARCHAR(20) DEFAULT 'normal', -- Niveau d'urgence : normal | high | critical

-- Acteurs
requested_by TEXT, approver_name VARCHAR,

-- Contexte
workshop VARCHAR(255),

-- Dates
created_at TIMESTAMPTZ DEFAULT now(),
updated_at TIMESTAMPTZ DEFAULT now(),
approved_at TIMESTAMPTZ,

-- Contraintes
CONSTRAINT purchase_request_pkey PRIMARY KEY (id),
    CONSTRAINT purchase_request_intervention_id_foreign FOREIGN KEY (intervention_id)
        REFERENCES public.intervention(id) ON DELETE SET NULL,
    CONSTRAINT purchase_request_stock_item_id_fkey FOREIGN KEY (stock_item_id)
        REFERENCES public.stock_item(id) ON DELETE SET NULL,
    CONSTRAINT purchase_request_quantity_check CHECK (quantity > 0)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_purchase_request_status ON public.purchase_request (status);

CREATE INDEX IF NOT EXISTS idx_purchase_request_stock_item ON public.purchase_request (stock_item_id);

CREATE INDEX IF NOT EXISTS idx_purchase_request_created ON public.purchase_request (created_at DESC);

-- Commentaires
COMMENT ON TABLE public.purchase_request IS 'Demandes d''achat articles stock';

COMMENT ON COLUMN public.purchase_request.urgency IS 'Niveau d''urgence de la demande : normal, high, critical';

COMMENT ON COLUMN public.purchase_request.workshop IS 'Atelier à l''origine de la demande';