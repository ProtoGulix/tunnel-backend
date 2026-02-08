from fastapi import APIRouter, Request, Query
from datetime import date, datetime, timedelta
from api.stats.repo import StatsRepository
from api.stats.schemas import ServiceStatusResponse, ChargeTechniqueResponse
from api.errors.exceptions import ValidationError

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


@router.get("/charge-technique", response_model=ChargeTechniqueResponse)
async def get_charge_technique(
    request: Request,
    start_date: date = Query(None, description="Date de début (format: YYYY-MM-DD)"),
    end_date: date = Query(None, description="Date de fin (format: YYYY-MM-DD)"),
    period_type: str = Query("custom", description="Découpage: month, week, quarter, custom"),
):
    """Analyse de la charge technique: où va le temps de maintenance et quelle part est évitable."""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)

    valid_types = ("month", "week", "quarter", "custom")
    if period_type not in valid_types:
        raise ValidationError(
            f"period_type doit être un de: {', '.join(valid_types)}"
        )

    repo = StatsRepository()
    return repo.get_charge_technique(start_date, end_date, period_type)
