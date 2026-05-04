"""Créer les tables manquantes de l'auth souveraine et du système de permissions

Ces tables font partie du schéma v3.x mais n'existaient pas en prod car
la migration 000_baseline_clean a été stampée (pas exécutée) sur une base
pre-v3.1.0. Crée les tables manquantes avec leurs contraintes.

Tables créées :
  tunnel_role, tunnel_endpoint, auth_attempt, email_domain_rule,
  intervention_type, ip_blocklist, security_log, refresh_token,
  permission_audit_log, api_key, tunnel_permission

Revision ID: 002_create_missing_tables
Revises: 001_fk_tunnel_user
Create Date: 2026-05-04
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_create_missing_tables"
down_revision: Union[str, None] = "001_fk_tunnel_user"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # Séquence pour intervention_type
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS intervention_type_id_seq"))

    # Tables sans dépendances sur les nouvelles tables
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tunnel_role (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            code VARCHAR(20) NOT NULL,
            label VARCHAR(100) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text(
        "ALTER TABLE tunnel_role ADD CONSTRAINT tunnel_role_code_key UNIQUE (code)"
    ))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tunnel_endpoint (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            code VARCHAR(100) NOT NULL,
            method VARCHAR(10) NOT NULL,
            path VARCHAR(200) NOT NULL,
            description VARCHAR(255),
            module VARCHAR(50),
            is_sensitive BOOLEAN DEFAULT false NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text(
        "ALTER TABLE tunnel_endpoint ADD CONSTRAINT tunnel_endpoint_code_key UNIQUE (code)"
    ))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS auth_attempt (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            email VARCHAR(255),
            ip_address VARCHAR(45) NOT NULL,
            success BOOLEAN DEFAULT false NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS email_domain_rule (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            domain VARCHAR(255) NOT NULL,
            allowed BOOLEAN DEFAULT true NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text(
        "ALTER TABLE email_domain_rule ADD CONSTRAINT email_domain_rule_domain_key UNIQUE (domain)"
    ))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS intervention_type (
            id INTEGER DEFAULT nextval('intervention_type_id_seq') NOT NULL,
            code VARCHAR(10) NOT NULL,
            label TEXT NOT NULL,
            color VARCHAR(30),
            is_active BOOLEAN DEFAULT true NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text(
        "ALTER TABLE intervention_type ADD CONSTRAINT intervention_type_code_key UNIQUE (code)"
    ))

    # Tables dépendant de tunnel_user (existe depuis migration 001)
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS ip_blocklist (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            ip_address VARCHAR(45) NOT NULL,
            reason VARCHAR(255),
            blocked_until TIMESTAMPTZ,
            created_by UUID,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text(
        "ALTER TABLE ip_blocklist ADD CONSTRAINT ip_blocklist_ip_address_key UNIQUE (ip_address)"
    ))
    op.execute(sa.text("""
        ALTER TABLE ip_blocklist ADD CONSTRAINT ip_blocklist_created_by_fkey
            FOREIGN KEY (created_by) REFERENCES tunnel_user(id)
    """))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS security_log (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            user_id UUID,
            ip_address VARCHAR(45),
            detail JSONB,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text("""
        ALTER TABLE security_log ADD CONSTRAINT security_log_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES tunnel_user(id) ON DELETE SET NULL
    """))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS refresh_token (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            user_id UUID NOT NULL,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked BOOLEAN DEFAULT false NOT NULL,
            ip_address VARCHAR(45),
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text(
        "ALTER TABLE refresh_token ADD CONSTRAINT refresh_token_token_hash_key UNIQUE (token_hash)"
    ))
    op.execute(sa.text("""
        ALTER TABLE refresh_token ADD CONSTRAINT refresh_token_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES tunnel_user(id) ON DELETE CASCADE
    """))

    # Tables dépendant de tunnel_role et/ou tunnel_endpoint
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS api_key (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            name VARCHAR(255) NOT NULL,
            key_prefix VARCHAR(12) NOT NULL,
            key_hash VARCHAR(64) NOT NULL,
            role_id UUID NOT NULL,
            is_active BOOLEAN DEFAULT true NOT NULL,
            expires_at TIMESTAMPTZ,
            last_used_at TIMESTAMPTZ,
            created_by UUID,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text(
        "ALTER TABLE api_key ADD CONSTRAINT api_key_key_hash_key UNIQUE (key_hash)"
    ))
    op.execute(sa.text("""
        ALTER TABLE api_key ADD CONSTRAINT api_key_created_by_fkey
            FOREIGN KEY (created_by) REFERENCES tunnel_user(id)
    """))
    op.execute(sa.text("""
        ALTER TABLE api_key ADD CONSTRAINT api_key_role_id_fkey
            FOREIGN KEY (role_id) REFERENCES tunnel_role(id)
    """))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tunnel_permission (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            role_id UUID NOT NULL,
            endpoint_id UUID NOT NULL,
            allowed BOOLEAN DEFAULT true NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text("""
        ALTER TABLE tunnel_permission ADD CONSTRAINT tunnel_permission_role_id_endpoint_id_key
            UNIQUE (role_id, endpoint_id)
    """))
    op.execute(sa.text("""
        ALTER TABLE tunnel_permission ADD CONSTRAINT tunnel_permission_endpoint_id_fkey
            FOREIGN KEY (endpoint_id) REFERENCES tunnel_endpoint(id)
    """))
    op.execute(sa.text("""
        ALTER TABLE tunnel_permission ADD CONSTRAINT tunnel_permission_role_id_fkey
            FOREIGN KEY (role_id) REFERENCES tunnel_role(id)
    """))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS permission_audit_log (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            changed_by UUID NOT NULL,
            role_id UUID NOT NULL,
            endpoint_id UUID NOT NULL,
            old_allowed BOOLEAN,
            new_allowed BOOLEAN NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text("""
        ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_changed_by_fkey
            FOREIGN KEY (changed_by) REFERENCES tunnel_user(id)
    """))
    op.execute(sa.text("""
        ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_endpoint_id_fkey
            FOREIGN KEY (endpoint_id) REFERENCES tunnel_endpoint(id)
    """))
    op.execute(sa.text("""
        ALTER TABLE permission_audit_log ADD CONSTRAINT permission_audit_log_role_id_fkey
            FOREIGN KEY (role_id) REFERENCES tunnel_role(id)
    """))

    # FK tunnel_user -> tunnel_role (impossible dans 001 car tunnel_role n'existait pas)
    op.execute(sa.text("""
        ALTER TABLE tunnel_user ADD CONSTRAINT tunnel_user_role_id_fkey
            FOREIGN KEY (role_id) REFERENCES tunnel_role(id)
    """))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE tunnel_user DROP CONSTRAINT IF EXISTS tunnel_user_role_id_fkey"))
    op.execute(sa.text("DROP TABLE IF EXISTS permission_audit_log"))
    op.execute(sa.text("DROP TABLE IF EXISTS tunnel_permission"))
    op.execute(sa.text("DROP TABLE IF EXISTS api_key"))
    op.execute(sa.text("DROP TABLE IF EXISTS refresh_token"))
    op.execute(sa.text("DROP TABLE IF EXISTS security_log"))
    op.execute(sa.text("DROP TABLE IF EXISTS ip_blocklist"))
    op.execute(sa.text("DROP TABLE IF EXISTS intervention_type"))
    op.execute(sa.text("DROP TABLE IF EXISTS email_domain_rule"))
    op.execute(sa.text("DROP TABLE IF EXISTS auth_attempt"))
    op.execute(sa.text("DROP TABLE IF EXISTS tunnel_endpoint"))
    op.execute(sa.text("DROP TABLE IF EXISTS tunnel_role"))
    op.execute(sa.text("DROP SEQUENCE IF EXISTS intervention_type_id_seq"))
