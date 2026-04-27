-- Migration v1.7.0 -> v1.6.0 (DOWN)
-- Rollback du module Demandes d'Intervention

-- ═══════════════════════════════════════════════════════════════
-- 1. TRIGGERS & FONCTIONS
-- ═══════════════════════════════════════════════════════════════

DROP TRIGGER IF EXISTS trg_request_updated_at ON public.intervention_request;

DROP TRIGGER IF EXISTS trg_log_request_status_change ON public.intervention_request;

DROP TRIGGER IF EXISTS trg_apply_request_status ON public.request_status_log;

DROP TRIGGER IF EXISTS trg_init_request_status_log ON public.intervention_request;

DROP TRIGGER IF EXISTS trg_request_code ON public.intervention_request;

DROP FUNCTION IF EXISTS public.fn_log_request_status_change ();

DROP FUNCTION IF EXISTS public.fn_apply_request_status ();

DROP FUNCTION IF EXISTS public.fn_init_request_status_log ();

DROP FUNCTION IF EXISTS public.fn_generate_request_code ();

-- ═══════════════════════════════════════════════════════════════
-- 2. TABLES (ordre inverse des FK)
-- ═══════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS public.request_status_log;

DROP TABLE IF EXISTS public.intervention_request;

DROP TABLE IF EXISTS public.request_status_ref;