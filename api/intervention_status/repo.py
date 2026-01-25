from typing import List, Dict, Any

from api.settings import settings
from api.errors.exceptions import DatabaseError


class InterventionStatusRepository:
    """Repository pour les statuts d'intervention"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}")

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
            conn.close()

    def get_active_status_ids(self) -> List[str]:
        """Récupère les IDs des statuts considérés comme 'actifs' (ouvert ou en cours)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            # Statuts actifs : ceux qui ne sont pas fermés/annulés
            cur.execute(
                """
                SELECT id
                FROM intervention_status_ref
                WHERE code NOT IN ('closed', 'cancelled', 'archived')
                ORDER BY id ASC
                """
            )

            rows = cur.fetchall()
            return [row[0] for row in rows]

        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()
