-- ============================================================================
-- trg_supplier_order.sql - Numérotation automatique commandes fournisseurs
-- ============================================================================
-- Génère numéro commande : CMD-YYYYMMDD-NNNN
-- Exemple : CMD-20241228-0001
--
-- @see supplier_order.sql (01_core)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.generate_supplier_order_number()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.order_number IS NULL OR NEW.order_number = '' THEN
    NEW.order_number := 'CMD-' || 
                        to_char(current_date, 'YYYYMMDD') || '-' || 
                        LPAD(nextval('supplier_order_seq')::TEXT, 4, '0');
  END IF;
  
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_generate_supplier_order_number
  BEFORE INSERT ON public.supplier_order
  FOR EACH ROW
  EXECUTE FUNCTION public.generate_supplier_order_number();

-- Commentaires
COMMENT ON FUNCTION public.generate_supplier_order_number() IS 'Génère numéro commande fournisseur automatiquement';
