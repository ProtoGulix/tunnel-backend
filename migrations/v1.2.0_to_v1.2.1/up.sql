-- Migration v1.2.0 -> v1.2.1
-- Align machine schema with production DDL

-- Ensure name is not null before constraint
UPDATE public.machine
SET name = code
WHERE name IS NULL;

-- Drop deprecated column
ALTER TABLE public.machine
    DROP COLUMN IF EXISTS type_equipement;

-- Supprimer temporairement les vues qui dépendent de machine.code
DROP VIEW IF EXISTS preventive_suggestion_by_status;

-- Column adjustments
DO $$
DECLARE
    no_machine_type TEXT;
BEGIN
    -- Vérifier le type actuel de no_machine
    SELECT data_type INTO no_machine_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'machine'
      AND column_name = 'no_machine';
    
    -- Si no_machine est de type text/varchar, le convertir en INTEGER
    IF no_machine_type IN ('character varying', 'text', 'character') THEN
        ALTER TABLE public.machine
            ALTER COLUMN no_machine TYPE INTEGER USING NULLIF(no_machine, '')::INTEGER;
    END IF;
    
    -- Autres ajustements de colonnes
    ALTER TABLE public.machine
        ALTER COLUMN code TYPE VARCHAR(50),
        ALTER COLUMN code SET DEFAULT NULL,
        ALTER COLUMN name TYPE VARCHAR(200),
        ALTER COLUMN name SET NOT NULL,
        ALTER COLUMN affectation TYPE VARCHAR(255),
        ALTER COLUMN fabricant TYPE VARCHAR,
        ALTER COLUMN numero_serie TYPE VARCHAR;
END $$;

-- Indexes (safe to re-run)
CREATE INDEX IF NOT EXISTS machine_code_index ON public.machine(code);
CREATE INDEX IF NOT EXISTS machine_equipement_mere_index ON public.machine(equipement_mere);

-- FK for parent equipment
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'machine_equipement_mere_foreign'
    ) THEN
        ALTER TABLE public.machine
            ADD CONSTRAINT machine_equipement_mere_foreign
            FOREIGN KEY (equipement_mere) REFERENCES public.machine(id)
            ON UPDATE NO ACTION
            ON DELETE NO ACTION;
    END IF;
END $$;

-- Recréer la vue preventive_suggestion_by_status
CREATE OR REPLACE VIEW preventive_suggestion_by_status AS
SELECT 
  ps.id,
  ps.intervention_action_id,
  ps.machine_id,
  ps.preventive_code,
  ps.preventive_label,
  ps.score,
  ps.status,
  ps.detected_at,
  ps.handled_at,
  ps.handled_by,
  m.code AS machine_code,
  m.name AS machine_name
FROM preventive_suggestion ps
LEFT JOIN machine m ON ps.machine_id = m.id
ORDER BY ps.detected_at DESC;
