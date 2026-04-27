-- ============================================================================
-- trg_calculate_totals.sql - Calculs automatiques
-- ============================================================================
-- Calcule totaux lignes commandes (unit_price × quantity)
-- Met à jour timestamps (updated_at)
--
-- @see supplier_order_line.sql (01_core)
-- ============================================================================

-- ============================================================================
-- 1. Calcul total ligne commande
-- ============================================================================

CREATE OR REPLACE FUNCTION public.calculate_line_total()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.unit_price IS NOT NULL AND NEW.quantity IS NOT NULL THEN
    NEW.total_price = NEW.unit_price * NEW.quantity;
  END IF;
  
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_calculate_line_total
  BEFORE INSERT OR UPDATE OF unit_price, quantity ON public.supplier_order_line
  FOR EACH ROW
  EXECUTE FUNCTION public.calculate_line_total();

-- ============================================================================
-- 2. Mise à jour timestamp updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- Triggers sur toutes les tables avec updated_at
CREATE TRIGGER trg_purchase_request_updated_at
  BEFORE UPDATE ON public.purchase_request
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER trg_stock_item_supplier_updated_at
  BEFORE UPDATE ON public.stock_item_supplier
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER trg_supplier_order_line_updated_at
  BEFORE UPDATE ON public.supplier_order_line
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER trg_supplier_order_updated_at
  BEFORE UPDATE ON public.supplier_order
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER trg_supplier_updated_at
  BEFORE UPDATE ON public.supplier
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Commentaires
COMMENT ON FUNCTION public.calculate_line_total() IS 'Calcule total ligne commande (prix × quantité)';
COMMENT ON FUNCTION public.update_updated_at_column() IS 'Met à jour timestamp updated_at automatiquement';
