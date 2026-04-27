"""Endpoints pour le dashboard et les badges de menu."""
from fastapi import APIRouter
from typing import Dict, Any
from api.dashboard.repo import DashboardRepository


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=Dict[str, Any])
def get_dashboard_summary():
    """Retourne un résumé des comptages pour les badges du menu.

    Endpoint public, léger et rapide. Retourne les compteurs principaux
    pour afficher des badges dans les sections du menu (Interventions,
    Tâches, Équipements, Stock, etc.).

    Aucune authentification requise (endpoint instrumental).
    """
    repo = DashboardRepository()
    return repo.get_summary()
