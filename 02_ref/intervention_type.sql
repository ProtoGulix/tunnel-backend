-- ============================================================================
-- intervention_type.sql - Types d'intervention maintenance
-- ============================================================================
-- Référentiel des types d'intervention (CUR, PRE, REA, BAT, PRO, COF, PIL, MES)
--
-- @see intervention.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.intervention_type (
    id       SERIAL       PRIMARY KEY,

-- Code technique unique (ex: CUR, PRE, BAT)
code VARCHAR(10) NOT NULL UNIQUE,

-- Libellé affiché dans l'interface
label TEXT NOT NULL,

-- Couleur pour badges UI (ex: red, green, #3b82f6)
color VARCHAR(30),

-- Actif/inactif (soft delete)
is_active BOOLEAN NOT NULL DEFAULT true );

-- Index
CREATE INDEX IF NOT EXISTS intervention_type_code_index ON public.intervention_type (code);

-- Commentaires
COMMENT ON TABLE public.intervention_type IS 'Référentiel des types d''intervention maintenance';

COMMENT ON COLUMN public.intervention_type.code IS 'Code technique unique (ex : CUR, PRE, BAT)';

COMMENT ON COLUMN public.intervention_type.color IS 'Couleur pour badges UI';

-- Données de référence
-- INSERT INTO intervention_type (code, label, color) VALUES
--   ('CUR', 'Curatif',              'red'),
--   ('PRE', 'Préventif',            'green'),
--   ('REA', 'Réapprovisionnement',  'blue'),
--   ('BAT', 'Batiment',             'gray'),
--   ('PRO', 'Projet',               'blue'),
--   ('COF', 'Remise en conformité', 'amber'),
--   ('PIL', 'Pilotage',             'blue'),
--   ('MES', 'Mise en service',      'amber');