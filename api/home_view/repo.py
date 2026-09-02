import logging
from typing import Any, Dict, List, Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, NotFoundError, ValidationError, raise_db_error

logger = logging.getLogger(__name__)

# Vue d'accueil par défaut : comportement actuel (réservoir de tâches + fiche
# semaine, HomeSplit.jsx côté frontend), appliquée à tout rôle sans ligne
# explicite dans role_home_view. Ne JAMAIS changer cette valeur sans
# s'assurer qu'elle reste le comportement historique — c'est la garantie
# de non-régression du projet.
DEFAULT_HOME_VIEW_CODE = "technicien"


class HomeViewRepository:
    """Référentiel des vues d'accueil disponibles (home_view_ref)."""

    def _get_connection(self):
        return get_connection()

    def get_all(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT code, label FROM home_view_ref ORDER BY code")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            raise DatabaseError("Erreur récupération vues d'accueil: %s" % str(e)) from e
        finally:
            release_connection(conn)

    def get_label(self, code: str) -> Optional[str]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT label FROM home_view_ref WHERE code = %s", (code,))
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            raise DatabaseError("Erreur récupération vue d'accueil: %s" % str(e)) from e
        finally:
            release_connection(conn)


class RoleHomeViewRepository:
    """Mapping rôle → vue d'accueil (role_home_view)."""

    def _get_connection(self):
        return get_connection()

    def get_for_role_code(self, role_code: str) -> Dict[str, Any]:
        """Résout la vue d'accueil pour un code de rôle donné.
        Retourne toujours {code, label} — DEFAULT_HOME_VIEW_CODE si le rôle
        n'a pas de configuration explicite (comportement par défaut requis).
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT hv.code, hv.label
                FROM tunnel_role tr
                JOIN role_home_view rhv ON rhv.role_id = tr.id
                JOIN home_view_ref hv ON hv.code = rhv.home_view
                WHERE tr.code = %s
                """,
                (role_code,),
            )
            row = cur.fetchone()
            if row:
                return {"code": row[0], "label": row[1]}

            cur.execute("SELECT label FROM home_view_ref WHERE code = %s", (DEFAULT_HOME_VIEW_CODE,))
            default_row = cur.fetchone()
            return {
                "code": DEFAULT_HOME_VIEW_CODE,
                "label": default_row[0] if default_row else DEFAULT_HOME_VIEW_CODE,
            }
        except Exception as e:
            raise DatabaseError("Erreur résolution vue d'accueil: %s" % str(e)) from e
        finally:
            release_connection(conn)

    def list_all(self) -> List[Dict[str, Any]]:
        """Liste toutes les assignations rôle → vue (admin). Les rôles sans
        ligne explicite n'apparaissent PAS ici : ils sont sur la vue par
        défaut, ce qui n'est pas une "assignation" au sens de cet écran.
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT rhv.id, rhv.role_id, tr.code AS role_code, tr.label AS role_label,
                       rhv.home_view, hv.label AS home_view_label,
                       rhv.updated_at, rhv.updated_by
                FROM role_home_view rhv
                JOIN tunnel_role tr ON tr.id = rhv.role_id
                LEFT JOIN home_view_ref hv ON hv.code = rhv.home_view
                ORDER BY tr.code
                """
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            raise DatabaseError("Erreur liste assignations accueil: %s" % str(e)) from e
        finally:
            release_connection(conn)

    def upsert(self, role_id: str, home_view: str, updated_by: Optional[str]) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, code, label FROM tunnel_role WHERE id = %s", (role_id,))
            role_row = cur.fetchone()
            if not role_row:
                raise NotFoundError(f"Rôle {role_id} non trouvé")

            cur.execute(
                """
                INSERT INTO role_home_view (role_id, home_view, updated_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (role_id) DO UPDATE
                    SET home_view = EXCLUDED.home_view,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = now()
                RETURNING id
                """,
                (role_id, home_view, updated_by),
            )
            new_id = cur.fetchone()[0]
            conn.commit()

            cur.execute(
                """
                SELECT rhv.id, rhv.role_id, tr.code AS role_code, tr.label AS role_label,
                       rhv.home_view, hv.label AS home_view_label,
                       rhv.updated_at, rhv.updated_by
                FROM role_home_view rhv
                JOIN tunnel_role tr ON tr.id = rhv.role_id
                LEFT JOIN home_view_ref hv ON hv.code = rhv.home_view
                WHERE rhv.id = %s
                """,
                (new_id,),
            )
            row = cur.fetchone()
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        except NotFoundError:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "assignation vue d'accueil")
        finally:
            release_connection(conn)

    def delete(self, role_id: str) -> None:
        """Retire la configuration explicite d'un rôle — il retombe sur le défaut."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM role_home_view WHERE role_id = %s RETURNING id", (role_id,))
            if cur.fetchone() is None:
                raise NotFoundError(f"Aucune assignation pour le rôle {role_id}")
            conn.commit()
        except NotFoundError:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "suppression assignation vue d'accueil")
        finally:
            release_connection(conn)
