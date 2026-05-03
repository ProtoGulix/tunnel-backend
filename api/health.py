from api.settings import settings
from api.db import check_connection
from pydantic import BaseModel

__version__ = settings.API_VERSION


class HealthCheckResponse(BaseModel):
    """Réponse du health check"""
    status: str
    version: str
    database: str
    auth_service: str


def check_database_connection() -> str:
    """Vérifie la connexion à PostgreSQL via le pool."""
    return check_connection()


def check_auth_service() -> str:
    """Vérifie que le système d'auth JWT natif est opérationnel."""
    try:
        key = settings.JWT_SECRET_KEY
        if not key or len(key) < 32:
            return "warning: JWT_SECRET_KEY absent ou trop court"
        return "connected"
    except Exception as e:
        return f"error: {str(e)}"


async def health_check() -> HealthCheckResponse:
    """Vérification complète de santé de l'API"""
    db_status = check_database_connection()
    auth_status = check_auth_service()

    overall_status = "ok" if db_status == "connected" and auth_status == "connected" else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version=__version__,
        database=db_status,
        auth_service=auth_status,
    )
