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

    def _get_gamme_steps_for_action(self, action_id: str, conn) -> List[Dict[str, Any]]:
        """Récupère les steps de gamme validés/skippés par cette action"""
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    gsv.id, gsv.step_id,
                    gs.label AS step_label,
                    gs.sort_order AS step_sort_order,
                    gs.optional AS step_optional,
                    gsv.status, gsv.skip_reason, gsv.validated_at, gsv.validated_by
                FROM gamme_step_validation gsv
                LEFT JOIN preventive_plan_gamme_step gs ON gs.id = gsv.step_id
                WHERE gsv.action_id = %s
                ORDER BY gs.sort_order ASC
                """,
                (action_id,)
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception:
            return []

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

            # Première passe : mapper toutes les actions
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
                action['gamme_steps'] = []
                all_actions.append(action)

            # Batch PR : 2 requêtes pour toutes les actions
            if all_actions:
                action_ids = [str(a['id']) for a in all_actions]
                placeholders = ','.join(['%s'] * len(action_ids))
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

                # Batch gamme steps : récupère les steps liés
                cur.execute(
                    f"""
                    SELECT
                        gsv.action_id, gsv.id, gsv.step_id,
                        gs.label AS step_label,
                        gs.sort_order AS step_sort_order,
                        gs.optional AS step_optional,
                        gsv.status, gsv.skip_reason, gsv.validated_at, gsv.validated_by
                    FROM gamme_step_validation gsv
                    LEFT JOIN preventive_plan_gamme_step gs ON gs.id = gsv.step_id
                    WHERE gsv.action_id IN ({placeholders})
                    ORDER BY gs.sort_order ASC
                    """,
                    action_ids
                )
                steps_rows = cur.fetchall()
                if steps_rows:
                    action_steps_map: Dict[str, List] = {}
                    cols_steps = [d[0] for d in cur.description]
                    for row in steps_rows:
                        row_dict = dict(zip(cols_steps, row))
                        action_id = str(row_dict.pop('action_id'))
                        action_steps_map.setdefault(action_id, []).append(row_dict)
                    for action in all_actions:
                        action['gamme_steps'] = action_steps_map.get(str(action['id']), [])

            # Groupement par date
            groups: Dict[date, List[Dict[str, Any]]] = {}
            for action in all_actions:
                day = action['created_at'].date() if action.get(
                    'created_at') else None
                if day is not None:
                    groups.setdefault(day, []).append(action)

            # Retourne les jours du plus récent au plus ancien
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
            action['gamme_steps'] = self._get_gamme_steps_for_action(
                str(action['id']), conn)
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
                action['gamme_steps'] = []
                results.append(action)

            if not results:
                return results

            # Batch : récupère tous les PR liés à toutes les actions en 2 requêtes
            action_ids = [str(a['id']) for a in results]
            placeholders = ','.join(['%s'] * len(action_ids))
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

                # Index : action_id → [pr_id, ...]
                action_pr_map: Dict[str, List] = {}
                for action_id, pr_id in links:
                    action_pr_map.setdefault(
                        str(action_id), []).append(str(pr_id))

                for action in results:
                    action['purchase_requests'] = [
                        pr_by_id[pid] for pid in action_pr_map.get(str(action['id']), [])
                        if pid in pr_by_id
                    ]

            # Batch : récupère les steps de gamme liés à toutes les actions
            cur.execute(
                f"""
                SELECT
                    gsv.action_id, gsv.id, gsv.step_id,
                    gs.label AS step_label,
                    gs.sort_order AS step_sort_order,
                    gs.optional AS step_optional,
                    gsv.status, gsv.skip_reason, gsv.validated_at, gsv.validated_by
                FROM gamme_step_validation gsv
                LEFT JOIN preventive_plan_gamme_step gs ON gs.id = gsv.step_id
                WHERE gsv.action_id IN ({placeholders})
                ORDER BY gs.sort_order ASC
                """,
                action_ids
            )
            steps_rows = cur.fetchall()

            if steps_rows:
                # Index : action_id → [steps...]
                action_steps_map: Dict[str, List] = {}
                cols_steps = [d[0] for d in cur.description]
                for row in steps_rows:
                    row_dict = dict(zip(cols_steps, row))
                    action_id = str(row_dict.pop('action_id'))
                    action_steps_map.setdefault(action_id, []).append(row_dict)

                for action in results:
                    action['gamme_steps'] = action_steps_map.get(str(action['id']), [])

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
        """Ajoute une nouvelle action à une intervention

        Si gamme_step_validations est fourni (liste), valide/skippe les steps après création.
        Chaque validatior peut être :
          - status="validated" : lie l'action_id au step
          - status="skipped" : skippe le step avec skip_reason
        """
        # Extraction des validations de gamme steps avant la validation
        gamme_step_validations = action_data.pop('gamme_step_validations', None)

        # Validation et préparation des données — lève ValidationError (400) si invalide
        validated_data = InterventionActionValidator.validate_and_prepare(
            action_data)

        import uuid as _uuid

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
                    created_at,
                    now
                )
            )
            conn.commit()

            # Valider/skipper les gamme steps si fournis
            if gamme_step_validations:
                # Import lazy pour éviter la circularité
                from api.gamme_step_validations.repo import GammeStepValidationRepository
                from api.gamme_step_validations.schemas import GammeStepValidationPatch

                gsv_repo = GammeStepValidationRepository()

                for gsv_request in gamme_step_validations:
                    if gsv_request.get('status') == "skipped":
                        # Mode skip
                        patch_data = GammeStepValidationPatch(
                            status="skipped",
                            skip_reason=gsv_request.get('skip_reason'),
                            validated_by=validated_data['tech'],
                            action_id=None
                        )
                    else:
                        # Mode validation : lier à l'action créée
                        patch_data = GammeStepValidationPatch(
                            status="validated",
                            action_id=_uuid.UUID(action_id),
                            validated_by=validated_data['tech'],
                            skip_reason=None
                        )

                    gsv_repo.patch_validation(
                        str(gsv_request.get('step_validation_id')),
                        patch_data
                    )

            return self.get_by_id(action_id)
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
        # Vérification d'existence (légère)
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

        # Valide la règle score > 5 → complexity_factor obligatoire (valeurs fusionnées)
        score = updates.get('complexity_score',
                            current.get('complexity_score'))
        factor = updates.get('complexity_factor',
                             current.get('complexity_factor'))
        if isinstance(score, int) and score > 5 and (not factor or not str(factor).strip()):
            raise ValidationError(
                "complexity_factor est obligatoire quand complexity_score > 5"
            )

        # Respect de l'exclusivité bornes/time_spent imposée par le trigger PostgreSQL :
        # si le PATCH passe en mode bornes (action_start+action_end), on efface time_spent,
        # et inversement.
        has_bounds = 'action_start' in updates or 'action_end' in updates
        has_direct = 'time_spent' in updates
        if has_bounds and not has_direct:
            # forcer NULL pour satisfaire le trigger
            updates['time_spent'] = None
        elif has_direct and not has_bounds:
            updates['action_start'] = None
            updates['action_end'] = None

        # Normalise les UUID en str pour psycopg2 (compatibilité avec ou sans register_uuid)
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
