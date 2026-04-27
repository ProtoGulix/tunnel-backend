-- Migration v1.4.1 -> v1.4.0 (DOWN)
-- Rollback: Restaurer la version originale du trigger

-- ============================================================================
-- Restauration du trigger de génération de référence article stock
-- ============================================================================
-- Retour à la version originale (sans gestion des NULL)
-- ============================================================================

CREATE OR REPLACE FUNCTION public.generate_stock_item_ref()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  -- Génère référence : FAM-SFAM-SPEC-DIM
  NEW.ref := NEW.family_code || '-' || NEW.sub_family_code || '-' || NEW.spec || '-' || NEW.dimension;
  
  RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.generate_stock_item_ref () IS 'Génère référence article stock automatiquement';