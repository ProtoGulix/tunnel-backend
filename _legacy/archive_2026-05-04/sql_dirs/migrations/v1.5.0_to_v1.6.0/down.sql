-- Migration v1.5.0 -> v1.6.0 (DOWN)
-- Restauration des colonnes supprimées dans purchase_request

ALTER TABLE public.purchase_request
    ADD COLUMN IF NOT EXISTS requester_name  CHARACTER VARYING,
    ADD COLUMN IF NOT EXISTS quantity_requested INTEGER,
    ADD COLUMN IF NOT EXISTS urgent          BOOLEAN;

-- Réhydrater requester_name depuis requested_by
UPDATE public.purchase_request
SET requester_name = requested_by
WHERE requester_name IS NULL;
