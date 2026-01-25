from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class NotFoundError(HTTPException):
    """Ressource non trouvée (404)"""

    def __init__(self, detail: str = "Ressource non trouvée"):
        logger.info(f"404 Not Found: {detail}")
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class UnauthorizedError(HTTPException):
    """Authentification échouée (401)"""

    def __init__(self, detail: str = "Non authentifié"):
        logger.warning(f"401 Unauthorized: {detail}")
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(HTTPException):
    """Accès refusé (403)"""

    def __init__(self, detail: str = "Accès refusé"):
        logger.warning(f"403 Forbidden: {detail}")
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class DatabaseError(HTTPException):
    """Erreur de base de données (500)"""

    def __init__(self, detail: str = "Erreur base de données"):
        logger.error(f"Database Error: {detail}")
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ValidationError(HTTPException):
    """Erreur de validation (400)"""

    def __init__(self, detail: str = "Erreur de validation"):
        logger.warning(f"400 Validation Error: {detail}")
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
