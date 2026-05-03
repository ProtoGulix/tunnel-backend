"""auth_sovereign_v3 — système d'auth natif Tunnel

Revision ID: s4t5u6v7w8x9
Revises: r3s4t5u6v7w8
Create Date: 2026-05-03

Crée les tables d'auth souveraines et migre les utilisateurs Directus.
Ne supprime pas directus_users (FKs historiques existantes).
"""
from alembic import op

revision = 's4t5u6v7w8x9'
down_revision = 'r3s4t5u6v7w8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Tables                                                            #
    # ------------------------------------------------------------------ #
    op.execute("""
        CREATE TABLE IF NOT EXISTS tunnel_role (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code       VARCHAR(20)  UNIQUE NOT NULL,
            label      VARCHAR(100) NOT NULL,
            created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tunnel_user (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email         VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name    VARCHAR(100),
            last_name     VARCHAR(100),
            initial       VARCHAR(5)   NOT NULL,
            role_id       UUID         NOT NULL REFERENCES tunnel_role(id),
            auth_provider VARCHAR(20)  NOT NULL DEFAULT 'local',
            external_id   VARCHAR(255),
            is_active     BOOLEAN      NOT NULL DEFAULT true,
            provisioning  VARCHAR(20)  NOT NULL DEFAULT 'manual',
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tunnel_endpoint (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code         VARCHAR(100) UNIQUE NOT NULL,
            method       VARCHAR(10)  NOT NULL,
            path         VARCHAR(200) NOT NULL,
            description  VARCHAR(255),
            module       VARCHAR(50),
            is_sensitive BOOLEAN      NOT NULL DEFAULT false,
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tunnel_permission (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            role_id     UUID    NOT NULL REFERENCES tunnel_role(id),
            endpoint_id UUID    NOT NULL REFERENCES tunnel_endpoint(id),
            allowed     BOOLEAN NOT NULL DEFAULT true,
            UNIQUE(role_id, endpoint_id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS refresh_token (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID         NOT NULL REFERENCES tunnel_user(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMPTZ  NOT NULL,
            revoked    BOOLEAN      NOT NULL DEFAULT false,
            ip_address VARCHAR(45),
            created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth_attempt (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email      VARCHAR(255),
            ip_address VARCHAR(45) NOT NULL,
            success    BOOLEAN     NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ip_blocklist (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ip_address    VARCHAR(45)  UNIQUE NOT NULL,
            reason        VARCHAR(255),
            blocked_until TIMESTAMPTZ,
            created_by    UUID REFERENCES tunnel_user(id),
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS email_domain_rule (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            domain     VARCHAR(255) UNIQUE NOT NULL,
            allowed    BOOLEAN      NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS security_log (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_type VARCHAR(50)  NOT NULL,
            user_id    UUID REFERENCES tunnel_user(id) ON DELETE SET NULL,
            ip_address VARCHAR(45),
            detail     JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS permission_audit_log (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            changed_by  UUID NOT NULL REFERENCES tunnel_user(id),
            role_id     UUID NOT NULL REFERENCES tunnel_role(id),
            endpoint_id UUID NOT NULL REFERENCES tunnel_endpoint(id),
            old_allowed BOOLEAN,
            new_allowed BOOLEAN NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # ------------------------------------------------------------------ #
    # 2. Trigger updated_at sur tunnel_user                               #
    # ------------------------------------------------------------------ #
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trg_tunnel_user_updated_at ON tunnel_user;
        CREATE TRIGGER trg_tunnel_user_updated_at
        BEFORE UPDATE ON tunnel_user
        FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at()
    """)

    # ------------------------------------------------------------------ #
    # 3. Seed des 4 rôles                                                 #
    # ------------------------------------------------------------------ #
    op.execute("""
        INSERT INTO tunnel_role (code, label) VALUES
            ('RESP',       'Responsable'),
            ('TECH',       'Technicien'),
            ('CONSULTANT', 'Consultant'),
            ('ADMIN',      'Administrateur')
        ON CONFLICT (code) DO NOTHING
    """)

    # ------------------------------------------------------------------ #
    # 4. Migration directus_users → tunnel_user                           #
    # Résolution du rôle : via directus_users.role (UUID Directus)        #
    # On mappe les rôles Directus sur les codes Tunnel par convention.    #
    # Les utilisateurs sans rôle correspondant reçoivent TECH par défaut. #
    # password_hash : copié depuis directus_users.password tel quel.      #
    # Directus utilise argon2id — le login gère la vérification + re-hash #
    # automatique en bcrypt au premier login réussi.                      #
    # ------------------------------------------------------------------ #
    op.execute("""
        INSERT INTO tunnel_user (
            email, password_hash, first_name, last_name, initial,
            role_id, auth_provider, external_id, is_active,
            provisioning, created_at, updated_at
        )
        SELECT
            du.email,
            COALESCE(du.password, '$2b$12$PLACEHOLDERxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'),
            du.first_name,
            du.last_name,
            COALESCE(du.initial, UPPER(LEFT(du.first_name, 1) || LEFT(du.last_name, 1)), 'XX'),
            COALESCE(
                (
                    SELECT tr.id FROM tunnel_role tr
                    WHERE tr.code = CASE
                        WHEN du.role::text IN (
                            SELECT r.id::text FROM directus_roles r WHERE LOWER(r.name) LIKE '%admin%'
                        ) THEN 'ADMIN'
                        WHEN du.role::text IN (
                            SELECT r.id::text FROM directus_roles r WHERE LOWER(r.name) LIKE '%resp%'
                        ) THEN 'RESP'
                        WHEN du.role::text IN (
                            SELECT r.id::text FROM directus_roles r WHERE LOWER(r.name) LIKE '%consult%'
                        ) THEN 'CONSULTANT'
                        ELSE 'TECH'
                    END
                    LIMIT 1
                ),
                (SELECT id FROM tunnel_role WHERE code = 'TECH')
            ),
            'local',
            du.id::text,
            du.status = 'active',
            'migrated',
            now(),
            now()
        FROM directus_users du
        WHERE du.email IS NOT NULL
          AND du.email <> ''
        ON CONFLICT (email) DO NOTHING
    """)

    # ------------------------------------------------------------------ #
    # 5. Log de migration dans security_log                               #
    # ------------------------------------------------------------------ #
    op.execute("""
        INSERT INTO security_log (event_type, detail)
        SELECT
            'USER_MIGRATED_V3',
            jsonb_build_object(
                'source', 'directus_users',
                'migrated_count', (SELECT COUNT(*) FROM tunnel_user WHERE provisioning = 'migrated'),
                'migration_date', now()
            )
        WHERE EXISTS (SELECT 1 FROM tunnel_user WHERE provisioning = 'migrated')
    """)

    # ------------------------------------------------------------------ #
    # 6. Seed matrice de permissions initiale                             #
    # Les endpoints seront créés au boot (scanner), ici on pré-seed       #
    # les codes connus pour que la matrice soit prête dès le démarrage.   #
    # ------------------------------------------------------------------ #
    op.execute("""
        INSERT INTO tunnel_endpoint (code, method, path, description, module, is_sensitive)
        VALUES
            ('interventions:list',            'GET',   '/interventions',           'Liste des interventions',           'interventions', false),
            ('interventions:create',          'POST',  '/interventions',           'Créer une intervention',            'interventions', false),
            ('interventions:update',          'PATCH', '/interventions/{id}',      'Modifier une intervention',         'interventions', false),
            ('interventions:create_planifie', 'POST',  '/interventions/planifie',  'Créer intervention planifiée',      'interventions', false),
            ('actions:create',                'POST',  '/intervention-actions',    'Créer une action',                  'interventions', false),
            ('admin:users:read',              'GET',   '/admin/users',             'Lister les utilisateurs',           'admin',         true),
            ('admin:users:write',             'POST',  '/admin/users',             'Créer un utilisateur',              'admin',         true),
            ('admin:users:update',            'PUT',   '/admin/users/{id}',        'Modifier un utilisateur',           'admin',         true),
            ('admin:referentiel:read',        'GET',   '/admin/action-categories', 'Lire le référentiel',               'admin',         true),
            ('admin:referentiel:write',       'PATCH', '/admin/action-categories/{id}', 'Modifier le référentiel',      'admin',         true),
            ('admin:security:read',           'GET',   '/admin/security-logs',     'Lire les logs sécurité',            'admin',         true),
            ('admin:security:write',          'POST',  '/admin/ip-blocklist',      'Gérer la liste de blocage IP',      'admin',         true),
            ('admin:permissions:read',        'GET',   '/admin/roles',             'Lire les permissions',              'admin',         true),
            ('admin:permissions:write',       'PATCH', '/admin/permissions/{id}',  'Modifier les permissions',          'admin',         true)
        ON CONFLICT (code) DO NOTHING
    """)

    op.execute("""
        INSERT INTO tunnel_permission (role_id, endpoint_id, allowed)
        SELECT r.id, e.id, true
        FROM tunnel_role r, tunnel_endpoint e
        WHERE (r.code, e.code) IN (
            -- RESP
            ('RESP', 'interventions:list'),
            ('RESP', 'interventions:create'),
            ('RESP', 'interventions:update'),
            ('RESP', 'interventions:create_planifie'),
            ('RESP', 'actions:create'),
            ('RESP', 'admin:users:read'),
            ('RESP', 'admin:users:write'),
            ('RESP', 'admin:users:update'),
            ('RESP', 'admin:referentiel:read'),
            ('RESP', 'admin:referentiel:write'),
            -- TECH
            ('TECH', 'interventions:list'),
            ('TECH', 'interventions:create'),
            ('TECH', 'interventions:update'),
            ('TECH', 'actions:create'),
            -- CONSULTANT
            ('CONSULTANT', 'interventions:list'),
            -- ADMIN
            ('ADMIN', 'interventions:list'),
            ('ADMIN', 'interventions:create'),
            ('ADMIN', 'interventions:update'),
            ('ADMIN', 'interventions:create_planifie'),
            ('ADMIN', 'actions:create'),
            ('ADMIN', 'admin:users:read'),
            ('ADMIN', 'admin:users:write'),
            ('ADMIN', 'admin:users:update'),
            ('ADMIN', 'admin:referentiel:read'),
            ('ADMIN', 'admin:referentiel:write'),
            ('ADMIN', 'admin:security:read'),
            ('ADMIN', 'admin:security:write'),
            ('ADMIN', 'admin:permissions:read'),
            ('ADMIN', 'admin:permissions:write')
        )
        ON CONFLICT (role_id, endpoint_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_tunnel_user_updated_at ON tunnel_user")
    op.execute("DROP TABLE IF EXISTS permission_audit_log CASCADE")
    op.execute("DROP TABLE IF EXISTS security_log CASCADE")
    op.execute("DROP TABLE IF EXISTS email_domain_rule CASCADE")
    op.execute("DROP TABLE IF EXISTS ip_blocklist CASCADE")
    op.execute("DROP TABLE IF EXISTS auth_attempt CASCADE")
    op.execute("DROP TABLE IF EXISTS refresh_token CASCADE")
    op.execute("DROP TABLE IF EXISTS tunnel_permission CASCADE")
    op.execute("DROP TABLE IF EXISTS tunnel_endpoint CASCADE")
    op.execute("DROP TABLE IF EXISTS tunnel_user CASCADE")
    op.execute("DROP TABLE IF EXISTS tunnel_role CASCADE")
    op.execute("DROP FUNCTION IF EXISTS fn_set_updated_at CASCADE")
