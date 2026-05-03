import hashlib
import logging
import secrets
from typing import Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import NotFoundError, raise_db_error

logger = logging.getLogger(__name__)

_KEY_PREFIX = "gmao_"


def _generate_secret() -> str:
    return _KEY_PREFIX + secrets.token_urlsafe(24)


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


class ApiKeyRepository:
    """Accès DB pour les clés d'API machine-to-machine."""

    def get_all(self) -> list[dict]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        ak.id::text,
                        ak.name,
                        ak.key_prefix,
                        tr.code AS role_code,
                        ak.is_active,
                        ak.expires_at,
                        ak.last_used_at,
                        ak.created_at
                    FROM api_key ak
                    JOIN tunnel_role tr ON tr.id = ak.role_id
                    ORDER BY ak.created_at DESC
                    """
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as e:
            raise_db_error(e, "liste des clés d'API")
        finally:
            if conn:
                release_connection(conn)

    def create(self, name: str, created_by: Optional[str]) -> dict:
        """Crée une clé avec le rôle MCP. Retourne le secret brut une seule fois."""
        secret = _generate_secret()
        key_hash = _hash_secret(secret)
        key_prefix = secret[:10]  # ex: "gmao_a1b2c"

        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO api_key (name, key_prefix, key_hash, role_id, created_by)
                    VALUES (
                        %s,
                        %s,
                        %s,
                        (SELECT id FROM tunnel_role WHERE code = 'MCP'),
                        %s::uuid
                    )
                    RETURNING id::text, name, key_prefix, created_at
                    """,
                    (name, key_prefix, key_hash, created_by),
                )
                row = cur.fetchone()
            conn.commit()
            return {
                "id": row[0],
                "name": row[1],
                "key_prefix": row[2],
                "secret": secret,
                "role_code": "MCP",
                "created_at": row[3],
            }
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "création clé d'API")
        finally:
            if conn:
                release_connection(conn)

    def update(self, key_id: str, is_active: Optional[bool], expires_at) -> dict:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE api_key
                    SET
                        is_active  = COALESCE(%s, is_active),
                        expires_at = CASE WHEN %s::bool THEN %s ELSE expires_at END
                    WHERE id = %s::uuid
                    RETURNING
                        id::text, name, key_prefix, is_active, expires_at,
                        last_used_at, created_at
                    """,
                    (
                        is_active,
                        expires_at is not None,
                        expires_at,
                        key_id,
                    ),
                )
                row = cur.fetchone()
            if not row:
                raise NotFoundError("Clé d'API introuvable")
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT tr.code FROM api_key ak JOIN tunnel_role tr ON tr.id = ak.role_id WHERE ak.id = %s::uuid",
                    (key_id,),
                )
                role_row = cur.fetchone()
            return {
                "id": row[0],
                "name": row[1],
                "key_prefix": row[2],
                "role_code": role_row[0] if role_row else "MCP",
                "is_active": row[3],
                "expires_at": row[4],
                "last_used_at": row[5],
                "created_at": row[6],
            }
        except NotFoundError:
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "modification clé d'API")
        finally:
            if conn:
                release_connection(conn)

    def delete(self, key_id: str) -> None:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM api_key WHERE id = %s::uuid RETURNING id",
                    (key_id,),
                )
                row = cur.fetchone()
            if not row:
                raise NotFoundError("Clé d'API introuvable")
            conn.commit()
        except NotFoundError:
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "suppression clé d'API")
        finally:
            if conn:
                release_connection(conn)

    def verify(self, raw_secret: str) -> Optional[dict]:
        """Vérifie un secret brut, retourne {role_code, key_id} ou None."""
        key_hash = _hash_secret(raw_secret)
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ak.id::text, tr.code AS role_code
                    FROM api_key ak
                    JOIN tunnel_role tr ON tr.id = ak.role_id
                    WHERE ak.key_hash = %s
                      AND ak.is_active = true
                      AND (ak.expires_at IS NULL OR ak.expires_at > now())
                    """,
                    (key_hash,),
                )
                row = cur.fetchone()
            if not row:
                return None
            return {"key_id": row[0], "role_code": row[1]}
        except Exception as e:
            logger.error("Erreur vérification clé d'API : %s", e)
            return None
        finally:
            if conn:
                release_connection(conn)

    def touch_last_used(self, key_id: str) -> None:
        """Met à jour last_used_at de façon best-effort (appelé en fire-and-forget)."""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE api_key SET last_used_at = now() WHERE id = %s::uuid",
                    (key_id,),
                )
            conn.commit()
        except Exception as e:
            logger.warning("Impossible de mettre à jour last_used_at pour %s : %s", key_id, e)
        finally:
            if conn:
                release_connection(conn)
