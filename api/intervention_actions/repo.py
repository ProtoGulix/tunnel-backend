from fastapi import HTTPException
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime, date

from api.settings import settings
from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, raise_db_error, NotFoundError, ValidationError
from api.utils.sanitizer import strip_html
from api.intervention_actions.validators import InterventionActionValidator


class InterventionActionRepository:
    """Requêtes pour le domaine intervention_action"""

    def _get_connection(self):
        return get_connection()

    def _map_action_with_subcategory(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Mappe une row avec subcategory et category imbriquées"""
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

            # Import lazy pour éviter import circulaire
            from api.purchase_requests.repo import PurchaseRequestRepository
            return PurchaseRequestRepository().get_list(ids=pr_ids)
        except Exception:
            return []

    def _get_task_for_action(self, action_id: str, conn) -> Optional[Dict[str, Any]]:
        """Récupère la tâche liée à cette action via task_id."""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT it.id, it.label, it.status, it.origin
                FROM intervention_action ia
                JOIN intervention_task it ON it.id = ia.task_id
                WHERE ia.id = %s
                """,
                (action_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        except Exception:
            return None

    def get_all(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        tech_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Récupère les actions groupées par date (created_at::date), triées du plus récent au plus ancien"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where_clauses = []
            params: List[Any] = []

            if date_from is not None:
                where_clauses.append("ia.created_at::date >= %s")
                params.append(date_from)
            if date_to is not None:
                where_clauses.append("ia.created_at::date <= %s")
                params.append(date_to)
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
                ORDER BY ia.created_at::date DESC, ia.created_at ASC
            """, params)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            all_actions = []
            for row in rows:
                action = self._map_action_with_subcategory(
                    dict(zip(cols, row)))
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
                action['purchase_requests'] = []
                action['task'] = None
                all_actions.append(action)

            if all_actions:
                action_ids = [str(a['id']) for a in all_actions]
                placeholders = ','.join(['%s'] * len(action_ids))

                # Batch PR
                cur.execute(
                    f"""
                    SELECT intervention_action_id, purchase_request_id
                    FROM intervention_action_purchase_request
                    WHERE intervention_action_id IN ({placeholders})
                    """,
                    action_ids
                )
                links = cur.fetchall()
                if links:
                    pr_ids = list({str(row[1]) for row in links if row[1]})
                    from api.purchase_requests.repo import PurchaseRequestRepository
                    all_prs = PurchaseRequestRepository().get_list(ids=pr_ids)
                    pr_by_id = {str(pr['id']): pr for pr in all_prs}
                    action_pr_map: Dict[str, List] = {}
                    for action_id, pr_id in links:
                        action_pr_map.setdefault(
                            str(action_id), []).append(str(pr_id))
                    for action in all_actions:
                        action['purchase_requests'] = [
                            pr_by_id[pid] for pid in action_pr_map.get(str(action['id']), [])
                            if pid in pr_by_id
                        ]

                # Batch tâches liées via task_id
                cur.execute(
                    f"""
                    SELECT ia.id AS action_id, it.id, it.label, it.status, it.origin
                    FROM intervention_action ia
                    JOIN intervention_task it ON it.id = ia.task_id
                    WHERE ia.id IN ({placeholders})
                    """,
                    action_ids
                )
                task_rows = cur.fetchall()
                if task_rows:
                    task_by_action: Dict[str, Dict] = {}
                    cols_task = [d[0] for d in cur.description]
                    for row in task_rows:
                        row_dict = dict(zip(cols_task, row))
                        aid = str(row_dict.pop('action_id'))
                        task_by_action[aid] = row_dict
                    for action in all_actions:
                        action['task'] = task_by_action.get(str(action['id']))

            # Groupement par date
            groups: Dict[date, List[Dict[str, Any]]] = {}
            for action in all_actions:
                day = action['created_at'].date() if action.get(
                    'created_at') else None
                if day is not None:
                    groups.setdefault(day, []).append(action)

            return [
                {'date': d, 'actions': groups[d]}
                for d in sorted(groups.keys(), reverse=True)
            ]
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def get_by_id(self, action_id: str) -> Dict[str, Any]:
        """Récupère une action par ID avec tech, subcategory et intervention hydratés"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
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
                WHERE ia.id = %s
            """, (action_id,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Action {action_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
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
            action['purchase_requests'] = self._get_linked_purchase_requests(
                str(action['id']), conn)
            action['task'] = self._get_task_for_action(str(action['id']), conn)
            return action
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
                    ia.action_start, ia.action_end,
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
                action['purchase_requests'] = []
                action['task'] = None
                results.append(action)

            if not results:
                return results

            action_ids = [str(a['id']) for a in results]
            placeholders = ','.join(['%s'] * len(action_ids))

            # Batch PR
            cur.execute(
                f"""
                SELECT intervention_action_id, purchase_request_id
                FROM intervention_action_purchase_request
                WHERE intervention_action_id IN ({placeholders})
                """,
                action_ids
            )
            links = cur.fetchall()

            if links:
                pr_ids = list({str(row[1]) for row in links if row[1]})
                from api.purchase_requests.repo import PurchaseRequestRepository
                all_prs = PurchaseRequestRepository().get_list(ids=pr_ids)
                pr_by_id = {str(pr['id']): pr for pr in all_prs}

                action_pr_map: Dict[str, List] = {}
                for action_id, pr_id in links:
                    action_pr_map.setdefault(
                        str(action_id), []).append(str(pr_id))

                for action in results:
                    action['purchase_requests'] = [
                        pr_by_id[pid] for pid in action_pr_map.get(str(action['id']), [])
                        if pid in pr_by_id
                    ]

            # Batch tâches liées via task_id
            cur.execute(
                f"""
                SELECT ia.id AS action_id, it.id, it.label, it.status, it.origin
                FROM intervention_action ia
                JOIN intervention_task it ON it.id = ia.task_id
                WHERE ia.id IN ({placeholders})
                """,
                action_ids
            )
            task_rows = cur.fetchall()
            if task_rows:
                task_by_action: Dict[str, Dict] = {}
                cols_task = [d[0] for d in cur.description]
                for row in task_rows:
                    row_dict = dict(zip(cols_task, row))
                    aid = str(row_dict.pop('action_id'))
                    task_by_action[aid] = row_dict
                for action in results:
                    action['task'] = task_by_action.get(str(action['id']))

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
        """Ajoute une nouvelle action à une intervention.

        Si task_id est fourni, vérifie que la tâche appartient à l'intervention,
        lie l'action à la tâche et passe la tâche todo→in_progress.
        """
        task_id = action_data.pop('task_id', None)
        if task_id is None:
            raise ValidationError("Champs obligatoires manquants : task_id")
        task_id = str(task_id)

        validated_data = InterventionActionValidator.validate_and_prepare(
            action_data)

        import uuid as _uuid

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            action_id = str(uuid4())
            now = datetime.now()

            created_at = validated_data.get('created_at', now)

            # Vérifier que la tâche appartient à la même intervention
            cur.execute(
                "SELECT intervention_id FROM intervention_task WHERE id = %s",
                (task_id,)
            )
            task_row = cur.fetchone()
            if not task_row:
                raise ValidationError(f"Tâche {task_id} introuvable")
            if str(task_row[0]) != str(validated_data['intervention_id']):
                raise ValidationError(
                    "La tâche fournie n'appartient pas à la même intervention"
                )

            cur.execute(
                """
                INSERT INTO intervention_action
                (id, intervention_id, description, time_spent, action_subcategory,
                 tech, complexity_score, complexity_factor, action_start, action_end,
                 task_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    action_id,
                    str(validated_data['intervention_id']) if isinstance(
                        validated_data['intervention_id'], _uuid.UUID) else validated_data['intervention_id'],
                    validated_data['description'],
                    validated_data.get('time_spent'),
                    validated_data['action_subcategory'],
                    str(validated_data['tech']) if isinstance(
                        validated_data['tech'], _uuid.UUID) else validated_data['tech'],
                    validated_data['complexity_score'],
                    validated_data.get('complexity_factor'),
                    validated_data.get('action_start'),
                    validated_data.get('action_end'),
                    task_id,
                    created_at,
                    now
                )
            )

            # Transition automatique todo → in_progress à la première action liée
            if task_id:
                # Import lazy pour éviter la circularité avec intervention_tasks.repo
                from api.intervention_tasks.repo import InterventionTaskRepository
                InterventionTaskRepository().transition_to_in_progress(task_id, conn)

            conn.commit()
            return self.get_by_id(action_id)
        except (ValidationError, NotFoundError):
            conn.rollback()
            raise
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
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT complexity_score, complexity_factor FROM intervention_action WHERE id = %s", (action_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Action {action_id} non trouvée")
            cols = [desc[0] for desc in cur.description]
            current = dict(zip(cols, row))
        except NotFoundError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

        updatable_fields = {
            'description', 'time_spent', 'action_subcategory', 'tech',
            'complexity_score', 'complexity_factor', 'action_start', 'action_end',
            'created_at',
        }

        updates = {k: v for k, v in patch_data.items()
                   if k in updatable_fields and v is not None}

        if not updates:
            return self.get_by_id(action_id)

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

        score = updates.get('complexity_score',
                            current.get('complexity_score'))
        factor = updates.get('complexity_factor',
                             current.get('complexity_factor'))
        if isinstance(score, int) and score > 5 and (not factor or not str(factor).strip()):
            raise ValidationError(
                "complexity_factor est obligatoire quand complexity_score > 5"
            )

        has_bounds = 'action_start' in updates or 'action_end' in updates
        has_direct = 'time_spent' in updates
        if has_bounds and not has_direct:
            updates['time_spent'] = None
        elif has_direct and not has_bounds:
            updates['action_start'] = None
            updates['action_end'] = None

        import uuid as _uuid
        params_updates = {
            k: str(v) if isinstance(v, _uuid.UUID) else v
            for k, v in updates.items()
        }

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            set_clauses = [f"{field} = %s" for field in params_updates]
            params = list(params_updates.values())
            set_clauses.append("updated_at = %s")
            params.append(datetime.now())
            params.append(action_id)

            cur.execute(
                f"UPDATE intervention_action SET {', '.join(set_clauses)} WHERE id = %s",
                params
            )
            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "mise à jour action")
        finally:
            release_connection(conn)

        return self.get_by_id(action_id)
