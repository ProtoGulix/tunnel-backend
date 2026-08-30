"""Ajoute des références utilisateur réelles (requested_by_id, approver_id) sur purchase_request

Demandeur et Approbateur étaient des champs texte libre (requested_by,
approver_name), sans lien vers un compte tunnel_user réel — impossible de
savoir qui a réellement demandé/approuvé, ni de proposer un sélecteur
d'utilisateur fiable côté front.

Approche additive et non destructive : requested_by_id / approver_id sont
de nouvelles colonnes UUID nullables, FK vers tunnel_user, SANS supprimer
requested_by / approver_name (texte libre). Les DA existantes créées via
CSV, formulaire public, ou saisie manuelle (valeurs comme "Système" qui ne
correspondent à aucun tunnel_user) gardent leur valeur texte affichable ;
seules les nouvelles saisies via le formulaire de qualification (utilisateur
authentifié) renseignent désormais la référence réelle.

Revision ID: 021_purchase_request_user_refs
Revises: 020_supplier_order_audit_routine
Create Date: 2026-07-26
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "021_purchase_request_user_refs"
down_revision: Union[str, None] = "020_supplier_order_audit_routine"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE purchase_request ADD COLUMN requested_by_id UUID")
    op.execute("ALTER TABLE purchase_request ADD COLUMN approver_id UUID")

    op.execute("""
        ALTER TABLE purchase_request
        ADD CONSTRAINT purchase_request_requested_by_id_fkey
        FOREIGN KEY (requested_by_id) REFERENCES tunnel_user(id) ON DELETE SET NULL
    """)
    op.execute("""
        ALTER TABLE purchase_request
        ADD CONSTRAINT purchase_request_approver_id_fkey
        FOREIGN KEY (approver_id) REFERENCES tunnel_user(id) ON DELETE SET NULL
    """)

    op.execute("CREATE INDEX idx_purchase_request_requested_by_id ON purchase_request(requested_by_id)")
    op.execute("CREATE INDEX idx_purchase_request_approver_id ON purchase_request(approver_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_purchase_request_requested_by_id")
    op.execute("DROP INDEX IF EXISTS idx_purchase_request_approver_id")
    op.execute("ALTER TABLE purchase_request DROP CONSTRAINT IF EXISTS purchase_request_requested_by_id_fkey")
    op.execute("ALTER TABLE purchase_request DROP CONSTRAINT IF EXISTS purchase_request_approver_id_fkey")
    op.execute("ALTER TABLE purchase_request DROP COLUMN IF EXISTS requested_by_id")
    op.execute("ALTER TABLE purchase_request DROP COLUMN IF EXISTS approver_id")
