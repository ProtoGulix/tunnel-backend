-- Vue : purchase_request_derived_status
-- Source de vérité unique pour le statut dérivé des demandes d'achat.
--
-- Logique de dérivation (priorité ordre décroissant) :
--   TO_QUALIFY      — pas de référence stock normalisée
--   NO_SUPPLIER_REF — aucune référence fournisseur liée au stock_item
--   PENDING_DISPATCH— référence ok, pas encore dans un supplier order
--   REJECTED        — toutes les lignes dans un panier terminal (CANCELLED/CLOSED), aucune sélectionnée
--   RECEIVED        — toutes les lignes terminales avec au moins une sélectionnée,
--                     OU livraison complète (total_received >= total_allocated)
--   CONSULTATION    — panier verrouillé (SENT/ACK), sans devis ni sélection
--   PARTIAL         — livraison partielle
--   ORDERED         — au moins une ligne sélectionnée
--   QUOTED          — au moins un devis reçu
--   OPEN            — dans un panier ouvert, pas encore de mouvement
--
-- Usage :
--   SELECT id, derived_status FROM purchase_request_derived_status WHERE id = $1;
--   SELECT COUNT(*) FILTER (WHERE derived_status = 'RECEIVED') FROM purchase_request_derived_status;

CREATE OR REPLACE VIEW purchase_request_derived_status AS
SELECT
    pr.id,
    pr.stock_item_id,
    pr.item_label,
    pr.quantity,
    pr.unit,
    pr.urgency,
    pr.requested_by,
    pr.intervention_id,
    pr.created_at,
    pr.updated_at,

    -- Agrégats des order lines
    sol_agg.supplier_refs_count,
    sol_agg.quotes_count,
    sol_agg.selected_count,
    sol_agg.total_allocated,
    sol_agg.total_received,
    sol_agg.has_locked_order,
    sol_agg.all_terminal,
    sol_agg.has_order_lines,

    -- Statut dérivé — source de vérité unique
    CASE
        WHEN pr.stock_item_id IS NULL
            THEN 'TO_QUALIFY'
        WHEN COALESCE(sol_agg.supplier_refs_count, 0) = 0
            THEN 'NO_SUPPLIER_REF'
        WHEN NOT COALESCE(sol_agg.has_order_lines, FALSE)
            THEN 'PENDING_DISPATCH'
        WHEN COALESCE(sol_agg.all_terminal, FALSE) AND COALESCE(sol_agg.selected_count, 0) = 0
            THEN 'REJECTED'
        WHEN COALESCE(sol_agg.all_terminal, FALSE) AND COALESCE(sol_agg.selected_count, 0) > 0
            THEN 'RECEIVED'
        WHEN COALESCE(sol_agg.total_received, 0) >= COALESCE(sol_agg.total_allocated, 1)
             AND COALESCE(sol_agg.total_allocated, 0) > 0
            THEN 'RECEIVED'
        WHEN COALESCE(sol_agg.has_locked_order, FALSE)
             AND COALESCE(sol_agg.selected_count, 0) = 0
             AND COALESCE(sol_agg.quotes_count, 0) = 0
            THEN 'CONSULTATION'
        WHEN COALESCE(sol_agg.total_received, 0) > 0
            THEN 'PARTIAL'
        WHEN COALESCE(sol_agg.selected_count, 0) > 0
            THEN 'ORDERED'
        WHEN COALESCE(sol_agg.quotes_count, 0) > 0
            THEN 'QUOTED'
        ELSE 'OPEN'
    END AS derived_status

FROM purchase_request pr
LEFT JOIN LATERAL (
    SELECT
        (SELECT COUNT(*) FROM stock_item_supplier WHERE stock_item_id = pr.stock_item_id) AS supplier_refs_count,
        COUNT(DISTINCT CASE WHEN sol.quote_received  THEN sol.id END)  AS quotes_count,
        COUNT(DISTINCT CASE WHEN sol.is_selected     THEN sol.id END)  AS selected_count,
        COALESCE(SUM(solpr.quantity), 0)                               AS total_allocated,
        COALESCE(SUM(sol.quantity_received), 0)                        AS total_received,
        BOOL_OR(so.status IN ('SENT', 'ACK'))                          AS has_locked_order,
        BOOL_AND(so.status IN ('CANCELLED', 'CLOSED'))                 AS all_terminal,
        COUNT(sol.id) > 0                                              AS has_order_lines
    FROM supplier_order_line_purchase_request solpr
    JOIN supplier_order_line sol ON solpr.supplier_order_line_id = sol.id
    JOIN supplier_order so       ON sol.supplier_order_id = so.id
    WHERE solpr.purchase_request_id = pr.id
) sol_agg ON TRUE;

-- Commentaire de vue
COMMENT ON VIEW purchase_request_derived_status IS
    'Source de vérité unique du statut dérivé des demandes d''achat. '
    'Ne pas dupliquer la logique CASE WHEN en Python ou dans d''autres requêtes SQL — '
    'toujours joindre cette vue.';
