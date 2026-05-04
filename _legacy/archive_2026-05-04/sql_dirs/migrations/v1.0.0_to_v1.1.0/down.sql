-- Rollback v1.1.0 → v1.0.0
-- Suppression de la fonction derive_pr_status et des index associés

-- Supprimer les index
DROP INDEX IF EXISTS idx_solpr_pr_id;
DROP INDEX IF EXISTS idx_sol_quote_received;
DROP INDEX IF EXISTS idx_sol_is_selected;

-- Supprimer la fonction
DROP FUNCTION IF EXISTS derive_pr_status(UUID);
