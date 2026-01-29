from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.purchase_requests.repo import PurchaseRequestRepository
from api.purchase_requests.schemas import PurchaseRequestOut, PurchaseRequestIn

router = APIRouter(prefix="/purchase_requests", tags=["purchase_requests"])


@router.get("/", response_model=List[PurchaseRequestOut])
async def list_purchase_requests(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    intervention_id: Optional[str] = Query(None, description="Filtrer par intervention"),
    urgency: Optional[str] = Query(None, description="Filtrer par urgence")
):
    """Liste toutes les demandes d'achat avec filtres optionnels"""
    repo = PurchaseRequestRepository()
    return repo.get_all(
        limit=limit,
        offset=skip,
        status=status,
        intervention_id=intervention_id,
        urgency=urgency
    )


@router.get("/intervention/{intervention_id}", response_model=List[PurchaseRequestOut])
async def get_purchase_requests_by_intervention(intervention_id: str):
    """Récupère toutes les demandes d'achat liées à une intervention"""
    repo = PurchaseRequestRepository()
    return repo.get_by_intervention(intervention_id)


@router.get("/{request_id}", response_model=PurchaseRequestOut)
async def get_purchase_request(request_id: str):
    """Récupère une demande d'achat par ID"""
    repo = PurchaseRequestRepository()
    return repo.get_by_id(request_id)


@router.post("/", response_model=PurchaseRequestOut)
async def create_purchase_request(purchase_request: PurchaseRequestIn):
    """Crée une nouvelle demande d'achat"""
    repo = PurchaseRequestRepository()
    try:
        return repo.add(purchase_request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{request_id}", response_model=PurchaseRequestOut)
async def update_purchase_request(request_id: str, purchase_request: PurchaseRequestIn):
    """Met à jour une demande d'achat existante"""
    repo = PurchaseRequestRepository()
    try:
        return repo.update(request_id, purchase_request.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{request_id}")
async def delete_purchase_request(request_id: str):
    """Supprime une demande d'achat"""
    repo = PurchaseRequestRepository()
    try:
        repo.delete(request_id)
        return {"message": f"Demande d'achat {request_id} supprimée"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
