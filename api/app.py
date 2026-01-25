import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.settings import settings
from api.auth.middleware import JWTMiddleware
from api.auth.routes import router as auth_router
from api.interventions.routes import router as intervention_router
from api.intervention_actions.routes import router as intervention_action_router
from api.intervention_status.routes import router as intervention_status_router
from api.action_categories.routes import router as action_category_router
from api.action_subcategories.routes import router as action_subcategory_router
from api.equipements.routes import router as equipement_router
from api.stats.routes import router as stats_router
from api.errors.handlers import register_error_handlers
from api.health import health_check

# Simple logging setup
logging.basicConfig(
    level=logging.DEBUG if settings.API_ENV == "development" else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI Proxy Gateway
# Frontend → API → PostgreSQL (données) / Directus (auth)
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="API Proxy - Gateway entre frontend et données"
)

# Enregistre les handlers d'erreur (404, 401, 403, 500, etc.)
register_error_handlers(app)

# Middleware CORS (permet frontend d'appeler l'API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes métier (PostgreSQL)
app.include_router(intervention_router)
app.include_router(intervention_action_router)
app.include_router(intervention_status_router)
app.include_router(action_category_router)
app.include_router(action_subcategory_router)
app.include_router(equipement_router)
app.include_router(stats_router)
app.include_router(auth_router)


@app.get("/health")
async def health_endpoint():
    """Route publique: vérification de santé de l'API avec état des dépendances"""
    return await health_check()


# Middleware JWT (appliqué à toutes les routes sauf exceptions publiques)
# Vérifie que le JWT Directus est valide et extrait user_id + role
app.add_middleware(JWTMiddleware)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
