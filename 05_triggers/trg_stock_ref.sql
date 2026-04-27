-- ============================================================================
-- trg_stock_ref.sql - Génération automatique référence article stock
-- ============================================================================
-- Génère référence article : FAMILLE-SOUSFAMILLE-SPEC-DIMENSION
-- Exemple : VIS-CHC-M8-20
--
-- @see stock_item.sql (01_core)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.generate_stock_item_ref()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  -- Génère référence : FAM-SFAM-SPEC-DIM (sans tirets inutiles)
  -- Ne concatène le séparateur que si la valeur existe
  NEW.ref := NEW.family_code;
  
  IF NEW.sub_family_code IS NOT NULL AND NEW.sub_family_code != '' THEN
    NEW.ref := NEW.ref || '-' || NEW.sub_family_code;
  END IF;
  
  IF NEW.spec IS NOT NULL AND NEW.spec != '' THEN
    NEW.ref := NEW.ref || '-' || NEW.spec;
  END IF;
  
  IF NEW.dimension IS NOT NULL AND NEW.dimension != '' THEN
    NEW.ref := NEW.ref || '-' || NEW.dimension;
  END IF;
  
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_generate_stock_item_ref
  BEFORE INSERT OR UPDATE OF family_code, sub_family_code, spec, dimension ON public.stock_item
  FOR EACH ROW
  EXECUTE FUNCTION public.generate_stock_item_ref();

-- Commentaires
COMMENT ON FUNCTION public.generate_stock_item_ref () IS 'Génère référence article stock automatiquement';