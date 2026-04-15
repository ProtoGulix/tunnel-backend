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

            # Attacher les gamme_step_validation en batch (évite le N+1)
            if occurrences:
                occ_ids = [str(o["id"]) for o in occurrences]
                steps_by_occ = self._fetch_steps_batch(cur, occ_ids)
                for occ in occurrences:
                    occ["gamme_steps"] = steps_by_occ.get(str(occ["id"]), [])
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
            steps_by_occ = self._fetch_steps_batch(cur, [occurrence_id])
            occ["gamme_steps"] = steps_by_occ.get(occurrence_id, [])
            return occ
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "récupération de l'occurrence")
        finally:
            release_connection(conn)

    def _fetch_steps_batch(self, cur: Any, occurrence_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Charge les gamme_step_validation pour une liste d'occurrence_ids en une seule requête.
        Retourne un dict { occurrence_id: [steps...] }.
        """
        placeholders = ",".join(["%s"] * len(occurrence_ids))
        cur.execute(
            f"""
            SELECT
                gsv.id, gsv.step_id,
                gs.label AS step_label,
                gs.sort_order AS step_sort_order,
                gs.optional AS step_optional,
                gsv.occurrence_id, gsv.intervention_id, gsv.action_id,
                gsv.status, gsv.skip_reason, gsv.validated_at, gsv.validated_by
            FROM gamme_step_validation gsv
            LEFT JOIN preventive_plan_gamme_step gs ON gs.id = gsv.step_id
            WHERE gsv.occurrence_id IN ({placeholders})
            ORDER BY gsv.occurrence_id, gs.sort_order ASC
            """,
            occurrence_ids,
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        result: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            step = dict(zip(cols, row))
            occ_key = str(step["occurrence_id"])
            result.setdefault(occ_key, []).append(step)
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

            # Calcul de la date/seuil selon le trigger_type
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

            # INSERT occurrence avec ON CONFLICT DO NOTHING
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

            # INSERT intervention_request liée
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

            # UPDATE occurrence : lier la DI et passer en 'generated'
            cur.execute(
                "UPDATE preventive_occurrence SET di_id = %s, status = 'generated' WHERE id = %s",
                (di_id, occurrence_id),
            )

            # Générer les gamme_step_validation liées à l'occurrence
            # (le trigger DB est supprimé — génération manuelle depuis ici)
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
                cur.execute(
                    """
                    INSERT INTO gamme_step_validation
                        (step_id, occurrence_id, intervention_id, status)
                    VALUES (%s, %s, NULL, 'pending')
                    ON CONFLICT (step_id, occurrence_id) DO NOTHING
                    """,
                    (str(step_row[0]), occurrence_id),
                )
            logger.info(
                "Gamme : %s step(s) générés pour l'occurrence %s",
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

        # Auto-accept : dans une transaction séparée après le commit ci-dessus
        if plan["auto_accept"]:
            self._auto_accept_occurrence(occurrence_id, di_id, machine_id, plan["id"])

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
                    "UPDATE preventive_occurrence SET intervention_id = %s WHERE id = %s",
                    (intervention_id, occurrence_id),
                )
                # ✅ Mettre à jour les gamme_step_validation avec l'intervention_id
                cur.execute(
                    """
                    UPDATE gamme_step_validation
                    SET intervention_id = %s
                    WHERE occurrence_id = %s AND intervention_id IS NULL
                    """,
                    (intervention_id, occurrence_id),
                )
                conn.commit()
                logger.info(
                    "Rattachement gamme auto-accept : intervention %s liée à l'occurrence %s",
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
        Répare les données corrompues par deux bugs désormais corrigés :

        Bug 1 — gamme_step_validation sans intervention_id :
          Lors de l'acceptation manuelle d'une DI préventive, le curseur partagé
          causait un fetchone() vide → les steps restaient avec intervention_id = NULL
          même si l'occurrence était liée à une intervention.
          Fix : UPDATE gamme_step_validation SET intervention_id depuis l'occurrence.

        Bug 2 — occurrence préventive bloquée à 'generated' après fermeture :
          _notify_if_closed() comparait un UUID au code texte 'ferme' → toujours faux
          → on_intervention_closed() jamais appelé → occurrence jamais passée à 'completed'.
          Fix : détecter les interventions fermées liées à une occurrence 'generated'
          et les passer à 'completed' + clôturer la demande liée si encore 'acceptee'.
        """
        conn = self._get_connection()
        steps_relinked = 0
        occurrences_relinked = 0
        occurrences_completed = 0
        requests_closed = 0
        details = []

        try:
            cur = conn.cursor()

            # ── Bug 1 : steps orphelins sans intervention_id ──────────────────
            # Cas : occurrence a un intervention_id, mais ses gamme_step_validation non.
            cur.execute(
                """
                UPDATE gamme_step_validation gsv
                SET intervention_id = po.intervention_id
                FROM preventive_occurrence po
                WHERE gsv.occurrence_id = po.id
                  AND po.intervention_id IS NOT NULL
                  AND gsv.intervention_id IS NULL
                RETURNING gsv.id, po.intervention_id
                """
            )
            rows = cur.fetchall()
            steps_relinked = len(rows)
            if rows:
                affected_interventions = list({str(r[1]) for r in rows})
                details.append(
                    f"Bug 1 : {steps_relinked} step(s) rattaché(s) aux interventions : "
                    + ", ".join(affected_interventions)
                )
                logger.info(
                    "Repair Bug 1 : %s gamme_step_validation rattachés", steps_relinked
                )

            # ── Bug 2 : occurrences bloquées à 'generated' ────────────────────
            # Inclut le cas où po.intervention_id est NULL mais ir.intervention_id
            # est renseigné (ancien bug de curseur lors de l'acceptation manuelle).
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
                WHERE po.status = 'generated'
                  AND isr.code = 'ferme'
                """
            )
            stale_occurrences = cur.fetchall()

            for occ_id, intervention_id, di_id, needs_relink in stale_occurrences:
                occ_id = str(occ_id)
                intervention_id = str(intervention_id)

                # Rétablir intervention_id si manquant (ancien bug curseur)
                if needs_relink:
                    cur.execute(
                        "UPDATE preventive_occurrence SET intervention_id = %s WHERE id = %s",
                        (intervention_id, occ_id),
                    )
                    occurrences_relinked += 1

                # Passer l'occurrence à 'completed'
                cur.execute(
                    "UPDATE preventive_occurrence SET status = 'completed' WHERE id = %s",
                    (occ_id,),
                )
                occurrences_completed += 1
                details.append(
                    f"Bug 2 : occurrence {occ_id} → 'completed' "
                    f"(intervention fermée : {intervention_id})"
                )

                # Clôturer la demande liée si encore 'acceptee'
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
                        cur.execute("SET LOCAL app.skip_request_status_log = 'true'")
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
                "Repair terminé : %s steps rattachés, %s occurrences reliées, %s complétées, %s demandes clôturées",
                steps_relinked, occurrences_relinked, occurrences_completed, requests_closed,
            )

        except Exception as e:
            conn.rollback()
            raise_db_error(e, "procédure de réparation des occurrences")
        finally:
            release_connection(conn)

        return {
            "steps_relinked": steps_relinked,
            "occurrences_relinked": occurrences_relinked,
            "occurrences_completed": occurrences_completed,
            "requests_closed": requests_closed,
            "details": details,
        }
