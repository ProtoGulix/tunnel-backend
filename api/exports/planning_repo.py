from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from api.errors.exceptions import NotFoundError, DatabaseError
from api.db import get_connection, release_connection


_TYPE_MAP = {
    "PRE": "preventif",
    "CUR": "curatif",
    "PRO": "projet",
}


def _infer_type(inter_code: Optional[str]) -> str:
    """Inférer type depuis le code intervention (ex: VLT-PRE-... → preventif)."""
    if not inter_code:
        return "projet"
    parts = inter_code.split("-")
    if len(parts) >= 2:
        return _TYPE_MAP.get(parts[1].upper(), "projet")
    return "projet"


class PlanningRepository:
    """Repository spécialisé pour export fiche de semaine technicien."""

    def _get_connection(self):
        return get_connection()

    def get_tech_info(self, tech_id: str) -> Dict[str, Any]:
        """Récupère first_name, last_name, initial du technicien."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, first_name, last_name, initial
                FROM tunnel_user
                WHERE id = %s
                """,
                (tech_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Technicien {tech_id} non trouvé")
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur DB (get_tech_info): {str(e)}")
        finally:
            release_connection(conn)

    def get_tasks_for_week(
        self, tech_id: str, monday: date, friday: date
    ) -> List[Dict[str, Any]]:
        """
        Retourne les tâches assignées au technicien entre monday et friday (inclus),
        statut todo ou in_progress, triées par due_date puis sort_order.

        Chaque entrée contient :
        {
            "equip_code": str,
            "inter_code": str,
            "type": str,       # preventif | curatif | projet
            "label": str,
            "due_date": date,
        }
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    it.label,
                    it.due_date,
                    it.sort_order,
                    i.code  AS inter_code,
                    m.code  AS equip_code
                FROM intervention_task it
                JOIN intervention i  ON i.id  = it.intervention_id
                LEFT JOIN machine m ON m.id   = i.machine_id
                WHERE it.assigned_to = %s
                  AND it.due_date >= %s
                  AND it.due_date <= %s
                  AND it.status IN ('todo', 'in_progress')
                ORDER BY it.due_date ASC, it.sort_order ASC
                LIMIT 200
                """,
                (tech_id, monday, friday),
            )
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            for row in rows:
                row["type"] = _infer_type(row.get("inter_code"))
            return rows
        except Exception as e:
            raise DatabaseError(f"Erreur DB (get_tasks_for_week): {str(e)}")
        finally:
            release_connection(conn)
