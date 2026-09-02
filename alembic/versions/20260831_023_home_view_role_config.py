"""Configuration de l'accueil par rôle + rôle ACHETEUR

La page d'accueil actuelle (réservoir de tâches + fiche semaine, HomeSplit.jsx
côté frontend) est aujourd'hui la seule vue d'accueil, indépendamment du rôle
de l'utilisateur connecté. On introduit la possibilité d'assigner une vue
d'accueil différente par rôle (vue acheteur, vue direction technique), tout
en garantissant qu'un rôle sans configuration explicite garde exactement le
comportement actuel.

- Nouveau rôle `ACHETEUR` dans tunnel_role. Pour la direction technique, le
  rôle `RESP` existant est réutilisé (pas de nouveau rôle) : c'est déjà un
  rôle hiérarchique proche du besoin, pas la peine d'en ajouter un.
- `home_view_ref` : référentiel des vues d'accueil disponibles
  (code/label), même modèle que les autres tables *_ref du projet.
  Seedé avec 'technicien' (comportement actuel, HomeSplit.jsx),
  'acheteur' et 'direction_technique'.
- `role_home_view` : mapping role_id → home_view code. Une seule ligne par
  rôle (contrainte UNIQUE sur role_id). Absence de ligne pour un rôle =
  comportement par défaut (vue 'technicien'), résolu côté application —
  volontairement pas de valeur DEFAULT en base pour ne pas avoir à
  pré-remplir une ligne par rôle existant à chaque nouveau rôle créé.

Pas de système de permissions généralisé : ce n'est qu'un mapping simple
rôle → code de vue, cohérent avec le besoin actuel ("quelle page s'affiche"),
pas une matrice de droits comme tunnel_permission (qui reste le mécanisme
pour les permissions fines par endpoint, non concerné par ce changement).

Revision ID: 023_home_view_role_config
Revises: 022_amelioration_request_type
Create Date: 2026-08-31
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "023_home_view_role_config"
down_revision: Union[str, None] = "022_amelioration_request_type"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # ── Nouveau rôle ACHETEUR ───────────────────────────────────────
    op.execute("""
        INSERT INTO tunnel_role (id, code, label)
        VALUES (gen_random_uuid(), 'ACHETEUR', 'Acheteur')
        ON CONFLICT (code) DO NOTHING
    """)

    # ── Référentiel des vues d'accueil ──────────────────────────────
    op.execute("""
        CREATE TABLE home_view_ref (
            code VARCHAR(50) NOT NULL,
            label TEXT NOT NULL,
            PRIMARY KEY (code)
        )
    """)
    op.execute("""
        INSERT INTO home_view_ref (code, label) VALUES
            ('technicien', 'Technicien (réservoir de tâches + fiche semaine)'),
            ('acheteur', 'Acheteur (demandes d''achat par statut)'),
            ('direction_technique', 'Direction technique (DI par statut, porteur, deadline)')
    """)

    # ── Mapping rôle → vue d'accueil ────────────────────────────────
    op.execute("""
        CREATE TABLE role_home_view (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            role_id UUID NOT NULL,
            home_view VARCHAR(50) NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            updated_by UUID,
            PRIMARY KEY (id),
            CONSTRAINT role_home_view_role_id_key UNIQUE (role_id),
            CONSTRAINT role_home_view_role_id_fkey
                FOREIGN KEY (role_id) REFERENCES tunnel_role(id) ON DELETE CASCADE,
            CONSTRAINT role_home_view_home_view_fkey
                FOREIGN KEY (home_view) REFERENCES home_view_ref(code),
            CONSTRAINT role_home_view_updated_by_fkey
                FOREIGN KEY (updated_by) REFERENCES tunnel_user(id) ON DELETE SET NULL
        )
    """)

    # Pas de ligne pré-remplie pour TECH : l'absence de configuration DOIT
    # rester le chemin qui produit la vue technicien (comportement par
    # défaut requis), pas une ligne explicite qu'on pourrait supprimer par
    # erreur en pensant "reset" un rôle vers un autre défaut.


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS role_home_view")
    op.execute("DROP TABLE IF EXISTS home_view_ref")
    op.execute("DELETE FROM tunnel_role WHERE code = 'ACHETEUR'")
