"""Ajoute supplier_order aux entités auditées silencieusement (routine)

Le module achats a un onglet "Historique" prévu sur les demandes d'achat ET
les paniers fournisseurs, sur le modèle de l'onglet Historique des
interventions. Les demandes d'achat sont déjà tracées par AuditMiddleware
(purchase_request est dans _ENTITY_MAP/_TABLE_MAP depuis l'origine du
middleware) — mais supplier_order n'y était pas: /supplier-orders/{id}
n'envoie jamais de reason_code, donc _write_audit_log() n'écrivait jamais
la moindre ligne pour un panier.

On ajoute supplier_order à la liste des entités auditées (voir
api/audits/middleware.py, modifié dans le même changement) avec une règle
par défaut "routine" (ROUTINE, injectée silencieusement) — même pattern que
task/action/request/intervention/purchase_request (migration 017) : aucun
dialog de raison n'apparaît côté front, l'historique se remplit
automatiquement.

Revision ID: 020_supplier_order_audit_routine
Revises: 019_purchase_request_code
Create Date: 2026-07-26
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "020_supplier_order_audit_routine"
down_revision: Union[str, None] = "019_purchase_request_code"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE audit_reason_code
        SET entity_types = array_append(entity_types, 'supplier_order')
        WHERE code = 'ROUTINE'
          AND NOT ('supplier_order' = ANY(entity_types))
    """)

    op.execute("""
        INSERT INTO audit_rule (entity_type, field, is_routine, default_reason_code)
        VALUES ('supplier_order', NULL, TRUE, 'ROUTINE')
        ON CONFLICT (entity_type, field) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM audit_rule WHERE entity_type = 'supplier_order' AND field IS NULL
    """)
    op.execute("""
        UPDATE audit_reason_code
        SET entity_types = array_remove(entity_types, 'supplier_order')
        WHERE code = 'ROUTINE'
    """)
