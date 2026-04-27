-- ============================================================================
-- TABLE : part_template_field
-- ============================================================================
-- Définit les champs structurés de chaque template
-- Chaque champ peut être de type number, text ou enum
-- ============================================================================

CREATE TABLE IF NOT EXISTS part_template_field (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id uuid NOT NULL,
    field_key varchar(50) NOT NULL,
    label varchar(100) NOT NULL,
    field_type varchar(30) NOT NULL,
    unit varchar(20),
    required boolean DEFAULT false,
    sortable boolean DEFAULT true,
    sort_order integer NOT NULL,
    
    -- Contraintes
    CONSTRAINT part_template_field_template_fk 
        FOREIGN KEY (template_id) 
        REFERENCES part_template(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT part_template_field_type_check 
        CHECK (field_type IN ('number', 'text', 'enum')),
    
    CONSTRAINT part_template_field_sort_order_positive 
        CHECK (sort_order > 0),
    
    CONSTRAINT part_template_field_unique 
        UNIQUE (template_id, field_key)
);

-- Index pour optimiser les requêtes
CREATE INDEX idx_part_template_field_template_id ON part_template_field(template_id);
CREATE INDEX idx_part_template_field_sort_order ON part_template_field(template_id, sort_order);

-- Commentaires
COMMENT ON TABLE part_template_field IS 'Champs structurés définissant les caractéristiques d''un template';
COMMENT ON COLUMN part_template_field.field_key IS 'Clé unique du champ au sein du template';
COMMENT ON COLUMN part_template_field.field_type IS 'Type de données : number, text ou enum';
COMMENT ON COLUMN part_template_field.unit IS 'Unité de mesure (pour les champs numériques)';
COMMENT ON COLUMN part_template_field.required IS 'Indique si le champ est obligatoire';
COMMENT ON COLUMN part_template_field.sortable IS 'Indique si le champ peut être trié';
COMMENT ON COLUMN part_template_field.sort_order IS 'Ordre d''affichage du champ';
