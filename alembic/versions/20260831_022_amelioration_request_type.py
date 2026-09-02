"""Idées d'amélioration comme type de demande d'intervention (DI)

Jusqu'ici intervention_request n'avait aucune notion de "type" : toutes les
DI étaient implicitement des demandes d'intervention classiques. Le backlog
d'idées d'amélioration vivait en dehors de la GMAO (fichier externe).

Cette migration introduit :

- `request_type_ref` : référentiel des types de DI, sur le même modèle que
  `request_status_ref` déjà en place (code/label/color/sort_order). Deux
  valeurs seedées : 'standard' (DI classiques, comportement actuel) et
  'amelioration' (nouveau).
- `intervention_request.type` : VARCHAR NOT NULL DEFAULT 'standard',
  FK vers request_type_ref(code). Toutes les DI existantes basculent
  explicitement sur 'standard' via le DEFAULT — aucune régression sur le
  workflow générique (statut/transitions/historique), qui continue de
  s'appliquer identiquement quel que soit le type.
- `amelioration_category_ref` : référentiel des catégories d'idées
  (sécurité, productivité/performance, ergonomie/qualité de vie au travail,
  qualité/fiabilité), même modèle que request_type_ref.
- `amelioration_sous_statut_ref` : référentiel du sous-statut spécifique aux
  idées d'amélioration (à confirmer / à planifier / en cours / réalisé).
  Volontairement distinct de `request_status_ref` (statut générique
  nouvelle/en_attente/acceptee/rejetee/cloturee) : le sous-statut ne pilote
  aucune transition du workflow DI standard, c'est un axe de suivi
  complémentaire propre aux idées.
- Sur intervention_request : `categorie` (VARCHAR, FK amelioration_category_ref,
  nullable), `priorite` (VARCHAR, nullable, valeurs basse/moyenne/haute
  validées applicativement — même pattern que PRIORITY_TYPES), `sous_statut`
  (VARCHAR, FK amelioration_sous_statut_ref, nullable), `porteur_id` (UUID,
  FK tunnel_user, nullable), `deadline` (DATE, nullable).

Toutes les nouvelles colonnes sont nullables (sauf `type`, qui a un DEFAULT) :
approche additive, aucune donnée existante à backfiller au-delà du DEFAULT.

Revision ID: 022_amelioration_request_type
Revises: 021_purchase_request_user_refs
Create Date: 2026-08-31
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "022_amelioration_request_type"
down_revision: Union[str, None] = "021_purchase_request_user_refs"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # ── Référentiel des types de DI ────────────────────────────────
    op.execute("""
        CREATE TABLE request_type_ref (
            code VARCHAR(50) NOT NULL,
            label TEXT NOT NULL,
            color VARCHAR(7) NOT NULL,
            sort_order INTEGER NOT NULL,
            PRIMARY KEY (code)
        )
    """)
    op.execute("""
        INSERT INTO request_type_ref (code, label, color, sort_order) VALUES
            ('standard', 'Demande d''intervention', '#6B7280', 1),
            ('amelioration', 'Idée d''amélioration', '#0EA5E9', 2)
    """)

    op.execute("ALTER TABLE intervention_request ADD COLUMN type VARCHAR(50) NOT NULL DEFAULT 'standard'")
    op.execute("""
        ALTER TABLE intervention_request
        ADD CONSTRAINT intervention_request_type_fkey
        FOREIGN KEY (type) REFERENCES request_type_ref(code)
    """)
    op.execute("CREATE INDEX idx_intervention_request_type ON intervention_request(type)")

    # ── Référentiel des catégories d'idées d'amélioration ──────────
    op.execute("""
        CREATE TABLE amelioration_category_ref (
            code VARCHAR(50) NOT NULL,
            label TEXT NOT NULL,
            color VARCHAR(7) NOT NULL,
            sort_order INTEGER NOT NULL,
            PRIMARY KEY (code)
        )
    """)
    op.execute("""
        INSERT INTO amelioration_category_ref (code, label, color, sort_order) VALUES
            ('securite', 'Sécurité', '#EF4444', 1),
            ('productivite', 'Productivité / performance', '#3B82F6', 2),
            ('ergonomie', 'Ergonomie / qualité de vie au travail', '#10B981', 3),
            ('qualite', 'Qualité / fiabilité', '#F59E0B', 4)
    """)

    # ── Référentiel du sous-statut idées d'amélioration ────────────
    op.execute("""
        CREATE TABLE amelioration_sous_statut_ref (
            code VARCHAR(50) NOT NULL,
            label TEXT NOT NULL,
            color VARCHAR(7) NOT NULL,
            sort_order INTEGER NOT NULL,
            PRIMARY KEY (code)
        )
    """)
    op.execute("""
        INSERT INTO amelioration_sous_statut_ref (code, label, color, sort_order) VALUES
            ('a_confirmer', 'À confirmer', '#F59E0B', 1),
            ('a_planifier', 'À planifier', '#8B5CF6', 2),
            ('en_cours', 'En cours', '#3B82F6', 3),
            ('realise', 'Réalisé', '#10B981', 4)
    """)

    # ── Colonnes sur intervention_request ──────────────────────────
    op.execute("ALTER TABLE intervention_request ADD COLUMN categorie VARCHAR(50)")
    op.execute("""
        ALTER TABLE intervention_request
        ADD CONSTRAINT intervention_request_categorie_fkey
        FOREIGN KEY (categorie) REFERENCES amelioration_category_ref(code)
    """)

    # priorite : VARCHAR nullable, validée applicativement (pattern PRIORITY_TYPES),
    # pas de table de référence — cohérent avec l'absence de référentiel SQL pour
    # la priorité d'intervention existante (intervention.priority).
    op.execute("ALTER TABLE intervention_request ADD COLUMN priorite VARCHAR(20)")

    op.execute("ALTER TABLE intervention_request ADD COLUMN sous_statut VARCHAR(50)")
    op.execute("""
        ALTER TABLE intervention_request
        ADD CONSTRAINT intervention_request_sous_statut_fkey
        FOREIGN KEY (sous_statut) REFERENCES amelioration_sous_statut_ref(code)
    """)

    op.execute("ALTER TABLE intervention_request ADD COLUMN porteur_id UUID")
    op.execute("""
        ALTER TABLE intervention_request
        ADD CONSTRAINT intervention_request_porteur_id_fkey
        FOREIGN KEY (porteur_id) REFERENCES tunnel_user(id) ON DELETE SET NULL
    """)

    op.execute("ALTER TABLE intervention_request ADD COLUMN deadline DATE")

    op.execute("CREATE INDEX idx_intervention_request_categorie ON intervention_request(categorie)")
    op.execute("CREATE INDEX idx_intervention_request_sous_statut ON intervention_request(sous_statut)")
    op.execute("CREATE INDEX idx_intervention_request_porteur_id ON intervention_request(porteur_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_intervention_request_porteur_id")
    op.execute("DROP INDEX IF EXISTS idx_intervention_request_sous_statut")
    op.execute("DROP INDEX IF EXISTS idx_intervention_request_categorie")

    op.execute("ALTER TABLE intervention_request DROP COLUMN IF EXISTS deadline")
    op.execute("ALTER TABLE intervention_request DROP CONSTRAINT IF EXISTS intervention_request_porteur_id_fkey")
    op.execute("ALTER TABLE intervention_request DROP COLUMN IF EXISTS porteur_id")
    op.execute("ALTER TABLE intervention_request DROP CONSTRAINT IF EXISTS intervention_request_sous_statut_fkey")
    op.execute("ALTER TABLE intervention_request DROP COLUMN IF EXISTS sous_statut")
    op.execute("ALTER TABLE intervention_request DROP COLUMN IF EXISTS priorite")
    op.execute("ALTER TABLE intervention_request DROP CONSTRAINT IF EXISTS intervention_request_categorie_fkey")
    op.execute("ALTER TABLE intervention_request DROP COLUMN IF EXISTS categorie")

    op.execute("DROP TABLE IF EXISTS amelioration_sous_statut_ref")
    op.execute("DROP TABLE IF EXISTS amelioration_category_ref")

    op.execute("DROP INDEX IF EXISTS idx_intervention_request_type")
    op.execute("ALTER TABLE intervention_request DROP CONSTRAINT IF EXISTS intervention_request_type_fkey")
    op.execute("ALTER TABLE intervention_request DROP COLUMN IF EXISTS type")

    op.execute("DROP TABLE IF EXISTS request_type_ref")
