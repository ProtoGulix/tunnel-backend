from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ApiKeyCreate(BaseModel):
    """Payload de création d'une clé d'API."""
    name: str


class ApiKeyCreated(BaseModel):
    """Réponse unique à la création — contient le secret brut (une seule fois)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    key_prefix: str
    secret: str  # Retourné une seule fois, jamais stocké
    role_code: str
    created_at: datetime


class ApiKeyListItem(BaseModel):
    """Clé d'API dans la liste — sans secret ni hash."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    key_prefix: str
    role_code: str
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime


class ApiKeyPatch(BaseModel):
    """Modification partielle d'une clé d'API."""
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
