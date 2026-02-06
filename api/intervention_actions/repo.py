from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.utils.sanitizer import strip_html
from api.intervention_actions.validators import InterventionActionValidator


class InterventionActionRepository:
    """Requêtes pour le domaine intervention_action"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

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

    def _get_linked_purchase_requests(self, action_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les demandes d'achat liées à une action via PurchaseRequestRepository"""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT purchase_request_id
                FROM intervention_action_purchase_request
                WHERE intervention_action_id = %s
                """,
                (action_id,)
            )
            pr_ids = [str(row[0]) for row in cur.fetchall()]

            if not pr_ids:
                return []

            # Import ici pour éviter import circulaire
            from api.purchase_requests.repo import PurchaseRequestRepository
            pr_repo = PurchaseRequestRepository()

            results = []
            for pr_id in pr_ids:
                try:
                    pr = pr_repo.get_by_id(pr_id)
                    results.append(pr)
                except Exception:
                    continue
            return results
        except Exception:
            # Table peut ne pas exister, retourne liste vide
            return []

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère toutes les actions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM intervention_action ORDER BY created_at DESC")
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, action_id: str) -> Dict[str, Any]:
        """Récupère une action par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM intervention_action WHERE id = %s", (action_id,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Action {action_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
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

            results = []
            for row in rows:
                action = self._map_action_with_subcategory(dict(zip(cols, row)))
                action['purchase_requests'] = self._get_linked_purchase_requests(
                    str(action['id']), conn)
                results.append(action)
            return results
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id_with_subcategory(self, action_id: str) -> Dict[str, Any]:
        """Récupère une action avec détail de sous-catégorie et couleur"""
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
                WHERE ia.id = %s
                """,
                (action_id,)
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Action {action_id} non trouvée")
            cols = [desc[0] for desc in cur.description]
            action = self._map_action_with_subcategory(dict(zip(cols, row)))
            action['purchase_requests'] = self._get_linked_purchase_requests(
                action_id, conn)
            return action
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ajoute une nouvelle action à une intervention"""
        # Validation et préparation des données selon les règles métier
        try:
            validated_data = InterventionActionValidator.validate_and_prepare(
                action_data)
        except ValueError as e:
            raise DatabaseError(f"Erreur de validation: {str(e)}") from e

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            action_id = str(uuid4())
            now = datetime.now()
            # Persist complexity as JSON object {code: true} to match DB json type
            # Si complexity_anotation est None, stocker None au lieu d'un objet JSON
            complexity_anotation = validated_data.get('complexity_anotation')
            complexity_json = {complexity_anotation: True} if complexity_anotation else None

            # Utilise created_at du validator (qui utilise now() si None)
            created_at = validated_data.get('created_at', now)

            cur.execute(
                """
                INSERT INTO intervention_action
                (id, intervention_id, description, time_spent, action_subcategory,
                 tech, complexity_score, complexity_anotation, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    action_id,
                    validated_data['intervention_id'],
                    validated_data['description'],
                    validated_data['time_spent'],
                    validated_data['action_subcategory'],
                    validated_data['tech'],
                    validated_data['complexity_score'],
                    complexity_json,
                    created_at,
                    now
                )
            )
            conn.commit()
            # Renvoie l'action avec les informations de sous-catégorie
            return self.get_by_id_with_subcategory(action_id)
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de l'ajout de l'action: {str(e)}") from e
        finally:
            conn.close()
