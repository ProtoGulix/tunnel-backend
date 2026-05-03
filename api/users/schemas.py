from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


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
