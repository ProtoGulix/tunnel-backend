"""Repository pour /tasks/workspace — endpoint unifié pour page Tasks."""
import logging
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import math

from api.db import get_connection, release_connection
from api.errors.exceptions import raise_db_error
from api.tasks.schemas import (
    TaskDetail, TasksCounter, TasksOptions, TasksPagination,
    TasksMetadata, TasksWorkspaceResponse, UserRef, InterventionRef,
    EquipementRef, ActionRef, InterventionGroup
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
        skip: int = 0,
        limit: int = 50,
        include_closed: bool = False,
        include_actions: bool = False,
        include_options: bool = False,
        include_counters: bool = False,
    ) -> TasksWorkspaceResponse:
        """Récupère les tâches groupées par intervention avec pagination offset sur les interventions."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Filtres appliqués au niveau des tâches
            task_where: List[str] = []
            params: List[Any] = []

            if not include_closed:
                task_where.append("it.status NOT IN ('done', 'skipped')")

            if status:
                ph = ",".join(["%s"] * len(status))
                task_where.append(f"it.status IN ({ph})")
                params.extend(status)

            if origin:
                ph = ",".join(["%s"] * len(origin))
                task_where.append(f"it.origin IN ({ph})")
                params.extend(origin)

            if assignee_id == "unassigned":
                task_where.append("it.assigned_to IS NULL")
            elif assignee_id:
                task_where.append("it.assigned_to = %s")
                params.append(assignee_id)

            if q and q.strip():
                like = f"%{q}%"
                task_where.append(
                    "(it.label ILIKE %s OR i.title ILIKE %s OR i.code ILIKE %s)")
                params.extend([like, like, like])

            task_where_sql = ("WHERE " + " AND ".join(task_where)) if task_where else ""

            # Compter les interventions distinctes matchées (pour la pagination)
            count_query = f"""
                SELECT COUNT(DISTINCT it.intervention_id)
                FROM intervention_task it
                LEFT JOIN intervention i ON it.intervention_id = i.id
                {task_where_sql}
            """
            cur.execute(count_query, params)
            total_interventions = cur.fetchone()[0] or 0

            # Récupérer les interventions de la page demandée
            interv_query = f"""
                SELECT DISTINCT
                    i.id        AS interv_id,
                    i.code      AS interv_code,
                    i.title     AS interv_title,
                    i.status_actual AS interv_status,
                    m.id        AS equip_id,
                    m.name      AS equip_name,
                    m.code      AS equip_code
                FROM intervention_task it
                LEFT JOIN intervention i ON it.intervention_id = i.id
                LEFT JOIN machine m ON i.machine_id = m.id
                {task_where_sql}
                ORDER BY i.id
                LIMIT %s OFFSET %s
            """
            cur.execute(interv_query, (*params, limit, skip))
            interv_rows = cur.fetchall()
            interv_cols = [d[0] for d in cur.description]
            interventions_page = [dict(zip(interv_cols, r)) for r in interv_rows]

            if not interventions_page:
                return self._empty_response(skip, limit, total_interventions)

            interv_ids = [str(r['interv_id']) for r in interventions_page]

            # Charger toutes les tâches pour ces interventions (en appliquant les mêmes filtres)
            task_extra_where = list(task_where) + [
                f"it.intervention_id IN ({','.join(['%s'] * len(interv_ids))})"
            ]
            task_full_where_sql = "WHERE " + " AND ".join(task_extra_where)
            task_params = [*params, *interv_ids]

            task_query = f"""
                SELECT
                    it.id, it.label, it.status, it.origin, it.optional,
                    it.due_date, it.skip_reason, it.created_at,
                    it.intervention_id,
                    COALESCE(agg.time_spent, 0.0) AS time_spent_total,
                    u_created.id         AS created_by_id,
                    u_created.initial    AS created_by_initial,
                    u_created.first_name AS created_by_first_name,
                    u_created.last_name  AS created_by_last_name,
                    u_assigned.id        AS assigned_id,
                    u_assigned.initial   AS assigned_initial,
                    u_assigned.first_name AS assigned_first_name,
                    u_assigned.last_name  AS assigned_last_name
                FROM intervention_task it
                LEFT JOIN intervention i ON it.intervention_id = i.id
                LEFT JOIN tunnel_user u_created ON it.created_by = u_created.id
                LEFT JOIN tunnel_user u_assigned ON it.assigned_to = u_assigned.id
                LEFT JOIN LATERAL (
                    SELECT COALESCE(SUM(ia.time_spent), 0.0) AS time_spent
                    FROM intervention_action_task iat
                    INNER JOIN intervention_action ia ON ia.id = iat.action_id
                    WHERE iat.task_id = it.id
                ) agg ON TRUE
                {task_full_where_sql}
                ORDER BY it.created_at DESC, it.id DESC
            """
            cur.execute(task_query, task_params)
            task_rows = cur.fetchall()
            task_cols = [d[0] for d in cur.description]

            # Grouper les tâches par intervention_id
            tasks_by_interv: Dict[str, List[TaskDetail]] = {iid: [] for iid in interv_ids}
            all_tasks: Dict[str, TaskDetail] = {}
            for row in task_rows:
                d = dict(zip(task_cols, row))
                task = self._map_task_detail(d)
                iid = str(d['intervention_id'])
                if iid in tasks_by_interv:
                    tasks_by_interv[iid].append(task)
                all_tasks[str(task.id)] = task

            # Charger les actions si demandé
            if include_actions and all_tasks:
                self._load_actions_for_tasks(cur, list(all_tasks.keys()), all_tasks)

            # Assembler les groupes d'interventions
            items: List[InterventionGroup] = []
            for r in interventions_page:
                iid = str(r['interv_id'])
                equipement = None
                if r.get('equip_id'):
                    equipement = EquipementRef(
                        id=r['equip_id'],
                        name=r.get('equip_name'),
                        code=r.get('equip_code'),
                    )
                items.append(InterventionGroup(
                    id=r['interv_id'],
                    code=r.get('interv_code'),
                    title=r.get('interv_title'),
                    status=r.get('interv_status'),
                    equipement=equipement,
                    tasks=tasks_by_interv.get(iid, []),
                ))

            # Options et compteurs (optionnels)
            options = self._load_options(cur) if include_options else None
            counters = self._calculate_counters(cur) if include_counters else None

            total_pages = math.ceil(total_interventions / limit) if limit else 1
            page = (skip // limit) + 1 if limit else 1
            pagination = TasksPagination(
                total=total_interventions,
                page=page,
                page_size=limit,
                total_pages=total_pages,
                offset=skip,
                count=len(items),
            )
            meta = TasksMetadata(
                generated_at=datetime.now(),
                etag=self._compute_etag(items),
            )

            conn.commit()
            return TasksWorkspaceResponse(
                items=items,
                pagination=pagination,
                counters=counters,
                options=options,
                meta=meta,
                errors=None,
            )

        except Exception as e:
            raise_db_error(e, "chargement workspace tâches")
        finally:
            release_connection(conn)

    def _empty_response(self, skip: int, limit: int, total: int) -> TasksWorkspaceResponse:
        return TasksWorkspaceResponse(
            items=[],
            pagination=TasksPagination(
                total=total, page=(skip // limit) + 1 if limit else 1,
                page_size=limit, total_pages=0, offset=skip, count=0,
            ),
            meta=TasksMetadata(generated_at=datetime.now(), etag=None),
        )

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
            actions=[],
        )

    def _load_actions_for_tasks(self, cur, task_ids: List[str], tasks_dict: Dict[str, TaskDetail]):
        """Charge les actions liées aux tâches (si include_actions=true)."""
        if not task_ids:
            return

        ph = ",".join(["%s"] * len(task_ids))
        cur.execute(f"""
            SELECT
                ia.id, ia.created_at, ia.description, ia.time_spent,
                u.id AS tech_id, u.initial AS tech_initial,
                u.first_name AS tech_first_name, u.last_name AS tech_last_name,
                iat.task_id
            FROM intervention_action_task iat
            INNER JOIN intervention_action ia ON ia.id = iat.action_id
            LEFT JOIN tunnel_user u ON ia.tech = u.id
            WHERE iat.task_id IN ({ph})
            ORDER BY ia.created_at DESC
        """, task_ids)

        actions_by_task: Dict[str, List[ActionRef]] = {}
        for row in cur.fetchall():
            task_id = str(row[8])
            tech = None
            if row[4]:
                tech = UserRef(id=row[4], initials=row[5], first_name=row[6], last_name=row[7])
            action = ActionRef(
                id=row[0], created_at=row[1], description=row[2],
                time_spent=float(row[3]) if row[3] is not None else None,
                tech=tech,
            )
            actions_by_task.setdefault(task_id, []).append(action)

        for task_id, actions in actions_by_task.items():
            if task_id in tasks_dict:
                tasks_dict[task_id].actions = actions

    def _load_options(self, cur) -> TasksOptions:
        """Charge les options pour les dropdowns (users, interventions)."""
        cur.execute("""
            SELECT DISTINCT u.id, u.initial, u.first_name, u.last_name
            FROM tunnel_user u
            WHERE u.is_active = true
            ORDER BY u.first_name, u.last_name
            LIMIT 100
        """)
        users = [UserRef(id=r[0], initials=r[1], first_name=r[2], last_name=r[3])
                 for r in cur.fetchall()]

        cur.execute("""
            SELECT DISTINCT i.id, i.code, i.title, i.status_actual
            FROM intervention i
            WHERE i.status_actual != (
                SELECT id FROM intervention_status_ref WHERE code = 'ferme' LIMIT 1
            )
            ORDER BY i.id
            LIMIT 100
        """)
        interventions = [InterventionRef(id=r[0], code=r[1], title=r[2], status=r[3])
                         for r in cur.fetchall()]

        return TasksOptions(users=users, interventions=interventions)

    def _calculate_counters(self, cur) -> TasksCounter:
        """Calcule les compteurs globaux (toutes tâches, sans filtre de page)."""
        cur.execute("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE status = 'todo') AS todo,
                COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress,
                COUNT(*) FILTER (WHERE status = 'done') AS done,
                COUNT(*) FILTER (WHERE status = 'skipped') AS skipped,
                COUNT(*) FILTER (WHERE status = 'todo' AND assigned_to IS NULL) AS backlog_unassigned
            FROM intervention_task
        """)
        row = cur.fetchone()
        return TasksCounter(
            total=row[0] or 0, todo=row[1] or 0, in_progress=row[2] or 0,
            done=row[3] or 0, skipped=row[4] or 0, backlog_unassigned_todo=row[5] or 0,
        )

    def _compute_etag(self, items: List[InterventionGroup]) -> str:
        """Génère un etag basé sur les IDs d'interventions et de tâches retournées."""
        payload = "".join(
            str(g.id) + "".join(str(t.id) for t in g.tasks)
            for g in items
        )
        return hashlib.md5(payload.encode()).hexdigest()
