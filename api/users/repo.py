from typing import List, Dict, Any, Optional

import bcrypt

from api.constants import PAGINATION_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT
from api.errors.exceptions import DatabaseError, NotFoundError, ValidationError
from api.db import get_connection, release_connection
from api.utils.sanitizer import strip_html


LIST_COLUMNS = "tu.id, tu.first_name, tu.last_name, tu.email, tu.initial, tu.is_active, tr.code AS role"
DETAIL_COLUMNS = (
    "tu.id, tu.first_name, tu.last_name, tu.email, tu.initial, "
    "tu.is_active, tr.code AS role, tu.created_at AS last_access"
)


class UserRepository:

    def get_all(
        self,
        limit: int = PAGINATION_DEFAULT_LIMIT,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                where_clauses: List[str] = []
                params: List[Any] = []

                if status is not None:
                    # Compatibilité : "active" → is_active=true, tout autre valeur → is_active=false
                    where_clauses.append("tu.is_active = %s")
                    params.append(status == "active")

                if search is not None:
                    where_clauses.append(
                        "(tu.first_name ILIKE %s OR tu.last_name ILIKE %s OR tu.email ILIKE %s)"
                    )
                    like = f"%{search}%"
                    params.extend([like, like, like])

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

                cur.execute(
                    f"""
                    SELECT {LIST_COLUMNS}
                    FROM tunnel_user tu
                    JOIN tunnel_role tr ON tr.id = tu.role_id
                    {where_sql}
                    ORDER BY tu.last_name ASC, tu.first_name ASC
                    LIMIT %s OFFSET %s
                    """,
                    [*params, limit, offset],
                )
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            if conn:
                release_connection(conn)

    def get_by_id(self, user_id: str) -> Dict[str, Any]:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {DETAIL_COLUMNS}
                    FROM tunnel_user tu
                    JOIN tunnel_role tr ON tr.id = tu.role_id
                    WHERE tu.id = %s
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Utilisateur {user_id} non trouvé")
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            if conn:
                release_connection(conn)

    def update_profile(self, user_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour prénom, nom et/ou initiales de l'utilisateur."""
        allowed = {"first_name", "last_name", "initial"}
        updates = {k: strip_html(v) for k, v in fields.items() if k in allowed and v is not None}
        if not updates:
            raise ValidationError("Aucun champ valide à mettre à jour")

        set_clause = ", ".join(f"{col} = %s" for col in updates)
        params = list(updates.values()) + [user_id]

        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE tunnel_user SET {set_clause}, updated_at = now() WHERE id = %s::uuid",
                    params,
                )
                if cur.rowcount == 0:
                    raise NotFoundError(f"Utilisateur {user_id} non trouvé")
            conn.commit()
            return self.get_by_id(user_id)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Erreur mise à jour profil: {str(e)}") from e
        finally:
            if conn:
                release_connection(conn)

    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        """Vérifie le mot de passe actuel puis enregistre le nouveau hash bcrypt."""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT password_hash FROM tunnel_user WHERE id = %s::uuid AND is_active = true",
                    (user_id,),
                )
                row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Utilisateur {user_id} non trouvé")

            raw_hash: str = row[0]

            # Vérification du mot de passe actuel (supporte argon2id héritage et bcrypt)
            password_ok = False
            if raw_hash.startswith("$argon2"):
                from argon2 import PasswordHasher
                from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
                try:
                    PasswordHasher().verify(raw_hash, current_password)
                    password_ok = True
                except (VerifyMismatchError, VerificationError, InvalidHashError):
                    password_ok = False
            else:
                normalized = raw_hash.replace("$2y$", "$2b$").encode()
                try:
                    password_ok = bcrypt.checkpw(current_password.encode(), normalized)
                except ValueError:
                    password_ok = False

            if not password_ok:
                raise ValidationError("Mot de passe actuel incorrect")

            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tunnel_user SET password_hash = %s, updated_at = now() WHERE id = %s::uuid",
                    (new_hash, user_id),
                )
            conn.commit()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Erreur changement de mot de passe: {str(e)}") from e
        finally:
            if conn:
                release_connection(conn)
