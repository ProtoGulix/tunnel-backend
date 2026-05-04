-- ============================================================================
-- action_category.sql - Catégories d'actions maintenance
-- ============================================================================
-- Catégories haut niveau (DEP, FAB, PREV, SUP, BAT)
-- Avec couleur hexadécimale pour UI
--
-- @see action_subcategory.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.action_category (
    id INTEGER PRIMARY KEY,
    
    -- Code catégorie (ex: DEP, FAB, PREV, SUP, BAT)
    code VARCHAR(255) UNIQUE,
    
    -- Nom catégorie
    name TEXT NOT NULL,
    
    -- Couleur hexadécimale pour UI (ex: #FF5733)
    color VARCHAR(255)
);

-- Séquence pour ID
CREATE SEQUENCE IF NOT EXISTS public.action_category_id_seq
    AS INTEGER
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.action_category_id_seq OWNED BY public.action_category.id;
ALTER TABLE public.action_category ALTER COLUMN id SET DEFAULT nextval('public.action_category_id_seq'::regclass);

-- Index
CREATE INDEX IF NOT EXISTS action_category_code_index ON public.action_category(code);

-- Commentaires
COMMENT ON TABLE public.action_category IS 'Catégories d''actions maintenance (haut niveau)';
COMMENT ON COLUMN public.action_category.color IS 'Couleur hexadécimale pour badges UI';

-- Données de référence
-- INSERT INTO action_category (code, name, color) VALUES
--   ('DEP', 'Dépannage', '#ef4444'),
--   ('FAB', 'Fabrication', '#8b5cf6'),
--   ('PREV', 'Préventif', '#3b82f6'),
--   ('SUP', 'Support/Administratif', '#f59e0b'),
--   ('BAT', 'Bâtiment/Nettoyage', '#10b981');
