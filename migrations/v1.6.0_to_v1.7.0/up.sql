-- Migration v1.6.0 -> v1.7.0 (UP)
-- Module Demandes d'Intervention : request_status_ref, intervention_request,
-- request_status_log, triggers de statut et de code DI-YYYY-NNNN

-- ═══════════════════════════════════════════════════════════════
-- 1. RÉFÉRENTIEL DES STATUTS
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE public.request_status_ref (
    code VARCHAR(50) PRIMARY KEY,
    label TEXT NOT NULL,
    color VARCHAR(7) NOT NULL,
    sort_order INTEGER NOT NULL
);

INSERT INTO
    public.request_status_ref (
        code,
        label,
        color,
        sort_order
    )
VALUES (
        'nouvelle',
        'Nouvelle',
        '#3b82f6',
        1
    ),
    (
        'en_attente',
        'En attente',
        '#f59e0b',
        2
    ),
    (
        'acceptee',
        'Acceptée',
        '#22c55e',
        3
    ),
    (
        'rejetee',
        'Rejetée',
        '#ef4444',
        4
    ),
    (
        'cloturee',
        'Clôturée',
        '#6b7280',
        5
    );

-- ═══════════════════════════════════════════════════════════════
-- 2. TABLE PRINCIPALE
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE public.intervention_request (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    -- DI-YYYY-NNNN, généré par trigger BEFORE INSERT
    code VARCHAR(255) UNIQUE NOT NULL,
    machine_id UUID NOT NULL REFERENCES public.machine (id) ON DELETE RESTRICT,
    demandeur_nom TEXT NOT NULL,
    demandeur_service TEXT,
    description TEXT NOT NULL,
    -- Positionné exclusivement par trigger via request_status_log (pas de DEFAULT)
    statut VARCHAR(50) NOT NULL REFERENCES public.request_status_ref (code),
    -- NULL tant qu'aucune intervention n'est créée depuis la demande
    intervention_id UUID UNIQUE REFERENCES public.intervention (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- motif_rejet vit dans request_status_log.notes à la transition → rejetee

-- ═══════════════════════════════════════════════════════════════
-- 3. LOG DES TRANSITIONS DE STATUT
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE public.request_status_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    request_id UUID NOT NULL REFERENCES public.intervention_request (id) ON DELETE CASCADE,
    -- NULL à la création (première ligne du log)
    status_from VARCHAR(50) REFERENCES public.request_status_ref (code),
    status_to VARCHAR(50) NOT NULL REFERENCES public.request_status_ref (code),
    -- UUID Directus, nullable (demande publique / sans authentification)
    changed_by UUID,
    notes TEXT,
    date TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- status_from : cohérence enforced en trigger (sous-requête interdite en CHECK)

-- ═══════════════════════════════════════════════════════════════
-- 4. TRIGGERS
-- ═══════════════════════════════════════════════════════════════

-- 4.1 Génération du code DI-YYYY-NNNN
-- BEFORE INSERT : code présent avant insertion, contrainte NOT NULL tenue

CREATE OR REPLACE FUNCTION public.fn_generate_request_code()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_year TEXT := to_char(now(), 'YYYY');
    v_seq  INT;
BEGIN
    SELECT COUNT(*) + 1
    INTO v_seq
    FROM public.intervention_request
    WHERE code LIKE 'DI-' || v_year || '-%';

    NEW.code := 'DI-' || v_year || '-' || lpad(v_seq::TEXT, 4, '0');
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_request_code
    BEFORE INSERT ON public.intervention_request
    FOR EACH ROW EXECUTE FUNCTION public.fn_generate_request_code();

-- 4.2 Initialisation : INSERT request → INSERT log
--     Le log INSERT déclenche trg_apply_request_status qui pose statut = 'nouvelle'.
--     trg_log_request_status_change est court-circuité pendant cet UPDATE interne
--     via le flag de session app.skip_request_status_log.

CREATE OR REPLACE FUNCTION public.fn_init_request_status_log()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    PERFORM set_config('app.skip_request_status_log', 'true', true);

    INSERT INTO public.request_status_log (request_id, status_from, status_to, notes)
    VALUES (NEW.id, NULL, 'nouvelle', 'Création demande');

    PERFORM set_config('app.skip_request_status_log', 'false', true);
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_init_request_status_log
    AFTER INSERT ON public.intervention_request
    FOR EACH ROW EXECUTE FUNCTION public.fn_init_request_status_log();

-- 4.3 Log → actualise statut sur intervention_request

CREATE OR REPLACE FUNCTION public.fn_apply_request_status()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    UPDATE public.intervention_request
    SET statut = NEW.status_to
    WHERE id = NEW.request_id;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_apply_request_status
    AFTER INSERT ON public.request_status_log
    FOR EACH ROW EXECUTE FUNCTION public.fn_apply_request_status();

-- 4.4 UPDATE statut → INSERT log (transitions applicatives)
--     Court-circuité si flag de session actif (init interne) ou statut inchangé.

CREATE OR REPLACE FUNCTION public.fn_log_request_status_change()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF current_setting('app.skip_request_status_log', true) = 'true' THEN
        RETURN NEW;
    END IF;

    IF NEW.statut IS DISTINCT FROM OLD.statut THEN
        -- Vérifie que le statut actuel correspond à la dernière entrée du log
        IF OLD.statut IS DISTINCT FROM (
            SELECT status_to FROM public.request_status_log
            WHERE request_id = NEW.id
            ORDER BY date DESC
            LIMIT 1
        ) THEN
            RAISE EXCEPTION
                'Incohérence statut : statut actuel "%" ne correspond pas à la dernière entrée du log',
                OLD.statut;
        END IF;

        INSERT INTO public.request_status_log (request_id, status_from, status_to)
        VALUES (NEW.id, OLD.statut, NEW.statut);
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_log_request_status_change
    AFTER UPDATE OF statut ON public.intervention_request
    FOR EACH ROW EXECUTE FUNCTION public.fn_log_request_status_change();

-- 4.5 updated_at — convention Tunnel (update_updated_at_column déjà définie dans le schéma)

CREATE TRIGGER trg_request_updated_at
    BEFORE UPDATE ON public.intervention_request
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();