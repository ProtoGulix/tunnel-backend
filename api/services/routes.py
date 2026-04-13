"""Routes API pour les services"""
from fastapi import APIRouter, status, Depends

from .schemas import ServiceOut, ServiceCreate, ServiceUpdate
from .repo import ServiceRepository

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/services",
                   tags=["services"], dependencies=[Depends(require_authenticated)])
repo = ServiceRepository()


@router.get("", response_model=list[ServiceOut])
def list_services():
    """Liste tous les services actifs"""
    return repo.get_all()


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: str):
    """Récupère un service par ID"""
    return repo.get_by_id(service_id)


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(data: ServiceCreate):
    """Crée un nouveau service"""
    return repo.create(
        code=data.code,
        label=data.label,
        is_active=data.is_active
    )


@router.patch("/{service_id}", response_model=ServiceOut)
def update_service(service_id: str, data: ServiceUpdate):
    """
    Met à jour un service

    Seuls `label` et `is_active` peuvent être modifiés.
    Le `code` est immuable et ne peut pas être changé.
    """
    return repo.update(
        service_id=service_id,
        label=data.label,
        is_active=data.is_active
    )
