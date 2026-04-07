from fastapi import APIRouter, HTTPException, Depends
from typing import List

from api.stock_sub_families.repo import StockSubFamilyRepository
from api.stock_sub_families.schemas import StockSubFamilyCreate, StockSubFamilyCreateInFamily, StockSubFamilyUpdate
from api.stock_items.template_schemas import StockSubFamily
from api.errors.exceptions import DatabaseError, NotFoundError, ValidationError

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/stock-sub-families",
                   tags=["stock-sub-families"], dependencies=[Depends(require_authenticated)])


@router.get("", response_model=List[StockSubFamily])
def list_stock_sub_families():
    """
    Liste toutes les sous-familles avec leurs templates associés

    Retourne :
    - Données de la sous-famille
    - Template complet avec fields et enum_values si existant
    - template = null si la sous-famille n'a pas de template
    """
    repo = StockSubFamilyRepository()
    return repo.get_all_with_templates()


@router.post("", response_model=StockSubFamily, status_code=201)
def create_stock_sub_family(data: StockSubFamilyCreate):
    """Crée une nouvelle sous-famille de stock (family_code dans le body)"""
    repo = StockSubFamilyRepository()
    return repo.create(
        family_code=data.family_code,
        code=data.code,
        label=data.label,
        template_id=data.template_id
    )


@router.post("/{family_code}", response_model=StockSubFamily, status_code=201)
def create_stock_sub_family_in_family(family_code: str, data: StockSubFamilyCreateInFamily):
    """Crée une nouvelle sous-famille sous la famille donnée dans l'URL"""
    repo = StockSubFamilyRepository()
    return repo.create(
        family_code=family_code,
        code=data.code,
        label=data.label,
        template_id=data.template_id
    )


@router.get("/{family_code}/{sub_family_code}", response_model=StockSubFamily)
def get_stock_sub_family(family_code: str, sub_family_code: str):
    """
    Récupère une sous-famille par ses codes avec son template associé
    """
    repo = StockSubFamilyRepository()
    return repo.get_by_codes_with_template(family_code, sub_family_code)


@router.patch("/{family_code}/{sub_family_code}", response_model=StockSubFamily)
def update_stock_sub_family(
    family_code: str,
    sub_family_code: str,
    data: StockSubFamilyUpdate
):
    """
    Met à jour une sous-famille de stock

    Champs modifiables :
    - label : libellé de la sous-famille
    - template_id : UUID du template à associer (null pour dissocier)
    """
    repo = StockSubFamilyRepository()
    return repo.update(
        family_code=family_code,
        sub_family_code=sub_family_code,
        label=data.label,
        template_id=data.template_id
    )
