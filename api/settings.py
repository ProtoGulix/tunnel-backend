import os
import sys
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration globale de l'API"""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/gmao"
    )
    DB_POOL_MIN: int = int(os.getenv("DB_POOL_MIN", "2"))
    DB_POOL_MAX: int = int(os.getenv("DB_POOL_MAX", "10"))

    # JWT souverain
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_HOURS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_HOURS", "8"))

    # Mail
    MAIL_ENABLED: bool = os.getenv("MAIL_ENABLED", "false").lower() == "true"
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.example.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "tunnel@example.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Tunnel GMAO")
    SMTP_STARTTLS: bool = os.getenv("SMTP_STARTTLS", "true").lower() == "true"

    # API
    API_TITLE: str = "GMAO API"
    API_VERSION: str = "3.2.0"
    API_ENV: str = os.getenv("API_ENV", "development")
    AUTH_DISABLED: bool = os.getenv("AUTH_DISABLED", "false").lower() == "true"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "")

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
        parsed_origins = [
            origin.strip().rstrip("/")
            for origin in self.CORS_ORIGINS_RAW.split(",")
            if origin.strip()
        ]

        if parsed_origins:
            return parsed_origins

        frontend_origin = self.FRONTEND_URL.rstrip("/")

        if self.API_ENV == "development":
            # En dev: autorise localhost sur plusieurs ports communs
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
                "http://192.168.1.137:5174",
                frontend_origin
            ]
        # En prod: uniquement l'origine configurée
        return [frontend_origin]

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

if settings.API_ENV == "production" and len(settings.JWT_SECRET_KEY) < 32:
    logger.critical(
        "ERREUR DE SÉCURITÉ CRITIQUE : JWT_SECRET_KEY absent ou trop court (< 32 chars) en production. "
        "Les JWT ne peuvent pas être signés. Configurer JWT_SECRET_KEY."
    )
    sys.exit(1)

if settings.API_ENV != "production" and settings.AUTH_DISABLED:
    logger.warning(
        "⚠️  AUTH_DISABLED=true — authentification désactivée (mode développement uniquement)"
    )

if settings.API_ENV != "production" and len(settings.JWT_SECRET_KEY) < 32:
    logger.warning(
        "⚠️  JWT_SECRET_KEY absent ou trop court — les JWT sont signés avec une clé faible"
    )
