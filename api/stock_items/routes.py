from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from pydantic import BaseModel
from api.stock_items.repo import StockItemRepository
from api.stock_items.schemas import StockItemOut, StockItemIn
from api.stock_items.stock_item_service import StockItemService
from api.errors.exceptions import ValidationError, NotFoundError, DatabaseError
from api.utils.pagination import create_pagination_meta

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/stock-items", tags=["stock-items"], dependencies=[Depends(require_authenticated)])


class QuantityUpdate(BaseModel):
    """Schéma pour la mise à jour de quantité"""
    quantity: int


@router.get("")
async def list_stock_items(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(50, ge=1, le=1000,
                       description="Nombre max d'éléments par page"),
    family_code: Optional[str] = Query(
        None, description="Filtrer par code famille"),
    sub_family_code: Optional[str] = Query(
        None, description="Filtrer par code sous-famille"),
    search: Optional[str] = Query(
        None, description="Recherche par nom ou référence"),
    has_supplier: Optional[bool] = Query(
        None, description="true = avec fournisseur, false = sans fournisseur"),
    sort_by: Optional[str] = Query(
        None, description="Tri : name, ref, family_code, sub_family_code")
):
    """Liste les articles avec filtres, pagination et facettes famille/sous-famille"""
    repo = StockItemRepository()

    items = repo.get_all(
        limit=limit,
        offset=skip,
        family_code=family_code,
        sub_family_code=sub_family_code,
        search=search,
        has_supplier=has_supplier,
        sort_by=sort_by
    )

    total = repo.count_all(
        family_code=family_code,
        sub_family_code=sub_family_code,
        search=search,
        has_supplier=has_supplier
    )

    facets = repo.get_facets(search=search)

    pagination_meta = create_pagination_meta(
        total=total,
        offset=skip,
        limit=limit,
        count=len(items)
    )

    return {
        "items": items,
        "pagination": pagination_meta,
        "facets": facets
    }


@router.get("/ref/{ref}", response_model=StockItemOut)
async def get_stock_item_by_ref(ref: str):
    """Récupère un article par sa référence"""
    repo = StockItemRepository()
    return repo.get_by_ref(ref)


@router.get("/{item_id}", response_model=StockItemOut)
async def get_stock_item(item_id: str):
    """Récupère un article par ID avec ses fournisseurs, template et caractéristiques"""
    repo = StockItemRepository()
    return repo.get_by_id(item_id)


@router.post("", response_model=StockItemOut)
async def create_stock_item(item: StockItemIn):
    """Crée un nouvel article en stock (legacy ou template-based)"""
    service = StockItemService()
    return service.create_stock_item(item.model_dump())


@router.put("/{item_id}", response_model=StockItemOut)
async def update_stock_item(item_id: str, item: StockItemIn):
    """Met à jour un article existant (respect immutabilité template)"""
    service = StockItemService()
    return service.update_stock_item(item_id, item.model_dump(exclude_unset=True))


@router.patch("/{item_id}/quantity", response_model=StockItemOut)
async def update_stock_quantity(item_id: str, data: QuantityUpdate):
    """Met à jour uniquement la quantité d'un article"""
    repo = StockItemRepository()
    return repo.update_quantity(item_id, data.quantity)


@router.delete("/{item_id}")
async def delete_stock_item(item_id: str):
    """Supprime un article"""
    repo = StockItemRepository()
    repo.delete(item_id)
    return {"message": f"Article {item_id} supprimé"}
