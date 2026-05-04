-- Migration v1.4.0 -> v1.4.1 (UP)
-- Fix: Trigger generate_stock_item_ref pour gérer les valeurs NULL

-- ============================================================================
-- Correctif du trigger de génération de référence article stock
-- ============================================================================
-- Problème : La concaténation avec || retourne NULL si une valeur est NULL
-- Solution : Utiliser COALESCE pour remplacer les NULL par des chaînes vides
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

COMMENT ON FUNCTION public.generate_stock_item_ref () IS 'Génère référence article stock automatiquement (gère les NULL)';