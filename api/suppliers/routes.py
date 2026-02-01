from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.suppliers.repo import SupplierRepository
from api.suppliers.schemas import SupplierOut, SupplierIn, SupplierListItem

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("/", response_model=List[SupplierListItem])
async def list_suppliers(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    search: Optional[str] = Query(None, description="Recherche par nom, code ou contact")
):
    """Liste tous les fournisseurs avec filtres optionnels"""
    repo = SupplierRepository()
    return repo.get_all(
        limit=limit,
        offset=skip,
        is_active=is_active,
        search=search
    )


@router.get("/{supplier_id}", response_model=SupplierOut)
async def get_supplier(supplier_id: str):
    """Récupère un fournisseur par ID"""
    repo = SupplierRepository()
    return repo.get_by_id(supplier_id)


@router.get("/code/{code}", response_model=SupplierOut)
async def get_supplier_by_code(code: str):
    """Récupère un fournisseur par code"""
    repo = SupplierRepository()
    return repo.get_by_code(code)


@router.post("/", response_model=SupplierOut)
async def create_supplier(supplier: SupplierIn):
    """Crée un nouveau fournisseur"""
    repo = SupplierRepository()
    try:
        return repo.add(supplier.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{supplier_id}", response_model=SupplierOut)
async def update_supplier(supplier_id: str, supplier: SupplierIn):
    """Met à jour un fournisseur existant"""
    repo = SupplierRepository()
    try:
        return repo.update(supplier_id, supplier.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{supplier_id}")
async def delete_supplier(supplier_id: str):
    """Supprime un fournisseur"""
    repo = SupplierRepository()
    try:
        repo.delete(supplier_id)
        return {"message": f"Fournisseur {supplier_id} supprimé"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
