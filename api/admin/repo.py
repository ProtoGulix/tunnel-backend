import secrets
import logging
from typing import Any, Dict, List, Optional

import bcrypt

from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, NotFoundError, ConflictError
from api.utils.sanitizer import strip_html

logger = logging.getLogger(__name__)


def _raise(e: Exception, context: str):
    from api.errors.exceptions import raise_db_error
    raise_db_error(e, context)


class AdminUserRepository:
    """Accès BDD pour la gestion admin des utilisateurs tunnel_user."""

    def get_all(self, search: Optional[str] = None,
                is_active: Optional[bool] = None,
                role_code: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            wheres, params = [], []
            if search:
                wheres.append(
                    "(tu.email ILIKE %s OR tu.first_name ILIKE %s OR tu.last_name ILIKE %s)"
                )
                like = f"%{search}%"
                params += [like, like, like]
            if is_active is not None:
                wheres.append("tu.is_active = %s")
                params.append(is_active)
            if role_code:
                wheres.append("tr.code = %s")
                params.append(role_code)
            where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT tu.id, tu.email, tu.first_name, tu.last_name, tu.initial,
                           tr.code AS role_code, tu.role_id,
                           tu.auth_provider, tu.is_active, tu.provisioning,
                           tu.created_at, tu.updated_at
                    FROM tunnel_user tu
                    JOIN tunnel_role tr ON tr.id = tu.role_id
                    {where_sql}
                    ORDER BY tu.last_name ASC, tu.first_name ASC
                    """,
                    params,
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            _raise(e, "liste utilisateurs admin")
        finally:
            if conn:
                release_connection(conn)

    def get_by_id(self, user_id: str) -> Dict[str, Any]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tu.id, tu.email, tu.first_name, tu.last_name, tu.initial,
                           tr.code AS role_code, tu.role_id,
                           tu.auth_provider, tu.is_active, tu.provisioning,
                           tu.created_at, tu.updated_at
                    FROM tunnel_user tu
                    JOIN tunnel_role tr ON tr.id = tu.role_id
                    WHERE tu.id = %s::uuid
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Utilisateur {user_id} non trouvé")
            cols = ["id", "email", "first_name", "last_name", "initial",
                    "role_code", "role_id", "auth_provider", "is_active",
                    "provisioning", "created_at", "updated_at"]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            _raise(e, f"récupération utilisateur {user_id}")
        finally:
            if conn:
                release_connection(conn)

    def create(self, email: str, password: str, first_name: Optional[str],
               last_name: Optional[str], initial: str, role_id: str) -> Dict[str, Any]:
        conn = None
        try:
            conn = get_connection()
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tunnel_user
                        (email, password_hash, first_name, last_name, initial, role_id)
                    VALUES (%s, %s, %s, %s, %s, %s::uuid)
                    RETURNING id
                    """,
                    (email, password_hash,
                     strip_html(first_name) if first_name else None,
                     strip_html(last_name) if last_name else None,
                     strip_html(initial), role_id),
                )
                new_id = cur.fetchone()[0]
            conn.commit()
            return self.get_by_id(str(new_id))
        except Exception as e:
            if conn:
                conn.rollback()
            if "unique" in str(e).lower():
                raise ConflictError(f"Email déjà utilisé : {email}")
            _raise(e, "création utilisateur")
        finally:
            if conn:
                release_connection(conn)

    def update(self, user_id: str, email: Optional[str], first_name: Optional[str],
               last_name: Optional[str], initial: Optional[str]) -> Dict[str, Any]:
        conn = None
        try:
            conn = get_connection()
            sets, params = [], []
            if email is not None:
                sets.append("email = %s"); params.append(email)
            if first_name is not None:
                sets.append("first_name = %s"); params.append(strip_html(first_name))
            if last_name is not None:
                sets.append("last_name = %s"); params.append(strip_html(last_name))
            if initial is not None:
                sets.append("initial = %s"); params.append(strip_html(initial))
            if not sets:
                return self.get_by_id(user_id)
            params.append(user_id)
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE tunnel_user SET {', '.join(sets)} WHERE id = %s::uuid",
                    params,
                )
            conn.commit()
            return self.get_by_id(user_id)
        except NotFoundError:
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"mise à jour utilisateur {user_id}")
        finally:
            if conn:
                release_connection(conn)

    def set_role(self, user_id: str, role_id: str, changed_by: str) -> None:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tunnel_user SET role_id = %s::uuid WHERE id = %s::uuid",
                    (role_id, user_id),
                )
                # Révoquer tous les refresh tokens
                cur.execute(
                    "UPDATE refresh_token SET revoked = true WHERE user_id = %s::uuid",
                    (user_id,),
                )
                # Log
                cur.execute(
                    """
                    INSERT INTO security_log (event_type, user_id, detail)
                    VALUES ('ROLE_CHANGE', %s::uuid, %s::jsonb)
                    """,
                    (user_id, __import__("json").dumps(
                        {"changed_by": changed_by, "new_role_id": str(role_id)})),
                )
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"changement rôle utilisateur {user_id}")
        finally:
            if conn:
                release_connection(conn)

    def set_active(self, user_id: str, is_active: bool, changed_by: str) -> None:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tunnel_user SET is_active = %s WHERE id = %s::uuid",
                    (is_active, user_id),
                )
                if not is_active:
                    cur.execute(
                        "UPDATE refresh_token SET revoked = true WHERE user_id = %s::uuid",
                        (user_id,),
                    )
                    cur.execute(
                        """
                        INSERT INTO security_log (event_type, user_id, detail)
                        VALUES ('USER_DEACTIVATED', %s::uuid, %s::jsonb)
                        """,
                        (user_id, __import__("json").dumps({"changed_by": changed_by})),
                    )
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"activation/désactivation utilisateur {user_id}")
        finally:
            if conn:
                release_connection(conn)

    def reset_password(self, user_id: str) -> str:
        """Génère un mot de passe temporaire, met à jour le hash, retourne le mot de passe en clair."""
        conn = None
        try:
            conn = get_connection()
            temp_password = secrets.token_urlsafe(16)
            password_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tunnel_user SET password_hash = %s WHERE id = %s::uuid",
                    (password_hash, user_id),
                )
            conn.commit()
            return temp_password
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"reset password utilisateur {user_id}")
        finally:
            if conn:
                release_connection(conn)

    def soft_delete(self, user_id: str) -> None:
        """Désactive, obfusque l'email et efface le hash."""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tunnel_user SET
                        is_active     = false,
                        email         = 'deleted_' || id::text || '@deleted',
                        password_hash = ''
                    WHERE id = %s::uuid
                    """,
                    (user_id,),
                )
                cur.execute(
                    "UPDATE refresh_token SET revoked = true WHERE user_id = %s::uuid",
                    (user_id,),
                )
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"suppression utilisateur {user_id}")
        finally:
            if conn:
                release_connection(conn)


class AdminRoleRepository:
    """Accès BDD pour les rôles et permissions."""

    def get_roles(self) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT id, code, label, created_at FROM tunnel_role ORDER BY code")
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            _raise(e, "liste rôles")
        finally:
            if conn:
                release_connection(conn)

    def get_role_permissions(self, role_id: str) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tp.id, tp.role_id, tp.endpoint_id, tp.allowed,
                           te.code AS endpoint_code, te.method AS endpoint_method,
                           te.path AS endpoint_path
                    FROM tunnel_permission tp
                    JOIN tunnel_endpoint te ON te.id = tp.endpoint_id
                    WHERE tp.role_id = %s::uuid
                    ORDER BY te.module, te.code
                    """,
                    (role_id,),
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            _raise(e, f"permissions rôle {role_id}")
        finally:
            if conn:
                release_connection(conn)

    def patch_permission(self, permission_id: str, allowed: bool,
                         changed_by: str) -> Dict[str, Any]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role_id, endpoint_id, allowed FROM tunnel_permission WHERE id = %s::uuid",
                    (permission_id,),
                )
                row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Permission {permission_id} non trouvée")
            role_id, endpoint_id, old_allowed = row

            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tunnel_permission SET allowed = %s WHERE id = %s::uuid",
                    (allowed, permission_id),
                )
                cur.execute(
                    """
                    INSERT INTO permission_audit_log
                        (changed_by, role_id, endpoint_id, old_allowed, new_allowed)
                    VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s)
                    """,
                    (changed_by, role_id, endpoint_id, old_allowed, allowed),
                )
                cur.execute(
                    """
                    INSERT INTO security_log (event_type, user_id, detail)
                    VALUES ('PERMISSION_CHANGED', %s::uuid, %s::jsonb)
                    """,
                    (changed_by, __import__("json").dumps({
                        "permission_id": permission_id,
                        "old_allowed": old_allowed,
                        "new_allowed": allowed,
                    })),
                )
            conn.commit()

            # Invalider le cache permissions
            from api.auth.permissions import reload_permissions
            reload_permissions()

            return {"id": permission_id, "allowed": allowed}
        except NotFoundError:
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"modification permission {permission_id}")
        finally:
            if conn:
                release_connection(conn)

    def get_audit_log(self, role_id: Optional[str] = None,
                      start_date=None, end_date=None) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            wheres, params = [], []
            if role_id:
                wheres.append("pal.role_id = %s::uuid"); params.append(role_id)
            if start_date:
                wheres.append("pal.created_at >= %s"); params.append(start_date)
            if end_date:
                wheres.append("pal.created_at <= %s"); params.append(end_date)
            where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT pal.id, pal.changed_by, tu.email AS changed_by_email,
                           pal.role_id, tr.code AS role_code,
                           pal.endpoint_id, te.code AS endpoint_code,
                           pal.old_allowed, pal.new_allowed, pal.created_at
                    FROM permission_audit_log pal
                    JOIN tunnel_user    tu ON tu.id = pal.changed_by
                    JOIN tunnel_role    tr ON tr.id = pal.role_id
                    JOIN tunnel_endpoint te ON te.id = pal.endpoint_id
                    {where_sql}
                    ORDER BY pal.created_at DESC
                    LIMIT 200
                    """,
                    params,
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            _raise(e, "audit log permissions")
        finally:
            if conn:
                release_connection(conn)


class AdminEndpointRepository:
    """Accès BDD pour le catalogue des endpoints."""

    def get_all(self, module: Optional[str] = None,
                method: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            wheres, params = [], []
            if module:
                wheres.append("te.module = %s"); params.append(module)
            if method:
                wheres.append("te.method = %s"); params.append(method.upper())
            where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT te.id, te.code, te.method, te.path,
                           te.description, te.module, te.is_sensitive
                    FROM tunnel_endpoint te
                    {where_sql}
                    ORDER BY te.module, te.path, te.method
                    """,
                    params,
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            _raise(e, "liste endpoints")
        finally:
            if conn:
                release_connection(conn)

    def get_modules(self) -> List[str]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT module FROM tunnel_endpoint WHERE module IS NOT NULL ORDER BY module"
                )
                return [r[0] for r in cur.fetchall()]
        except Exception as e:
            _raise(e, "liste modules")
        finally:
            if conn:
                release_connection(conn)

    def patch(self, endpoint_id: str, description: Optional[str],
              module: Optional[str], is_sensitive: Optional[bool]) -> Dict[str, Any]:
        conn = None
        try:
            conn = get_connection()
            sets, params = [], []
            if description is not None:
                sets.append("description = %s"); params.append(description)
            if module is not None:
                sets.append("module = %s"); params.append(module)
            if is_sensitive is not None:
                sets.append("is_sensitive = %s"); params.append(is_sensitive)
            if not sets:
                raise NotFoundError(f"Rien à mettre à jour pour {endpoint_id}")
            params.append(endpoint_id)
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE tunnel_endpoint SET {', '.join(sets)} WHERE id = %s::uuid",
                    params,
                )
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, code, method, path, description, module, is_sensitive FROM tunnel_endpoint WHERE id = %s::uuid",
                    (endpoint_id,),
                )
                row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Endpoint {endpoint_id} non trouvé")
            cols = ["id", "code", "method", "path", "description", "module", "is_sensitive"]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"modification endpoint {endpoint_id}")
        finally:
            if conn:
                release_connection(conn)


class AdminSecurityRepository:
    """Accès BDD pour les logs et outils sécurité."""

    def get_security_logs(self, event_type: Optional[str] = None,
                          user_id: Optional[str] = None,
                          ip_address: Optional[str] = None,
                          start_date=None, end_date=None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            wheres, params = [], []
            if event_type:
                wheres.append("event_type = %s"); params.append(event_type)
            if user_id:
                wheres.append("user_id = %s::uuid"); params.append(user_id)
            if ip_address:
                wheres.append("ip_address = %s"); params.append(ip_address)
            if start_date:
                wheres.append("created_at >= %s"); params.append(start_date)
            if end_date:
                wheres.append("created_at <= %s"); params.append(end_date)
            where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
            params.append(min(limit, 1000))
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, event_type, user_id, ip_address, detail, created_at
                    FROM security_log
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    params,
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            _raise(e, "logs sécurité")
        finally:
            if conn:
                release_connection(conn)

    def get_ip_blocklist(self) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, ip_address, reason, blocked_until, created_by, created_at FROM ip_blocklist ORDER BY created_at DESC"
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            _raise(e, "liste IP bloquées")
        finally:
            if conn:
                release_connection(conn)

    def add_ip_block(self, ip_address: str, reason: Optional[str],
                     blocked_until, created_by: str) -> Dict[str, Any]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ip_blocklist (ip_address, reason, blocked_until, created_by)
                    VALUES (%s, %s, %s, %s::uuid)
                    ON CONFLICT (ip_address) DO UPDATE SET
                        reason        = EXCLUDED.reason,
                        blocked_until = EXCLUDED.blocked_until
                    RETURNING id, ip_address, reason, blocked_until, created_by, created_at
                    """,
                    (ip_address, reason, blocked_until, created_by),
                )
                row = cur.fetchone()
            conn.commit()
            cols = ["id", "ip_address", "reason", "blocked_until", "created_by", "created_at"]
            return dict(zip(cols, row))
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"blocage IP {ip_address}")
        finally:
            if conn:
                release_connection(conn)

    def remove_ip_block(self, block_id: str) -> None:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ip_blocklist WHERE id = %s::uuid", (block_id,))
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"suppression blocage IP {block_id}")
        finally:
            if conn:
                release_connection(conn)

    def get_email_domain_rules(self) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, domain, allowed, created_at FROM email_domain_rule ORDER BY domain"
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            _raise(e, "règles domaines email")
        finally:
            if conn:
                release_connection(conn)

    def add_email_domain_rule(self, domain: str, allowed: bool) -> Dict[str, Any]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO email_domain_rule (domain, allowed)
                    VALUES (%s, %s)
                    ON CONFLICT (domain) DO UPDATE SET allowed = EXCLUDED.allowed
                    RETURNING id, domain, allowed, created_at
                    """,
                    (domain.lower(), allowed),
                )
                row = cur.fetchone()
            conn.commit()
            cols = ["id", "domain", "allowed", "created_at"]
            return dict(zip(cols, row))
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"ajout règle domaine {domain}")
        finally:
            if conn:
                release_connection(conn)

    def remove_email_domain_rule(self, rule_id: str) -> None:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM email_domain_rule WHERE id = %s::uuid", (rule_id,))
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            _raise(e, f"suppression règle domaine {rule_id}")
        finally:
            if conn:
                release_connection(conn)
