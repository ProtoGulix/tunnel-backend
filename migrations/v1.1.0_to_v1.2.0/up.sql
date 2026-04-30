-- Migration v1.1.0 -> v1.2.0
-- Add equipement_class reference table and machine relation

-- Reference table
CREATE TABLE IF NOT EXISTS public.equipement_class (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(255) NOT NULL UNIQUE,
    label TEXT NOT NULL,
    description TEXT
);

CREATE INDEX IF NOT EXISTS equipement_class_code_index ON public.equipement_class(code);

COMMENT ON TABLE public.equipement_class IS 'Equipment classes (reference)';
COMMENT ON COLUMN public.equipement_class.code IS 'Unique equipment class code';
COMMENT ON COLUMN public.equipement_class.label IS 'Equipment class label';

-- Seed data (safe to re-run)
INSERT INTO public.equipement_class (code, label)
VALUES
    ('ALM', 'Alarme'),
    ('ASP', 'Aspirateur'),
    ('AM', 'Aspirateur de matiére'),
    ('BDP', 'Barre de pont'),
    ('BAL', 'Basculeur'),
    ('BET', 'Bétonniére '),
    ('BRO', 'Broyeur'),
    ('CER', 'Cercleuse'),
    ('CHL', 'Chalumeau'),
    ('CHA', 'Chariot'),
    ('CHF', 'Chauffage'),
    ('CN', 'CN'),
    ('COP', 'Compresseur'),
    ('COV', 'Convoyeur'),
    ('CDA', 'Cuve d''air'),
    ('DIA', 'Diable'),
    ('EER', 'Electro-Erosion'),
    ('ENR', 'Enrouleur'),
    ('ETU', 'Etuve'),
    ('EXT', 'Extrudeuse'),
    ('FIL', 'Filmeuse'),
    ('FSA', 'Filtre à sable'),
    ('FRS', 'Fraiseuse'),
    ('GRB', 'Gerbeur'),
    ('GRA', 'Granulateur '),
    ('GFR', 'Groupe froid'),
    ('GLT', 'Guillotine'),
    ('IMP', 'Imprimante'),
    ('KAR', 'Karcher'),
    ('LIG', 'Ligne'),
    ('MEL', 'Mélangeur'),
    ('MTR', 'Metrologie'),
    ('MM', 'Monte matiére'),
    ('PER', 'Perceuse'),
    ('PCH', 'Pied de chauffe'),
    ('PLI', 'Plieuse'),
    ('POI', 'Poinconeuse'),
    ('POE', 'Pompe à eau'),
    ('POV', 'Pompe à vide'),
    ('PCB', 'Ponceuse  bande'),
    ('PRL', 'Pont roulant'),
    ('POU', 'Poubelle'),
    ('PRE', 'Presse'),
    ('PIJ', 'Presse à injecter'),
    ('PRM', 'Presse manuel'),
    ('RBT', 'Raboteuse'),
    ('REC', 'Réchauffeur'),
    ('RCT', 'Réctifieuse'),
    ('SBL', 'Sableuse'),
    ('SCI', 'Scie '),
    ('SCH', 'Sécheur'),
    ('STU', 'Structureuse'),
    ('SBB', 'Support BIG BAG'),
    ('TAB', 'Table'),
    ('TDP', 'Tapis de poncage '),
    ('TRD', 'Taraudeuse'),
    ('TEN', 'Tenoneuse'),
    ('TOU', 'Toupie'),
    ('TOR', 'Tour'),
    ('TRM', 'Touret à meulé'),
    ('TRA', 'Transpalette'),
    ('TPE', 'Transpalette électrique'),
    ('OTH', 'Travail en hauteur'),
    ('TRY', 'Trémie '),
    ('VIL', 'Viellisement'),
    ('VHL', 'VL')
ON CONFLICT (code) DO UPDATE SET label = EXCLUDED.label;

-- Machine relation (many machines -> one equipement_class)
ALTER TABLE public.machine
    ADD COLUMN IF NOT EXISTS equipement_class_id UUID;

CREATE INDEX IF NOT EXISTS machine_equipement_class_index ON public.machine(equipement_class_id);

COMMENT ON COLUMN public.machine.equipement_class_id IS 'Equipment class (FK equipement_class)';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'machine_equipement_class_id_fkey'
    ) THEN
        ALTER TABLE public.machine
            ADD CONSTRAINT machine_equipement_class_id_fkey
            FOREIGN KEY (equipement_class_id) REFERENCES public.equipement_class(id);
    END IF;
END $$;
