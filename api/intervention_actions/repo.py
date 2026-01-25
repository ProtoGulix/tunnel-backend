from typing import Dict, Any, List

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.utils.sanitizer import strip_html


class InterventionActionRepository:
    """Requêtes pour le domaine intervention_action"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(f"Erreur de connexion base de données: {str(e)}")

    def _map_action_with_subcategory(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Mappe une row avec subcategory et category imbriquées"""
        # Nettoie la description HTML
        if row_dict.get('description'):
            row_dict['description'] = strip_html(row_dict['description'])
        
        if row_dict.get('subcategory_id') is not None:
            row_dict['subcategory'] = {
                'id': row_dict['subcategory_id'],
                'name': row_dict['subcategory_name'],
                'code': row_dict['subcategory_code'],
                'category': {
                    'id': row_dict['category_id'],
                    'name': row_dict['category_name'],
                    'code': row_dict['category_code'],
                    'color': row_dict['color']
                }
            }
        else:
            row_dict['subcategory'] = None
        
        # Nettoie les colonnes intermédiaires
        for key in ['subcategory_id', 'subcategory_name', 'subcategory_code', 
                    'category_id', 'category_name', 'category_code', 'color']:
            row_dict.pop(key, None)
        
        return row_dict

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère toutes les actions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM intervention_action ORDER BY created_at DESC")
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_id(self, action_id: str) -> Dict[str, Any]:
        """Récupère une action par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM intervention_action WHERE id = %s", (action_id,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Action {action_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_intervention(self, intervention_id: str) -> List[Dict[str, Any]]:
        """Récupère les actions d'une intervention avec détail de sous-catégorie et couleur"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 
                    ia.id, ia.intervention_id, ia.description, ia.time_spent, 
                    ia.tech, ia.complexity_score, ia.complexity_anotation, 
                    ia.created_at, ia.updated_at,
                    sc.id as subcategory_id, sc.name as subcategory_name, sc.code as subcategory_code,
                    ac.id as category_id, ac.name as category_name, ac.code as category_code, ac.color
                FROM intervention_action ia
                LEFT JOIN action_subcategory sc ON ia.action_subcategory = sc.id
                LEFT JOIN action_category ac ON sc.category_id = ac.id
                WHERE ia.intervention_id = %s 
                ORDER BY ia.created_at ASC
                """,
                (intervention_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            
            return [
                self._map_action_with_subcategory(dict(zip(cols, row)))
                for row in rows
            ]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()
