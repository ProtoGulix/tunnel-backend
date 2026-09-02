from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class HomeViewRef(BaseModel):
    """Référentiel des vues d'accueil disponibles (home_view_ref)."""
    model_config = ConfigDict(from_attributes=True)
    code: str
    label: str


class CurrentHomeViewOut(BaseModel):
    """Vue d'accueil assignée à l'utilisateur courant.
    `code` vaut toujours une valeur du référentiel — 'technicien' par défaut
    quand le rôle de l'utilisateur n'a pas de configuration explicite.
    """
    code: str
    label: str


class RoleHomeViewOut(BaseModel):
    """Une ligne d'assignation rôle → vue d'accueil."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role_id: UUID
    role_code: str
    role_label: str
    home_view: str
    home_view_label: Optional[str] = None
    updated_at: datetime
    updated_by: Optional[UUID] = None


class RoleHomeViewUpsert(BaseModel):
    """PUT admin : assigne (ou remplace) la vue d'accueil d'un rôle."""
    home_view: str
