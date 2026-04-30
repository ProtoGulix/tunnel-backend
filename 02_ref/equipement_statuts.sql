-- ============================================================================
-- equipement_statuts.sql - Référentiel statuts des équipements
-- ============================================================================
-- Statuts du cycle de vie d'un équipement (machine).
--
-- @see machine.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.equipement_statuts (
    id              SERIAL       PRIMARY KEY,
    code            VARCHAR(30)  NOT NULL UNIQUE,
    libelle         VARCHAR(100) NOT NULL,
    interventions   BOOLEAN      NOT NULL DEFAULT true,  -- création d'intervention autorisée
    est_actif       BOOLEAN      NOT NULL DEFAULT true,  -- statut sélectionnable dans l'UI
    ordre_affichage INT          NOT NULL DEFAULT 0,     -- tri dans les selects UI
    couleur         VARCHAR(7),                          -- #HEX pour badge UI
    description     TEXT                                 -- tooltip / doc interne
);

COMMENT ON TABLE  public.equipement_statuts                 IS 'Référentiel des statuts d''équipement (cycle de vie).';
COMMENT ON COLUMN public.equipement_statuts.code            IS 'Code technique unique (ex : EN_SERVICE).';
COMMENT ON COLUMN public.equipement_statuts.libelle         IS 'Libellé affiché dans l''interface utilisateur.';
COMMENT ON COLUMN public.equipement_statuts.interventions   IS 'Indique si la création d''intervention est autorisée pour ce statut.';
COMMENT ON COLUMN public.equipement_statuts.est_actif       IS 'Indique si le statut est encore sélectionnable dans l''UI.';
COMMENT ON COLUMN public.equipement_statuts.ordre_affichage IS 'Ordre de tri dans les listes déroulantes.';
COMMENT ON COLUMN public.equipement_statuts.couleur         IS 'Code couleur hexadécimal pour les badges UI (ex : #10B981).';
COMMENT ON COLUMN public.equipement_statuts.description     IS 'Description longue optionnelle (tooltip / doc interne).';

-- Données initiales
INSERT INTO public.equipement_statuts (code, libelle, interventions, couleur, ordre_affichage)
VALUES
    ('EN_PROJET',       'En projet',       false, '#8B5CF6', 1),
    ('EN_CONSTRUCTION', 'En construction', true,  '#F59E0B', 2),
    ('EN_SERVICE',      'En service',      true,  '#10B981', 3),
    ('ARRET',           'À l''arrêt',      true,  '#EF4444', 4),
    ('REBUT',           'Rebut',           false, '#6B7280', 5),
    ('INCONNU',         'Inconnu',         false, '#D1D5DB', 6)
ON CONFLICT (code) DO NOTHING;
