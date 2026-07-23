"""Créer la table audit_rule (règles routine/sensible administrables par champ)

Remplace les dicts en dur _SILENT_ENTITY_TYPES / _SILENT_FIELDS_BY_ENTITY de
api/utils/audit.py par une table administrable depuis /admin/audit-rules.

Une règle est identifiée par (entity_type, field) :
  - field = NULL      : règle par défaut de l'entité (ex. création sans diff)
  - field = 'assigned_to' etc. : règle spécifique à un champ modifié

is_routine=True  → default_reason_code est injecté automatiquement par le front,
                   aucun dialog affiché.
is_routine=False → le front doit demander une raison parmi les codes actifs
                   compatibles avec l'entité (picker), default_reason_code est NULL.

Le seed reprend à l'identique le comportement actuel de _SILENT_FIELDS_BY_ENTITY
pour ne rien changer en production au moment du déploiement.

On corrige aussi au passage le scope de la raison ROUTINE, qui n'incluait que
['task', 'action'] alors que _SILENT_ENTITY_TYPES couvrait déjà request/
intervention/purchase_request (incohérence latente entre le seed 007 et le
code Python, jamais alignée depuis).

Revision ID: 017_audit_rule_table
Revises: 016_pr_single_closed_basket
Create Date: 2026-07-22
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "017_audit_rule_table"
down_revision: Union[str, None] = "016_pr_single_closed_basket"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE audit_rule (
            id BIGSERIAL PRIMARY KEY,
            entity_type TEXT NOT NULL,
            field TEXT,
            is_routine BOOLEAN NOT NULL DEFAULT FALSE,
            default_reason_code TEXT REFERENCES audit_reason_code(code),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT audit_rule_entity_field_uniq UNIQUE (entity_type, field),
            CONSTRAINT audit_rule_routine_needs_default CHECK (
                (is_routine = FALSE) OR (default_reason_code IS NOT NULL)
            )
        )
    """)

    op.execute("""
        CREATE INDEX idx_audit_rule_entity_type ON audit_rule(entity_type)
    """)

    # Aligner le scope de ROUTINE sur les entités réellement silencieuses
    # côté Python (_SILENT_ENTITY_TYPES incluait déjà request/intervention/
    # purchase_request, jamais reporté dans le seed de la migration 007).
    op.execute("""
        UPDATE audit_reason_code
        SET entity_types = ARRAY['task', 'action', 'request', 'intervention', 'purchase_request']
        WHERE code = 'ROUTINE'
    """)

    # ── Seed : reprise à l'identique de _SILENT_FIELDS_BY_ENTITY / _SILENT_ENTITY_TYPES ──

    # Règles par défaut d'entité (field NULL) : toutes silencieuses aujourd'hui
    for entity_type in ("task", "action", "request", "intervention", "purchase_request"):
        op.execute(f"""
            INSERT INTO audit_rule (entity_type, field, is_routine, default_reason_code)
            VALUES ('{entity_type}', NULL, TRUE, 'ROUTINE')
            ON CONFLICT (entity_type, field) DO NOTHING
        """)

    _silent_fields = {
        "intervention": ["printed_fiche", "title"],
        "task": ["status", "sort_order", "skip_reason"],
        "request": [
            "status_to", "machine_id", "demandeur_nom", "service_id",
            "description", "is_system", "suggested_type_inter",
            "type_inter", "tech_initials", "priority", "reported_date", "changed_by",
        ],
    }
    for entity_type, fields in _silent_fields.items():
        for field in fields:
            op.execute(f"""
                INSERT INTO audit_rule (entity_type, field, is_routine, default_reason_code)
                VALUES ('{entity_type}', '{field}', TRUE, 'ROUTINE')
                ON CONFLICT (entity_type, field) DO NOTHING
            """)

    # Champs explicitement sensibles aujourd'hui (dialog obligatoire, cf.
    # commentaires _SILENT_FIELDS_BY_ENTITY et migration 008) : pas de
    # default_reason_code, is_routine=FALSE.
    _sensitive_fields = {
        "task": ["due_date", "assigned_to"],
    }
    for entity_type, fields in _sensitive_fields.items():
        for field in fields:
            op.execute(f"""
                INSERT INTO audit_rule (entity_type, field, is_routine, default_reason_code)
                VALUES ('{entity_type}', '{field}', FALSE, NULL)
                ON CONFLICT (entity_type, field) DO NOTHING
            """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_rule")
    op.execute("""
        UPDATE audit_reason_code
        SET entity_types = ARRAY['task', 'action']
        WHERE code = 'ROUTINE'
    """)
