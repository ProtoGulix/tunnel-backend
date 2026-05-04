-- ============================================================================
-- TABLE : stock_item_characteristic
-- ============================================================================
-- Stocke les valeurs des caractéristiques pour chaque pièce
-- Trois colonnes dédiées pour les trois types de données possibles
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_item_characteristic (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_item_id uuid NOT NULL,
    field_id uuid NOT NULL,
    value_text text,
    value_number numeric,
    value_enum varchar(50),

-- Contraintes de clés étrangères
CONSTRAINT stock_item_characteristic_item_fk FOREIGN KEY (stock_item_id) REFERENCES stock_item (id) ON DELETE CASCADE,
CONSTRAINT stock_item_characteristic_field_fk FOREIGN KEY (field_id) REFERENCES part_template_field (id) ON DELETE RESTRICT,

-- Contrainte d'unicité : une seule valeur par champ et par pièce
CONSTRAINT stock_item_characteristic_unique UNIQUE (stock_item_id, field_id),

-- Contrainte de cohérence : exactement une valeur doit être renseignée
CONSTRAINT stock_item_characteristic_single_value_check 
        CHECK (
            (value_text IS NOT NULL AND value_number IS NULL AND value_enum IS NULL) OR
            (value_text IS NULL AND value_number IS NOT NULL AND value_enum IS NULL) OR
            (value_text IS NULL AND value_number IS NULL AND value_enum IS NOT NULL)
        )
);

-- Index pour optimiser les requêtes
CREATE INDEX idx_stock_item_characteristic_item_id ON stock_item_characteristic (stock_item_id);

CREATE INDEX idx_stock_item_characteristic_field_id ON stock_item_characteristic (field_id);

CREATE INDEX idx_stock_item_characteristic_value_number ON stock_item_characteristic (value_number)
WHERE
    value_number IS NOT NULL;

CREATE INDEX idx_stock_item_characteristic_value_enum ON stock_item_characteristic (value_enum)
WHERE
    value_enum IS NOT NULL;

CREATE INDEX idx_stock_item_char_item_field ON stock_item_characteristic (stock_item_id, field_id);

-- Commentaires
COMMENT ON TABLE stock_item_characteristic IS 'Valeurs des caractéristiques pour chaque pièce selon son template';

COMMENT ON COLUMN stock_item_characteristic.value_text IS 'Valeur textuelle (pour field_type = text)';

COMMENT ON COLUMN stock_item_characteristic.value_number IS 'Valeur numérique (pour field_type = number)';

COMMENT ON COLUMN stock_item_characteristic.value_enum IS 'Valeur énumérée (pour field_type = enum)';