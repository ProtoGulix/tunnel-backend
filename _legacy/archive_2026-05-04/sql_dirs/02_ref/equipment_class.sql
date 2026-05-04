-- ============================================================================
-- equipment_class.sql - Classes d'equipement
-- ============================================================================
-- Classification des equipements (ex: SCIE, EXTRUDEUSE, ...)
--
-- @see machine.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.equipment_class (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Code unique de classe (ex: SCIE, EXTRUDEUSE)
    code VARCHAR(255) NOT NULL UNIQUE,

    -- Libelle court
    label TEXT NOT NULL,

    -- Description optionnelle
    description TEXT
);

-- Index
CREATE INDEX IF NOT EXISTS equipment_class_code_index ON public.equipment_class(code);

-- Commentaires
COMMENT ON TABLE public.equipment_class IS 'Classes d''equipement (reference)';
COMMENT ON COLUMN public.equipment_class.code IS 'Code unique de classe equipement';
COMMENT ON COLUMN public.equipment_class.label IS 'Libelle classe equipement';
