-- Migration v1.0.0 → v1.1.0
-- Ajout de la fonction derive_pr_status pour le calcul automatique du statut des demandes d'achat

-- Fonction PostgreSQL pour dériver le statut d'une demande d'achat
-- Basé sur l'état des lignes de commande fournisseur liées

CREATE OR REPLACE FUNCTION derive_pr_status(pr_id UUID)
RETURNS TEXT AS $$
DECLARE
    has_quotes BOOLEAN;
    has_selected BOOLEAN;
    all_received BOOLEAN;
    some_received BOOLEAN;
    selected_count INT;
BEGIN
    -- Vérifier si au moins un devis reçu
    SELECT EXISTS(
        SELECT 1 FROM supplier_order_line_purchase_request solpr
        JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
        WHERE solpr.purchase_request_id = pr_id AND sol.quote_received = TRUE
    ) INTO has_quotes;
    
    -- Vérifier si au moins une ligne sélectionnée
    SELECT 
        EXISTS(
            SELECT 1 FROM supplier_order_line_purchase_request solpr
            JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
            WHERE solpr.purchase_request_id = pr_id AND sol.is_selected = TRUE
        ),
        COUNT(CASE WHEN sol.is_selected = TRUE THEN 1 END)
    INTO has_selected, selected_count
    FROM supplier_order_line_purchase_request solpr
    JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
    WHERE solpr.purchase_request_id = pr_id;
    
    -- Vérifier réceptions (uniquement pour lignes sélectionnées)
    IF selected_count > 0 THEN
        SELECT 
            COUNT(*) = COUNT(CASE WHEN sol.quantity_received >= solpr.quantity THEN 1 END),
            COUNT(CASE WHEN sol.quantity_received > 0 THEN 1 END) > 0
        INTO all_received, some_received
        FROM supplier_order_line_purchase_request solpr
        JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
        WHERE solpr.purchase_request_id = pr_id AND sol.is_selected = TRUE;
    ELSE
        all_received := FALSE;
        some_received := FALSE;
    END IF;
    
    -- Logique de dérivation
    IF all_received THEN
        RETURN 'RECEIVED';
    ELSIF some_received THEN
        RETURN 'PARTIAL';
    ELSIF has_selected THEN
        RETURN 'ORDERED';
    ELSIF has_quotes THEN
        RETURN 'QUOTED';
    ELSE
        RETURN 'OPEN';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Index pour optimiser les requêtes de dérivation
CREATE INDEX IF NOT EXISTS idx_solpr_pr_id ON supplier_order_line_purchase_request(purchase_request_id);
CREATE INDEX IF NOT EXISTS idx_sol_quote_received ON supplier_order_line(quote_received) WHERE quote_received = TRUE;
CREATE INDEX IF NOT EXISTS idx_sol_is_selected ON supplier_order_line(is_selected) WHERE is_selected = TRUE;

-- Commentaire pour documentation
COMMENT ON FUNCTION derive_pr_status(UUID) IS 'Calcule le statut dérivé d''une demande d''achat basé sur l''état des lignes de commande fournisseur liées';
