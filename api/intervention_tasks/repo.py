import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException

from api.constants import CLOSED_STATUS_CODE
from api.db import get_connection, release_connection
from api.errors.exceptions import NotFoundError, ValidationError, raise_db_error
from api.intervention_tasks.schemas import InterventionTaskIn, InterventionTaskPatch

logger = logging.getLogger(__name__)


def _audit_task(cur, task_id: str, decision_type: str,
                old_value: Optional[Dict], new_value: Optional[Dict],
                reason_code: str, changed_by: Optional[str] = None) -> None:
    """Insère une entrée d'audit pour une tâche via fn_audit_log_decision().
    Les erreurs sont loggées mais n'interrompent jamais la mutation métier.
    """
    try:
        cur.execute(
            """
            SELECT public.fn_audit_log_decision(
                %s, %s::uuid, %s, %s::jsonb, %s::jsonb, %s, %s, %s::uuid, %s
            )
            """,
            (
                "task",
                task_id,
                decision_type,
                json.dumps(old_value) if old_value is not None else None,
                json.dumps(new_value) if new_value is not None else None,
                reason_code,
                None,
                changed_by,
                True,
            ),
        )
    except Exception as exc:
        logger.error("audit_task(%s, %s) : %s", task_id, decision_type, exc)

_TASK_SELECT = """
    SELECT
        it.id, it.intervention_id, it.label, it.origin, it.status,
        it.optional, it.due_date, it.sort_order, it.skip_reason,
        it.gamme_step_id, it.occurrence_id,
        it.closed_by, it.created_by, it.created_at, it.updated_at,
        COALESCE(agg.action_count, 0)  AS action_count,
        COALESCE(agg.time_spent, 0.0)  AS time_spent,
        u.id        AS assigned_id,
        u.first_name AS assigned_first_name,
        u.last_name  AS assigned_last_name,
        u.email      AS assigned_email,
        u.initial    AS assigned_initial,
        NULL::text   AS assigned_status,
        NULL::text   AS assigned_role
    FROM intervention_task it
    LEFT JOIN tunnel_user u ON u.id = it.assigned_to
    LEFT JOIN LATERAL (
        SELECT
            COUNT(DISTINCT iat.action_id)    AS action_count,
            COALESCE(SUM(ia.time_spent), 0)  AS time_spent
        FROM intervention_action_task iat
        INNER JOIN intervention_action ia ON ia.id = iat.action_id
        WHERE iat.task_id = it.id
    ) agg ON TRUE
"""


def _map_task(row: Dict[str, Any]) -> Dict[str, Any]:
    """Mappe les colonnes assigned_* en objet assigned_to imbriqué.
    Convertit aussi les Decimal psycopg2 en float pour Pydantic.
    """
    if row.get("time_spent") is not None:
        row["time_spent"] = float(row["time_spent"])
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

    def _ensure_intervention_editable(self, cur, intervention_id: str) -> None:
        """Bloque toute écriture sur une intervention fermée."""
        cur.execute(
            "SELECT status_actual FROM intervention WHERE id = %s",
            (intervention_id,),
        )
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Intervention {intervention_id} non trouvée")

        status_actual = str(row[0] or "").strip().lower()
        if status_actual == CLOSED_STATUS_CODE:
            raise ValidationError(
                "Intervention fermée : aucune modification des tâches n'est autorisée"
            )

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
            self._ensure_intervention_editable(cur, str(data.intervention_id))

            # Auto-assigner au pilote de l'intervention si assigned_to absent
            assigned_to = str(data.assigned_to) if data.assigned_to else None
            if not assigned_to:
                cur.execute(
                    "SELECT tech_id FROM intervention WHERE id = %s",
                    (str(data.intervention_id),),
                )
                pilot = cur.fetchone()
                if pilot and pilot[0]:
                    assigned_to = str(pilot[0])

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
                    assigned_to,
                    data.due_date,
                    data.sort_order,
                    created_by,
                ),
            )
            _audit_task(cur, task_id, "created", None, {
                "intervention_id": str(data.intervention_id),
                "label": data.label,
                "origin": data.origin,
                "status": "todo",
                "optional": data.optional,
                "assigned_to": assigned_to,
                "due_date": str(data.due_date) if data.due_date else None,
            }, data.reason_code, created_by)
            conn.commit()
        except (NotFoundError, ValidationError):
            conn.rollback()
            raise
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
                """
                SELECT status, intervention_id, label, assigned_to, due_date, sort_order, skip_reason
                FROM intervention_task WHERE id = %s
                """,
                (task_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Tâche {task_id} non trouvée")

            old_status, intervention_id, old_label, old_assigned, old_due_date, old_sort, old_skip = row
            self._ensure_intervention_editable(cur, str(intervention_id))

            set_parts: List[str] = []
            params: List[Any] = []
            # Suivi des champs modifiés pour l'audit
            old_vals: Dict[str, Any] = {}
            new_vals: Dict[str, Any] = {}

            if data.label is not None and data.label != old_label:
                set_parts.append("label = %s")
                params.append(data.label)
                old_vals["label"] = old_label
                new_vals["label"] = data.label
            if data.status is not None and data.status != old_status:
                set_parts.append("status = %s")
                params.append(data.status)
                old_vals["status"] = old_status
                new_vals["status"] = data.status
                if data.status in ("done", "skipped"):
                    set_parts.append("closed_by = %s")
                    params.append(closed_by)
            if data.skip_reason is not None and data.skip_reason != old_skip:
                set_parts.append("skip_reason = %s")
                params.append(data.skip_reason)
                old_vals["skip_reason"] = old_skip
                new_vals["skip_reason"] = data.skip_reason
            if data.assigned_to is not None and str(data.assigned_to) != str(old_assigned or ""):
                set_parts.append("assigned_to = %s")
                params.append(str(data.assigned_to))
                old_vals["assigned_to"] = str(old_assigned) if old_assigned else None
                new_vals["assigned_to"] = str(data.assigned_to)
            if data.due_date is not None and data.due_date != old_due_date:
                set_parts.append("due_date = %s")
                params.append(data.due_date)
                old_vals["due_date"] = str(old_due_date) if old_due_date else None
                new_vals["due_date"] = str(data.due_date)
            if data.sort_order is not None and data.sort_order != old_sort:
                set_parts.append("sort_order = %s")
                params.append(data.sort_order)
                old_vals["sort_order"] = old_sort
                new_vals["sort_order"] = data.sort_order

            if not set_parts:
                return self.get_by_id(task_id)

            set_parts.append("updated_at = NOW()")
            params.append(task_id)

            cur.execute(
                f"UPDATE intervention_task SET {', '.join(set_parts)} WHERE id = %s",
                params,
            )

            _audit_task(cur, task_id, "updated", old_vals, new_vals, data.reason_code, closed_by)

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

    def delete(self, task_id: str, deleted_by: Optional[str] = None, reason_code: str = "TASK_DELETED") -> None:
        """Supprime une tâche (status=todo et aucune action liée)."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT status, intervention_id, label FROM intervention_task WHERE id = %s",
                (task_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Tâche {task_id} non trouvée")

            status, intervention_id, label = row
            self._ensure_intervention_editable(cur, str(intervention_id))

            if status != "todo":
                raise ValidationError(
                    "Seule une tâche en statut 'todo' peut être supprimée")

            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM intervention_action_task WHERE task_id = %s)",
                (task_id,),
            )
            if cur.fetchone()[0]:
                raise ValidationError(
                    "Impossible de supprimer une tâche liée à une action")

            _audit_task(cur, task_id, "deleted",
                        {"label": label, "status": status}, None,
                        reason_code, deleted_by)
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
