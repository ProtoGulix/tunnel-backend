import asyncio
import logging
import random

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.auth.jwt_handler import extract_user_from_token
from api.settings import settings

logger = logging.getLogger(__name__)


def _is_public(path: str, method: str, api_env: str) -> bool:
    always_public = {"/health", "/server/ping", "/favicon.ico", "/auth/login", "/auth/refresh"}
    if path in always_public:
        return True
    if path.endswith("/qrcode"):
        return True
    if api_env != "production" and path in {"/docs", "/openapi.json", "/redoc"}:
        return True
    if path.startswith("/static"):
        return True
    return False


async def _random_delay() -> None:
    """Délai aléatoire 50-200 ms pour contrer le timing attack sur les 401."""
    await asyncio.sleep(random.uniform(0.05, 0.20))


class JWTMiddleware(BaseHTTPMiddleware):
    """
    Middleware d'authentification JWT natif Tunnel v3.
    Vérifie signature, expiration, cohérence rôle BDD et statut actif.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if _is_public(path, request.method, settings.API_ENV):
            return await call_next(request)

        # --- Mode AUTH_DISABLED (dev uniquement) ---
        if settings.AUTH_DISABLED:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                try:
                    scheme, token = auth_header.split()
                    if scheme.lower() == "bearer":
                        user_info = extract_user_from_token(token)
                        request.state.user_id = user_info["user_id"]
                        request.state.role = user_info["role"]
                        request.state.permissions = user_info.get("permissions", [])
                        logger.info(
                            "[AUTH_DISABLED] ✓ JWT valide — user=%s role=%s %s %s",
                            user_info["user_id"], user_info["role"],
                            request.method, path,
                        )
                    else:
                        request.state.user_id = None
                        request.state.role = None
                        request.state.permissions = []
                except Exception as e:
                    logger.warning("[AUTH_DISABLED] JWT invalide — %s %s : %s",
                                   request.method, path, e)
                    request.state.user_id = None
                    request.state.role = None
                    request.state.permissions = []
            else:
                request.state.user_id = None
                request.state.role = None
                request.state.permissions = []
            return await call_next(request)

        # --- Auth obligatoire ---
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            await _random_delay()
            logger.warning("Authorization manquant — %s %s", request.method, path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Header Authorization manquant",
                         "error_type": "UnauthorizedError"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise ValueError("Format invalide")
            token = parts[1]
        except ValueError:
            await _random_delay()
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Format Authorization invalide",
                         "error_type": "UnauthorizedError"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_info = extract_user_from_token(token)
        except Exception as e:
            await _random_delay()
            logger.warning("JWT invalide — %s %s : %s", request.method, path, e)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token invalide ou expiré",
                         "error_type": "UnauthorizedError"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Vérification BDD : user actif + cohérence rôle
        user_id = user_info["user_id"]
        token_role = user_info["role"]
        db_check_ok = await _verify_user_db(user_id, token_role, path, request.method)
        if not db_check_ok:
            await _random_delay()
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token invalide ou expiré",
                         "error_type": "UnauthorizedError"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.user_id = user_id
        request.state.role = token_role
        request.state.permissions = user_info.get("permissions", [])
        logger.info("✓ JWT valide — user=%s role=%s %s %s",
                    user_id, token_role, request.method, path)

        return await call_next(request)


async def _verify_user_db(user_id: str, token_role: str, path: str, method: str) -> bool:
    """
    Vérifie en BDD que l'utilisateur existe, est actif,
    et que son rôle correspond au token.
    Retourne False (sans révéler la raison) si incohérent.
    """
    # Import lazy pour éviter la circularité avec db au niveau module
    from api.db import get_connection, release_connection
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tu.is_active, tr.code AS role_code
                FROM tunnel_user tu
                JOIN tunnel_role tr ON tr.id = tu.role_id
                WHERE tu.id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
        if not row:
            logger.warning("user_id inconnu en BDD : %s", user_id)
            return False
        is_active, db_role = row
        if not is_active:
            logger.warning("Utilisateur inactif : %s", user_id)
            return False
        if db_role != token_role:
            logger.warning(
                "Incohérence rôle token (%s) vs BDD (%s) pour user %s",
                token_role, db_role, user_id,
            )
            return False
        return True
    except Exception as e:
        logger.error("Erreur vérification BDD user %s : %s", user_id, e)
        # En cas d'erreur BDD on laisse passer (fail-open en dev, géré par guard prod)
        return True
    finally:
        if conn:
            release_connection(conn)
