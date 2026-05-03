import logging
from typing import Dict, Set
from fastapi import Depends, Request

from api.db import get_connection, release_connection
from api.errors.exceptions import UnauthorizedError, ForbiddenError

logger = logging.getLogger(__name__)


class PermissionCache:
    """
    Cache mémoire de la matrice role_code → {endpoint_code}.
    Chargé depuis tunnel_permission au démarrage, invalidable explicitement.
    """

    def __init__(self):
        self._cache: Dict[str, Set[str]] = {}
        self._loaded = False

    def load(self) -> None:
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tr.code AS role_code, te.code AS endpoint_code
                    FROM tunnel_permission tp
                    JOIN tunnel_role     tr ON tr.id = tp.role_id
                    JOIN tunnel_endpoint te ON te.id = tp.endpoint_id
                    WHERE tp.allowed = true
                    """
                )
                rows = cur.fetchall()
            self._cache = {}
            for role_code, endpoint_code in rows:
                self._cache.setdefault(role_code, set()).add(endpoint_code)
            self._loaded = True
            logger.info("PermissionCache chargé : %d rôles", len(self._cache))
        except Exception as e:
            logger.error("Impossible de charger PermissionCache : %s", e)
        finally:
            if conn:
                release_connection(conn)

    def reload(self) -> None:
        self._loaded = False
        self.load()

    def check(self, role_code: str, endpoint_code: str) -> bool:
        if not self._loaded:
            self.load()
        return endpoint_code in self._cache.get(role_code, set())

    def permissions_for_role(self, role_code: str) -> list[str]:
        if not self._loaded:
            self.load()
        return sorted(self._cache.get(role_code, set()))


permission_cache = PermissionCache()


# --- Dépendances FastAPI ---

def require_authenticated(request: Request) -> str:
    """
    Vérifie que l'utilisateur est authentifié (tout rôle).
    Maintenu pour compatibilité avec les routes existantes.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise UnauthorizedError("Authentification requise")
    return user_id


def require_role(*roles: str):
    """
    Dépendance FastAPI : restreint l'accès aux rôles listés.

    Usage : Depends(require_role("RESP", "ADMIN"))
    """
    def _check(request: Request) -> str:
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            raise UnauthorizedError("Authentification requise")
        role = getattr(request.state, "role", None)
        if role not in roles:
            raise ForbiddenError(f"Rôle requis : {', '.join(roles)}")
        return user_id
    return _check


def require_permission(endpoint_code: str):
    """
    Dépendance FastAPI : vérifie qu'un endpoint_code est autorisé pour le rôle.

    Usage : Depends(require_permission("interventions:create"))
    """
    def _check(request: Request) -> str:
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            raise UnauthorizedError("Authentification requise")
        role = getattr(request.state, "role", None)
        if not permission_cache.check(role, endpoint_code):
            raise ForbiddenError(f"Permission refusée : {endpoint_code}")
        return user_id
    return _check


def check_permission(role_code: str, endpoint_code: str) -> bool:
    return permission_cache.check(role_code, endpoint_code)


def reload_permissions() -> None:
    permission_cache.reload()
