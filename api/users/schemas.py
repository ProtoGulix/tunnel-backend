from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
import re


class UserListItem(BaseModel):
    """Schema léger pour listes d'utilisateurs"""
    id: UUID
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    initial: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    role: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    """Schema complet pour détail utilisateur"""
    id: UUID
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    initial: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    role: Optional[str] = Field(default=None)
    last_access: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    """Mise à jour du profil : prénom, nom, initiales"""
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    initial: Optional[str] = Field(default=None, max_length=5)

    @field_validator("initial")
    @classmethod
    def initial_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{1,5}$", v):
            raise ValueError("Les initiales doivent être des lettres uniquement (1 à 5 caractères)")
        return v


class PasswordChange(BaseModel):
    """Changement de mot de passe"""
    current_password: str = Field(..., max_length=256)
    new_password: str = Field(..., min_length=8, max_length=256)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r"[0-9]", v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v
