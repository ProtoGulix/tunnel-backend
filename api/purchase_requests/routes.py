from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Literal, Union
from datetime import date
from api.purchase_requests.repo import PurchaseRequestRepository
from api.purchase_requests.schemas import (
    PurchaseRequestIn,
    PurchaseRequestOut,  # Legacy
    PurchaseRequestListItem,  # v1.2.0 optimisé
    PurchaseRequestDetail,  # v1.2.0 optimisé
    PurchaseRequestStats,  # v1.2.0 nouveau
    DispatchResult  # v1.2.12 nouveau
)

router = APIRouter(prefix="/purchase_requests", tags=["purchase_requests"])


# ========== Endpoints optimisés v1.2.0 ==========

@router.get("/stats", response_model=PurchaseRequestStats)
async def get_purchase_requests_stats(
    start_date: Optional[date] = Query(
        None, description="Date début (default: -3 mois)"),
    end_date: Optional[date] = Query(
        None, description="Date fin (default: aujourd'hui)"),
    group_by: str = Query(
        "status", description="Grouper par (status, urgency)")
):
    """
    [v1.2.0] Statistiques agrégées pour dashboards.
    Retourne compteurs totaux, par statut, par urgence, top articles.
    """
    repo = PurchaseRequestRepository()
    try:
        return repo.get_stats(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/list", response_model=List[PurchaseRequestListItem])
async def list_purchase_requests_optimized(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre max d'éléments"),
    status: Optional[str] = Query(
        None, description="Filtrer par statut dérivé (TO_QUALIFY, NO_SUPPLIER_REF, PENDING_DISPATCH, OPEN, QUOTED, ORDERED, PARTIAL, RECEIVED, REJECTED)"),
    intervention_id: Optional[str] = Query(
        None, description="Filtrer par intervention"),
    urgency: Optional[str] = Query(None, description="Filtrer par urgence")
):
    """
    [v1.2.0] Liste optimisée légère pour tableaux.
    - Statut dérivé calculé en SQL
    - Compteurs agrégés (quotes_count, selected_count, suppliers_count)
    - Pas d'objets imbriqués (références directes)
    - Payload ~95% plus léger que version legacy
    """
    repo = PurchaseRequestRepository()
    try:
        return repo.get_list(
            limit=limit,
            offset=skip,
            status=status,
            intervention_id=intervention_id,
            urgency=urgency
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/detail/{request_id}", response_model=PurchaseRequestDetail)
async def get_purchase_request_detail(request_id: str):
    """
    [v1.2.0] Détail complet avec contexte enrichi.
    - Intervention complète avec équipement
    - Stock item complet
    - Order lines avec fournisseurs enrichis
    - Statut dérivé avec règles appliquées
    """
    repo = PurchaseRequestRepository()
    try:
        return repo.get_detail(request_id)
    except Exception as e:
        raise HTTPException(status_code=404 if "non trouvée" in str(
            e) else 400, detail=str(e)) from e


@router.get("/intervention/{intervention_id}/optimized")
async def get_purchase_requests_by_intervention_optimized(
    intervention_id: str,
    view: Literal['list', 'full'] = Query(
        'list', description="Niveau de détail (list=léger, full=complet)")
) -> Union[List[PurchaseRequestListItem], List[PurchaseRequestDetail]]:
    """
    [v1.2.0] Filtre par intervention avec choix de granularité.
    - view=list : retourne PurchaseRequestListItem (rapide)
    - view=full : retourne PurchaseRequestDetail (complet avec contexte)
    """
    repo = PurchaseRequestRepository()
    try:
        return repo.get_by_intervention_optimized(intervention_id, view=view)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/dispatch", response_model=DispatchResult)
async def dispatch_pending_requests():
    """
    [v1.2.12] Dispatch automatique des demandes PENDING_DISPATCH.

    Pour chaque demande prête à dispatcher:
    - Récupère les fournisseurs liés au stock_item
    - Trouve ou crée un supplier_order ouvert par fournisseur
    - Crée une supplier_order_line liée à la demande

    Les demandes passent automatiquement de PENDING_DISPATCH à OPEN.
    """
    repo = PurchaseRequestRepository()
    try:
        return repo.dispatch_all()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ========== Endpoints legacy (maintien compatibilité) ==========

@router.get("/", response_model=List[PurchaseRequestOut])
async def list_purchase_requests(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre max d'éléments"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    intervention_id: Optional[str] = Query(
        None, description="Filtrer par intervention"),
    urgency: Optional[str] = Query(None, description="Filtrer par urgence")
):
    """
    [LEGACY] Liste toutes les demandes d'achat avec filtres optionnels.
    Utiliser /purchase_requests/list pour payload optimisé
    """
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
    """
    [LEGACY] Récupère toutes les demandes d'achat liées à une intervention.
    Utiliser /purchase_requests/intervention/{id}/optimized?view=list
    """
    repo = PurchaseRequestRepository()
    return repo.get_by_intervention(intervention_id)


@router.get("/{request_id}", response_model=PurchaseRequestOut)
async def get_purchase_request(request_id: str):
    """
    [LEGACY] Récupère une demande d'achat par ID.
    Utiliser /purchase_requests/detail/{id} pour contexte enrichi
    """
    repo = PurchaseRequestRepository()
    return repo.get_by_id(request_id)


# ========== Endpoints CRUD (maintien) ==========

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
