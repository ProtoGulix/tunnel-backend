from typing import List, Dict, Any

from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError


class InterventionStatusRepository:
    """Repository pour les statuts d'intervention"""

    def _get_connection(self):
        return get_connection()

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les statuts d'intervention"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, code, label, color, value
                FROM intervention_status_ref
                ORDER BY code ASC
                """
            )

            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]

        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            release_connection(conn)

