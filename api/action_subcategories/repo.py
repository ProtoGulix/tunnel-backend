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
        """Récupère toutes les sous-catégories avec leur catégorie"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    s.*,
                    c.id as cat_id,
                    c.name as cat_name,
                    c.code as cat_code,
                    c.color as cat_color
                FROM action_subcategory s
                LEFT JOIN action_category c ON s.category_id = c.id
                ORDER BY s.name ASC
            """)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            
            result = []
            for row in rows:
                data = dict(zip(cols, row))
                
                # Construire l'objet sous-catégorie avec catégorie imbriquée
                subcategory = {
                    'id': data['id'],
                    'category_id': data['category_id'],
                    'name': data['name'],
                    'code': data['code'],
                    'category': {
                        'id': data['cat_id'],
                        'name': data['cat_name'],
                        'code': data['cat_code'],
                        'color': data['cat_color']
                    } if data['cat_id'] else None
                }
                result.append(subcategory)
            
            return result
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
