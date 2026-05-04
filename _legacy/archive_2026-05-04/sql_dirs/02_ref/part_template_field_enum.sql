-- ============================================================================
-- TABLE : part_template_field_enum
-- ============================================================================
-- Stocke les valeurs possibles pour les champs de type enum
-- Permet un contrôle strict des valeurs autorisées
-- ============================================================================

CREATE TABLE IF NOT EXISTS part_template_field_enum (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    field_id uuid NOT NULL,
    value varchar(50) NOT NULL,
    label varchar(100),
    
    -- Contraintes
    CONSTRAINT part_template_field_enum_field_fk 
        FOREIGN KEY (field_id) 
        REFERENCES part_template_field(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT part_template_field_enum_unique 
        UNIQUE (field_id, value)
);

-- Index pour optimiser les requêtes
CREATE INDEX idx_part_template_field_enum_field_id ON part_template_field_enum(field_id);

-- Commentaires
COMMENT ON TABLE part_template_field_enum IS 'Valeurs autorisées pour les champs de type enum';
COMMENT ON COLUMN part_template_field_enum.value IS 'Valeur technique de l''énumération';
COMMENT ON COLUMN part_template_field_enum.label IS 'Libellé affiché de la valeur';
