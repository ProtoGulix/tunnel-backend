from typing import Dict, Any, List

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError


class ActionSubcategoryRepository:
    """Requêtes pour le domaine action_subcategory"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(f"Erreur de connexion base de données: {str(e)}")

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère toutes les sous-catégories"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM action_subcategory ORDER BY name ASC")
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_id(self, subcategory_id: int) -> Dict[str, Any]:
        """Récupère une sous-catégorie par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM action_subcategory WHERE id = %s", (subcategory_id,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Sous-catégorie {subcategory_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Récupère les sous-catégories d'une catégorie"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM action_subcategory WHERE category_id = %s ORDER BY name ASC",
                (category_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()
