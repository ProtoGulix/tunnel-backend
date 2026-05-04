-- ============================================================================
-- machine.sql - Équipements et machines
-- ============================================================================
-- Inventaire équipements soumis à maintenance
-- Support hiérarchie (equipement_mere pour sous-équipements)
--
-- @see location.sql
-- @see equipement_statuts.sql (02_ref)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.machine (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),

    -- Code unique (ex: CONV-01, POMP-02)
    code VARCHAR(50) NOT NULL DEFAULT NULL::character varying,

    -- Informations équipement
    name VARCHAR(200) NOT NULL,
    no_machine INTEGER, -- Numéro machine (Ancien code compatible avec code intervention)
    affectation VARCHAR(255), -- Lieu ou département d'affectation
    equipement_mere UUID, -- FK auto-référence
    is_mere BOOLEAN DEFAULT FALSE, -- Indique si c'est un équipement mère
    fabricant VARCHAR,
    numero_serie VARCHAR,
    date_mise_service DATE,
    notes TEXT,
    equipment_class_id UUID,
    statut_id INT NOT NULL DEFAULT 3, -- FK equipement_statuts (EN_SERVICE par défaut)

    CONSTRAINT machine_pkey PRIMARY KEY (id),
    CONSTRAINT machine_code_key UNIQUE (code),
    CONSTRAINT machine_equipment_class_id_fkey FOREIGN KEY (equipment_class_id)
        REFERENCES public.equipment_class (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE SET NULL,
    CONSTRAINT machine_equipement_mere_foreign FOREIGN KEY (equipement_mere)
        REFERENCES public.machine (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT machine_statut_id_fkey FOREIGN KEY (statut_id)
        REFERENCES public.equipement_statuts (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE RESTRICT
);

-- Index
CREATE INDEX IF NOT EXISTS machine_code_index ON public.machine(code);
CREATE INDEX IF NOT EXISTS machine_equipement_mere_index ON public.machine(equipement_mere);
CREATE INDEX IF NOT EXISTS machine_equipment_class_index ON public.machine(equipment_class_id);

-- Commentaires
COMMENT ON TABLE public.machine IS 'Équipements et machines soumis à maintenance';
COMMENT ON COLUMN public.machine.code IS 'Code unique équipement (utilisé dans code intervention)';
COMMENT ON COLUMN public.machine.equipment_class_id IS 'Classe équipement (FK equipment_class)';
COMMENT ON COLUMN public.machine.equipement_mere IS 'Équipement parent (pour hiérarchie)';
COMMENT ON COLUMN public.machine.statut_id IS 'Statut courant de l''équipement (FK → equipement_statuts). EN_SERVICE par défaut.';
