"""api_keys — table api_key + rôle MCP read-only

Revision ID: u6v7w8x9y0z1
Revises: t5u6v7w8x9y0
Create Date: 2026-05-03

Crée la table api_key pour l'authentification machine-to-machine (serveur MCP).
Ajoute le rôle MCP avec permissions en lecture seule sur tous les endpoints non-sensibles.
"""
from alembic import op

revision = 'u6v7w8x9y0z1'
down_revision = 't5u6v7w8x9y0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Table api_key                                                     #
    # ------------------------------------------------------------------ #
    op.execute("""
        CREATE TABLE IF NOT EXISTS api_key (
            id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            name         VARCHAR(255) NOT NULL,
            key_prefix   VARCHAR(12)  NOT NULL,
            key_hash     VARCHAR(64)  NOT NULL UNIQUE,
            role_id      UUID         NOT NULL REFERENCES tunnel_role(id),
            is_active    BOOLEAN      NOT NULL DEFAULT true,
            expires_at   TIMESTAMPTZ,
            last_used_at TIMESTAMPTZ,
            created_by   UUID         REFERENCES tunnel_user(id),
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_key_hash ON api_key (key_hash)
        WHERE is_active = true
    """)

    # ------------------------------------------------------------------ #
    # 2. Rôle MCP                                                          #
    # ------------------------------------------------------------------ #
    op.execute("""
        INSERT INTO tunnel_role (code, label)
        VALUES ('MCP', 'Serveur MCP (lecture seule)')
        ON CONFLICT (code) DO NOTHING
    """)

    # ------------------------------------------------------------------ #
    # 3. Seed permissions MCP : tous les endpoints GET non-sensibles       #
    # Les endpoints créés au boot via sync_endpoints_catalog seront        #
    # ajoutés avec allowed=false automatiquement (comportement existant).  #
    # Ici on pré-seed les endpoints connus pour que MCP soit opérationnel  #
    # dès le premier démarrage.                                            #
    # ------------------------------------------------------------------ #
    op.execute("""
        INSERT INTO tunnel_permission (role_id, endpoint_id, allowed)
        SELECT
            (SELECT id FROM tunnel_role WHERE code = 'MCP'),
            te.id,
            true
        FROM tunnel_endpoint te
        WHERE te.method = 'GET'
          AND te.is_sensitive = false
        ON CONFLICT (role_id, endpoint_id) DO NOTHING
    """)


def downgrade() -> None:
    # Supprime les permissions MCP
    op.execute("""
        DELETE FROM tunnel_permission
        WHERE role_id = (SELECT id FROM tunnel_role WHERE code = 'MCP')
    """)
    # Supprime le rôle MCP
    op.execute("DELETE FROM tunnel_role WHERE code = 'MCP'")
    # Supprime la table
    op.execute("DROP TABLE IF EXISTS api_key CASCADE")
