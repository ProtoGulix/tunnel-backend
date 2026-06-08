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


class ConflictError(HTTPException):
    """Conflit — ressource déjà existante (409)"""

    def __init__(self, detail: str = "Conflit : la ressource existe déjà"):
        logger.warning(f"409 Conflict: {detail}")
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class DatabaseError(HTTPException):
    """Erreur de base de données (500)"""

    def __init__(self, detail: str = "Erreur base de données"):
        logger.error(f"Database Error: {detail}")
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur base de données"
        )


class ValidationError(HTTPException):
    """Erreur de validation (400)"""

    def __init__(self, detail: str = "Erreur de validation"):
        logger.warning(f"400 Validation Error: {detail}")
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ExportError(HTTPException):
    """Erreur lors de la génération d'export (500)"""

    def __init__(self, detail: str = "Erreur lors de l'export"):
        logger.error(f"Export Error: {detail}")
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'export"
        )


class RenderError(HTTPException):
    """Erreur rendu PDF/QR (500)"""

    def __init__(self, detail: str = "Erreur lors du rendu"):
        logger.error(f"Render Error: {detail}")
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du rendu"
        )


def raise_db_error(e: Exception, context: str = "opération") -> None:
    """
    Convertit une exception psycopg2 en exception HTTP appropriée.
    - Violation de contrainte unique (23505) → ConflictError 409
    - Violation de clé étrangère (23503) → ValidationError 400
    - Tout le reste → DatabaseError 500 (message générique)
    """
    pgcode = getattr(e, "pgcode", None) or (
        getattr(getattr(e, "orig", None), "pgcode", None)
    )

    if pgcode == "23505":
        raise ConflictError(f"Cette ressource existe déjà ({context})")
    if pgcode == "23503":
        raise ValidationError(f"Référence invalide : une ressource liée est introuvable ({context})")
    if pgcode == "P0001":
        msg = getattr(getattr(e, "diag", None), "message_primary", None) or str(e)
        raise ValidationError(msg)

    raise DatabaseError(str(e))
