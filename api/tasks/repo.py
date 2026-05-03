"""Repository pour /tasks/workspace — endpoint unifié pour page Tasks."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import hashlib

from fastapi import HTTPException
from api.db import get_connection, release_connection
from api.errors.exceptions import raise_db_error, ValidationError, NotFoundError
from api.tasks.schemas import (
    TaskDetail, TasksCounter, TasksOptions, TasksPagination,
    TasksMetadata, TasksWorkspaceResponse, UserRef, InterventionRef,
    EquipementRef, ActionRef
)

logger = logging.getLogger(__name__)


class TasksRepository:
    """Repository pour l'endpoint /tasks/workspace."""

    def _get_connection(self):
        return get_connection()

    def get_workspace(
        self,
        q: Optional[str] = None,
        status: Optional[List[str]] = None,
        origin: Optional[List[str]] = None,
        assignee_id: Optional[str] = None,
        grouping: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
        include_closed: bool = False,
        include_actions: bool = False,
        include_options: bool = False,
        include_counters: bool = False,
    ) -> TasksWorkspaceResponse:
        """Récupère les tâches avec filtres, pagination et options."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Construire la requête principale de tâches
            where_clauses = []
            params: List[Any] = []

            # Filtres de base
            if not include_closed:
                where_clauses.append("it.status NOT IN ('done', 'skipped')")

            if status:
                ph = ",".join(["%s"] * len(status))
                where_clauses.append(f"it.status IN ({ph})")
                params.extend(status)

            if origin:
                ph = ",".join(["%s"] * len(origin))
                where_clauses.append(f"it.origin IN ({ph})")
                params.extend(origin)

            if assignee_id == "unassigned":
                where_clauses.append("it.assigned_to IS NULL")
            elif assignee_id:
                where_clauses.append("it.assigned_to = %s")
                params.append(assignee_id)

            if q and q.strip():
                like = f"%{q}%"
                where_clauses.append(
                    "(it.label ILIKE %s OR i.title ILIKE %s OR i.code ILIKE %s)")
                params.extend([like, like, like])

            # Pagination par cursor (basé sur id + order by created_at, id)
            if cursor:
                where_clauses.append(
                    "(it.created_at, it.id) > (SELECT (created_at, id) FROM intervention_task WHERE id = %s)")
                params.append(cursor)

            where_sql = ("WHERE " + " AND ".join(where_clauses)
                         ) if where_clauses else ""

            # Requête principale
            query = f"""
                SELECT
                    it.id, it.label, it.status, it.origin, it.optional,
                    it.due_date, it.skip_reason, it.created_at,
                    it.created_by, it.assigned_to,
                    i.id as interv_id, i.code as interv_code, i.title as interv_title, i.status_actual as interv_status,
                    m.id as equip_id, m.name as equip_name, m.code as equip_code,
                    COALESCE(agg.time_spent, 0.0) as time_spent_total,
                    u_created.id as created_by_id, u_created.initial as created_by_initial, u_created.first_name as created_by_first_name, u_created.last_name as created_by_last_name,
                    u_assigned.id as assigned_id, u_assigned.initial as assigned_initial, u_assigned.first_name as assigned_first_name, u_assigned.last_name as assigned_last_name
                FROM intervention_task it
                LEFT JOIN intervention i ON it.intervention_id = i.id
                LEFT JOIN machine m ON i.machine_id = m.id
                LEFT JOIN tunnel_user u_created ON it.created_by = u_created.id
                LEFT JOIN tunnel_user u_assigned ON it.assigned_to = u_assigned.id
                LEFT JOIN LATERAL (
                    SELECT COALESCE(SUM(ia.time_spent), 0.0) as time_spent
                    FROM intervention_action ia
                    WHERE ia.task_id = it.id
                ) agg ON TRUE
                {where_sql}
                ORDER BY it.created_at DESC, it.id DESC
                LIMIT %s
            """
            params.append(limit + 1)  # +1 pour détecter s'il y a plus

            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

            # Parser les tâches
            tasks_raw = [dict(zip(cols, row)) for row in rows]
            has_more = len(tasks_raw) > limit
            if has_more:
                tasks_raw = tasks_raw[:limit]

            tasks = []
            for task_raw in tasks_raw:
                task = self._map_task_detail(task_raw)
                tasks.append(task)

            # Charger actions si demandé
            if include_actions and tasks:
                task_ids = [str(t.id) for t in tasks]
                tasks_dict = {str(t.id): t for t in tasks}
                self._load_actions_for_tasks(cur, task_ids, tasks_dict)

            # Charger options si demandées
            options = None
            if include_options:
                options = self._load_options(cur)

            # Calculer compteurs si demandés
            counters = None
            if include_counters:
                counters = self._calculate_counters(cur)

            # Pagination
            next_cursor = str(tasks[-1].id) if has_more and tasks else None
            pagination = TasksPagination(
                next_cursor=next_cursor, has_more=has_more)

            # Métadonnées
            meta = TasksMetadata(
                generated_at=datetime.now(),
                etag=self._compute_etag(tasks)
            )

            conn.commit()
            return TasksWorkspaceResponse(
                tasks=tasks,
                counters=counters,
                options=options,
                pagination=pagination,
                meta=meta,
                errors=None
            )

        except Exception as e:
            raise_db_error(e, "chargement workspace tâches")
        finally:
            release_connection(conn)

    def _map_task_detail(self, row: Dict[str, Any]) -> TaskDetail:
        """Mappe une row DB vers TaskDetail."""
        created_by = None
        if row.get('created_by_id'):
            created_by = UserRef(
                id=row['created_by_id'],
                initials=row.get('created_by_initial'),
                first_name=row.get('created_by_first_name'),
                last_name=row.get('created_by_last_name'),
            )

        assigned_to = None
        if row.get('assigned_id'):
            assigned_to = UserRef(
                id=row['assigned_id'],
                initials=row.get('assigned_initial'),
                first_name=row.get('assigned_first_name'),
                last_name=row.get('assigned_last_name'),
            )

        intervention = None
        if row.get('interv_id'):
            intervention = InterventionRef(
                id=row['interv_id'],
                code=row.get('interv_code'),
                title=row.get('interv_title'),
                status=row.get('interv_status'),
            )

        equipement = None
        if row.get('equip_id'):
            equipement = EquipementRef(
                id=row['equip_id'],
                name=row.get('equip_name'),
                code=row.get('equip_code'),
            )

        return TaskDetail(
            id=row['id'],
            label=row['label'],
            status=row['status'],
            origin=row.get('origin'),
            optional=row.get('optional', False),
            due_date=row.get('due_date'),
            skip_reason=row.get('skip_reason'),
            time_spent_total=row.get('time_spent_total'),
            created_at=row.get('created_at'),
            created_by=created_by,
            assigned_to=assigned_to,
            intervention=intervention,
            equipement=equipement,
            actions=[]
        )

    def _load_actions_for_tasks(self, cur, task_ids: List[str], tasks_dict: Dict[str, TaskDetail]):
        """Charge les actions liées aux tâches (si include_actions=true)."""
        if not task_ids:
            return

        ph = ",".join(["%s"] * len(task_ids))
        cur.execute(f"""
            SELECT
                ia.id, ia.created_at, ia.description, ia.time_spent,
                u.id as tech_id, u.initial as tech_initial, u.first_name as tech_first_name, u.last_name as tech_last_name,
                it.id as task_id
            FROM intervention_action ia
            LEFT JOIN tunnel_user u ON ia.tech = u.id
            JOIN intervention_task it ON ia.task_id = it.id
            WHERE it.id IN ({ph})
            ORDER BY ia.created_at DESC
        """, task_ids)

        actions_by_task = {}
        for row in cur.fetchall():
            task_id = str(row[8])
            if task_id not in actions_by_task:
                actions_by_task[task_id] = []

            tech = None
            if row[4]:  # tech_id
                tech = UserRef(
                    id=row[4],
                    initials=row[5],
                    first_name=row[6],
                    last_name=row[7],
                )

            action = ActionRef(
                id=row[0],
                created_at=row[1],
                description=row[2],
                time_spent=row[3],
                tech=tech,
            )
            actions_by_task[task_id].append(action)

        for task_id, actions in actions_by_task.items():
            if task_id in tasks_dict:
                tasks_dict[task_id].actions = actions

    def _load_options(self, cur) -> TasksOptions:
        """Charge les options pour les dropdowns (users, interventions)."""
        # Utilisateurs assignables
        cur.execute("""
            SELECT DISTINCT u.id, u.initial, u.first_name, u.last_name
            FROM tunnel_user u
            WHERE u.is_active = true
            ORDER BY u.first_name, u.last_name
            LIMIT 100
        """)
        users = [UserRef(id=row[0], initials=row[1], first_name=row[2],
                         last_name=row[3]) for row in cur.fetchall()]

        # Interventions (pour filtrage)
        cur.execute("""
            SELECT DISTINCT i.id, i.code, i.title, i.status_actual, i.reported_date
            FROM intervention i
            WHERE i.status_actual != (SELECT id FROM intervention_status_ref WHERE code = 'ferme' LIMIT 1)
            ORDER BY i.reported_date DESC
            LIMIT 100
        """)
        interventions = [InterventionRef(
            id=row[0], code=row[1], title=row[2], status=row[3]) for row in cur.fetchall()]

        return TasksOptions(users=users, interventions=interventions)

    def _calculate_counters(self, cur) -> TasksCounter:
        """Calcule les compteurs globaux."""
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'todo') as todo,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                COUNT(*) FILTER (WHERE status = 'done') as done,
                COUNT(*) FILTER (WHERE status = 'skipped') as skipped,
                COUNT(*) FILTER (WHERE status = 'todo' AND assigned_to IS NULL) as backlog_unassigned
            FROM intervention_task
        """)
        row = cur.fetchone()
        return TasksCounter(
            total=row[0] or 0,
            todo=row[1] or 0,
            in_progress=row[2] or 0,
            done=row[3] or 0,
            skipped=row[4] or 0,
            backlog_unassigned_todo=row[5] or 0,
        )

    def _compute_etag(self, tasks: List[TaskDetail]) -> str:
        """Génère un etag basé sur les tâches pour cache client."""
        task_ids = "".join([str(t.id) for t in tasks])
        return hashlib.md5(task_ids.encode()).hexdigest()
