from fastapi import HTTPException
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime, date

from api.settings import settings
from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, raise_db_error, NotFoundError
from api.utils.sanitizer import strip_html
from api.intervention_actions.validators import InterventionActionValidator


class InterventionActionRepository:
    """Requêtes pour le domaine intervention_action"""

    def _get_connection(self):
        return get_connection()

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

    def _map_tech_user(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Mappe les colonnes tech_* en objet tech imbriqué"""
        if row_dict.get('tech_id') is not None:
            row_dict['tech'] = {
                'id': row_dict['tech_id'],
                'first_name': row_dict.get('tech_first_name'),
                'last_name': row_dict.get('tech_last_name'),
                'email': row_dict.get('tech_email'),
                'initial': row_dict.get('tech_initial'),
                'status': row_dict.get('tech_status', 'active'),
                'role': row_dict.get('tech_role'),
            }
        else:
            row_dict['tech'] = None

        for key in ['tech_id', 'tech_first_name', 'tech_last_name',
                    'tech_email', 'tech_initial', 'tech_status', 'tech_role']:
            row_dict.pop(key, None)

        return row_dict

    def _get_linked_purchase_requests(self, action_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les demandes d'achat liées à une action (PurchaseRequestListItem)"""
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
            pr_ids = [str(row[0])
                      for row in cur.fetchall() if row[0] is not None]

            if not pr_ids:
                return []

            # Import ici pour éviter import circulaire
            from api.purchase_requests.repo import PurchaseRequestRepository
            return PurchaseRequestRepository().get_list(ids=pr_ids)
        except Exception:
            return []

    def get_all(
        self,
        filter_date: Optional[date] = None,
        tech_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Récupère toutes les actions avec subcategory, tech et purchase_requests hydratés"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where_clauses = []
            params: List[Any] = []

            if filter_date is not None:
                where_clauses.append("ia.created_at::date = %s")
                params.append(filter_date)
            if tech_id is not None:
                where_clauses.append("ia.tech = %s")
                params.append(tech_id)

            where_sql = ("WHERE " + " AND ".join(where_clauses)
                         ) if where_clauses else ""

            cur.execute(f"""
                SELECT
                    ia.id, ia.intervention_id, ia.description, ia.time_spent,
                    ia.tech, ia.complexity_score, ia.complexity_factor,
                    ia.action_start, ia.action_end,
                    ia.created_at, ia.updated_at,
                    sc.id as subcategory_id, sc.name as subcategory_name, sc.code as subcategory_code,
                    ac.id as category_id, ac.name as category_name, ac.code as category_code, ac.color,
                    u.id as tech_id, u.first_name as tech_first_name,
                    u.last_name as tech_last_name, u.email as tech_email,
                    u.initial as tech_initial, u.status as tech_status,
                    u.role as tech_role,
                    i.code as interv_code, i.title as interv_title, i.status_actual as interv_status,
                    m.id as interv_equipement_id, m.code as interv_equipement_code, m.name as interv_equipement_name
                FROM intervention_action ia
                LEFT JOIN action_subcategory sc ON ia.action_subcategory = sc.id
                LEFT JOIN action_category ac ON sc.category_id = ac.id
                LEFT JOIN directus_users u ON ia.tech = u.id
                LEFT JOIN intervention i ON ia.intervention_id = i.id
                LEFT JOIN machine m ON i.machine_id = m.id
                {where_sql}
                ORDER BY ia.created_at DESC
            """, params)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                action = self._map_action_with_subcategory(dict(zip(cols, row)))
                action = self._map_tech_user(action)
                action['intervention'] = {
                    'id': action['intervention_id'],
                    'code': action.pop('interv_code', None),
                    'title': action.pop('interv_title', None),
                    'status_actual': action.pop('interv_status', None),
                    'equipement_id': action.pop('interv_equipement_id', None),
                    'equipement_code': action.pop('interv_equipement_code', None),
                    'equipement_name': action.pop('interv_equipement_name', None),
                } if action.get('intervention_id') else None
                action['purchase_requests'] = self._get_linked_purchase_requests(str(action['id']), conn)
                results.append(action)
            return results
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def get_by_id(self, action_id: str) -> Dict[str, Any]:
        """Récupère une action par ID avec tech hydraté"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT ia.*,
                    u.id as tech_id, u.first_name as tech_first_name,
                    u.last_name as tech_last_name, u.email as tech_email,
                    u.initial as tech_initial, u.status as tech_status,
                    u.role as tech_role
                FROM intervention_action ia
                LEFT JOIN directus_users u ON ia.tech = u.id
                WHERE ia.id = %s
            """, (action_id,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Action {action_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            return self._map_tech_user(dict(zip(cols, row)))
        except NotFoundError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def get_by_intervention(self, intervention_id: str) -> List[Dict[str, Any]]:
        """Récupère les actions d'une intervention avec détail de sous-catégorie et couleur"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    ia.id, ia.intervention_id, ia.description, ia.time_spent,
                    ia.tech, ia.complexity_score, ia.complexity_factor,
                    ia.created_at, ia.updated_at,
                    sc.id as subcategory_id, sc.name as subcategory_name, sc.code as subcategory_code,
                    ac.id as category_id, ac.name as category_name, ac.code as category_code, ac.color,
                    u.id as tech_id, u.first_name as tech_first_name,
                    u.last_name as tech_last_name, u.email as tech_email,
                    u.initial as tech_initial, u.status as tech_status,
                    u.role as tech_role
                FROM intervention_action ia
                LEFT JOIN action_subcategory sc ON ia.action_subcategory = sc.id
                LEFT JOIN action_category ac ON sc.category_id = ac.id
                LEFT JOIN directus_users u ON ia.tech = u.id
                WHERE ia.intervention_id = %s
                ORDER BY ia.created_at ASC
                """,
                (intervention_id,)
            )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            results = []
            for row in rows:
                action = self._map_action_with_subcategory(
                    dict(zip(cols, row)))
                action = self._map_tech_user(action)
                action['purchase_requests'] = self._get_linked_purchase_requests(
                    str(action['id']), conn)
                results.append(action)
            return results
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def get_by_id_with_subcategory(self, action_id: str) -> Dict[str, Any]:
        """Récupère une action avec détail de sous-catégorie et couleur"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    ia.id, ia.intervention_id, ia.description, ia.time_spent,
                    ia.tech, ia.complexity_score, ia.complexity_factor,
                    ia.created_at, ia.updated_at,
                    sc.id as subcategory_id, sc.name as subcategory_name, sc.code as subcategory_code,
                    ac.id as category_id, ac.name as category_name, ac.code as category_code, ac.color,
                    u.id as tech_id, u.first_name as tech_first_name,
                    u.last_name as tech_last_name, u.email as tech_email,
                    u.initial as tech_initial, u.status as tech_status,
                    u.role as tech_role
                FROM intervention_action ia
                LEFT JOIN action_subcategory sc ON ia.action_subcategory = sc.id
                LEFT JOIN action_category ac ON sc.category_id = ac.id
                LEFT JOIN directus_users u ON ia.tech = u.id
                WHERE ia.id = %s
                """,
                (action_id,)
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Action {action_id} non trouvée")
            cols = [desc[0] for desc in cur.description]
            action = self._map_action_with_subcategory(dict(zip(cols, row)))
            action = self._map_tech_user(action)
            action['purchase_requests'] = self._get_linked_purchase_requests(
                action_id, conn)
            return action
        except NotFoundError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

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

            # Utilise created_at du validator (qui utilise now() si None)
            created_at = validated_data.get('created_at', now)

            cur.execute(
                """
                INSERT INTO intervention_action
                (id, intervention_id, description, time_spent, action_subcategory,
                 tech, complexity_score, complexity_factor, action_start, action_end,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    action_id,
                    validated_data['intervention_id'],
                    validated_data['description'],
                    validated_data.get('time_spent'),
                    validated_data['action_subcategory'],
                    validated_data['tech'],
                    validated_data['complexity_score'],
                    validated_data.get('complexity_factor'),
                    validated_data.get('action_start'),
                    validated_data.get('action_end'),
                    created_at,
                    now
                )
            )
            conn.commit()
            # Renvoie l'action avec les informations de sous-catégorie
            return self.get_by_id_with_subcategory(action_id)
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "ajout action")
        finally:
            release_connection(conn)

    def update(self, action_id: str, patch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour partiellement une action existante"""
        self.get_by_id_with_subcategory(action_id)

        updatable_fields = {
            'description': None,
            'time_spent': None,
            'action_subcategory': None,
            'tech': None,
            'complexity_score': None,
            'complexity_factor': None,
        }

        updates = {k: v for k, v in patch_data.items(
        ) if k in updatable_fields and v is not None}

        if not updates:
            return self.get_by_id_with_subcategory(action_id)

        # Validation partielle des champs fournis
        if 'description' in updates:
            updates['description'] = InterventionActionValidator.sanitize_description(
                updates['description'])
        if 'time_spent' in updates:
            InterventionActionValidator.validate_time_spent(
                updates['time_spent'])
        if 'complexity_score' in updates:
            InterventionActionValidator.validate_complexity_score(
                updates['complexity_score'])
        if 'complexity_factor' in updates:
            updates['complexity_factor'] = InterventionActionValidator.validate_complexity_factor(
                updates['complexity_factor'])

        # Si l'un des deux score/factor est fourni, on valide la règle score > 5
        current = self.get_by_id_with_subcategory(action_id)
        score = updates.get('complexity_score',
                            current.get('complexity_score'))
        factor = updates.get('complexity_factor',
                             current.get('complexity_factor'))
        InterventionActionValidator.validate_complexity_with_factor(
            score, factor)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            set_clauses = [f"{field} = %s" for field in updates]
            params = list(updates.values())
            set_clauses.append("updated_at = %s")
            params.append(datetime.now())
            params.append(action_id)

            cur.execute(
                f"UPDATE intervention_action SET {', '.join(set_clauses)} WHERE id = %s",
                params
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            release_connection(conn)

        return self.get_by_id_with_subcategory(action_id)
