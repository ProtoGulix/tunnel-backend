from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from api.parts.repo import PartRepository
from api.parts.schemas import (
    PartCreate, PartDetail, PartListItem, PartManufacturerRefCreate,
    PartSupplierRefCreate, PartUpdate,
)
from api.auth.permissions import require_authenticated
from api.utils.response import paginated, single

router = APIRouter(
    prefix="/parts",
    tags=["parts"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("", response_model=List[PartListItem])
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


@router.get("/ref/{internal_ref}", response_model=PartDetail)
def get_part_by_ref(internal_ref: str):
    """Récupère une pièce par sa référence interne (ex: P000042)"""
    repo = PartRepository()
    return single(repo.get_by_internal_ref(internal_ref))


@router.get("/{part_id}", response_model=PartDetail)
def get_part(part_id: str):
    """Récupère une pièce par ID avec toutes ses références"""
    repo = PartRepository()
    return single(repo.get_by_id(part_id))


@router.post("", response_model=PartDetail, status_code=201)
def create_part(data: PartCreate):
    """Crée une nouvelle pièce (internal_ref P000001 générée automatiquement)"""
    repo = PartRepository()
    return single(repo.create(data.model_dump()))


@router.patch("/{part_id}", response_model=PartDetail)
def update_part(part_id: str, data: PartUpdate):
    """Met à jour une pièce (modification partielle)"""
    repo = PartRepository()
    return single(repo.update(part_id, data.model_dump(exclude_unset=True)))


@router.post("/{part_id}/manufacturer-refs", response_model=PartDetail, status_code=201)
def add_manufacturer_ref(part_id: str, data: PartManufacturerRefCreate):
    """Ajoute une référence fabricant à une pièce"""
    repo = PartRepository()
    return single(repo.add_manufacturer_ref(part_id, data.model_dump()))


@router.post(
    "/{part_id}/manufacturer-refs/{mfr_ref_id}/supplier-refs",
    response_model=PartDetail,
    status_code=201,
)
def add_supplier_ref(part_id: str, mfr_ref_id: str, data: PartSupplierRefCreate):
    """Ajoute une référence fournisseur à une référence fabricant"""
    repo = PartRepository()
    return single(repo.add_supplier_ref(part_id, mfr_ref_id, data.model_dump()))
