import os
from pydantic_settings import BaseSettings
from urllib.parse import urlparse
import pg8000.dbapi


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
    API_VERSION: str = "1.5.2"
    API_ENV: str = os.getenv("API_ENV", "development")
    AUTH_DISABLED: bool = os.getenv("AUTH_DISABLED", "false").lower() == "true"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
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
