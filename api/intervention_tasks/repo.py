import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException

from api.db import get_connection, release_connection
from api.errors.exceptions import NotFoundError, ValidationError, raise_db_error
from api.intervention_tasks.schemas import InterventionTaskIn, InterventionTaskPatch

logger = logging.getLogger(__name__)

_TASK_SELECT = """
    SELECT
        it.id, it.intervention_id, it.label, it.origin, it.status,
        it.optional, it.due_date, it.sort_order, it.skip_reason,
        it.gamme_step_id, it.occurrence_id, it.action_id,
        it.closed_by, it.created_by, it.created_at, it.updated_at,
        COALESCE(agg.action_count, 0)  AS action_count,
        COALESCE(agg.time_spent, 0.0)  AS time_spent,
        u.id        AS assigned_id,
        u.first_name AS assigned_first_name,
        u.last_name  AS assigned_last_name,
        u.email      AS assigned_email,
        u.initial    AS assigned_initial,
        u.status     AS assigned_status,
        u.role       AS assigned_role
    FROM intervention_task it
    LEFT JOIN directus_users u ON u.id = it.assigned_to
    LEFT JOIN LATERAL (
        SELECT
            COUNT(ia.id)            AS action_count,
            COALESCE(SUM(ia.time_spent), 0) AS time_spent
        FROM intervention_action ia
        WHERE ia.id = it.action_id
    ) agg ON TRUE
"""


def _map_task(row: Dict[str, Any]) -> Dict[str, Any]:
    """Mappe les colonnes assigned_* en objet assigned_to imbriqué."""
    if row.get("assigned_id"):
        row["assigned_to"] = {
            "id": row.pop("assigned_id"),
            "first_name": row.pop("assigned_first_name", None),
            "last_name": row.pop("assigned_last_name", None),
            "email": row.pop("assigned_email", None),
            "initial": row.pop("assigned_initial", None),
            "status": row.pop("assigned_status", "active"),
            "role": row.pop("assigned_role", None),
        }
    else:
        row["assigned_to"] = None
        for k in ("assigned_id", "assigned_first_name", "assigned_last_name",
                  "assigned_email", "assigned_initial", "assigned_status", "assigned_role"):
            row.pop(k, None)
    return row


class InterventionTaskRepository:
    """Requêtes pour le domaine intervention_task"""

    def _get_connection(self):
        return get_connection()

    # ── Lecture ──────────────────────────────────────────────────

    def get_list(
        self,
        intervention_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        origins: Optional[List[str]] = None,
        include_done: bool = False,
    ) -> List[Dict[str, Any]]:
        """Liste les tâches avec filtres optionnels."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where: List[str] = []
            params: List[Any] = []

            if intervention_id:
                where.append("it.intervention_id = %s")
                params.append(intervention_id)
            if assigned_to:
                where.append("it.assigned_to = %s")
                params.append(assigned_to)
            if statuses:
                ph = ",".join(["%s"] * len(statuses))
                where.append(f"it.status IN ({ph})")
                params.extend(statuses)
            if origins:
                ph = ",".join(["%s"] * len(origins))
                where.append(f"it.origin IN ({ph})")
                params.extend(origins)
            if not include_done:
                where.append("it.status NOT IN ('done', 'skipped')")

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cur.execute(
                f"{_TASK_SELECT} {where_sql} ORDER BY it.sort_order ASC, it.created_at ASC",
                params,
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [_map_task(dict(zip(cols, row))) for row in rows]
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "liste des tâches")
        finally:
            release_connection(conn)

    def get_by_id(self, task_id: str) -> Dict[str, Any]:
        """Récupère une tâche par ID avec agrégats."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"{_TASK_SELECT} WHERE it.id = %s", (task_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Tâche {task_id} non trouvée")
            cols = [d[0] for d in cur.description]
            return _map_task(dict(zip(cols, row)))
        except NotFoundError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "récupération de la tâche")
        finally:
            release_connection(conn)

    def get_by_intervention(self, intervention_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les tâches d'une intervention, triées par sort_order."""
        return self.get_list(intervention_id=intervention_id, include_done=True)

    def get_progress(self, intervention_id: str) -> Dict[str, Any]:
        """Calcule la progression des tâches pour une intervention."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COUNT(*)                                                             AS total,
                    COUNT(*) FILTER (WHERE status = 'todo')                             AS todo,
                    COUNT(*) FILTER (WHERE status = 'in_progress')                      AS in_progress,
                    COUNT(*) FILTER (WHERE status = 'done')                             AS done,
                    COUNT(*) FILTER (WHERE status = 'skipped')                          AS skipped,
                    COUNT(*) FILTER (WHERE status IN ('todo','in_progress')
                                     AND optional = FALSE)                              AS blocking_pending
                FROM intervention_task
                WHERE intervention_id = %s
                """,
                (intervention_id,),
            )
            row = cur.fetchone()
            total, todo, in_progress, done, skipped, blocking_pending = (
                row[0], row[1], row[2], row[3], row[4], row[5]
            )
            return {
                "total": total,
                "todo": todo,
                "in_progress": in_progress,
                "done": done,
                "skipped": skipped,
                "blocking_pending": blocking_pending,
                "is_complete": blocking_pending == 0 and total > 0,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "calcul de la progression des tâches")
        finally:
            release_connection(conn)

    def get_progress_by_occurrence(self, occurrence_id: str) -> Dict[str, Any]:
        """Calcule la progression des tâches pour une occurrence (avant acceptation DI)."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COUNT(*)                                                             AS total,
                    COUNT(*) FILTER (WHERE status = 'todo')                             AS todo,
                    COUNT(*) FILTER (WHERE status = 'in_progress')                      AS in_progress,
                    COUNT(*) FILTER (WHERE status = 'done')                             AS done,
                    COUNT(*) FILTER (WHERE status = 'skipped')                          AS skipped,
                    COUNT(*) FILTER (WHERE status IN ('todo','in_progress')
                                     AND optional = FALSE)                              AS blocking_pending
                FROM intervention_task
                WHERE occurrence_id = %s
                """,
                (occurrence_id,),
            )
            row = cur.fetchone()
            total, todo, in_progress, done, skipped, blocking_pending = (
                row[0], row[1], row[2], row[3], row[4], row[5]
            )
            return {
                "total": total,
                "todo": todo,
                "in_progress": in_progress,
                "done": done,
                "skipped": skipped,
                "blocking_pending": blocking_pending,
                "is_complete": blocking_pending == 0 and total > 0,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(
                e, "calcul de la progression des tâches par occurrence")
        finally:
            release_connection(conn)

    def rattach_to_intervention(self, occurrence_id: str, intervention_id: str) -> int:
        """
        Rattache toutes les tâches d'une occurrence à l'intervention créée lors
        de l'acceptation de la DI. Retourne le nombre de lignes mises à jour.
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE intervention_task
                SET intervention_id = %s
                WHERE occurrence_id = %s
                AND intervention_id IS NULL
                """,
                (intervention_id, occurrence_id),
            )
            count = cur.rowcount
            conn.commit()
            logger.info(
                "Rattachement tâches : %s tâche(s) liées à l'intervention %s",
                count, intervention_id,
            )
            return count
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "rattachement des tâches à l'intervention")
        finally:
            release_connection(conn)

    # ── Création ─────────────────────────────────────────────────

    def create(self, data: InterventionTaskIn, created_by: Optional[str] = None) -> Dict[str, Any]:
        """Crée une tâche manuelle (origin resp ou tech)."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            task_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO intervention_task
                    (id, intervention_id, label, origin, status, optional,
                     assigned_to, due_date, sort_order, created_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 'todo', %s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (
                    task_id,
                    str(data.intervention_id),
                    data.label,
                    data.origin,
                    data.optional,
                    str(data.assigned_to) if data.assigned_to else None,
                    data.due_date,
                    data.sort_order,
                    created_by,
                ),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "création de la tâche")
        finally:
            release_connection(conn)

        return self.get_by_id(task_id)

    # ── Mise à jour ───────────────────────────────────────────────

    def patch(self, task_id: str, data: InterventionTaskPatch, closed_by: Optional[str] = None) -> Dict[str, Any]:
        """Met à jour partiellement une tâche."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT status FROM intervention_task WHERE id = %s", (task_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Tâche {task_id} non trouvée")

            set_parts: List[str] = []
            params: List[Any] = []

            if data.label is not None:
                set_parts.append("label = %s")
                params.append(data.label)
            if data.status is not None:
                set_parts.append("status = %s")
                params.append(data.status)
                if data.status in ("done", "skipped"):
                    set_parts.append("closed_by = %s")
                    params.append(closed_by)
            if data.skip_reason is not None:
                set_parts.append("skip_reason = %s")
                params.append(data.skip_reason)
            if data.assigned_to is not None:
                set_parts.append("assigned_to = %s")
                params.append(str(data.assigned_to))
            if data.due_date is not None:
                set_parts.append("due_date = %s")
                params.append(data.due_date)
            if data.sort_order is not None:
                set_parts.append("sort_order = %s")
                params.append(data.sort_order)

            if not set_parts:
                return self.get_by_id(task_id)

            set_parts.append("updated_at = NOW()")
            params.append(task_id)

            cur.execute(
                f"UPDATE intervention_task SET {', '.join(set_parts)} WHERE id = %s",
                params,
            )
            conn.commit()
        except (NotFoundError, ValidationError):
            conn.rollback()
            raise
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "mise à jour de la tâche")
        finally:
            release_connection(conn)

        return self.get_by_id(task_id)

    # ── Suppression ───────────────────────────────────────────────

    def delete(self, task_id: str) -> None:
        """Supprime une tâche (status=todo et aucune action liée)."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT status, action_id FROM intervention_task WHERE id = %s",
                (task_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Tâche {task_id} non trouvée")

            status, action_id = row[0], row[1]
            if status != "todo":
                raise ValidationError(
                    "Seule une tâche en statut 'todo' peut être supprimée")
            if action_id is not None:
                raise ValidationError(
                    "Impossible de supprimer une tâche liée à une action")

            cur.execute(
                "DELETE FROM intervention_task WHERE id = %s", (task_id,))
            conn.commit()
        except (NotFoundError, ValidationError):
            conn.rollback()
            raise
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "suppression de la tâche")
        finally:
            release_connection(conn)

    # ── Transition automatique ────────────────────────────────────
    # La transition todo→in_progress est gérée par le trigger DB
    # trg_task_status_on_action_link (migration j5e6f7a8b9c0).
    # Cette méthode Python n'est plus nécessaire.
