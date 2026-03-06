import os
import sys
import logging
from pydantic_settings import BaseSettings
from urllib.parse import urlparse
import pg8000.dbapi

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration globale de l'API"""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/gmao"
    )

    # Directus
    DIRECTUS_URL: str = os.getenv(
        "DIRECTUS_URL",
        "http://localhost:8055"
    )
    DIRECTUS_SECRET: str = os.getenv("DIRECTUS_SECRET", "")
    DIRECTUS_KEY: str = os.getenv("DIRECTUS_KEY", "")

    # API
    API_TITLE: str = "GMAO API"
    API_VERSION: str = "2.7.2"
    API_ENV: str = os.getenv("API_ENV", "development")
    AUTH_DISABLED: bool = os.getenv("AUTH_DISABLED", "false").lower() == "true"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Export Configuration
    EXPORT_TEMPLATE_DIR: str = os.getenv(
        "EXPORT_TEMPLATE_DIR",
        "config/templates"
    )
    EXPORT_TEMPLATE_FILE: str = os.getenv(
        "EXPORT_TEMPLATE_FILE",
        "fiche_intervention_v8.html"
    )
    EXPORT_TEMPLATE_VERSION: str = os.getenv(
        "EXPORT_TEMPLATE_VERSION",
        "8.1"
    )
    EXPORT_TEMPLATE_DATE: str = os.getenv(
        "EXPORT_TEMPLATE_DATE",
        "2026-02-16"
    )
    EXPORT_QR_BASE_URL: str = os.getenv(
        "EXPORT_QR_BASE_URL",
        "http://localhost:5173/interventions"
    )
    EXPORT_QR_LOGO_PATH: str = os.getenv(
        "EXPORT_QR_LOGO_PATH",
        "config/templates/logo.png"
    )

    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Liste des origines autorisées pour CORS"""
        if self.API_ENV == "development":
            # En dev: autorise localhost sur plusieurs ports communs
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
                self.FRONTEND_URL
            ]
        # En prod: uniquement l'origine configurée
        return [self.FRONTEND_URL]

    def get_db_connection(self):
        """Créé une connexion PostgreSQL"""
        try:
            parsed = urlparse(self.DATABASE_URL)
            return pg8000.dbapi.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip("/"),
                timeout=3
            )
        except TimeoutError:
            raise Exception(
                f"PostgreSQL indisponible: {parsed.hostname}:{parsed.port or 5432} - vérifier que Docker est actif"
            )
        except ConnectionRefusedError:
            raise Exception(
                f"PostgreSQL refuse la connexion: {parsed.hostname}:{parsed.port or 5432} - vérifier que le service est démarré"
            )
        except Exception as e:
            if "timeout" in str(e).lower():
                raise Exception(
                    f"PostgreSQL indisponible: {parsed.hostname}:{parsed.port or 5432} - vérifier que Docker est actif"
                )
            raise

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignorer les champs non définis dans .env


settings = Settings()

# --- Guards de sécurité au démarrage ---

if settings.API_ENV == "production" and settings.AUTH_DISABLED:
    logger.critical(
        "ERREUR DE SÉCURITÉ CRITIQUE : AUTH_DISABLED=true en environnement production. "
        "L'API refuse de démarrer. Désactiver AUTH_DISABLED ou changer API_ENV."
    )
    sys.exit(1)

if settings.API_ENV == "production" and not settings.DIRECTUS_SECRET:
    logger.critical(
        "ERREUR DE SÉCURITÉ CRITIQUE : DIRECTUS_SECRET non configuré en production. "
        "Les JWT ne peuvent pas être vérifiés. Configurer DIRECTUS_SECRET."
    )
    sys.exit(1)

if settings.API_ENV != "production" and settings.AUTH_DISABLED:
    logger.warning(
        "⚠️  AUTH_DISABLED=true — authentification désactivée (mode développement uniquement)"
    )

if settings.API_ENV != "production" and not settings.DIRECTUS_SECRET:
    logger.warning(
        "⚠️  DIRECTUS_SECRET non configuré — les JWT sont décodés sans vérification de signature"
    )
