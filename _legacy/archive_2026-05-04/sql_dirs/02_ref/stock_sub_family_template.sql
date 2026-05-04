-- ============================================================================
-- MODIFICATION : stock_sub_family
-- ============================================================================
-- Ajout du lien entre sous-famille et template
-- Permet d'associer un template par défaut à une sous-famille
-- ============================================================================

ALTER TABLE stock_sub_family
ADD COLUMN IF NOT EXISTS template_id uuid;

-- Ajout de la clé étrangère
ALTER TABLE stock_sub_family
DROP CONSTRAINT IF EXISTS stock_sub_family_template_fk;

ALTER TABLE stock_sub_family
ADD CONSTRAINT stock_sub_family_template_fk
    FOREIGN KEY (template_id)
    REFERENCES part_template(id)
    ON DELETE SET NULL;

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_stock_sub_family_template_id ON stock_sub_family(template_id);

-- Commentaire
COMMENT ON COLUMN stock_sub_family.template_id IS 'Template de caractéristiques associé à cette sous-famille';
