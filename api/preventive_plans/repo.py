import logging
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import HTTPException

from api.db import get_connection, release_connection
from api.errors.exceptions import NotFoundError, raise_db_error
from api.preventive_plans.schemas import GammeStepIn, PreventivePlanIn, PreventivePlanUpdate

logger = logging.getLogger(__name__)


class PreventivePlanRepository:
    """Requêtes pour le domaine plans de maintenance préventive"""

    def _get_connection(self):
        return get_connection()

    # ── Helpers ──────────────────────────────────────────────────

    def _fetch_steps(self, cur, plan_id: str) -> List[Dict[str, Any]]:
        """Récupère les steps d'un plan triés par sort_order ASC"""
        cur.execute(
            """
            SELECT id, plan_id, label, sort_order, optional
            FROM preventive_plan_gamme_step
            WHERE plan_id = %s
            ORDER BY sort_order ASC
            """,
            (plan_id,),
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]

    def _insert_steps(self, cur, plan_id: str, steps: List[GammeStepIn]) -> None:
        """Insère des steps en batch dans une transaction existante"""
        for step in steps:
            cur.execute(
                """
                INSERT INTO preventive_plan_gamme_step (id, plan_id, label, sort_order, optional)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (str(uuid4()), plan_id, step.label, step.sort_order, step.optional),
            )

    def _replace_steps_in_tx(self, cur, plan_id: str, steps: List[GammeStepIn]) -> None:
        """Remplace les steps dans une transaction existante (sans commit).

        Utilise un UPSERT par sort_order pour préserver les IDs existants :
        intervention_task.gamme_step_id a une FK RESTRICT, un DELETE en masse
        échouerait si des tâches référencent déjà ces steps.
        - UPDATE les steps existants (même sort_order) en conservant leur ID
        - INSERT les nouveaux sort_order
        - DELETE les sort_order supprimés, seulement s'ils n'ont pas de tâches liées
        """
        # Récupérer les steps existants indexés par sort_order
        cur.execute(
            "SELECT id, sort_order FROM preventive_plan_gamme_step WHERE plan_id = %s",
            (plan_id,),
        )
        existing = {row[1]: str(row[0]) for row in cur.fetchall()}

        incoming_orders = {s.sort_order for s in steps}

        for step in steps:
            if step.sort_order in existing:
                # UPDATE en préservant l'ID (les FK intervention_task restent valides)
                cur.execute(
                    """
                    UPDATE preventive_plan_gamme_step
                    SET label = %s, optional = %s
                    WHERE id = %s
                    """,
                    (step.label, step.optional, existing[step.sort_order]),
                )
            else:
                # INSERT nouveau step
                cur.execute(
                    """
                    INSERT INTO preventive_plan_gamme_step (id, plan_id, label, sort_order, optional)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (str(uuid4()), plan_id, step.label, step.sort_order, step.optional),
                )

        # Supprimer les sort_order retirés, seulement s'ils n'ont pas de tâches liées
        for order, step_id in existing.items():
            if order not in incoming_orders:
                cur.execute(
                    "SELECT 1 FROM intervention_task WHERE gamme_step_id = %s LIMIT 1",
                    (step_id,),
                )
                if cur.fetchone():
                    logger.warning(
                        "Step %s (sort_order=%s) non supprimé : des tâches y font référence",
                        step_id, order,
                    )
                else:
                    cur.execute(
                        "DELETE FROM preventive_plan_gamme_step WHERE id = %s",
                        (step_id,),
                    )

    # ── Lecture ──────────────────────────────────────────────────

    def get_list(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Liste tous les plans préventifs avec leur classe d'équipement et leurs steps"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where = "WHERE pp.active = true" if active_only else ""
            cur.execute(
                f"""
                SELECT
                    pp.id, pp.code, pp.label, pp.equipement_class_id,
                    ec.label AS equipement_class_label,
                    pp.trigger_type, pp.periodicity_days, pp.hours_threshold,
                    pp.auto_accept, pp.active, pp.created_at, pp.updated_at
                FROM preventive_plan pp
                LEFT JOIN equipement_class ec ON ec.id = pp.equipement_class_id
                {where}
                ORDER BY pp.code ASC
                """
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            plans = [dict(zip(cols, row)) for row in rows]
            for plan in plans:
                plan["steps"] = self._fetch_steps(cur, str(plan["id"]))
            return plans
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "liste des plans préventifs")
        finally:
            release_connection(conn)

    def get_by_id(self, plan_id: str) -> Dict[str, Any]:
        """Récupère un plan préventif par ID avec ses steps"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    pp.id, pp.code, pp.label, pp.equipement_class_id,
                    ec.label AS equipement_class_label,
                    pp.trigger_type, pp.periodicity_days, pp.hours_threshold,
                    pp.auto_accept, pp.active, pp.created_at, pp.updated_at
                FROM preventive_plan pp
                LEFT JOIN equipement_class ec ON ec.id = pp.equipement_class_id
                WHERE pp.id = %s
                """,
                (plan_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Plan préventif {plan_id} non trouvé")
            cols = [d[0] for d in cur.description]
            plan = dict(zip(cols, row))
            plan["steps"] = self._fetch_steps(cur, plan_id)
            return plan
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "récupération du plan préventif")
        finally:
            release_connection(conn)

    # ── Création ─────────────────────────────────────────────────

    def create(self, data: PreventivePlanIn) -> Dict[str, Any]:
        """Crée un plan préventif avec ses steps dans une transaction unique"""
        conn = self._get_connection()
        plan_id = str(uuid4())
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO preventive_plan
                    (id, code, label, equipement_class_id, trigger_type,
                     periodicity_days, hours_threshold, auto_accept)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    plan_id,
                    data.code,
                    data.label,
                    str(data.equipement_class_id),
                    data.trigger_type,
                    data.periodicity_days,
                    data.hours_threshold,
                    data.auto_accept,
                ),
            )
            if data.steps:
                self._insert_steps(cur, plan_id, data.steps)
            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "création du plan préventif")
        finally:
            release_connection(conn)

        return self.get_by_id(plan_id)

    # ── Mise à jour ───────────────────────────────────────────────

    def update(self, plan_id: str, data: PreventivePlanUpdate) -> Dict[str, Any]:
        """Mise à jour partielle (PATCH sémantique). Le champ code est immuable."""
        fields = data.model_dump(exclude_unset=True)
        steps = fields.pop("steps", None)

        if not fields and steps is None:
            return self.get_by_id(plan_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if fields:
                field_map = {
                    "label":               "label",
                    "equipement_class_id": "equipement_class_id",
                    "trigger_type":        "trigger_type",
                    "periodicity_days":    "periodicity_days",
                    "hours_threshold":     "hours_threshold",
                    "auto_accept":         "auto_accept",
                }
                set_parts = []
                params: List[Any] = []
                for key, col in field_map.items():
                    if key in fields:
                        set_parts.append(f"{col} = %s")
                        val = fields[key]
                        # Convertir UUID en str pour psycopg2
                        params.append(str(val) if hasattr(val, "hex") else val)
                if set_parts:
                    params.append(plan_id)
                    cur.execute(
                        f"UPDATE preventive_plan SET {', '.join(set_parts)} WHERE id = %s",
                        params,
                    )
                    if cur.rowcount == 0:
                        raise NotFoundError(f"Plan préventif {plan_id} non trouvé")

            if steps is not None:
                if not fields:
                    # Vérifier existence si on n'a pas fait de UPDATE ci-dessus
                    cur.execute("SELECT id FROM preventive_plan WHERE id = %s", (plan_id,))
                    if not cur.fetchone():
                        raise NotFoundError(f"Plan préventif {plan_id} non trouvé")
                self._replace_steps_in_tx(cur, plan_id, steps)

            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "mise à jour du plan préventif")
        finally:
            release_connection(conn)

        return self.get_by_id(plan_id)

    # ── Suppression ───────────────────────────────────────────────

    def soft_delete(self, plan_id: str) -> bool:
        """Désactive un plan préventif (soft delete)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE preventive_plan SET active = false WHERE id = %s",
                (plan_id,),
            )
            if cur.rowcount == 0:
                raise NotFoundError(f"Plan préventif {plan_id} non trouvé")
            conn.commit()
            return True
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "suppression du plan préventif")
        finally:
            release_connection(conn)

    # ── Steps ─────────────────────────────────────────────────────

    def replace_steps(self, plan_id: str, steps: List[GammeStepIn]) -> List[Dict[str, Any]]:
        """Remplace entièrement les steps d'un plan (exposé via PATCH /steps)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM preventive_plan WHERE id = %s", (plan_id,))
            if not cur.fetchone():
                raise NotFoundError(f"Plan préventif {plan_id} non trouvé")
            self._replace_steps_in_tx(cur, plan_id, steps)
            conn.commit()
            return self._fetch_steps(cur, plan_id)
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "remplacement des steps")
        finally:
            release_connection(conn)
