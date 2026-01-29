import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.settings import settings
from api.auth.middleware import JWTMiddleware
from api.auth.routes import router as auth_router
from api.interventions.routes import router as intervention_router
from api.intervention_actions.routes import router as intervention_action_router
from api.intervention_status.routes import router as intervention_status_router
from api.intervention_status_log.routes import router as intervention_status_log_router
from api.action_categories.routes import router as action_category_router
from api.action_subcategories.routes import router as action_subcategory_router
from api.complexity_factors.routes import router as complexity_factor_router
from api.equipements.routes import router as equipement_router
from api.stats.routes import router as stats_router
from api.purchase_requests.routes import router as purchase_request_router
from api.stock_items.routes import router as stock_item_router
from api.supplier_order_lines.routes import router as supplier_order_line_router
from api.supplier_orders.routes import router as supplier_order_router
from api.errors.handlers import register_error_handlers
from api.health import health_check


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for log levels"""
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


# Simple logging setup
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColoredFormatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

logging.basicConfig(
    level=logging.DEBUG if settings.API_ENV == "development" else logging.INFO,
    handlers=[handler]
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
app.include_router(intervention_status_log_router)
app.include_router(action_category_router)
app.include_router(action_subcategory_router)
app.include_router(equipement_router)
app.include_router(stats_router)
app.include_router(complexity_factor_router)
app.include_router(purchase_request_router)
app.include_router(stock_item_router)
app.include_router(supplier_order_line_router)
app.include_router(supplier_order_router)
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
