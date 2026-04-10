"""Requêtes pour le domaine statuts d'équipement"""
import logging
from typing import Any, Dict, List

from fastapi import HTTPException

from api.db import get_connection, release_connection
from api.errors.exceptions import NotFoundError, raise_db_error

logger = logging.getLogger(__name__)


class EquipementStatutRepository:
    """Requêtes pour le domaine statuts d'équipement"""

    def _get_connection(self):
        return get_connection()

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les statuts actifs, triés par ordre_affichage"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, code, libelle AS label, interventions, couleur
                FROM equipement_statuts
                WHERE est_actif = true
                ORDER BY ordre_affichage ASC
            """)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)


def check_equipement_statut_allows_interventions(machine_id: str) -> None:
    """
    Vérifie que l'équipement peut recevoir des interventions selon son statut.
    Si le statut a interventions=false → 422 equipement_statut_bloque.
    Si l'équipement n'a pas de statut → autorisé (compatibilité ascendante).
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT es.interventions
            FROM machine m
            LEFT JOIN equipement_statuts es ON es.id = m.statut_id
            WHERE m.id = %s
            """,
            (machine_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise NotFoundError(f"Équipement {machine_id} non trouvé")
        statut_interventions = row[0]
        if statut_interventions is False:
            raise HTTPException(status_code=422, detail="equipement_statut_bloque")
    finally:
        release_connection(conn)
