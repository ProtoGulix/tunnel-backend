-- ============================================================================
-- TABLE : part_template
-- ============================================================================
-- Stocke les templates de caractérisation des pièces avec versionnement
-- Un template définit la structure des caractéristiques pour un type de pièce
-- ============================================================================

CREATE TABLE IF NOT EXISTS part_template (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    code varchar(50) NOT NULL,
    version integer NOT NULL DEFAULT 1,
    label varchar(100) NOT NULL,
    pattern text NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    
    -- Contraintes
    CONSTRAINT part_template_version_positive CHECK (version > 0),
    CONSTRAINT part_template_code_version_unique UNIQUE (code, version)
);

-- Index pour optimiser les requêtes
CREATE INDEX idx_part_template_code ON part_template(code);
CREATE INDEX idx_part_template_is_active ON part_template(is_active) WHERE is_active = true;
CREATE INDEX idx_part_template_active_code ON part_template(code, version) WHERE is_active = true;

-- Commentaires
COMMENT ON TABLE part_template IS 'Templates versionnés définissant la structure des caractéristiques des pièces';
COMMENT ON COLUMN part_template.code IS 'Code unique du template (le versionnement permet plusieurs versions)';
COMMENT ON COLUMN part_template.version IS 'Numéro de version du template';
COMMENT ON COLUMN part_template.label IS 'Libellé descriptif du template';
COMMENT ON COLUMN part_template.pattern IS 'Pattern de description ou règles associées au template';
COMMENT ON COLUMN part_template.is_active IS 'Indique si le template est actif';
