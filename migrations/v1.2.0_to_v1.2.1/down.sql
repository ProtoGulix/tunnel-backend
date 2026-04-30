-- Rollback v1.2.1 -> v1.2.0
-- Restore previous machine schema

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'machine_equipement_mere_foreign'
    ) THEN
        ALTER TABLE public.machine
            DROP CONSTRAINT machine_equipement_mere_foreign;
    END IF;
END $$;

ALTER TABLE public.machine
    ALTER COLUMN code TYPE VARCHAR(255),
    ALTER COLUMN code DROP DEFAULT,
    ALTER COLUMN name TYPE TEXT,
    ALTER COLUMN name DROP NOT NULL,
    ALTER COLUMN no_machine TYPE VARCHAR(255),
    ALTER COLUMN affectation TYPE CHAR(255),
    ALTER COLUMN fabricant TYPE VARCHAR(255),
    ALTER COLUMN numero_serie TYPE VARCHAR(255);

ALTER TABLE public.machine
    ADD COLUMN IF NOT EXISTS type_equipement VARCHAR(255);
