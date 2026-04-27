-- ============================================================================
-- action_subcategory.sql - Sous-catégories d'actions
-- ============================================================================
-- Sous-catégories granulaires pour classification actions
--
-- @see action_category.sql
-- @see intervention_action.sql (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.action_subcategory (
    id INTEGER PRIMARY KEY,
    
    -- Relation catégorie parent
    category_id INTEGER, -- FK vers action_category
    
    -- Code sous-catégorie (ex: DEP_ELEC, FAB_SOUD)
    code VARCHAR(255) UNIQUE,
    
    -- Nom sous-catégorie
    name TEXT NOT NULL
);

-- Séquence pour ID
CREATE SEQUENCE IF NOT EXISTS public.action_subcategory_id_seq
    AS INTEGER
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.action_subcategory_id_seq OWNED BY public.action_subcategory.id;
ALTER TABLE public.action_subcategory ALTER COLUMN id SET DEFAULT nextval('public.action_subcategory_id_seq'::regclass);

-- Commentaires
COMMENT ON TABLE public.action_subcategory IS 'Sous-catégories d''actions (classification granulaire)';
COMMENT ON COLUMN public.action_subcategory.code IS 'Code unique sous-catégorie (ex: DEP_ELEC)';

-- Données de référence exemples
-- INSERT INTO action_subcategory (category_id, code, name) VALUES
--   ((SELECT id FROM action_category WHERE code='DEP'), 'DEP_ELEC', 'Dépannage Électrique'),
--   ((SELECT id FROM action_category WHERE code='DEP'), 'DEP_MECA', 'Dépannage Mécanique'),
--   ((SELECT id FROM action_category WHERE code='PREV'), 'PREV_GRAIS', 'Graissage Préventif'),
--   ((SELECT id FROM action_category WHERE code='SUP'), 'SUP_INV', 'Inventaire');
