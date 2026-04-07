from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Literal, Union
from datetime import date
from api.purchase_requests.repo import PurchaseRequestRepository
from api.purchase_requests.schemas import (
    PurchaseRequestIn,
    PurchaseRequestListItem,
    PurchaseRequestDetail,
    PurchaseRequestStats,
    DispatchResult
)
from api.errors.exceptions import ValidationError
from api.constants import DERIVED_STATUS_CONFIG

VALID_STATUSES = tuple(DERIVED_STATUS_CONFIG.keys())

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/purchase-requests", tags=["purchase-requests"], dependencies=[Depends(require_authenticated)])


# ========== Endpoints optimisés v1.2.0 ==========

@router.get("/statuses")
def list_purchase_request_statuses():
    """Retourne tous les statuts dérivés possibles avec leur label et couleur."""
    return [
        {"code": code, "label": cfg["label"], "color": cfg["color"]}
        for code, cfg in DERIVED_STATUS_CONFIG.items()
    ]


@router.get("/stats", response_model=PurchaseRequestStats)
def get_purchase_requests_stats(
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
    return repo.get_stats(
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )


@router.get("/list", response_model=List[PurchaseRequestListItem])
def list_purchase_requests_optimized(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre max d'éléments"),
    status: Optional[str] = Query(
        None, description="Filtrer par statut dérivé (TO_QUALIFY, NO_SUPPLIER_REF, PENDING_DISPATCH, OPEN, QUOTED, ORDERED, PARTIAL, RECEIVED, REJECTED)"),
    exclude_statuses: Optional[str] = Query(
        None, description="Statuts à exclure, séparés par virgule. Ex: RECEIVED,REJECTED"),
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
    exclude_list = [s.strip() for s in exclude_statuses.split(",") if s.strip()] if exclude_statuses else None
    repo = PurchaseRequestRepository()
    return repo.get_list(
        limit=limit,
        offset=skip,
        status=status,
        intervention_id=intervention_id,
        urgency=urgency,
        exclude_statuses=exclude_list
    )


@router.get("/detail/{request_id}", response_model=PurchaseRequestDetail)
def get_purchase_request_detail(request_id: str):
    """
    [v1.2.0] Détail complet avec contexte enrichi.
    - Intervention complète avec équipement
    - Stock item complet
    - Order lines avec fournisseurs enrichis
    - Statut dérivé avec règles appliquées
    """
    repo = PurchaseRequestRepository()
    return repo.get_detail(request_id)


@router.get("/status/{status}", response_model=List[PurchaseRequestListItem])
def list_purchase_requests_by_status(
    status: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    urgency: Optional[str] = Query(None, description="Filtrer par urgence : normal, high, critical")
):
    """
    Liste les demandes d'achat filtrées par statut dérivé.

    Statuts valides : TO_QUALIFY, NO_SUPPLIER_REF, PENDING_DISPATCH, OPEN, QUOTED, ORDERED, PARTIAL, RECEIVED, REJECTED
    """
    if status not in VALID_STATUSES:
        raise ValidationError(f"Statut invalide '{status}'. Valeurs acceptées : {', '.join(VALID_STATUSES)}")
    repo = PurchaseRequestRepository()
    return repo.get_list(limit=limit, offset=skip, status=status, urgency=urgency)


@router.get("/intervention/{intervention_id}/optimized")
def get_purchase_requests_by_intervention_optimized(
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
    return repo.get_by_intervention_optimized(intervention_id, view=view)


@router.post("/dispatch", response_model=DispatchResult)
def dispatch_pending_requests():
    """
    [v1.2.12] Dispatch automatique des demandes PENDING_DISPATCH.

    Pour chaque demande prête à dispatcher:
    - Récupère les fournisseurs liés au stock_item
    - Trouve ou crée un supplier_order ouvert par fournisseur
    - Crée une supplier_order_line liée à la demande

    Les demandes passent automatiquement de PENDING_DISPATCH à OPEN.
    """
    repo = PurchaseRequestRepository()
    return repo.dispatch_all()


# ========== Endpoints CRUD ==========

@router.get("", response_model=List[PurchaseRequestListItem])
def list_purchase_requests(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    status: Optional[str] = Query(None, description="Filtrer par statut dérivé"),
    exclude_statuses: Optional[str] = Query(
        None, description="Statuts à exclure, séparés par virgule. Ex: RECEIVED,REJECTED"),
    intervention_id: Optional[str] = Query(None, description="Filtrer par intervention"),
    urgency: Optional[str] = Query(None, description="Filtrer par urgence")
):
    """Liste toutes les demandes d'achat. Alias de /list."""
    exclude_list = [s.strip() for s in exclude_statuses.split(",") if s.strip()] if exclude_statuses else None
    repo = PurchaseRequestRepository()
    return repo.get_list(
        limit=limit,
        offset=skip,
        status=status,
        intervention_id=intervention_id,
        urgency=urgency,
        exclude_statuses=exclude_list
    )


@router.get("/intervention/{intervention_id}", response_model=List[PurchaseRequestListItem])
def get_purchase_requests_by_intervention(intervention_id: str):
    """Demandes liées à une intervention. Alias de /intervention/{id}/optimized?view=list."""
    repo = PurchaseRequestRepository()
    return repo.get_list(limit=1000, offset=0, intervention_id=intervention_id)


@router.get("/{request_id}", response_model=PurchaseRequestDetail)
def get_purchase_request(request_id: str):
    """Détail d'une demande d'achat. Alias de /detail/{id}."""
    repo = PurchaseRequestRepository()
    return repo.get_detail(request_id)


@router.post("", response_model=PurchaseRequestDetail)
def create_purchase_request(purchase_request: PurchaseRequestIn):
    """Crée une nouvelle demande d'achat"""
    repo = PurchaseRequestRepository()
    return repo.add(purchase_request.model_dump())


EDITABLE_STATUSES = {'TO_QUALIFY', 'NO_SUPPLIER_REF', 'PENDING_DISPATCH'}

@router.put("/{request_id}", response_model=PurchaseRequestDetail)
def update_purchase_request(request_id: str, purchase_request: PurchaseRequestIn):
    """Met à jour une demande d'achat existante"""
    repo = PurchaseRequestRepository()
    current = repo.get_detail(request_id)
    derived = current['derived_status']
    if derived['code'] not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Cette demande ne peut plus être modifiée (statut : {derived['label']})"
        )
    return repo.update(request_id, purchase_request.model_dump(exclude_unset=True))


@router.delete("/{request_id}")
def delete_purchase_request(request_id: str):
    """Supprime une demande d'achat"""
    repo = PurchaseRequestRepository()
    repo.delete(request_id)
    return {"message": f"Demande d'achat {request_id} supprimée"}
