import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from api.auth.jwt_handler import extract_user_from_token
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
            # Requêtes OPTIONS (CORS preflight) : laisser passer sans auth
            if request.method == "OPTIONS":
                return await call_next(request)

            # QR codes publics (conçus pour impression sur rapports physiques)
            if request.url.path.endswith("/qrcode"):
                return await call_next(request)

            # Routes publiques : laisser passer sans auth
            if request.url.path in self.PUBLIC_ROUTES or request.url.path.startswith("/static"):
                return await call_next(request)

            # Extraction du token
            auth_header = request.headers.get("Authorization")

            # Mode test : valider le JWT mais ne pas bloquer si invalide
            if settings.AUTH_DISABLED:
                if auth_header:
                    try:
                        scheme, token = auth_header.split()
                        if scheme.lower() == "bearer":
                            user_info = extract_user_from_token(token)
                            logger.info(
                                "[AUTH_DISABLED] \u2713 JWT VALIDE - User: %s, Role: %s, Route: %s %s",
                                user_info['user_id'], user_info['role'],
                                request.method, request.url.path
                            )
                            request.state.user_id = user_info["user_id"]
                            request.state.role = user_info["role"]
                        else:
                            logger.warning(
                                "[AUTH_DISABLED] Invalid auth scheme: %s",
                                scheme
                            )
                            request.state.user_id = None
                    except Exception as e:
                        logger.warning(
                            "[AUTH_DISABLED] \u2717 JWT INVALIDE - Route: %s %s, Erreur: %s",
                            request.method, request.url.path, str(e)
                        )
                        request.state.user_id = None
                else:
                    logger.info(
                        "[AUTH_DISABLED] No Authorization header for %s %s",
                        request.method, request.url.path
                    )
                    request.state.user_id = None

                return await call_next(request)

            if not auth_header:
                logger.warning(
                    "Missing Authorization header for %s %s",
                    request.method, request.url.path
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Header Authorization manquant",
                             "error_type": "UnauthorizedError"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    logger.warning("Invalid auth scheme: %s", scheme)
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

                logger.info(
                    "\u2713 JWT VALIDE - User: %s, Role: %s, Route: %s %s",
                    user_info['user_id'], user_info['role'],
                    request.method, request.url.path
                )
            except Exception as e:
                logger.warning(
                    "\u2717 JWT INVALIDE - Route: %s %s, Erreur: %s",
                    request.method, request.url.path, str(e)
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token invalide ou expiré",
                             "error_type": "UnauthorizedError"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

            response = await call_next(request)
            return response

        except Exception as e:
            logger.error("Middleware error: %s", str(e), exc_info=e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Erreur lors du traitement de l'authentification"}
            )
