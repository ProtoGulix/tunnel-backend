"""Audit log centralisé — tables audit_reason_code, audit_log, fonction fn_audit_log_decision

Crée le système d'audit log permanent qui trace toutes les mutations métier.
Backfille les anciens logs depuis intervention_status_log et request_status_log.

Triggers conservés intentionnellement (phase 1) :
  - trg_init_status_log / trg_log_status_change  (sur intervention)
  - trg_init_request_status_log / trg_log_request_status_change  (sur intervention_request)
Ces triggers continuent à alimenter intervention_status_log et request_status_log
en parallèle pendant la période de validation de audit_log en production.
Ils seront supprimés en phase 2 (migration 003_cleanup_legacy_triggers) une fois
audit_log validé (~3 semaines après le déploiement de cette migration).

Revision ID: 002_audit_log
Revises: 001_fk_tunnel_user
Create Date: 2026-05-12
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_audit_log"
down_revision: Union[str, None] = "001_fk_tunnel_user"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # ── 1. audit_reason_code ──────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE audit_reason_code (
            id           SERIAL PRIMARY KEY,
            code         VARCHAR(100) UNIQUE NOT NULL,
            label        VARCHAR(255) NOT NULL,
            category     VARCHAR(50)  NOT NULL,
            entity_types TEXT[],
            decision_types TEXT[],
            color        VARCHAR(7),
            description  TEXT,
            is_active    BOOLEAN NOT NULL DEFAULT TRUE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX idx_audit_reason_code_active
            ON audit_reason_code (code, is_active)
    """)

    # ── 2. audit_log ──────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE audit_log (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_type    VARCHAR(50)  NOT NULL,
            entity_id      UUID         NOT NULL,
            decision_type  VARCHAR(100) NOT NULL,
            old_value      JSONB,
            new_value      JSONB,
            reason_code_id INT REFERENCES audit_reason_code(id),
            reason_text    TEXT,
            changed_by     UUID,
            is_system      BOOLEAN NOT NULL DEFAULT FALSE,
            logged_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX idx_audit_log_entity ON audit_log (entity_type, entity_id)")
    op.execute("CREATE INDEX idx_audit_log_time   ON audit_log (logged_at DESC)")
    op.execute("CREATE INDEX idx_audit_log_reason ON audit_log (reason_code_id)")

    # ── 3. Seed des raisons ───────────────────────────────────────────────────
    op.execute("""
        INSERT INTO audit_reason_code
            (code, label, category, entity_types, color, description)
        VALUES
            ('PURCHASE_RECEIVED',       'Demande d''achat reçue',      'system', ARRAY['intervention'],              '#10b981', 'Auto : toutes DA reçues'),
            ('HEALTH_THRESHOLD',        'Seuil santé atteint',         'system', ARRAY['intervention'],              '#f59e0b', 'Auto : santé > seuil'),
            ('EQUIPMENT_FAILURE',       'Panne équipement',            'manual', ARRAY['intervention'],              '#ef4444', 'Client signale panne'),
            ('CLIENT_REQUEST',          'Demande client',              'manual', ARRAY['intervention','task'],       '#8b5cf6', 'Client demande priorité'),
            ('RECLASSIFICATION',        'Reclassification',            'manual', ARRAY['intervention'],              '#ec4899', 'Erreur d''analyse'),
            ('TECHNICIAN_UNAVAILABLE',  'Technicien indisponible',     'manual', ARRAY['task'],                     '#6b7280', 'Congé / maladie'),
            ('SUPPLIER_DELAY',          'Délai fournisseur',           'manual', ARRAY['purchase_request'],         '#f97316', 'Dépassement délai'),
            ('PRIORITY_BOOST',          'Accélération demandée',       'manual', ARRAY['intervention','task'],      '#06b6d4', 'Nécessite plus vite'),
            ('RESOURCE_CONSTRAINT',     'Contrainte ressource',        'manual', ARRAY['task','intervention'],      '#a855f7', 'Manque de ressource'),
            ('OTHER',                   'Autre raison',                'user',   NULL,                              '#9ca3af', 'À justifier en texte libre'),
            ('LEGACY_STATUS_CHANGE',    'Changement historique',       'manual', NULL,                              '#d1d5db', 'Logs migrés depuis les anciennes tables de statut')
    """)

    # ── 4. Backfill depuis intervention_status_log ────────────────────────────
    op.execute("""
        INSERT INTO audit_log (
            entity_type, entity_id, decision_type,
            old_value, new_value,
            reason_code_id, reason_text,
            changed_by, is_system, logged_at
        )
        SELECT
            'intervention',
            isl.intervention_id,
            'status_changed',
            CASE WHEN isl.status_from IS NOT NULL
                 THEN jsonb_build_object('status', isl.status_from)
                 ELSE NULL END,
            CASE WHEN isl.status_to IS NOT NULL
                 THEN jsonb_build_object('status', isl.status_to)
                 ELSE NULL END,
            (SELECT id FROM audit_reason_code WHERE code = 'LEGACY_STATUS_CHANGE'),
            isl.notes,
            isl.technician_id,
            FALSE,
            isl.date
        FROM intervention_status_log isl
        WHERE NOT EXISTS (
            SELECT 1 FROM audit_log al
            WHERE al.entity_type = 'intervention'
              AND al.entity_id   = isl.intervention_id
              AND al.logged_at   = isl.date
              AND al.decision_type = 'status_changed'
        )
    """)

    # ── 5. Backfill depuis request_status_log ────────────────────────────────
    op.execute("""
        INSERT INTO audit_log (
            entity_type, entity_id, decision_type,
            old_value, new_value,
            reason_code_id, reason_text,
            changed_by, is_system, logged_at
        )
        SELECT
            'request',
            rsl.request_id,
            'status_changed',
            CASE WHEN rsl.status_from IS NOT NULL
                 THEN jsonb_build_object('status', rsl.status_from)
                 ELSE NULL END,
            CASE WHEN rsl.status_to IS NOT NULL
                 THEN jsonb_build_object('status', rsl.status_to)
                 ELSE NULL END,
            (SELECT id FROM audit_reason_code WHERE code = 'LEGACY_STATUS_CHANGE'),
            rsl.notes,
            rsl.changed_by,
            FALSE,
            rsl.date
        FROM request_status_log rsl
        WHERE NOT EXISTS (
            SELECT 1 FROM audit_log al
            WHERE al.entity_type = 'request'
              AND al.entity_id   = rsl.request_id
              AND al.logged_at   = rsl.date
              AND al.decision_type = 'status_changed'
        )
    """)

    # ── 6. Fonction PostgreSQL fn_audit_log_decision() ────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION public.fn_audit_log_decision(
            p_entity_type   VARCHAR,
            p_entity_id     UUID,
            p_decision_type VARCHAR,
            p_old_value     JSONB,
            p_new_value     JSONB,
            p_reason_code   VARCHAR,
            p_reason_text   TEXT    DEFAULT NULL,
            p_changed_by    UUID    DEFAULT NULL,
            p_is_system     BOOLEAN DEFAULT FALSE
        )
        RETURNS UUID AS $$
        DECLARE
            v_reason_id       INT;
            v_reason_category VARCHAR;
            v_log_id          UUID;
        BEGIN
            SELECT id, category
              INTO v_reason_id, v_reason_category
              FROM audit_reason_code
             WHERE code = p_reason_code AND is_active = TRUE;

            IF v_reason_id IS NULL THEN
                RAISE EXCEPTION 'Raison % inconnue ou inactive', p_reason_code;
            END IF;

            IF p_reason_code = 'OTHER' AND (p_reason_text IS NULL OR trim(p_reason_text) = '') THEN
                RAISE EXCEPTION 'reason_text obligatoire quand reason_code = OTHER';
            END IF;

            IF p_is_system = FALSE AND p_changed_by IS NULL THEN
                RAISE EXCEPTION 'changed_by obligatoire pour une mutation manuelle';
            END IF;

            IF p_is_system = TRUE AND v_reason_category != 'system' THEN
                RAISE EXCEPTION 'La raison % n''est pas une raison système', p_reason_code;
            END IF;

            INSERT INTO public.audit_log (
                entity_type, entity_id, decision_type,
                old_value, new_value,
                reason_code_id, reason_text,
                changed_by, is_system, logged_at
            ) VALUES (
                p_entity_type, p_entity_id, p_decision_type,
                p_old_value, p_new_value,
                v_reason_id, p_reason_text,
                p_changed_by, p_is_system,
                now()
            ) RETURNING id INTO v_log_id;

            RETURN v_log_id;

        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'fn_audit_log_decision: %', SQLERRM;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS public.fn_audit_log_decision CASCADE")
    op.execute("DROP TABLE IF EXISTS audit_log CASCADE")
    op.execute("DROP TABLE IF EXISTS audit_reason_code CASCADE")
