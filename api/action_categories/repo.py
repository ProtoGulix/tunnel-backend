from typing import Dict, Any, List

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError


class ActionCategoryRepository:
    """Requêtes pour le domaine action_category"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}")

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère toutes les catégories avec leurs sous-catégories"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Récupérer toutes les catégories
            cur.execute("SELECT * FROM action_category ORDER BY name ASC")
            categories = cur.fetchall()
            cat_cols = [desc[0] for desc in cur.description]

            # Récupérer toutes les sous-catégories
            cur.execute("SELECT * FROM action_subcategory ORDER BY name ASC")
            subcategories = cur.fetchall()
            subcat_cols = [desc[0] for desc in cur.description]

            # Construire le dict des sous-catégories par category_id
            subcat_by_cat = {}
            for row in subcategories:
                subcat = dict(zip(subcat_cols, row))
                cat_id = subcat.get('category_id')
                if cat_id:
                    if cat_id not in subcat_by_cat:
                        subcat_by_cat[cat_id] = []
                    subcat_by_cat[cat_id].append(subcat)

            # Construire les catégories avec sous-catégories imbriquées
            result = []
            for row in categories:
                category = dict(zip(cat_cols, row))
                category['subcategories'] = subcat_by_cat.get(
                    category['id'], [])
                result.append(category)

            return result
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_id(self, category_id: int) -> Dict[str, Any]:
        """Récupère une catégorie par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM action_category WHERE id = %s", (category_id,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Catégorie {category_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()
