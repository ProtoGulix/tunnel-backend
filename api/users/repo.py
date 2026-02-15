from typing import List, Dict, Any, Optional

from api.errors.exceptions import DatabaseError, NotFoundError
from api.settings import settings


# Champs exposés (exclusion des champs sensibles)
LIST_COLUMNS = "id, first_name, last_name, email, initial, status, role"
DETAIL_COLUMNS = (
    "id, first_name, last_name, email, location, title, description, "
    "tags, avatar, status, role, initial, last_access"
)


class UserRepository:

    def _get_connection(self):
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(f"Erreur de connexion: {str(e)}") from e

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where_clauses: List[str] = []
            params: List[Any] = []

            if status is not None:
                where_clauses.append("status = %s")
                params.append(status)

            if search is not None:
                where_clauses.append(
                    "(first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s)"
                )
                like = f"%{search}%"
                params.extend([like, like, like])

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            query = f"""
                SELECT {LIST_COLUMNS}
                FROM directus_users
                {where_sql}
                ORDER BY last_name ASC, first_name ASC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, user_id: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                f"SELECT {DETAIL_COLUMNS} FROM directus_users WHERE id = %s",
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
            conn.close()
