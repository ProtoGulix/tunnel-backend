import logging
from typing import Any, Dict, List

from fastapi import HTTPException

from api.db import get_connection, release_connection
from api.errors.exceptions import NotFoundError, ValidationError, raise_db_error
from api.gamme_step_validations.schemas import GammeStepValidationPatch

logger = logging.getLogger(__name__)


class GammeStepValidationRepository:
    """Requêtes pour le domaine validations des étapes de gamme"""

    def _get_connection(self):
        return get_connection()

    # ── Lecture ──────────────────────────────────────────────────

    def get_by_intervention(self, intervention_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les validations de gamme d'une intervention, triées par sort_order"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    gsv.id, gsv.step_id,
                    gs.label AS step_label,
                    gs.sort_order AS step_sort_order,
                    gs.optional AS step_optional,
                    gsv.occurrence_id, gsv.intervention_id, gsv.action_id,
                    gsv.status, gsv.skip_reason, gsv.validated_at, gsv.validated_by
                FROM gamme_step_validation gsv
                LEFT JOIN preventive_plan_gamme_step gs ON gs.id = gsv.step_id
                WHERE gsv.intervention_id = %s
                ORDER BY gs.sort_order ASC
                """,
                (intervention_id,),
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "récupération des validations de gamme")
        finally:
            release_connection(conn)

    def get_by_occurrence(self, occurrence_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les validations de gamme d'une occurrence, triées par sort_order"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    gsv.id, gsv.step_id,
                    gs.label AS step_label,
                    gs.sort_order AS step_sort_order,
                    gs.optional AS step_optional,
                    gsv.occurrence_id, gsv.intervention_id, gsv.action_id,
                    gsv.status, gsv.skip_reason, gsv.validated_at, gsv.validated_by
                FROM gamme_step_validation gsv
                LEFT JOIN preventive_plan_gamme_step gs ON gs.id = gsv.step_id
                WHERE gsv.occurrence_id = %s
                ORDER BY gs.sort_order ASC
                """,
                (occurrence_id,),
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "récupération des validations de gamme par occurrence")
        finally:
            release_connection(conn)

    def get_progress(self, intervention_id: str) -> Dict[str, Any]:
        """Calcule la progression de la gamme pour une intervention"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COUNT(*)                                                    AS total,
                    COUNT(*) FILTER (WHERE gsv.status = 'validated')           AS validated,
                    COUNT(*) FILTER (WHERE gsv.status = 'skipped')             AS skipped,
                    COUNT(*) FILTER (WHERE gsv.status = 'pending')             AS pending,
                    COUNT(*) FILTER (WHERE gsv.status = 'pending'
                                     AND pgs.optional = FALSE)                 AS blocking_pending
                FROM gamme_step_validation gsv
                JOIN preventive_plan_gamme_step pgs ON pgs.id = gsv.step_id
                WHERE gsv.intervention_id = %s
                """,
                (intervention_id,),
            )
            row = cur.fetchone()
            total, validated, skipped, pending, blocking_pending = (
                row[0], row[1], row[2], row[3], row[4]
            )
            return {
                "total": total,
                "validated": validated,
                "skipped": skipped,
                "pending": pending,
                "blocking_pending": blocking_pending,
                "is_complete": blocking_pending == 0 and total > 0,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "calcul de la progression de gamme")
        finally:
            release_connection(conn)

    def get_progress_by_occurrence(self, occurrence_id: str) -> Dict[str, Any]:
        """Calcule la progression de la gamme pour une occurrence (avant acceptation DI)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COUNT(*)                                                    AS total,
                    COUNT(*) FILTER (WHERE gsv.status = 'validated')           AS validated,
                    COUNT(*) FILTER (WHERE gsv.status = 'skipped')             AS skipped,
                    COUNT(*) FILTER (WHERE gsv.status = 'pending')             AS pending,
                    COUNT(*) FILTER (WHERE gsv.status = 'pending'
                                     AND pgs.optional = FALSE)                 AS blocking_pending
                FROM gamme_step_validation gsv
                JOIN preventive_plan_gamme_step pgs ON pgs.id = gsv.step_id
                WHERE gsv.occurrence_id = %s
                """,
                (occurrence_id,),
            )
            row = cur.fetchone()
            total, validated, skipped, pending, blocking_pending = (
                row[0], row[1], row[2], row[3], row[4]
            )
            return {
                "total": total,
                "validated": validated,
                "skipped": skipped,
                "pending": pending,
                "blocking_pending": blocking_pending,
                "is_complete": blocking_pending == 0 and total > 0,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "calcul de la progression de gamme par occurrence")
        finally:
            release_connection(conn)

    def rattach_to_intervention(
        self, occurrence_id: str, intervention_id: str
    ) -> int:
        """
        Rattache toutes les gamme_step_validation d'une occurrence
        à l'intervention créée lors de l'acceptation de la DI.
        Retourne le nombre de lignes mises à jour.
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE gamme_step_validation
                SET intervention_id = %s
                WHERE occurrence_id = %s
                AND intervention_id IS NULL
                """,
                (intervention_id, occurrence_id),
            )
            count = cur.rowcount
            conn.commit()
            logger.info(
                "Rattachement gamme : %s step(s) liés à l'intervention %s",
                count, intervention_id,
            )
            return count
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "rattachement des validations de gamme à l'intervention")
        finally:
            release_connection(conn)

    # ── Mise à jour ───────────────────────────────────────────────

    def patch_validation(self, validation_id: str, data: GammeStepValidationPatch) -> Dict[str, Any]:
        """Met à jour le statut d'une étape de gamme"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Récupérer l'état actuel
            cur.execute(
                """
                SELECT status, intervention_id
                FROM gamme_step_validation
                WHERE id = %s
                """,
                (validation_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Validation {validation_id} non trouvée")

            current_status, intervention_id = row[0], row[1]

            if current_status in ("validated", "skipped"):
                raise ValidationError("Ce step a déjà été traité")

            # Vérifier que action_id appartient à la même intervention
            if data.action_id is not None:
                cur.execute(
                    "SELECT intervention_id FROM intervention_action WHERE id = %s",
                    (str(data.action_id),),
                )
                action_row = cur.fetchone()
                if not action_row:
                    raise ValidationError(f"Action {data.action_id} introuvable")
                if str(action_row[0]) != str(intervention_id):
                    raise ValidationError(
                        "L'action fournie n'appartient pas à la même intervention"
                    )

            validated_at_sql = "validated_at = NOW()," if data.status == "validated" else ""

            cur.execute(
                f"""
                UPDATE gamme_step_validation
                SET status = %s,
                    {validated_at_sql}
                    skip_reason = %s,
                    action_id = %s,
                    validated_by = %s
                WHERE id = %s
                """,
                (
                    data.status,
                    data.skip_reason,
                    str(data.action_id) if data.action_id else None,
                    str(data.validated_by),
                    validation_id,
                ),
            )
            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "mise à jour de la validation de gamme")
        finally:
            release_connection(conn)

        # Récupérer l'objet enrichi
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    gsv.id, gsv.step_id,
                    gs.label AS step_label,
                    gs.sort_order AS step_sort_order,
                    gs.optional AS step_optional,
                    gsv.occurrence_id, gsv.intervention_id, gsv.action_id,
                    gsv.status, gsv.skip_reason, gsv.validated_at, gsv.validated_by
                FROM gamme_step_validation gsv
                LEFT JOIN preventive_plan_gamme_step gs ON gs.id = gsv.step_id
                WHERE gsv.id = %s
                """,
                (validation_id,),
            )
            row = cur.fetchone()
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "récupération de la validation mise à jour")
        finally:
            release_connection(conn)
