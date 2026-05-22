from datetime import date
from fastapi import HTTPException
from typing import Dict, Any, List
from uuid import uuid4

from api.settings import settings
from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, ValidationError, raise_db_error, NotFoundError
from api.constants import PRIORITY_TYPES, CLOSED_STATUS_CODE

from api.intervention_actions.repo import InterventionActionRepository
from api.intervention_status_log.repo import InterventionStatusLogRepository

# LATERAL join pour récupérer la liste complète des tâches d'une intervention
_TASKS_JSON_LATERAL = """
    LEFT JOIN LATERAL (
        SELECT COALESCE(
            json_agg(
                json_build_object(
                    'id',            it.id,
                    'intervention_id', it.intervention_id,
                    'label',         it.label,
                    'origin',        it.origin,
                    'status',        it.status,
                    'optional',      it.optional,
                    'due_date',      it.due_date,
                    'sort_order',    it.sort_order,
                    'skip_reason',   it.skip_reason,
                    'gamme_step_id', it.gamme_step_id,
                    'occurrence_id', it.occurrence_id,
                    'closed_by',     it.closed_by,
                    'created_by',    it.created_by,
                    'created_at',    it.created_at,
                    'updated_at',    it.updated_at,
                    'action_count',  COALESCE(tagg.action_count, 0),
                    'time_spent',    COALESCE(tagg.time_spent, 0.0),
                    'assigned_to',   CASE WHEN u.id IS NOT NULL THEN json_build_object(
                        'id',         u.id,
                        'first_name', u.first_name,
                        'last_name',  u.last_name,
                        'email',      u.email,
                        'initial',    u.initial
                    ) END
                )
                ORDER BY it.sort_order, it.created_at
            ),
            '[]'::json
        ) AS tasks_json
        FROM intervention_task it
        LEFT JOIN tunnel_user u ON u.id = it.assigned_to
        LEFT JOIN LATERAL (
            SELECT
                COUNT(DISTINCT iat.action_id) AS action_count,
                COALESCE(SUM(ia.time_spent), 0) AS time_spent
            FROM intervention_action_task iat
            INNER JOIN intervention_action ia ON ia.id = iat.action_id
            WHERE iat.task_id = it.id
        ) tagg ON TRUE
        WHERE it.intervention_id = i.id
    ) it_agg ON TRUE
"""


class InterventionRepository:
    """Requêtes pour le domaine interventions"""

    def _get_connection(self):
        return get_connection()

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        equipement_id: str | None = None,
        statuses: List[str] | None = None,
        priorities: List[str] | None = None,
        sort: str | None = None,
        include_stats: bool = True,
        include_tasks: bool = False,
        printed: bool | None = None,
        tech_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Récupère interventions avec filtres/sort et stats calculées en SQL (sans actions)"""
        # Garde-fou: limit max 1000
        limit = min(limit, 1000)

        # Valider priorités via PRIORITY_TYPES (source de vérité unique)
        priorities_norm = None
        if priorities:
            allowed_ids = {p['id'] for p in PRIORITY_TYPES}
            priorities_norm = [p for p in priorities if p in allowed_ids]

        # Construire SQL
        where_clauses = []
        params: List[Any] = []
        joins = []

        if search:
            like = f"%{search}%"
            where_clauses.append(
                "(i.code ILIKE %s OR i.title ILIKE %s OR m.code ILIKE %s OR m.name ILIKE %s)")
            params.extend([like, like, like, like])

        if equipement_id:
            where_clauses.append("i.machine_id = %s")
            params.append(equipement_id)

        if statuses and len(statuses) > 0:
            placeholders = ",".join(["%s"] * len(statuses))
            where_clauses.append(f"LOWER(i.status_actual) IN ({placeholders})")
            params.extend([s.lower() for s in statuses])

        if priorities_norm and len(priorities_norm) > 0:
            placeholders = ",".join(["%s"] * len(priorities_norm))
            where_clauses.append(f"i.priority IN ({placeholders})")
            params.extend(priorities_norm)

        if printed is not None:
            where_clauses.append("i.printed_fiche = %s")
            params.append(printed)

        if tech_id:
            where_clauses.append("i.tech_id = %s")
            params.append(tech_id)

        where_sql = ("WHERE " + " AND ".join(where_clauses)
                     ) if where_clauses else ""

        # Tri
        order_sql_parts = []
        if sort:
            for item in [s.strip() for s in sort.split(',') if s.strip()]:
                desc = item.startswith('-')
                key = item[1:] if desc else item
                if key == 'reported_date':
                    order_sql_parts.append(
                        f"i.reported_date {'DESC' if desc else 'ASC'}")
                elif key == 'priority':
                    # Tri de sévérité: urgent > important > normale > faible
                    case_expr = (
                        "CASE i.priority "
                        "WHEN 'urgent' THEN 0 "
                        "WHEN 'important' THEN 1 "
                        "WHEN 'normale' THEN 2 "
                        "WHEN 'faible' THEN 3 "
                        "ELSE 4 END"
                    )
                    order_sql_parts.append(
                        f"{case_expr} {'ASC' if desc else 'DESC'}")
                elif key == 'next_due_date':
                    # NULLS LAST : interventions sans tâches avec due_date toujours en fin
                    order_sql_parts.append(
                        f"task_agg.next_due_date {'DESC' if desc else 'ASC'} NULLS LAST")
        if not order_sql_parts:
            order_sql_parts.append("i.reported_date DESC")
        order_sql = " ORDER BY " + ", ".join(order_sql_parts)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            query = f"""
                SELECT
                    i.*,
                    ir.id        AS req_id,
                    ir.code      AS req_code,
                    ir.demandeur_nom, ir.demandeur_service_legacy AS demandeur_service, ir.description AS req_description,
                    ir.statut    AS req_statut,
                    rs2.label    AS req_statut_label,
                    rs2.color    AS req_statut_color,
                    ir.intervention_id AS req_intervention_id,
                    ir.created_at AS req_created_at,
                    ir.updated_at AS req_updated_at,
                    m.code as m_code, m.name as m_name,
                    pm.id   AS m_parent_id,
                    pm.code AS m_parent_code,
                    pm.name AS m_parent_name,
                    ec.id as ec_id, ec.code as ec_code, ec.label as ec_label,
                    COALESCE(SUM(ia.time_spent), 0) as total_time,
                    COUNT(DISTINCT ia.id) as action_count,
                    ROUND(AVG(ia.complexity_score)::numeric, 2)::float as avg_complexity,
                    task_agg.task_total,
                    task_agg.task_todo,
                    task_agg.task_in_progress,
                    task_agg.task_done,
                    task_agg.task_skipped,
                    task_agg.task_blocking_pending,
                    task_agg.next_due_date,
                    pr_agg.pr_total,
                    pr_agg.pr_received,
                    pr_agg.pr_to_qualify,
                    pr_agg.pr_no_supplier_ref,
                    pr_agg.pr_pending_dispatch,
                    pr_agg.pr_rejected,
                    pr_agg.pr_consultation,
                    pr_agg.pr_partial,
                    pr_agg.pr_ordered,
                    pr_agg.pr_quoted,
                    pr_agg.pr_open
                    {', it_agg.tasks_json::text AS tasks_json' if include_tasks else ''}
                FROM intervention i
                LEFT JOIN intervention_request ir ON ir.intervention_id = i.id
                LEFT JOIN request_status_ref rs2 ON rs2.code = ir.statut
                LEFT JOIN machine m ON i.machine_id = m.id
                LEFT JOIN machine pm ON pm.id = m.equipement_mere
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                LEFT JOIN intervention_action ia ON i.id = ia.intervention_id
                LEFT JOIN LATERAL (
                    SELECT
                        COUNT(*)                                                          AS task_total,
                        COUNT(*) FILTER (WHERE status = 'todo')                          AS task_todo,
                        COUNT(*) FILTER (WHERE status = 'in_progress')                   AS task_in_progress,
                        COUNT(*) FILTER (WHERE status = 'done')                          AS task_done,
                        COUNT(*) FILTER (WHERE status = 'skipped')                       AS task_skipped,
                        COUNT(*) FILTER (WHERE status IN ('todo','in_progress')
                                         AND optional = FALSE)                           AS task_blocking_pending,
                        MIN(due_date)                                                     AS next_due_date
                    FROM intervention_task
                    WHERE intervention_id = i.id
                ) task_agg ON TRUE
                LEFT JOIN LATERAL (
                    SELECT
                        COUNT(DISTINCT prd.id)                                                                  AS pr_total,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'RECEIVED')                  AS pr_received,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'TO_QUALIFY')                AS pr_to_qualify,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'NO_SUPPLIER_REF')           AS pr_no_supplier_ref,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'PENDING_DISPATCH')          AS pr_pending_dispatch,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'REJECTED')                  AS pr_rejected,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'CONSULTATION')              AS pr_consultation,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'PARTIAL')                   AS pr_partial,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'ORDERED')                   AS pr_ordered,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'QUOTED')                    AS pr_quoted,
                        COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'OPEN')                      AS pr_open
                    FROM intervention_action_purchase_request iapr2
                    INNER JOIN intervention_action ia2 ON ia2.id = iapr2.intervention_action_id
                    INNER JOIN purchase_request_derived_status prd ON prd.id = iapr2.purchase_request_id
                    WHERE ia2.intervention_id = i.id
                ) pr_agg ON TRUE
                {_TASKS_JSON_LATERAL if include_tasks else ''}
                {" ".join(joins)}
                {where_sql}
                GROUP BY i.id, ir.id, ir.code, ir.demandeur_nom, ir.demandeur_service_legacy, ir.description, ir.statut, rs2.label, rs2.color, ir.intervention_id, ir.created_at, ir.updated_at, m.id, pm.id, pm.code, pm.name, ec.id, task_agg.task_total, task_agg.task_todo, task_agg.task_in_progress, task_agg.task_done, task_agg.task_skipped, task_agg.task_blocking_pending, task_agg.next_due_date, pr_agg.pr_total, pr_agg.pr_received, pr_agg.pr_to_qualify, pr_agg.pr_no_supplier_ref, pr_agg.pr_pending_dispatch, pr_agg.pr_rejected, pr_agg.pr_consultation, pr_agg.pr_partial, pr_agg.pr_ordered, pr_agg.pr_quoted, pr_agg.pr_open
                {',' + 'it_agg.tasks_json::text' if include_tasks else ''}
                {order_sql}
                LIMIT %s OFFSET %s
            """
            cur.execute(query, (*params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            raw_rows = [dict(zip(cols, row)) for row in rows]

            # Import lazy pour rester aligné sur la logique health centralisée des équipements.
            from api.equipements.repo import EquipementRepository
            equipement_repo = EquipementRepository()
            equipement_ids = [str(r['machine_id'])
                              for r in raw_rows if r.get('machine_id') is not None]
            health_map = equipement_repo.get_health_map(cur, equipement_ids)

            result = []
            for row_dict in raw_rows:
                # Construire l'objet equipement depuis les colonnes préfixées
                if row_dict.get('machine_id') is not None:
                    machine_id = str(row_dict.get('machine_id'))
                    health = health_map.get(machine_id, {
                        'level': 'ok',
                        'reason': 'Aucune intervention ouverte',
                        'open_interventions_count': 0,
                        'urgent_count': 0,
                        'open_requests_count': 0,
                        'new_requests_count': 0,
                        'request_status_counts': {},
                        'open_tasks_count': 0,
                        'overdue_tasks_count': 0,
                        'unassigned_tasks_count': 0,
                        'open_purchase_requests_count': 0,
                        'purchase_request_status_counts': {},
                        'has_affectation': False,
                        'rules_triggered': []
                    })

                    ec_id = row_dict.pop('ec_id', None)
                    ec_code = row_dict.pop('ec_code', None)
                    ec_label = row_dict.pop('ec_label', None)

                    p_id = row_dict.pop('m_parent_id', None)
                    p_code = row_dict.pop('m_parent_code', None)
                    p_name = row_dict.pop('m_parent_name', None)

                    row_dict['equipements'] = {
                        'id': row_dict.pop('machine_id'),
                        'code': row_dict.pop('m_code', None),
                        'name': row_dict.pop('m_name', None),
                        'health': health,
                        'parent': {'id': p_id, 'code': p_code, 'name': p_name} if p_id else None,
                        'equipement_class': {'id': ec_id, 'code': ec_code, 'label': ec_label} if ec_id else None
                    }
                else:
                    row_dict['equipements'] = None
                    for key in list(row_dict.keys()):
                        if key.startswith('m_') or key.startswith('ec_'):
                            row_dict.pop(key)

                # Créer l'objet stats si demandé
                if include_stats:
                    pr_total = int(row_dict.pop('pr_total', 0) or 0)
                    pr_received = int(row_dict.pop('pr_received', 0) or 0)
                    row_dict['stats'] = {
                        'action_count': row_dict.pop('action_count', 0),
                        'total_time': row_dict.pop('total_time', 0),
                        'avg_complexity': row_dict.pop('avg_complexity', None),
                        'purchase_count': pr_total,
                        'tasks': {
                            'total': int(row_dict.pop('task_total', 0) or 0),
                            'todo': int(row_dict.pop('task_todo', 0) or 0),
                            'in_progress': int(row_dict.pop('task_in_progress', 0) or 0),
                            'done': int(row_dict.pop('task_done', 0) or 0),
                            'skipped': int(row_dict.pop('task_skipped', 0) or 0),
                            'blocking_pending': int(row_dict.pop('task_blocking_pending', 0) or 0),
                        },
                        'purchase_requests': {
                            'total': pr_total,
                            'received': pr_received,
                            'to_qualify': int(row_dict.pop('pr_to_qualify', 0) or 0),
                            'no_supplier_ref': int(row_dict.pop('pr_no_supplier_ref', 0) or 0),
                            'pending_dispatch': int(row_dict.pop('pr_pending_dispatch', 0) or 0),
                            'rejected': int(row_dict.pop('pr_rejected', 0) or 0),
                            'consultation': int(row_dict.pop('pr_consultation', 0) or 0),
                            'partial': int(row_dict.pop('pr_partial', 0) or 0),
                            'ordered': int(row_dict.pop('pr_ordered', 0) or 0),
                            'quoted': int(row_dict.pop('pr_quoted', 0) or 0),
                            'open': int(row_dict.pop('pr_open', 0) or 0),
                        },
                    }
                else:
                    # Nettoyer les colonnes stats si non demandées
                    for _k in ('action_count', 'total_time', 'avg_complexity',
                               'task_total', 'task_todo', 'task_in_progress', 'task_done',
                               'task_skipped', 'task_blocking_pending',
                               'pr_total', 'pr_received', 'pr_to_qualify', 'pr_no_supplier_ref',
                               'pr_pending_dispatch', 'pr_rejected', 'pr_consultation',
                               'pr_partial', 'pr_ordered', 'pr_quoted', 'pr_open'):
                        row_dict.pop(_k, None)

                # Champs de planification — toujours présents quelle que soit include_stats
                next_due_date = row_dict.pop('next_due_date', None)
                row_dict['next_due_date'] = next_due_date
                row_dict['overdue'] = (
                    next_due_date is not None and next_due_date < date.today()
                )

                # Construire l'objet request depuis les colonnes préfixées req_
                req_id = row_dict.pop('req_id', None)
                if req_id is not None:
                    row_dict['request'] = {
                        'id': req_id,
                        'code': row_dict.pop('req_code', None),
                        'demandeur_nom': row_dict.pop('demandeur_nom', None),
                        'demandeur_service': row_dict.pop('demandeur_service', None),
                        'description': row_dict.pop('req_description', None),
                        'statut': row_dict.pop('req_statut', None),
                        'statut_label': row_dict.pop('req_statut_label', None),
                        'statut_color': row_dict.pop('req_statut_color', None),
                        'intervention_id': row_dict.pop('req_intervention_id', None),
                        'created_at': row_dict.pop('req_created_at', None),
                        'updated_at': row_dict.pop('req_updated_at', None),
                        'equipement': None,
                    }
                else:
                    row_dict['request'] = None
                    for key in ['req_code', 'demandeur_nom', 'demandeur_service', 'req_description',
                                'req_statut', 'req_statut_label', 'req_statut_color',
                                'req_intervention_id', 'req_created_at', 'req_updated_at']:
                        row_dict.pop(key, None)

                row_dict['actions'] = []  # Vide pour get_all
                row_dict['status_logs'] = []  # Vide pour get_all

                # Tâches détaillées — uniquement si include_tasks=True
                if include_tasks:
                    raw_tasks = row_dict.pop('tasks_json', None)
                    if isinstance(raw_tasks, str):
                        import json as _json
                        raw_tasks = _json.loads(raw_tasks)
                    row_dict['tasks'] = raw_tasks or []
                else:
                    row_dict.pop('tasks_json', None)

                result.append(row_dict)

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def count_all(
        self,
        search: str | None = None,
        equipement_id: str | None = None,
        statuses: List[str] | None = None,
        priorities: List[str] | None = None,
        printed: bool | None = None,
        tech_id: str | None = None,
    ) -> int:
        """Compte le nombre total d'interventions correspondant aux filtres de get_all()"""
        priorities_norm = None
        if priorities:
            allowed_ids = {p['id'] for p in PRIORITY_TYPES}
            priorities_norm = [p for p in priorities if p in allowed_ids]

        where_clauses = []
        params: List[Any] = []

        if search:
            like = f"%{search}%"
            where_clauses.append(
                "(i.code ILIKE %s OR i.title ILIKE %s OR m.code ILIKE %s OR m.name ILIKE %s)")
            params.extend([like, like, like, like])

        if equipement_id:
            where_clauses.append("i.machine_id = %s")
            params.append(equipement_id)

        if statuses and len(statuses) > 0:
            placeholders = ",".join(["%s"] * len(statuses))
            where_clauses.append(f"LOWER(i.status_actual) IN ({placeholders})")
            params.extend([s.lower() for s in statuses])

        if priorities_norm and len(priorities_norm) > 0:
            placeholders = ",".join(["%s"] * len(priorities_norm))
            where_clauses.append(f"i.priority IN ({placeholders})")
            params.extend(priorities_norm)

        if printed is not None:
            where_clauses.append("i.printed_fiche = %s")
            params.append(printed)

        if tech_id:
            where_clauses.append("i.tech_id = %s")
            params.append(tech_id)

        where_sql = ("WHERE " + " AND ".join(where_clauses)
                     ) if where_clauses else ""

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            query = f"""
                SELECT COUNT(DISTINCT i.id)
                FROM intervention i
                LEFT JOIN machine m ON i.machine_id = m.id
                {where_sql}
            """
            cur.execute(query, params)
            row = cur.fetchone()
            return int(row[0]) if row else 0
        except Exception as e:
            raise_db_error(e, "comptage interventions")
        finally:
            release_connection(conn)

    def get_by_id(self, intervention_id: str, include_actions: bool = True) -> Dict[str, Any]:
        """Récupère une intervention par ID avec équipement et stats calculées depuis les actions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    i.*,
                    ir.id           AS req_id,
                    ir.code         AS req_code,
                    ir.demandeur_nom,
                    ir.demandeur_service_legacy AS demandeur_service,
                    ir.description  AS req_description,
                    ir.statut       AS req_statut,
                    rs2.label       AS req_statut_label,
                    rs2.color       AS req_statut_color,
                    ir.intervention_id AS req_intervention_id,
                    ir.created_at   AS req_created_at,
                    ir.updated_at   AS req_updated_at
                FROM intervention i
                LEFT JOIN intervention_request ir ON ir.intervention_id = i.id
                LEFT JOIN request_status_ref rs2 ON rs2.code = ir.statut
                WHERE i.id = %s
                """,
                (intervention_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(
                    f"Intervention {intervention_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            intervention = dict(zip(cols, row))

            # Construire l'objet request
            req_id = intervention.pop('req_id', None)
            if req_id is not None:
                intervention['request'] = {
                    'id': req_id,
                    'code': intervention.pop('req_code', None),
                    'demandeur_nom': intervention.pop('demandeur_nom', None),
                    'demandeur_service': intervention.pop('demandeur_service', None),
                    'description': intervention.pop('req_description', None),
                    'statut': intervention.pop('req_statut', None),
                    'statut_label': intervention.pop('req_statut_label', None),
                    'statut_color': intervention.pop('req_statut_color', None),
                    'intervention_id': intervention.pop('req_intervention_id', None),
                    'created_at': intervention.pop('req_created_at', None),
                    'updated_at': intervention.pop('req_updated_at', None),
                    'equipement': None,
                }
            else:
                intervention['request'] = None
                for key in ['req_code', 'demandeur_nom', 'demandeur_service', 'req_description',
                            'req_statut', 'req_statut_label', 'req_statut_color',
                            'req_intervention_id', 'req_created_at', 'req_updated_at']:
                    intervention.pop(key, None)

            # Récupérer l'équipement via EquipementRepository pour garantir la cohérence
            if intervention.get('machine_id'):
                from api.equipements.repo import EquipementRepository
                equipement_repo = EquipementRepository()
                try:
                    intervention['equipements'] = equipement_repo.get_by_id(
                        intervention['machine_id'])
                except NotFoundError:
                    intervention['equipements'] = None
            else:
                intervention['equipements'] = None

            # Récupérer les actions via InterventionActionRepository
            # Stats tâches et demandes d'achat — toujours calculées en SQL
            cur.execute(
                """
                SELECT
                    COUNT(*)                                                          AS task_total,
                    COUNT(*) FILTER (WHERE status = 'todo')                          AS task_todo,
                    COUNT(*) FILTER (WHERE status = 'in_progress')                   AS task_in_progress,
                    COUNT(*) FILTER (WHERE status = 'done')                          AS task_done,
                    COUNT(*) FILTER (WHERE status = 'skipped')                       AS task_skipped,
                    COUNT(*) FILTER (WHERE status IN ('todo','in_progress')
                                     AND optional = FALSE)                           AS task_blocking_pending
                FROM intervention_task WHERE intervention_id = %s
                """,
                (intervention_id,),
            )
            tr = cur.fetchone()
            task_stats = {
                'total': int(tr[0] or 0),
                'todo': int(tr[1] or 0),
                'in_progress': int(tr[2] or 0),
                'done': int(tr[3] or 0),
                'skipped': int(tr[4] or 0),
                'blocking_pending': int(tr[5] or 0),
            }

            cur.execute(
                """
                SELECT
                    COUNT(DISTINCT prd.id)                                                                 AS pr_total,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'RECEIVED')                 AS pr_received,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'TO_QUALIFY')               AS pr_to_qualify,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'NO_SUPPLIER_REF')          AS pr_no_supplier_ref,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'PENDING_DISPATCH')         AS pr_pending_dispatch,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'REJECTED')                 AS pr_rejected,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'CONSULTATION')             AS pr_consultation,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'PARTIAL')                  AS pr_partial,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'ORDERED')                  AS pr_ordered,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'QUOTED')                   AS pr_quoted,
                    COUNT(DISTINCT prd.id) FILTER (WHERE prd.derived_status = 'OPEN')                     AS pr_open
                FROM intervention_action_purchase_request iapr
                INNER JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                INNER JOIN purchase_request_derived_status prd ON prd.id = iapr.purchase_request_id
                WHERE ia.intervention_id = %s
                """,
                (intervention_id,),
            )
            pr_row = cur.fetchone()
            pr_total = int(pr_row[0] or 0)
            pr_stats = {
                'total': pr_total,
                'received': int(pr_row[1] or 0),
                'to_qualify': int(pr_row[2] or 0),
                'no_supplier_ref': int(pr_row[3] or 0),
                'pending_dispatch': int(pr_row[4] or 0),
                'rejected': int(pr_row[5] or 0),
                'consultation': int(pr_row[6] or 0),
                'partial': int(pr_row[7] or 0),
                'ordered': int(pr_row[8] or 0),
                'quoted': int(pr_row[9] or 0),
                'open': int(pr_row[10] or 0),
            }

            if include_actions:
                action_repo = InterventionActionRepository()
                actions = action_repo.get_by_intervention(intervention_id)
                intervention['actions'] = actions

                intervention['stats'] = {
                    'action_count': len(actions),
                    'total_time': sum(a.get('time_spent', 0) or 0 for a in actions),
                    'avg_complexity': (
                        round(sum(a.get('complexity_score', 0) or 0 for a in actions if a.get('complexity_score')) /
                              len([a for a in actions if a.get('complexity_score')]), 2)
                        if any(a.get('complexity_score') for a in actions) else None
                    ),
                    'purchase_count': pr_stats['total'],
                    'tasks': task_stats,
                    'purchase_requests': pr_stats,
                }
            else:
                intervention['actions'] = []
                intervention['stats'] = {
                    'action_count': 0,
                    'total_time': 0,
                    'avg_complexity': None,
                    'purchase_count': pr_stats['total'],
                    'tasks': task_stats,
                    'purchase_requests': pr_stats,
                }

            # Récupérer les status logs via InterventionStatusLogRepository
            status_log_repo = InterventionStatusLogRepository()
            intervention['status_logs'] = status_log_repo.get_by_intervention(
                intervention_id)

            # Charger les tâches liées à l'intervention (plan préventif ou tâches ad hoc)
            # On ne conditionne PAS sur plan_id : une intervention créée manuellement via
            # acceptation DI peut avoir des intervention_task sans que plan_id soit renseigné.
            # Import lazy pour éviter la circularité avec intervention_tasks.repo
            from api.intervention_tasks.repo import InterventionTaskRepository
            task_repo = InterventionTaskRepository()
            tasks = task_repo.get_by_intervention(intervention_id)
            intervention['tasks'] = tasks
            if tasks:
                intervention['task_progress'] = task_repo.get_progress(
                    intervention_id)
            else:
                intervention['task_progress'] = None

            return intervention
        except NotFoundError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg:
                raise DatabaseError(
                    "Table 'intervention' inexistante - vérifier la structure de la base") from e
            if "connection" in error_msg.lower():
                raise DatabaseError(
                    "Impossible de se connecter à la base de données") from e
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def _resolve_tech_initials(self, cur: Any, data: Dict[str, Any]) -> None:
        """Résout tech_initials depuis tunnel_user.initial si tech_id est fourni."""
        tech_id = data.get('tech_id')
        if not tech_id:
            return
        cur.execute(
            "SELECT initial FROM tunnel_user WHERE id = %s",
            (str(tech_id),),
        )
        row = cur.fetchone()
        if not row:
            raise ValidationError(f"Utilisateur {tech_id} introuvable")
        data['tech_initials'] = row[0]

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle intervention"""
        request_id = str(data['request_id']) if data.get(
            'request_id') else None

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            intervention_id = str(uuid4())

            # Résoudre tech_initials depuis l'UUID avant validation (le trigger en a besoin)
            self._resolve_tech_initials(cur, data)

            from api.interventions.validators import InterventionValidator
            InterventionValidator.validate_create(data)

            # Résoudre plan_id depuis l'occurrence préventive liée à la DI si non fourni
            # (cas acceptation manuelle d'une DI système préventive via POST /interventions)
            plan_id = data.get('plan_id')
            if plan_id is None and request_id:
                cur.execute(
                    "SELECT plan_id FROM preventive_occurrence WHERE di_id = %s LIMIT 1",
                    (request_id,),
                )
                occ_row = cur.fetchone()
                plan_id = str(occ_row[0]) if occ_row and occ_row[0] else None

            cur.execute(
                """
                INSERT INTO intervention
                (id, title, machine_id, type_inter, priority,
                 reported_by, tech_initials, tech_id, status_actual,
                 printed_fiche, reported_date, plan_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    intervention_id,
                    data.get('title'),
                    data.get('machine_id'),
                    data.get('type_inter'),
                    data.get('priority'),
                    data.get('reported_by'),
                    data.get('tech_initials'),
                    str(data['tech_id']) if data.get('tech_id') else None,
                    data.get('status_actual', 'ouvert'),
                    data.get('printed_fiche', False),
                    data.get('reported_date'),
                    plan_id,
                )
            )

            if request_id:
                self._link_request(cur, intervention_id, request_id)

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de l'intervention: {str(e)}") from e
        finally:
            release_connection(conn)

        return self.get_by_id(intervention_id)

    def _link_request(self, cur: Any, intervention_id: str, request_id: str) -> None:
        """
        Lie une demande d'intervention à l'intervention créée :
        - Vérifie que la demande existe et est dans un état linkable
        - Met à jour intervention_request.intervention_id
        - Insère le log de transition vers 'acceptee'
        """
        cur.execute(
            "SELECT id, statut, intervention_id FROM intervention_request WHERE id = %s",
            (request_id,),
        )
        row = cur.fetchone()
        if not row:
            raise DatabaseError(
                f"Demande d'intervention {request_id} introuvable")

        current_statut = row[1]
        existing_intervention_id = row[2]

        if existing_intervention_id is not None:
            raise DatabaseError(
                f"La demande '{request_id}' est déjà liée à l'intervention '{existing_intervention_id}'. "
                f"Une demande ne peut être liée qu'à une seule intervention."
            )

        linkable = ("nouvelle", "en_attente")
        if current_statut not in linkable:
            raise DatabaseError(
                f"La demande '{request_id}' est au statut '{current_statut}' "
                f"et ne peut pas être liée (statuts acceptés : {linkable})"
            )

        # Vérifier que l'intervention n'est pas déjà liée à une autre demande
        cur.execute(
            "SELECT id FROM intervention_request WHERE intervention_id = %s AND id != %s LIMIT 1",
            (intervention_id, request_id),
        )
        if cur.fetchone():
            raise DatabaseError(
                f"L'intervention '{intervention_id}' est déjà liée à une autre demande d'intervention."
            )

        cur.execute(
            "UPDATE intervention_request SET intervention_id = %s WHERE id = %s",
            (intervention_id, request_id),
        )
        cur.execute("SET LOCAL app.skip_request_status_log = 'true'")
        cur.execute(
            """
            INSERT INTO request_status_log (request_id, status_from, status_to, changed_by, notes)
            VALUES (%s, %s, 'acceptee', NULL, %s)
            """,
            (request_id, current_statut, "Intervention créée manuellement"),
        )

        # Vérifier si la DI appartient à une occurrence préventive non encore liée
        cur.execute(
            "SELECT id, plan_id FROM preventive_occurrence WHERE di_id = %s AND intervention_id IS NULL",
            (request_id,),
        )
        occ_row = cur.fetchone()
        if occ_row:
            occ_id = str(occ_row[0])
            occ_plan_id = occ_row[1]

            cur.execute(
                "UPDATE preventive_occurrence SET intervention_id = %s, status = 'in_progress' WHERE id = %s",
                (intervention_id, occ_id),
            )
            cur.execute(
                """
                UPDATE intervention_task
                SET intervention_id = %s,
                    assigned_to = COALESCE(assigned_to,
                        (SELECT tech_id FROM intervention WHERE id = %s)),
                    due_date = COALESCE(due_date,
                        (SELECT reported_date FROM intervention WHERE id = %s))
                WHERE occurrence_id = %s AND intervention_id IS NULL
                """,
                (intervention_id, intervention_id, intervention_id, occ_id),
            )
            if occ_plan_id:
                cur.execute(
                    "UPDATE intervention SET plan_id = %s WHERE id = %s",
                    (str(occ_plan_id), intervention_id),
                )

    def update(self, intervention_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une intervention existante"""
        existing = self.get_by_id(intervention_id, include_actions=False)

        # Bloquer la fermeture si des tâches non-optionnelles sont en attente
        if 'status_actual' in data:
            self._check_closable(intervention_id, data['status_actual'])

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            updatable_fields = [
                'title', 'machine_id', 'type_inter', 'priority',
                'reported_by', 'tech_initials', 'tech_id', 'status_actual',
                'printed_fiche', 'reported_date'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field])

            if not set_clauses:
                return self.get_by_id(intervention_id)

            params.append(intervention_id)

            query = f"""
                UPDATE intervention
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """

            cur.execute(query, params)
            conn.commit()
        except (ValidationError, DatabaseError):
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            release_connection(conn)

        result = self.get_by_id(intervention_id)

        # Si le statut vient de changer vers 'ferme', clôturer la demande liée
        if 'status_actual' in data:
            new_status = result.get('status_actual')
            old_status = existing.get('status_actual')
            if new_status != old_status:
                # Résoudre le code du nouveau statut
                self._notify_if_closed(intervention_id, new_status)

        return result

    def _check_closable(self, intervention_id: str, status_actual: Any) -> None:
        """Lève ValidationError si des tâches non-optionnelles bloquent la fermeture."""
        if not status_actual:
            return
        # intervention.status_actual stocke directement le code texte (ex: 'ferme')
        if str(status_actual) != CLOSED_STATUS_CODE:
            return

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM intervention_task
                    WHERE intervention_id = %s
                      AND status IN ('todo', 'in_progress')
                      AND optional = FALSE
                    """,
                    (intervention_id,),
                )
                blocking = cur.fetchone()[0]
        finally:
            release_connection(conn)

        if blocking > 0:
            raise ValidationError(
                f"Impossible de fermer : {blocking} tâche(s) non-optionnelle(s) en attente."
            )

    def _notify_if_closed(self, intervention_id: str, status_actual: Any) -> None:
        """Notifie le repo des demandes si l'intervention vient d'être fermée.

        intervention.status_actual stocke directement le code texte (ex: 'ferme'),
        identique à intervention_status_ref.id — pas besoin de résolution via DB.
        """
        if not status_actual:
            return
        try:
            if str(status_actual) == CLOSED_STATUS_CODE:
                from api.intervention_requests.repo import InterventionRequestRepository
                InterventionRequestRepository().on_intervention_closed(intervention_id)
        except Exception:
            logger.error(
                "Erreur cascade fermeture pour intervention %s",
                intervention_id,
                exc_info=True,
            )

    def force_close_request(self, intervention_id: str) -> Dict[str, Any]:
        """Force la clôture de la demande liée à une intervention fermée.

        À utiliser quand la cascade automatique a échoué : l'intervention est
        déjà au statut 'ferme' mais la demande est restée bloquée en 'acceptee'.
        Lève ValidationError si l'intervention n'est pas fermée ou si aucune
        demande 'acceptee' n'est liée.
        """
        existing = self.get_by_id(intervention_id, include_actions=False)
        if existing.get("status_actual") != CLOSED_STATUS_CODE:
            raise ValidationError(
                "Le forçage de clôture n'est possible que si l'intervention est déjà fermée."
            )

        from api.intervention_requests.repo import InterventionRequestRepository
        req_repo = InterventionRequestRepository()

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, statut FROM intervention_request
                    WHERE intervention_id = %s AND statut = 'acceptee'
                    LIMIT 1
                    """,
                    (intervention_id,),
                )
                row = cur.fetchone()

            if not row:
                raise ValidationError(
                    "Aucune demande en statut 'acceptee' n'est liée à cette intervention."
                )
        finally:
            release_connection(conn)

        req_repo.on_intervention_closed(intervention_id)
        return self.get_by_id(intervention_id)

    def delete(self, intervention_id: str) -> bool:
        """Supprime une intervention (interdit si actions ou demandes d'achat liées)"""
        from api.interventions.validators import InterventionValidator
        self.get_by_id(intervention_id, include_actions=False)
        InterventionValidator.validate_deletable(intervention_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM intervention WHERE id = %s",
                (intervention_id,)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            release_connection(conn)
