"""Ajouter la raison ROUTINE (catégorie auto) pour les mutations silencieuses

Les mutations "courantes" (création de tâche, saisie d'action par le tech)
n'ont pas besoin d'une raison explicite côté UX. Le front envoie ROUTINE
silencieusement sans afficher de sélecteur à l'utilisateur.

La catégorie 'auto' est distincte de :
  - 'system' : mutations internes/triggers (jamais initiées par le front)
  - 'manual' / 'user' : raisons affichées dans le picker UX

Revision ID: 007_audit_silent_routine
Revises: 006_remove_pr_intervention_id_legacy
Create Date: 2026-05-18
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "007_audit_silent_routine"
down_revision: Union[str, None] = "006_remove_pr_legacy_fk"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO audit_reason_code
            (code, label, category, entity_types, color, description)
        VALUES
            (
                'ROUTINE',
                'Opération courante',
                'auto',
                ARRAY['task', 'action'],
                '#94a3b8',
                'Envoyée silencieusement par le front pour les mutations courantes (création tâche, saisie action). Jamais affichée à l''utilisateur.'
            )
        ON CONFLICT (code) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM audit_reason_code WHERE code = 'ROUTINE'")
