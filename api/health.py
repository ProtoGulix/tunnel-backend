import httpx
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


def check_auth_service_connection() -> str:
    """Vérifie la connexion au service d'authentification"""
    try:
        # /server/info est un endpoint public qui ne nécessite pas d'auth
        response = httpx.get(
            f"{settings.DIRECTUS_URL}/server/info",
            timeout=5.0
        )
        if response.status_code == 200:
            return "connected"
        else:
            return f"error: HTTP {response.status_code}"
    except httpx.ConnectError:
        return "error: Connection refused"
    except httpx.TimeoutException:
        return "error: Timeout"
    except Exception as e:
        return f"error: {str(e)}"


async def health_check() -> HealthCheckResponse:
    """Vérification complète de santé de l'API"""
    db_status = check_database_connection()
    auth_status = check_auth_service_connection()

    overall_status = "ok" if db_status == "connected" and auth_status == "connected" else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version=__version__,
        database=db_status,
        auth_service=auth_status
    )
