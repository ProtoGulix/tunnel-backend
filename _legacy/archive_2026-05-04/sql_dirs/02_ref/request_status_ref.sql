-- ============================================================================
-- request_status_ref.sql - Référentiel statuts des demandes d'intervention
-- ============================================================================
-- Statuts du cycle de vie d'une demande d'intervention (DI-YYYY-NNNN).
--
-- @see intervention_request.sql (01_core)
-- @see request_status_log.sql   (01_core)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.request_status_ref (
    code VARCHAR(50) PRIMARY KEY,
    label TEXT NOT NULL,
    color VARCHAR(7) NOT NULL, -- Couleur hexadécimale pour UI (#RRGGBB)
    sort_order INTEGER NOT NULL
);

COMMENT ON TABLE public.request_status_ref IS 'Référentiel statuts des demandes d''intervention';

COMMENT ON COLUMN public.request_status_ref.color IS 'Couleur hexadécimale (#RRGGBB) pour affichage UI';

COMMENT ON COLUMN public.request_status_ref.sort_order IS 'Ordre d''affichage dans les listes';

-- Données initiales
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
    )
ON CONFLICT (code) DO NOTHING;