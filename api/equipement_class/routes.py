"""Routes API pour les classes d'équipement"""
from fastapi import APIRouter, status

from .schemas import EquipementClass, EquipementClassCreate, EquipementClassUpdate
from .repo import EquipementClassRepository

router = APIRouter(prefix="/equipement-class", tags=["equipement-class"])
repo = EquipementClassRepository()


@router.get("", response_model=list[EquipementClass])
@router.get("/", response_model=list[EquipementClass])
async def list_equipement_classes():
    """Liste toutes les classes d'équipement"""
    return repo.get_all()


@router.get("/{class_id}", response_model=EquipementClass)
async def get_equipement_class(class_id: str):
    """Récupère une classe d'équipement par ID"""
    return repo.get_by_id(class_id)


@router.post("", response_model=EquipementClass, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=EquipementClass, status_code=status.HTTP_201_CREATED)
async def create_equipement_class(data: EquipementClassCreate):
    """Crée une nouvelle classe d'équipement"""
    return repo.create(
        code=data.code,
        label=data.label,
        description=data.description
    )


@router.patch("/{class_id}", response_model=EquipementClass)
async def update_equipement_class(class_id: str, data: EquipementClassUpdate):
    """Met à jour une classe d'équipement"""
    return repo.update(
        class_id=class_id,
        code=data.code,
        label=data.label,
        description=data.description
    )


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipement_class(class_id: str):
    """Supprime une classe d'équipement"""
    repo.delete(class_id)
    return None
