-- Migration v1.11.1 → v1.12.0 (UP)
-- equipements : ajout de la table de référence equipement_statuts + colonne statut_id

-- ═══════════════════════════════════════════════════════════════
-- 1. TABLE DE RÉFÉRENCE equipement_statuts
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.equipement_statuts (
    id              SERIAL       PRIMARY KEY,
    code            VARCHAR(30)  NOT NULL UNIQUE,
    libelle         VARCHAR(100) NOT NULL,
    interventions   BOOLEAN      NOT NULL DEFAULT true,
    est_actif       BOOLEAN      NOT NULL DEFAULT true,
    ordre_affichage INT          NOT NULL DEFAULT 0,
    couleur         VARCHAR(7),
    description     TEXT
);

COMMENT ON TABLE  public.equipement_statuts                 IS 'Référentiel des statuts d''équipement (cycle de vie).';
COMMENT ON COLUMN public.equipement_statuts.code            IS 'Code technique unique (ex : EN_SERVICE).';
COMMENT ON COLUMN public.equipement_statuts.libelle         IS 'Libellé affiché dans l''interface utilisateur.';
COMMENT ON COLUMN public.equipement_statuts.interventions   IS 'Indique si la création d''intervention est autorisée pour ce statut.';
COMMENT ON COLUMN public.equipement_statuts.est_actif       IS 'Indique si le statut est encore sélectionnable dans l''UI.';
COMMENT ON COLUMN public.equipement_statuts.ordre_affichage IS 'Ordre de tri dans les listes déroulantes.';
COMMENT ON COLUMN public.equipement_statuts.couleur         IS 'Code couleur hexadécimal pour les badges UI (ex : #10B981).';
COMMENT ON COLUMN public.equipement_statuts.description     IS 'Description longue optionnelle (tooltip / doc interne).';

-- ═══════════════════════════════════════════════════════════════
-- 2. DONNÉES INITIALES (idempotent)
-- ═══════════════════════════════════════════════════════════════

INSERT INTO public.equipement_statuts (code, libelle, interventions, couleur, ordre_affichage)
VALUES
    ('EN_PROJET',       'En projet',       false, '#8B5CF6', 1),
    ('EN_CONSTRUCTION', 'En construction', true,  '#F59E0B', 2),
    ('EN_SERVICE',      'En service',      true,  '#10B981', 3),
    ('ARRET',           'À l''arrêt',      true,  '#EF4444', 4),
    ('REBUT',           'Rebut',           false, '#6B7280', 5),
    ('INCONNU',         'Inconnu',         false, '#D1D5DB', 6)
ON CONFLICT (code) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- 3. COLONNE statut_id SUR equipements (si absente)
--    DEFAULT 3 = EN_SERVICE (3e ligne insérée ci-dessus)
-- ═══════════════════════════════════════════════════════════════

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = 'machine'
          AND column_name  = 'statut_id'
    ) THEN
        ALTER TABLE public.machine
            ADD COLUMN statut_id INT NOT NULL
                DEFAULT 3
                REFERENCES public.equipement_statuts(id);

        COMMENT ON COLUMN public.machine.statut_id IS
            'Statut courant de l''équipement (FK → equipement_statuts). EN_SERVICE par défaut.';
    END IF;
END;
$$;
