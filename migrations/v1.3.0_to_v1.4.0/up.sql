-- ============================================================================
-- Migration v1.3.0 -> v1.4.0 (UP)
-- Système de caractérisation des pièces par templates versionnés
-- ============================================================================
-- Cette migration introduit un système robuste et scalable pour gérer
-- les caractéristiques des pièces via des templates versionnés avec
-- champs structurés (number, text, enum) et intégrité référentielle forte.
-- ============================================================================

-- ============================================================================
-- 1. TABLE : part_template
-- ============================================================================
-- Templates versionnés définissant la structure des caractéristiques

CREATE TABLE IF NOT EXISTS part_template (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
    code varchar(50) NOT NULL,
    version integer NOT NULL DEFAULT 1,
    label varchar(100) NOT NULL,
    pattern text NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT part_template_version_positive CHECK (version > 0),
    CONSTRAINT part_template_code_version_unique UNIQUE (code, version)
);

CREATE INDEX idx_part_template_code ON part_template (code);

CREATE INDEX idx_part_template_is_active ON part_template (is_active)
WHERE
    is_active = true;

CREATE INDEX idx_part_template_active_code ON part_template (code, version)
WHERE
    is_active = true;

COMMENT ON TABLE part_template IS 'Templates versionnés définissant la structure des caractéristiques des pièces';

COMMENT ON COLUMN part_template.code IS 'Code unique du template (le versionnement permet plusieurs versions)';

COMMENT ON COLUMN part_template.version IS 'Numéro de version du template';

COMMENT ON COLUMN part_template.label IS 'Libellé descriptif du template';

COMMENT ON COLUMN part_template.pattern IS 'Pattern de description ou règles associées au template';

COMMENT ON COLUMN part_template.is_active IS 'Indique si le template est actif';

-- ============================================================================
-- 2. TABLE : part_template_field
-- ============================================================================
-- Champs structurés de chaque template (number, text, enum)

CREATE TABLE IF NOT EXISTS part_template_field (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
    template_id uuid NOT NULL,
    field_key varchar(50) NOT NULL,
    label varchar(100) NOT NULL,
    field_type varchar(30) NOT NULL,
    unit varchar(20),
    required boolean DEFAULT false,
    sortable boolean DEFAULT true,
    sort_order integer NOT NULL,
    CONSTRAINT part_template_field_template_fk FOREIGN KEY (template_id) REFERENCES part_template (id) ON DELETE CASCADE,
    CONSTRAINT part_template_field_type_check CHECK (
        field_type IN ('number', 'text', 'enum')
    ),
    CONSTRAINT part_template_field_sort_order_positive CHECK (sort_order > 0),
    CONSTRAINT part_template_field_unique UNIQUE (template_id, field_key)
);

CREATE INDEX idx_part_template_field_template_id ON part_template_field (template_id);

CREATE INDEX idx_part_template_field_sort_order ON part_template_field (template_id, sort_order);

COMMENT ON TABLE part_template_field IS 'Champs structurés définissant les caractéristiques d''un template';

COMMENT ON COLUMN part_template_field.field_key IS 'Clé unique du champ au sein du template';

COMMENT ON COLUMN part_template_field.field_type IS 'Type de données : number, text ou enum';

COMMENT ON COLUMN part_template_field.unit IS 'Unité de mesure (pour les champs numériques)';

COMMENT ON COLUMN part_template_field.required IS 'Indique si le champ est obligatoire';

COMMENT ON COLUMN part_template_field.sortable IS 'Indique si le champ peut être trié';

COMMENT ON COLUMN part_template_field.sort_order IS 'Ordre d''affichage du champ';

-- ============================================================================
-- 3. TABLE : part_template_field_enum
-- ============================================================================
-- Valeurs autorisées pour les champs de type enum

CREATE TABLE IF NOT EXISTS part_template_field_enum (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
    field_id uuid NOT NULL,
    value varchar(50) NOT NULL,
    label varchar(100),
    CONSTRAINT part_template_field_enum_field_fk FOREIGN KEY (field_id) REFERENCES part_template_field (id) ON DELETE CASCADE,
    CONSTRAINT part_template_field_enum_unique UNIQUE (field_id, value)
);

CREATE INDEX idx_part_template_field_enum_field_id ON part_template_field_enum (field_id);

COMMENT ON TABLE part_template_field_enum IS 'Valeurs autorisées pour les champs de type enum';

COMMENT ON COLUMN part_template_field_enum.value IS 'Valeur technique de l''énumération';

COMMENT ON COLUMN part_template_field_enum.label IS 'Libellé affiché de la valeur';

-- ============================================================================
-- 4. MODIFICATION : stock_sub_family
-- ============================================================================
-- Ajout du lien template pour définir un template par défaut par sous-famille

ALTER TABLE stock_sub_family
ADD COLUMN IF NOT EXISTS template_id uuid;

ALTER TABLE stock_sub_family
DROP CONSTRAINT IF EXISTS stock_sub_family_template_fk;

ALTER TABLE stock_sub_family
ADD CONSTRAINT stock_sub_family_template_fk FOREIGN KEY (template_id) REFERENCES part_template (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_stock_sub_family_template_id ON stock_sub_family (template_id);

COMMENT ON COLUMN stock_sub_family.template_id IS 'Template de caractéristiques associé à cette sous-famille';

-- ============================================================================
-- 5. MODIFICATION : stock_item
-- ============================================================================
-- Ajout du versionnement template pour tracer la version utilisée

ALTER TABLE stock_item ADD COLUMN IF NOT EXISTS template_id uuid;

ALTER TABLE stock_item
ADD COLUMN IF NOT EXISTS template_version integer;

ALTER TABLE stock_item
DROP CONSTRAINT IF EXISTS stock_item_template_fk;

ALTER TABLE stock_item
ADD CONSTRAINT stock_item_template_fk FOREIGN KEY (template_id) REFERENCES part_template (id) ON DELETE RESTRICT;

ALTER TABLE stock_item
DROP CONSTRAINT IF EXISTS stock_item_template_version_positive;

ALTER TABLE stock_item
ADD CONSTRAINT stock_item_template_version_positive CHECK (
    template_version IS NULL
    OR template_version > 0
);

CREATE INDEX IF NOT EXISTS idx_stock_item_template_id ON stock_item (template_id);

CREATE INDEX IF NOT EXISTS idx_stock_item_template_version ON stock_item (template_id, template_version);

COMMENT ON COLUMN stock_item.template_id IS 'Template de caractéristiques utilisé pour cette pièce';

COMMENT ON COLUMN stock_item.template_version IS 'Version du template utilisée lors de la création de la pièce';

-- ============================================================================
-- 6. TABLE : stock_item_characteristic
-- ============================================================================
-- Valeurs des caractéristiques pour chaque pièce

CREATE TABLE IF NOT EXISTS stock_item_characteristic (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
    stock_item_id uuid NOT NULL,
    field_id uuid NOT NULL,
    value_text text,
    value_number numeric,
    value_enum varchar(50),
    CONSTRAINT stock_item_characteristic_item_fk FOREIGN KEY (stock_item_id) REFERENCES stock_item (id) ON DELETE CASCADE,
    CONSTRAINT stock_item_characteristic_field_fk FOREIGN KEY (field_id) REFERENCES part_template_field (id) ON DELETE RESTRICT,
    CONSTRAINT stock_item_characteristic_unique UNIQUE (stock_item_id, field_id),
    CONSTRAINT stock_item_characteristic_single_value_check CHECK (
        (
            value_text IS NOT NULL
            AND value_number IS NULL
            AND value_enum IS NULL
        )
        OR (
            value_text IS NULL
            AND value_number IS NOT NULL
            AND value_enum IS NULL
        )
        OR (
            value_text IS NULL
            AND value_number IS NULL
            AND value_enum IS NOT NULL
        )
    )
);

CREATE INDEX idx_stock_item_characteristic_item_id ON stock_item_characteristic (stock_item_id);

CREATE INDEX idx_stock_item_characteristic_field_id ON stock_item_characteristic (field_id);

CREATE INDEX idx_stock_item_characteristic_value_number ON stock_item_characteristic (value_number)
WHERE
    value_number IS NOT NULL;

CREATE INDEX idx_stock_item_characteristic_value_enum ON stock_item_characteristic (value_enum)
WHERE
    value_enum IS NOT NULL;

CREATE INDEX idx_stock_item_char_item_field ON stock_item_characteristic (stock_item_id, field_id);

COMMENT ON TABLE stock_item_characteristic IS 'Valeurs des caractéristiques pour chaque pièce selon son template';

COMMENT ON COLUMN stock_item_characteristic.value_text IS 'Valeur textuelle (pour field_type = text)';

COMMENT ON COLUMN stock_item_characteristic.value_number IS 'Valeur numérique (pour field_type = number)';

COMMENT ON COLUMN stock_item_characteristic.value_enum IS 'Valeur énumérée (pour field_type = enum)';

-- ============================================================================
-- FIN DE LA MIGRATION
-- ============================================================================