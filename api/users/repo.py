from typing import List, Dict, Any, Optional

from api.errors.exceptions import DatabaseError, NotFoundError
from api.db import get_connection, release_connection


LIST_COLUMNS = "tu.id, tu.first_name, tu.last_name, tu.email, tu.initial, tu.is_active, tr.code AS role"
DETAIL_COLUMNS = (
    "tu.id, tu.first_name, tu.last_name, tu.email, tu.initial, "
    "tu.is_active, tr.code AS role, tu.created_at AS last_access"
)


class UserRepository:

    def get_all(
        self,
        limit: int = 100,
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
