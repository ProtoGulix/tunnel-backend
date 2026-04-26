import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException

from api.db import get_connection, release_connection
from api.errors.exceptions import NotFoundError, ValidationError, raise_db_error

logger = logging.getLogger(__name__)


class PreventiveOccurrenceRepository:
    """Requêtes pour le domaine occurrences de maintenance préventive"""

    def _get_connection(self):
        return get_connection()

    # ── Lecture ──────────────────────────────────────────────────

    def get_list(
        self,
        plan_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        status: Optional[str] = None,
        scheduled_date_from: Optional[date] = None,
        scheduled_date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Liste les occurrences avec filtres optionnels"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where = []
            params: List[Any] = []

            if plan_id:
                where.append("po.plan_id = %s")
                params.append(plan_id)
            if machine_id:
                where.append("po.machine_id = %s")
                params.append(machine_id)
            if status:
                where.append("po.status = %s")
                params.append(status)
            if scheduled_date_from:
                where.append("po.scheduled_date >= %s")
                params.append(scheduled_date_from)
            if scheduled_date_to:
                where.append("po.scheduled_date <= %s")
                params.append(scheduled_date_to)

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cur.execute(
                f"""
                SELECT
                    po.id, po.plan_id, pp.label AS plan_label,
                    po.machine_id, m.code AS machine_code, m.name AS machine_name,
                    po.scheduled_date, po.triggered_at, po.hours_at_trigger,
                    po.di_id, ir.code AS di_code, ir.statut AS di_statut,
                    po.intervention_id,
                    po.status, po.skip_reason, po.created_at
                FROM preventive_occurrence po
                LEFT JOIN preventive_plan pp ON pp.id = po.plan_id
                LEFT JOIN machine m ON m.id = po.machine_id
                LEFT JOIN intervention_request ir ON ir.id = po.di_id
                {where_sql}
                ORDER BY po.scheduled_date DESC
                """,
                params,
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            occurrences = [dict(zip(cols, row)) for row in rows]

            if occurrences:
                occ_ids = [str(o["id"]) for o in occurrences]
                tasks_by_occ = self._fetch_tasks_batch(cur, occ_ids)
                for occ in occurrences:
                    occ["tasks"] = tasks_by_occ.get(str(occ["id"]), [])
            return occurrences
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "liste des occurrences préventives")
        finally:
            release_connection(conn)

    def get_by_id(self, occurrence_id: str) -> Dict[str, Any]:
        """Récupère une occurrence par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    po.id, po.plan_id, pp.label AS plan_label,
                    po.machine_id, m.code AS machine_code, m.name AS machine_name,
                    po.scheduled_date, po.triggered_at, po.hours_at_trigger,
                    po.di_id, ir.code AS di_code, ir.statut AS di_statut,
                    po.intervention_id,
                    po.status, po.skip_reason, po.created_at
                FROM preventive_occurrence po
                LEFT JOIN preventive_plan pp ON pp.id = po.plan_id
                LEFT JOIN machine m ON m.id = po.machine_id
                LEFT JOIN intervention_request ir ON ir.id = po.di_id
                WHERE po.id = %s
                """,
                (occurrence_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Occurrence {occurrence_id} non trouvée")
            cols = [d[0] for d in cur.description]
            occ = dict(zip(cols, row))
            tasks_by_occ = self._fetch_tasks_batch(cur, [occurrence_id])
            occ["tasks"] = tasks_by_occ.get(occurrence_id, [])
            return occ
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "récupération de l'occurrence")
        finally:
            release_connection(conn)

    def _fetch_tasks_batch(self, cur: Any, occurrence_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Charge les intervention_task pour une liste d'occurrence_ids en une seule requête.
        Retourne un dict { occurrence_id: [tasks...] }.
        """
        placeholders = ",".join(["%s"] * len(occurrence_ids))
        cur.execute(
            f"""
            SELECT
                it.id, it.gamme_step_id,
                it.label, it.origin,
                it.sort_order,
                it.optional,
                it.occurrence_id, it.intervention_id, it.action_id,
                it.status, it.skip_reason, it.updated_at, it.closed_by
            FROM intervention_task it
            WHERE it.occurrence_id IN ({placeholders})
            ORDER BY it.occurrence_id, it.sort_order ASC
            """,
            occurrence_ids,
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        result: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            task = dict(zip(cols, row))
            occ_key = str(task["occurrence_id"])
            result.setdefault(occ_key, []).append(task)
        return result

    # ── Skip ─────────────────────────────────────────────────────

    def skip_occurrence(self, occurrence_id: str, skip_reason: str) -> Dict[str, Any]:
        """Ignore une occurrence en statut 'pending'"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT status FROM preventive_occurrence WHERE id = %s",
                (occurrence_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Occurrence {occurrence_id} non trouvée")
            if row[0] != "pending":
                raise ValidationError(
                    "Seule une occurrence en statut pending peut être ignorée")

            cur.execute(
                """
                UPDATE preventive_occurrence
                SET status = 'skipped', skip_reason = %s
                WHERE id = %s
                """,
                (skip_reason, occurrence_id),
            )
            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "mise à jour du statut de l'occurrence")
        finally:
            release_connection(conn)

        return self.get_by_id(occurrence_id)

    # ── Génération ───────────────────────────────────────────────

    def generate_occurrences(self) -> Dict[str, Any]:
        """
        Génère les occurrences en attente pour tous les plans actifs.
        Chaque machine est traitée dans sa propre transaction.
        """
        today = date.today()
        plans = self._load_active_plans()

        generated = 0
        skipped_conflicts = 0
        errors: List[str] = []

        for plan in plans:
            plan_id = str(plan["id"])
            machines = self._load_machines_for_class(
                str(plan["equipement_class_id"]))
            if machines is None:
                errors.append(
                    f"Plan {plan['label']}: erreur chargement machines")
                continue

            for machine in machines:
                machine_id = str(machine["id"])
                machine_label = machine.get("code") or machine_id
                try:
                    result = self._generate_for_machine(
                        plan, machine_id, today)
                    if result == "generated":
                        generated += 1
                    elif result == "conflict":
                        skipped_conflicts += 1
                    # "skipped_not_due" et "skipped_no_hours" : pas comptés
                except Exception as e:
                    errors.append(
                        f"Plan {plan['label']} / Machine {machine_label}: {e}"
                    )

        return {"generated": generated, "skipped_conflicts": skipped_conflicts, "errors": errors}

    def _load_active_plans(self) -> List[Dict[str, Any]]:
        """Charge tous les plans actifs depuis la DB"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, label, trigger_type, periodicity_days,
                       hours_threshold, auto_accept, equipement_class_id
                FROM preventive_plan
                WHERE active = true
                """
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            raise_db_error(e, "chargement des plans préventifs actifs")
        finally:
            release_connection(conn)

    def _load_machines_for_class(self, class_id: str) -> Optional[List[Dict[str, Any]]]:
        """Charge les machines d'une classe d'équipement"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, code, name FROM machine WHERE equipement_class_id = %s",
                (class_id,),
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception:
            return None
        finally:
            release_connection(conn)

    def _generate_for_machine(
        self, plan: Dict[str, Any], machine_id: str, today: date
    ) -> str:
        """
        Génère une occurrence pour une machine donnée.
        Retourne : 'generated', 'conflict', 'skipped_not_due', 'skipped_no_hours'
        """
        plan_id = str(plan["id"])
        current_hours = None

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            if plan["trigger_type"] == "periodicity":
                cur.execute(
                    """
                    SELECT MAX(scheduled_date)
                    FROM preventive_occurrence
                    WHERE plan_id = %s AND machine_id = %s
                    """,
                    (plan_id, machine_id),
                )
                last_date = cur.fetchone()[0]
                if last_date is not None:
                    next_date = last_date + \
                        timedelta(days=plan["periodicity_days"])
                    if next_date > today:
                        return "skipped_not_due"
                    scheduled_date = next_date
                else:
                    scheduled_date = today

            else:  # hours
                cur.execute(
                    """
                    SELECT hours_at_trigger
                    FROM preventive_occurrence
                    WHERE plan_id = %s AND machine_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (plan_id, machine_id),
                )
                row = cur.fetchone()
                last_hours = row[0] if row else None

                cur.execute(
                    "SELECT hours_total FROM machine_hours WHERE machine_id = %s",
                    (machine_id,),
                )
                mh_row = cur.fetchone()
                current_hours = mh_row[0] if mh_row else None

                if current_hours is None:
                    return "skipped_no_hours"

                last_hours_val = last_hours or 0
                if (current_hours - last_hours_val) < plan["hours_threshold"]:
                    return "skipped_not_due"

                scheduled_date = today

            occurrence_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO preventive_occurrence
                    (id, plan_id, machine_id, scheduled_date, triggered_at,
                     hours_at_trigger, status)
                VALUES (%s, %s, %s, %s, NOW(), %s, 'pending')
                ON CONFLICT (plan_id, machine_id, scheduled_date) DO NOTHING
                """,
                (
                    occurrence_id,
                    plan_id,
                    machine_id,
                    scheduled_date,
                    current_hours if plan["trigger_type"] == "hours" else None,
                ),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return "conflict"

            cur.execute(
                """
                INSERT INTO intervention_request
                    (machine_id, demandeur_nom, description, is_system, suggested_type_inter, code, statut)
                VALUES (%s, 'Système préventif', %s, true, 'PRE', 'PLACEHOLDER', 'nouvelle')
                RETURNING id
                """,
                (machine_id, plan["label"]),
            )
            di_id = str(cur.fetchone()[0])

            cur.execute(
                "UPDATE preventive_occurrence SET di_id = %s, status = 'generated' WHERE id = %s",
                (di_id, occurrence_id),
            )

            # Générer les intervention_task liées (une par step de gamme du plan)
            cur.execute(
                """
                SELECT id FROM preventive_plan_gamme_step
                WHERE plan_id = %s
                ORDER BY sort_order ASC
                """,
                (plan_id,),
            )
            steps = cur.fetchall()
            for step_row in steps:
                step_id = str(step_row[0])
                cur.execute(
                    """
                    INSERT INTO intervention_task
                        (gamme_step_id, occurrence_id, intervention_id, label, origin, status,
                         optional, sort_order)
                    SELECT
                        %s, %s, NULL, pgs.label, 'plan', 'todo', pgs.optional, pgs.sort_order
                    FROM preventive_plan_gamme_step pgs
                    WHERE pgs.id = %s
                    ON CONFLICT (gamme_step_id, occurrence_id) DO NOTHING
                    """,
                    (step_id, occurrence_id, step_id),
                )
            logger.info(
                "Tâches préventives : %s tâche(s) générée(s) pour l'occurrence %s",
                len(steps), occurrence_id,
            )

            conn.commit()

        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise
        finally:
            release_connection(conn)

        if plan["auto_accept"]:
            self._auto_accept_occurrence(
                occurrence_id, di_id, machine_id, plan["id"])

        return "generated"

    def _auto_accept_occurrence(
        self, occurrence_id: str, di_id: str, machine_id: str, plan_id: str
    ) -> None:
        """
        Crée une intervention en acceptant la DI liée à l'occurrence.
        Import lazy pour éviter la circularité avec interventions.repo
        """
        try:
            from api.interventions.repo import InterventionRepository

            intervention = InterventionRepository().add(
                {
                    "machine_id": machine_id,
                    "type_inter": "PREV",
                    "tech_initials": "SYS",
                    "priority": "normale",
                    "request_id": di_id,
                    "plan_id": plan_id,
                }
            )
            intervention_id = str(intervention["id"])

            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE preventive_occurrence
                    SET intervention_id = %s, status = 'in_progress'
                    WHERE id = %s
                    """,
                    (intervention_id, occurrence_id),
                )
                cur.execute(
                    """
                    UPDATE intervention_task
                    SET intervention_id = %s
                    WHERE occurrence_id = %s AND intervention_id IS NULL
                    """,
                    (intervention_id, occurrence_id),
                )
                conn.commit()
                logger.info(
                    "Rattachement tâches auto-accept : intervention %s liée à l'occurrence %s",
                    intervention_id, occurrence_id,
                )
            except Exception:
                conn.rollback()
                raise
            finally:
                release_connection(conn)

        except Exception as e:
            logger.warning(
                "Auto-accept échoué pour l'occurrence %s: %s", occurrence_id, e)

    # ── Repair ───────────────────────────────────────────────────

    def repair_orphaned_data(self) -> dict:
        """
        Répare les données corrompues par plusieurs bugs désormais corrigés :

        Bug 1 — intervention_task sans intervention_id :
          Lors de l'acceptation manuelle d'une DI préventive, le curseur partagé
          causait un fetchone() vide → les tâches restaient avec intervention_id = NULL
          même si l'occurrence était liée à une intervention.
          Fix : UPDATE intervention_task SET intervention_id depuis l'occurrence.

        Bug 2 — occurrence préventive bloquée à 'generated' après fermeture :
          _notify_if_closed() comparait un UUID au code texte 'ferme' → toujours faux
          → on_intervention_closed() jamais appelé → occurrence jamais passée à 'completed'.
          Fix : détecter les interventions fermées liées à une occurrence 'generated'
          et les passer à 'completed' + clôturer la demande liée si encore 'acceptee'.

        Bug 3 — plan_id null sur une intervention préventive :
          Lors de l'acceptation manuelle via POST /interventions (chemin direct sans
          passer par transition_status), plan_id n'était pas résolu depuis l'occurrence.
          Fix : UPDATE intervention SET plan_id depuis preventive_occurrence.

        Bug 4 — tâches orphelines non rattachées à une intervention acceptée via DI :
          Même origine que Bug 1 mais côté DI : si l'acceptation passait par
          transition_status et que le curseur partagé plantait le rattachement.
          Fix : couvrir aussi le cas où occurrence.intervention_id IS NULL mais
          la DI a un intervention_id.
        """
        conn = self._get_connection()
        tasks_relinked = 0
        occurrences_relinked = 0
        occurrences_set_in_progress = 0
        occurrences_completed = 0
        requests_closed = 0
        interventions_plan_fixed = 0
        details = []

        try:
            cur = conn.cursor()

            # ── Bug 3 : plan_id null sur intervention préventive ───────────────
            # Interventions créées via POST /interventions avec request_id avant le fix
            # qui résout plan_id depuis l'occurrence liée.
            cur.execute(
                """
                UPDATE intervention i
                SET plan_id = po.plan_id
                FROM preventive_occurrence po
                WHERE po.intervention_id = i.id
                  AND i.plan_id IS NULL
                  AND po.plan_id IS NOT NULL
                RETURNING i.id, po.plan_id
                """
            )
            plan_rows = cur.fetchall()
            interventions_plan_fixed = len(plan_rows)
            if plan_rows:
                details.append(
                    f"Bug 3 : {interventions_plan_fixed} intervention(s) — plan_id rétabli"
                )
                logger.info(
                    "Repair Bug 3 : %s intervention(s) avec plan_id corrigé",
                    interventions_plan_fixed,
                )

            # Couvrir aussi le chemin DI → occurrence.intervention_id NULL mais
            # ir.intervention_id renseigné (Bug 3 via transition_status)
            cur.execute(
                """
                UPDATE intervention i
                SET plan_id = po.plan_id
                FROM preventive_occurrence po
                JOIN intervention_request ir ON ir.id = po.di_id
                WHERE ir.intervention_id = i.id
                  AND po.intervention_id IS NULL
                  AND i.plan_id IS NULL
                  AND po.plan_id IS NOT NULL
                RETURNING i.id, po.plan_id
                """
            )
            plan_rows2 = cur.fetchall()
            if plan_rows2:
                interventions_plan_fixed += len(plan_rows2)
                details.append(
                    f"Bug 3b : {len(plan_rows2)} intervention(s) — plan_id rétabli via DI"
                )

            # ── Bug 1 : tâches orphelines sans intervention_id ──────────────────
            cur.execute(
                """
                UPDATE intervention_task it
                SET intervention_id = po.intervention_id
                FROM preventive_occurrence po
                WHERE it.occurrence_id = po.id
                  AND po.intervention_id IS NOT NULL
                  AND it.intervention_id IS NULL
                RETURNING it.id, po.intervention_id
                """
            )
            rows = cur.fetchall()
            tasks_relinked = len(rows)
            if rows:
                affected_interventions = list({str(r[1]) for r in rows})
                details.append(
                    f"Bug 1 : {tasks_relinked} tâche(s) rattachée(s) aux interventions : "
                    + ", ".join(affected_interventions)
                )
                logger.info(
                    "Repair Bug 1 : %s intervention_task rattachés", tasks_relinked
                )

            # Bug 1 variante : occurrence sans intervention_id mais DI a intervention_id
            cur.execute(
                """
                UPDATE intervention_task it
                SET intervention_id = ir.intervention_id
                FROM preventive_occurrence po
                JOIN intervention_request ir ON ir.id = po.di_id
                WHERE it.occurrence_id = po.id
                  AND po.intervention_id IS NULL
                  AND ir.intervention_id IS NOT NULL
                  AND it.intervention_id IS NULL
                RETURNING it.id, ir.intervention_id
                """
            )
            rows2 = cur.fetchall()
            if rows2:
                tasks_relinked += len(rows2)
                affected_interventions2 = list({str(r[1]) for r in rows2})
                details.append(
                    f"Bug 1b : {len(rows2)} tâche(s) rattachée(s) via DI → interventions : "
                    + ", ".join(affected_interventions2)
                )
                logger.info(
                    "Repair Bug 1b : %s intervention_task rattachés via DI", len(rows2)
                )

            # ── Étape 3 : occurrences bloquées à 'generated' malgré DI acceptée ──
            cur.execute(
                """
                UPDATE preventive_occurrence po
                SET status = 'in_progress',
                    intervention_id = COALESCE(po.intervention_id, ir.intervention_id)
                FROM intervention_request ir
                WHERE po.di_id = ir.id
                  AND po.status = 'generated'
                  AND ir.statut = 'acceptee'
                  AND ir.intervention_id IS NOT NULL
                RETURNING po.id
                """
            )
            in_progress_rows = cur.fetchall()
            occurrences_set_in_progress = len(in_progress_rows)
            if in_progress_rows:
                details.append(
                    f"Étape 3 : {occurrences_set_in_progress} occurrence(s) → 'in_progress' (DI acceptée)"
                )
                logger.info(
                    "Repair étape 3 : %s occurrence(s) passées à 'in_progress'",
                    occurrences_set_in_progress,
                )

            # ── Bug 2 : occurrences bloquées à 'generated' ou 'in_progress' ──────
            cur.execute(
                """
                SELECT
                    po.id,
                    COALESCE(po.intervention_id, ir.intervention_id) AS intervention_id,
                    po.di_id,
                    (po.intervention_id IS NULL) AS needs_relink
                FROM preventive_occurrence po
                LEFT JOIN intervention_request ir
                    ON ir.id = po.di_id AND po.intervention_id IS NULL
                JOIN intervention i
                    ON i.id = COALESCE(po.intervention_id, ir.intervention_id)
                JOIN intervention_status_ref isr ON isr.id = i.status_actual
                WHERE po.status IN ('generated', 'in_progress')
                  AND isr.code = 'ferme'
                """
            )
            stale_occurrences = cur.fetchall()

            for occ_id, intervention_id, di_id, needs_relink in stale_occurrences:
                occ_id = str(occ_id)
                intervention_id = str(intervention_id)

                if needs_relink:
                    cur.execute(
                        "UPDATE preventive_occurrence SET intervention_id = %s WHERE id = %s",
                        (intervention_id, occ_id),
                    )
                    occurrences_relinked += 1

                cur.execute(
                    "UPDATE preventive_occurrence SET status = 'completed' WHERE id = %s",
                    (occ_id,),
                )
                occurrences_completed += 1
                details.append(
                    f"Bug 2 : occurrence {occ_id} → 'completed' "
                    f"(intervention fermée : {intervention_id})"
                )

                if di_id:
                    cur.execute(
                        """
                        SELECT id, statut FROM intervention_request
                        WHERE id = %s AND statut = 'acceptee'
                        LIMIT 1
                        """,
                        (str(di_id),),
                    )
                    req_row = cur.fetchone()
                    if req_row:
                        req_id, req_statut = str(req_row[0]), req_row[1]
                        cur.execute(
                            "SET LOCAL app.skip_request_status_log = 'true'")
                        cur.execute(
                            "UPDATE intervention_request SET statut = 'cloturee' WHERE id = %s",
                            (req_id,),
                        )
                        cur.execute(
                            """
                            INSERT INTO request_status_log
                                (request_id, status_from, status_to, changed_by, notes)
                            VALUES (%s, %s, 'cloturee', NULL, %s)
                            """,
                            (
                                req_id,
                                req_statut,
                                "Clôture automatique — procédure de réparation (bug cascade fermeture)",
                            ),
                        )
                        requests_closed += 1
                        details.append(
                            f"Bug 2 : demande {req_id} → 'cloturee' (liée à l'occurrence {occ_id})"
                        )

            conn.commit()
            logger.info(
                "Repair terminé : %s tâches rattachées, %s occurrences reliées, "
                "%s → in_progress, %s complétées, %s demandes clôturées, %s plan_id corrigés",
                tasks_relinked, occurrences_relinked, occurrences_set_in_progress,
                occurrences_completed, requests_closed, interventions_plan_fixed,
            )

        except Exception as e:
            conn.rollback()
            raise_db_error(e, "procédure de réparation des occurrences")
        finally:
            release_connection(conn)

        return {
            "tasks_relinked": tasks_relinked,
            "occurrences_relinked": occurrences_relinked,
            "occurrences_set_in_progress": occurrences_set_in_progress,
            "occurrences_completed": occurrences_completed,
            "requests_closed": requests_closed,
            "interventions_plan_fixed": interventions_plan_fixed,
            "details": details,
        }
