-- ============================================================================
-- MODIFICATION : stock_item
-- ============================================================================
-- Ajout du versionnement du template pour chaque pièce
-- Permet de tracer quelle version du template a été utilisée
-- ============================================================================

ALTER TABLE stock_item ADD COLUMN IF NOT EXISTS template_id uuid;

ALTER TABLE stock_item
ADD COLUMN IF NOT EXISTS template_version integer;

-- Ajout de la clé étrangère
ALTER TABLE stock_item
DROP CONSTRAINT IF EXISTS stock_item_template_fk;

ALTER TABLE stock_item
ADD CONSTRAINT stock_item_template_fk FOREIGN KEY (template_id) REFERENCES part_template (id) ON DELETE RESTRICT;

-- Contrainte de version positive
ALTER TABLE stock_item
DROP CONSTRAINT IF EXISTS stock_item_template_version_positive;

ALTER TABLE stock_item
ADD CONSTRAINT stock_item_template_version_positive CHECK (
    template_version IS NULL
    OR template_version > 0
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_stock_item_template_id ON stock_item (template_id);

CREATE INDEX IF NOT EXISTS idx_stock_item_template_version ON stock_item (template_id, template_version);

-- Commentaires
COMMENT ON COLUMN stock_item.template_id IS 'Template de caractéristiques utilisé pour cette pièce';

COMMENT ON COLUMN stock_item.template_version IS 'Version du template utilisée lors de la création de la pièce';