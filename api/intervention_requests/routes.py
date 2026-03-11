import logging
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from uuid import UUID

from api.intervention_requests.repo import InterventionRequestRepository
from api.intervention_requests.schemas import (
    InterventionRequestIn,
    InterventionRequestListItem,
    InterventionRequestDetail,
    RequestStatusRef,
    StatusTransitionIn,
)
from api.errors.exceptions import NotFoundError, ValidationError, DatabaseError
from api.auth.permissions import require_authenticated

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/intervention-requests",
    tags=["intervention-requests"],
    dependencies=[Depends(require_authenticated)],
)

repo = InterventionRequestRepository()


@router.get("/statuses", response_model=List[RequestStatusRef])
async def list_statuses():
    """Référentiel des statuts de demande d'intervention"""
    return repo.get_statuses()


@router.get("", response_model=dict)
async def list_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    statut: Optional[str] = Query(None),
    machine_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
):
    """
    Liste les demandes d'intervention avec filtres.
    Retourne une réponse paginée.
    """
    machine_id_str = str(machine_id) if machine_id else None
    items = repo.get_list(
        limit=limit, offset=skip,
        statut=statut, machine_id=machine_id_str, search=search,
    )
    total = repo.count_list(statut=statut, machine_id=machine_id_str, search=search)
    return {
        "items": items,
        "pagination": {
            "total": total,
            "offset": skip,
            "limit": limit,
            "count": len(items),
        },
    }


@router.get("/{request_id}", response_model=InterventionRequestDetail)
async def get_request(request_id: UUID):
    """Détail d'une demande d'intervention avec son historique de statuts"""
    return repo.get_by_id(str(request_id))


@router.post("", response_model=InterventionRequestDetail, status_code=201)
async def create_request(data: InterventionRequestIn):
    """
    Crée une nouvelle demande d'intervention.
    Le code DI-YYYY-NNNN et le statut initial (nouvelle) sont générés automatiquement.
    """
    return repo.create(data.model_dump())


@router.post("/{request_id}/transition", response_model=InterventionRequestDetail)
async def transition_request_status(request_id: UUID, body: StatusTransitionIn):
    """
    Effectue une transition de statut sur une demande.

    Transitions autorisées :
    - nouvelle → en_attente, acceptee, rejetee
    - en_attente → acceptee, rejetee
    - acceptee → cloturee
    - rejetee → (aucune)
    - cloturee → (aucune)

    Le motif (notes) est obligatoire pour le statut `rejetee`.
    """
    return repo.transition_status(
        request_id=str(request_id),
        status_to=body.status_to,
        notes=body.notes,
        changed_by=str(body.changed_by) if body.changed_by else None,
    )
