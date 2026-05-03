import logging
from typing import List

from fastapi import APIRouter, Depends, Request, status

from api.api_keys.repo import ApiKeyRepository
from api.api_keys.schemas import ApiKeyCreate, ApiKeyCreated, ApiKeyListItem, ApiKeyPatch
from api.auth.permissions import require_role
from api.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api-keys", tags=["api-keys"])

_admin_only = Depends(require_role("ADMIN"))


@router.get("", response_model=List[ApiKeyListItem], dependencies=[_admin_only])
def list_api_keys():
    return ApiKeyRepository().get_all()


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED,
             dependencies=[_admin_only])
@limiter.limit("20/minute")
def create_api_key(request: Request, payload: ApiKeyCreate):
    """Crée une clé d'API MCP. Le secret brut est retourné une seule fois."""
    created_by = str(getattr(request.state, "user_id", None) or "")
    return ApiKeyRepository().create(
        name=payload.name,
        created_by=created_by or None,
    )


@router.patch("/{key_id}", response_model=ApiKeyListItem, dependencies=[_admin_only])
def update_api_key(key_id: str, payload: ApiKeyPatch):
    return ApiKeyRepository().update(
        key_id=key_id,
        is_active=payload.is_active,
        expires_at=payload.expires_at,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[_admin_only])
def delete_api_key(key_id: str):
    ApiKeyRepository().delete(key_id)
