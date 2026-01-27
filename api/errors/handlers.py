"""
Gestion centralisée des erreurs et exceptions
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.errors.exceptions import (
    DatabaseError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ValidationError
)

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI):
    """Enregistre tous les handlers d'erreur personnalisés"""

    # Handler pour les erreurs 404 (NotFoundError)
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.detail, "error_type": "NotFoundError"}
        )

    # Handler pour les erreurs 401 (UnauthorizedError)
    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.detail, "error_type": "UnauthorizedError"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Handler pour les erreurs 403 (ForbiddenError)
    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": exc.detail, "error_type": "ForbiddenError"}
        )

    # Handler pour les erreurs 500 (DatabaseError)
    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": exc.detail, "error_type": "DatabaseError"}
        )

    # Handler pour les erreurs de validation (400)
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.detail, "error_type": "ValidationError"}
        )

    # Handler pour les erreurs de validation Pydantic
    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        logger.warning(
            f"Validation error on {request.url.path}: {len(errors)} errors")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Erreur de validation des données",
                "errors": errors
            }
        )

    # Handler générique pour toutes les HTTPException (Starlette)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None) or {}
        )

    # Handler pour les exceptions non gérées
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Une erreur interne s'est produite",
                "error_type": "InternalServerError"
            }
        )
