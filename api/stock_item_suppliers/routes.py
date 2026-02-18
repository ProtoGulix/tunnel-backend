from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.stock_item_suppliers.repo import StockItemSupplierRepository
from api.stock_item_suppliers.schemas import (
    StockItemSupplierOut, StockItemSupplierIn, StockItemSupplierListItem
)

router = APIRouter(prefix="/stock-item-suppliers", tags=["stock-item-suppliers"])


@router.get("/", response_model=List[StockItemSupplierListItem])
async def list_stock_item_suppliers(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    stock_item_id: Optional[str] = Query(None, description="Filtrer par article"),
    supplier_id: Optional[str] = Query(None, description="Filtrer par fournisseur"),
    is_preferred: Optional[bool] = Query(None, description="Filtrer par préféré")
):
    """Liste toutes les références fournisseurs avec filtres optionnels"""
    repo = StockItemSupplierRepository()
    return repo.get_all(
        limit=limit,
        offset=skip,
        stock_item_id=stock_item_id,
        supplier_id=supplier_id,
        is_preferred=is_preferred
    )


@router.get("/{ref_id}", response_model=StockItemSupplierOut)
async def get_stock_item_supplier(ref_id: str):
    """Récupère une référence fournisseur par ID"""
    repo = StockItemSupplierRepository()
    return repo.get_by_id(ref_id)


@router.get("/stock-item/{stock_item_id}", response_model=List[StockItemSupplierOut])
async def get_suppliers_by_stock_item(stock_item_id: str):
    """Récupère toutes les références fournisseurs d'un article"""
    repo = StockItemSupplierRepository()
    return repo.get_by_stock_item(stock_item_id)


@router.get("/supplier/{supplier_id}", response_model=List[StockItemSupplierOut])
async def get_stock_items_by_supplier(supplier_id: str):
    """Récupère toutes les références d'un fournisseur"""
    repo = StockItemSupplierRepository()
    return repo.get_by_supplier(supplier_id)


@router.post("/", response_model=StockItemSupplierOut)
async def create_stock_item_supplier(ref: StockItemSupplierIn):
    """Crée une nouvelle référence fournisseur"""
    repo = StockItemSupplierRepository()
    try:
        return repo.add(ref.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{ref_id}", response_model=StockItemSupplierOut)
async def update_stock_item_supplier(ref_id: str, ref: StockItemSupplierIn):
    """Met à jour une référence fournisseur existante"""
    repo = StockItemSupplierRepository()
    try:
        return repo.update(ref_id, ref.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{ref_id}/set-preferred", response_model=StockItemSupplierOut)
async def set_preferred_supplier(ref_id: str):
    """Définit cette référence comme fournisseur préféré pour l'article"""
    repo = StockItemSupplierRepository()
    try:
        return repo.set_preferred(ref_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{ref_id}")
async def delete_stock_item_supplier(ref_id: str):
    """Supprime une référence fournisseur"""
    repo = StockItemSupplierRepository()
    try:
        repo.delete(ref_id)
        return {"message": f"Référence fournisseur {ref_id} supprimée"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
