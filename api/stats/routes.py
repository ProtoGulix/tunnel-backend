from fastapi import APIRouter, Request, Query
from datetime import date, datetime, timedelta
from api.stats.repo import StatsRepository
from api.stats.schemas import ServiceStatusResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/service-status", response_model=ServiceStatusResponse)
async def get_service_status(
    request: Request,
    start_date: date = Query(None, description="Date de début (format: YYYY-MM-DD)"),
    end_date: date = Query(None, description="Date de fin (format: YYYY-MM-DD)")
):
    """Calcule les métriques de santé du service de maintenance."""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    repo = StatsRepository()
    return repo.get_service_status(start_date, end_date)
