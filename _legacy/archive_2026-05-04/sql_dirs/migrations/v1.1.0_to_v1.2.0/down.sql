-- Rollback v1.2.0 -> v1.1.0
-- Remove equipement_class and machine relation

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'machine_equipement_class_id_fkey'
    ) THEN
        ALTER TABLE public.machine
            DROP CONSTRAINT machine_equipement_class_id_fkey;
    END IF;
END $$;

DROP INDEX IF EXISTS machine_equipement_class_index;

ALTER TABLE public.machine
    DROP COLUMN IF EXISTS equipement_class_id;

DROP INDEX IF EXISTS equipement_class_code_index;

DROP TABLE IF EXISTS public.equipement_class;
