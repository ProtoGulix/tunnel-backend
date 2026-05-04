-- ============================================================================
-- location.sql - Localisations/emplacements
-- ============================================================================
-- Lieux physiques où se trouvent les équipements
--
-- @see machine.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.location (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Nom localisation (ex: Atelier A, Zone Production, Bâtiment B)
    name TEXT NOT NULL,
    
    -- Description optionnelle
    description TEXT
);

-- Commentaires
COMMENT ON TABLE public.location IS 'Localisations physiques des équipements';
