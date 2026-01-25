import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from api.auth.jwt_handler import extract_user_from_token
from api.errors.exceptions import UnauthorizedError
from api.settings import settings

logger = logging.getLogger(__name__)


class JWTMiddleware(BaseHTTPMiddleware):
    """
    Middleware qui extrait le JWT du header Authorization.
    Stocke les infos utilisateur dans request.state.
    Exclut les routes publiques (health, docs, etc).
    """

    # Routes publiques (pas d'auth requise)
    PUBLIC_ROUTES = {"/health", "/docs", "/openapi.json",
                     "/redoc", "/favicon.ico", "/auth/login"}

    async def dispatch(self, request: Request, call_next):
        try:
            # Mode test : skip auth si AUTH_DISABLED=true
            if settings.AUTH_DISABLED:
                logger.info("AUTH_DISABLED mode: skipping JWT validation")
                request.state.user_id = None
                return await call_next(request)

            # Routes publiques : laisser passer sans auth
            if request.url.path in self.PUBLIC_ROUTES or request.url.path.startswith("/static"):
                return await call_next(request)

            # Extraction du token
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                logger.warning(
                    f"Missing Authorization header for {request.method} {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Header Authorization manquant",
                             "error_type": "UnauthorizedError"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    logger.warning(f"Invalid auth scheme: {scheme}")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Schéma d'authentification invalide",
                                 "error_type": "UnauthorizedError"},
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            except ValueError:
                logger.warning("Invalid Authorization header format")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Format Authorization invalide",
                             "error_type": "UnauthorizedError"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Extraction des données utilisateur
            try:
                user_info = extract_user_from_token(token)
                request.state.user_id = user_info["user_id"]
                request.state.role = user_info["role"]
            except Exception as e:
                logger.warning(f"Token extraction error: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token invalide ou expiré",
                             "error_type": "UnauthorizedError"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Middleware error: {str(e)}", exc_info=e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Erreur lors du traitement de l'authentification"}
            )
