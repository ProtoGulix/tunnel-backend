from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from api.supplier_order_lines.repo import SupplierOrderLineRepository
from api.supplier_order_lines.schemas import (
    SupplierOrderLineOut,
    SupplierOrderLineIn,
    SupplierOrderLineListItem,
    PurchaseRequestLink
)

router = APIRouter(prefix="/supplier_order_lines", tags=["supplier_order_lines"])


class LinkPurchaseRequestBody(BaseModel):
    """Body pour lier une demande d'achat"""
    purchase_request_id: str
    quantity: int


@router.get("/", response_model=List[SupplierOrderLineListItem])
async def list_supplier_order_lines(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    supplier_order_id: Optional[str] = Query(None, description="Filtrer par commande"),
    stock_item_id: Optional[str] = Query(None, description="Filtrer par article"),
    is_selected: Optional[bool] = Query(None, description="Filtrer par sélection")
):
    """Liste toutes les lignes de commande avec filtres optionnels"""
    repo = SupplierOrderLineRepository()
    return repo.get_all(
        limit=limit,
        offset=skip,
        supplier_order_id=supplier_order_id,
        stock_item_id=stock_item_id,
        is_selected=is_selected
    )


@router.get("/order/{supplier_order_id}", response_model=List[SupplierOrderLineOut])
async def get_lines_by_order(supplier_order_id: str):
    """Récupère toutes les lignes d'une commande avec détails complets"""
    repo = SupplierOrderLineRepository()
    return repo.get_by_order(supplier_order_id)


@router.get("/{line_id}", response_model=SupplierOrderLineOut)
async def get_supplier_order_line(line_id: str):
    """Récupère une ligne par ID avec stock_item et purchase_requests"""
    repo = SupplierOrderLineRepository()
    return repo.get_by_id(line_id)


@router.post("/", response_model=SupplierOrderLineOut)
async def create_supplier_order_line(line: SupplierOrderLineIn):
    """Crée une nouvelle ligne de commande fournisseur"""
    repo = SupplierOrderLineRepository()
    try:
        data = line.model_dump()
        # Convertit les purchase_requests en dict si présents
        if data.get('purchase_requests'):
            data['purchase_requests'] = [
                {'purchase_request_id': str(pr['purchase_request_id']), 'quantity': pr['quantity']}
                for pr in data['purchase_requests']
            ]
        return repo.add(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{line_id}", response_model=SupplierOrderLineOut)
async def update_supplier_order_line(line_id: str, line: SupplierOrderLineIn):
    """Met à jour une ligne de commande existante"""
    repo = SupplierOrderLineRepository()
    try:
        data = line.model_dump(exclude_unset=True)
        # Convertit les purchase_requests en dict si présents
        if data.get('purchase_requests'):
            data['purchase_requests'] = [
                {'purchase_request_id': str(pr['purchase_request_id']), 'quantity': pr['quantity']}
                for pr in data['purchase_requests']
            ]
        return repo.update(line_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{line_id}")
async def delete_supplier_order_line(line_id: str):
    """Supprime une ligne de commande"""
    repo = SupplierOrderLineRepository()
    try:
        repo.delete(line_id)
        return {"message": f"Ligne {line_id} supprimée"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{line_id}/purchase_requests", response_model=SupplierOrderLineOut)
async def link_purchase_request(line_id: str, body: LinkPurchaseRequestBody):
    """Lie une demande d'achat à une ligne de commande"""
    repo = SupplierOrderLineRepository()
    try:
        return repo.link_purchase_request(
            line_id,
            body.purchase_request_id,
            body.quantity
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{line_id}/purchase_requests/{purchase_request_id}", response_model=SupplierOrderLineOut)
async def unlink_purchase_request(line_id: str, purchase_request_id: str):
    """Retire le lien avec une demande d'achat"""
    repo = SupplierOrderLineRepository()
    try:
        return repo.unlink_purchase_request(line_id, purchase_request_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
