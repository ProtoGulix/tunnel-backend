from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.supplier_orders.repo import SupplierOrderRepository
from api.supplier_orders.schemas import SupplierOrderOut, SupplierOrderIn, SupplierOrderListItem

router = APIRouter(prefix="/supplier_orders", tags=["supplier_orders"])


@router.get("/", response_model=List[SupplierOrderListItem])
async def list_supplier_orders(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    supplier_id: Optional[str] = Query(None, description="Filtrer par fournisseur")
):
    """Liste toutes les commandes fournisseur avec filtres optionnels"""
    repo = SupplierOrderRepository()
    return repo.get_all(
        limit=limit,
        offset=skip,
        status=status,
        supplier_id=supplier_id
    )


@router.get("/{order_id}", response_model=SupplierOrderOut)
async def get_supplier_order(order_id: str):
    """Récupère une commande fournisseur par ID avec ses lignes"""
    repo = SupplierOrderRepository()
    return repo.get_by_id(order_id)


@router.get("/number/{order_number}", response_model=SupplierOrderOut)
async def get_supplier_order_by_number(order_number: str):
    """Récupère une commande fournisseur par numéro"""
    repo = SupplierOrderRepository()
    return repo.get_by_order_number(order_number)


@router.post("/", response_model=SupplierOrderOut)
async def create_supplier_order(supplier_order: SupplierOrderIn):
    """Crée une nouvelle commande fournisseur"""
    repo = SupplierOrderRepository()
    try:
        return repo.add(supplier_order.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{order_id}", response_model=SupplierOrderOut)
async def update_supplier_order(order_id: str, supplier_order: SupplierOrderIn):
    """Met à jour une commande fournisseur existante"""
    repo = SupplierOrderRepository()
    try:
        return repo.update(order_id, supplier_order.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{order_id}")
async def delete_supplier_order(order_id: str):
    """Supprime une commande fournisseur"""
    repo = SupplierOrderRepository()
    try:
        repo.delete(order_id)
        return {"message": f"Commande fournisseur {order_id} supprimée"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
