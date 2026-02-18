from fastapi import APIRouter, HTTPException
from typing import List

from api.stock_sub_families.repo import StockSubFamilyRepository
from api.stock_sub_families.schemas import StockSubFamilyUpdate
from api.stock_items.template_schemas import StockSubFamily
from api.errors.exceptions import DatabaseError

router = APIRouter(prefix="/stock-sub-families", tags=["stock-sub-families"])


@router.get("/", response_model=List[StockSubFamily])
async def list_stock_sub_families():
    """
    Liste toutes les sous-familles avec leurs templates associés

    Retourne :
    - Données de la sous-famille
    - Template complet avec fields et enum_values si existant
    - template = null si la sous-famille n'a pas de template
    """
    repo = StockSubFamilyRepository()
    try:
        return repo.get_all_with_templates()
    except (DatabaseError, Exception) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{family_code}/{sub_family_code}", response_model=StockSubFamily)
async def get_stock_sub_family(family_code: str, sub_family_code: str):
    """
    Récupère une sous-famille par ses codes avec son template associé
    """
    repo = StockSubFamilyRepository()
    try:
        return repo.get_by_codes_with_template(family_code, sub_family_code)
    except DatabaseError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{family_code}/{sub_family_code}", response_model=StockSubFamily)
async def update_stock_sub_family(
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
    try:
        return repo.update(
            family_code=family_code,
            sub_family_code=sub_family_code,
            label=data.label,
            template_id=data.template_id
        )
    except DatabaseError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
