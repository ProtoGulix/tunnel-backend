from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


class UserListItem(BaseModel):
    """Schema léger pour listes d'utilisateurs"""
    id: UUID
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    initial: Optional[str] = Field(default=None)
    status: str = Field(default="active")
    role: Optional[UUID] = Field(default=None)

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    """Schema complet pour détail utilisateur"""
    id: UUID
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    tags: Optional[Any] = Field(default=None)
    avatar: Optional[UUID] = Field(default=None)
    status: str = Field(default="active")
    role: Optional[UUID] = Field(default=None)
    initial: Optional[str] = Field(default=None)
    last_access: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True
