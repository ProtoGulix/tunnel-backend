from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List

from api.intervention_status_log.repo import InterventionStatusLogRepository
from api.intervention_status_log.schemas import InterventionStatusLogIn, InterventionStatusLogOut
from api.errors.exceptions import ValidationError

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/intervention-status-log", tags=["intervention-status-log"], dependencies=[Depends(require_authenticated)])


@router.get("/", response_model=List[InterventionStatusLogOut])
def list_status_logs(
    intervention_id: str | None = Query(None, description="Filtrer par intervention_id"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner")
):
    """Liste tous les logs de changement de statut avec filtres optionnels"""
    repo = InterventionStatusLogRepository()
    return repo.get_all(intervention_id=intervention_id, limit=limit, offset=skip)


@router.get("/{log_id}", response_model=InterventionStatusLogOut)
def get_status_log(log_id: str):
    """Récupère un log de changement de statut par ID"""
    repo = InterventionStatusLogRepository()
    return repo.get_by_id(log_id)


@router.post("/", response_model=InterventionStatusLogOut, status_code=201)
def create_status_log(log: InterventionStatusLogIn, request: Request):
    """
    Crée un nouveau log de changement de statut

    Le trigger DB synchronisera automatiquement le statut de l'intervention.

    Règles de validation:
    - intervention_id, status_to, technician_id, date sont obligatoires
    - status_from doit correspondre au statut actuel de l'intervention (sauf si null)
    - Toutes les transitions de statut sont autorisées
    """
    repo = InterventionStatusLogRepository()
    try:
        return repo.add(log.model_dump())
    except ValueError as e:
        raise ValidationError(str(e)) from e
