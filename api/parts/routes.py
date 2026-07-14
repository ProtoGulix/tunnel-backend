from fastapi import APIRouter, Depends, Query
from typing import Optional

from api.parts.repo import PartRepository
from api.parts.schemas import (
    PartCreate, PartDetail, PartListItem, PartManufacturerRefCreate, PartManufacturerRefUpdate,
    PartSupplierRefCreate, PartSupplierRefListItem, PartSupplierRefUpdate, PartUpdate,
)
from api.auth.permissions import require_authenticated
from api.utils.pagination import PaginatedResponse, SingleResponse
from api.utils.response import paginated, single

router = APIRouter(
    prefix="/parts",
    tags=["parts"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("", response_model=PaginatedResponse[PartListItem])
def list_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    family_code: Optional[str] = Query(None),
    sub_family_code: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Recherche par ref interne, ref fabricant ou désignation"),
):
    """Liste les pièces du catalogue V4"""
    repo = PartRepository()
    items = repo.get_all(
        limit=limit,
        offset=skip,
        family_code=family_code,
        sub_family_code=sub_family_code,
        search=search,
    )
    total = repo.count_all(
        family_code=family_code,
        sub_family_code=sub_family_code,
        search=search,
    )
    return paginated(items, total=total, offset=skip, limit=limit)


@router.get("/supplier-refs", response_model=PaginatedResponse[PartSupplierRefListItem])
def list_supplier_refs(
    supplier_id: Optional[str] = Query(None, description="ID du fournisseur (optionnel — liste toutes les références si absent)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, description="Recherche par ref interne, ref fabricant ou ref fournisseur"),
):
    """Liste les références fournisseur, avec pièce et référence fabricant liées, filtrables par fournisseur"""
    repo = PartRepository()
    items = repo.get_supplier_refs_by_supplier(
        supplier_id, limit=limit, offset=skip, search=search,
    )
    total = repo.count_supplier_refs_by_supplier(supplier_id, search=search)
    return paginated(items, total=total, offset=skip, limit=limit)


@router.get("/ref/{internal_ref}", response_model=SingleResponse[PartDetail], response_model_exclude_none=True)
def get_part_by_ref(internal_ref: str):
    """Récupère une pièce par sa référence interne (ex: P000042)"""
    repo = PartRepository()
    return single(repo.get_by_internal_ref(internal_ref))


@router.get("/{part_id}", response_model=SingleResponse[PartDetail], response_model_exclude_none=True)
def get_part(part_id: str):
    """Récupère une pièce par ID avec toutes ses références"""
    repo = PartRepository()
    return single(repo.get_by_id(part_id))


@router.post("", response_model=SingleResponse[PartDetail], status_code=201, response_model_exclude_none=True)
def create_part(data: PartCreate):
    """Crée une nouvelle pièce (internal_ref P000001 générée automatiquement)"""
    repo = PartRepository()
    return single(repo.create(data.model_dump()))


@router.patch("/{part_id}", response_model=SingleResponse[PartDetail], response_model_exclude_none=True)
def update_part(part_id: str, data: PartUpdate):
    """Met à jour une pièce (modification partielle)"""
    repo = PartRepository()
    return single(repo.update(part_id, data.model_dump(exclude_unset=True)))


@router.post("/{part_id}/manufacturer-refs", response_model=SingleResponse[PartDetail], status_code=201, response_model_exclude_none=True)
def add_manufacturer_ref(part_id: str, data: PartManufacturerRefCreate):
    """Ajoute une référence fabricant à une pièce"""
    repo = PartRepository()
    return single(repo.add_manufacturer_ref(part_id, data.model_dump()))


@router.patch(
    "/manufacturer-refs/{mfr_ref_id}",
    response_model=SingleResponse[PartDetail],
    response_model_exclude_none=True,
)
def update_manufacturer_ref(mfr_ref_id: str, data: PartManufacturerRefUpdate):
    """Met à jour une référence fabricant (modification partielle)"""
    repo = PartRepository()
    return single(repo.update_manufacturer_ref(mfr_ref_id, data.model_dump(exclude_unset=True)))


@router.delete(
    "/manufacturer-refs/{mfr_ref_id}",
    response_model=SingleResponse[PartDetail],
    response_model_exclude_none=True,
)
def delete_manufacturer_ref(mfr_ref_id: str):
    """Supprime une référence fabricant"""
    repo = PartRepository()
    return single(repo.delete_manufacturer_ref(mfr_ref_id))


@router.post(
    "/manufacturer-refs/{mfr_ref_id}/set-preferred",
    response_model=SingleResponse[PartDetail],
    response_model_exclude_none=True,
)
def set_preferred_manufacturer_ref(mfr_ref_id: str):
    """Définit une référence fabricant comme préférée"""
    repo = PartRepository()
    return single(repo.set_preferred_manufacturer_ref(mfr_ref_id))


@router.post(
    "/manufacturer-refs/{mfr_ref_id}/supplier-refs",
    response_model=SingleResponse[PartDetail],
    status_code=201,
    response_model_exclude_none=True,
)
def add_supplier_ref(mfr_ref_id: str, data: PartSupplierRefCreate):
    """Ajoute une référence fournisseur à une référence fabricant"""
    repo = PartRepository()
    return single(repo.add_supplier_ref(mfr_ref_id, data.model_dump()))


@router.patch(
    "/supplier-refs/{supplier_ref_id}",
    response_model=SingleResponse[PartDetail],
    response_model_exclude_none=True,
)
def update_supplier_ref(supplier_ref_id: str, data: PartSupplierRefUpdate):
    """Met à jour une référence fournisseur (modification partielle)"""
    repo = PartRepository()
    return single(repo.update_supplier_ref(supplier_ref_id, data.model_dump(exclude_unset=True)))


@router.post(
    "/supplier-refs/{supplier_ref_id}/set-preferred",
    response_model=SingleResponse[PartDetail],
    response_model_exclude_none=True,
)
def set_preferred_supplier_ref(supplier_ref_id: str):
    """Définit une référence fournisseur comme préférée"""
    repo = PartRepository()
    return single(repo.set_preferred_supplier_ref(supplier_ref_id))


@router.delete(
    "/supplier-refs/{supplier_ref_id}",
    response_model=SingleResponse[PartDetail],
    response_model_exclude_none=True,
)
def delete_supplier_ref(supplier_ref_id: str):
    """Supprime une référence fournisseur"""
    repo = PartRepository()
    return single(repo.delete_supplier_ref(supplier_ref_id))
