-- ============================================================================
-- machine_hours.sql - Compteur heures par machine
-- ============================================================================
-- Table de synthèse du cumul heures d'intervention par machine.
-- Mise à jour automatiquement par le trigger trg_machine_hours_update
-- après chaque INSERT ou UPDATE de time_spent sur intervention_action.
--
-- @see machine.sql              (01_core)
-- @see intervention_action.sql  (01_core)
-- @see trg_preventive_v2.sql    (05_triggers)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.machine_hours (
    machine_id  UUID          PRIMARY KEY REFERENCES public.machine (id) ON DELETE CASCADE,
    hours_total NUMERIC(10,2) NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Commentaires
COMMENT ON TABLE  public.machine_hours             IS 'Compteur total heures par machine, mis à jour par trigger depuis intervention_action.';
COMMENT ON COLUMN public.machine_hours.hours_total IS 'Cumul des time_spent de toutes les actions liées à la machine (jamais négatif).';
